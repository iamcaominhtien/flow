"""Route the lines of a flowchart as horizontal and vertical segments, and place their labels.

A forward line runs straight when it can, in an L-shape when its ends are in different
columns, and around the flow when a node is in the way. A returning line always runs around
the flow, in a channel outside the nodes.
"""

import math
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import pairwise

from .forks import is_inside
from .html_nodes import CAPTION_WIDTH_PX
from .layered import Grid
from .model import SYMBOL_HEADS, Direction, Edge, EdgeLabel, LabelKind, Node, Point, Role, Shape
from .pathfind import SearchSpace, find_route
from .placement import Placement
from .spec import Spec, SpecEdge
from .theme import LayoutRules, load_theme

END_LABEL_ALONG_PX = 24.0  # distance of an end label from the end of its line
END_LABEL_ACROSS_PX = 12.0  # and how far it sits to the side of the line
BUS_ABOVE_TARGET_PX = 28.0  # a line between columns turns this far above its target
BUS_BELOW_SOURCE_PX = 12.0  # but never closer than this to the bottom of its source
SAME_LINE_TOLERANCE_PX = 1.0  # two centres closer than this count as on one line
CLEARANCE_PX = 4.0  # how far a line must stay from a node it passes
SEARCH_MARGIN_PX = 12.0  # how far a searched route keeps from every box
MULTIWAY_EXITS = 3  # a decision with this many exits fans them out
STUB_PX = 16.0  # a searched route leaves a box straight for this far before it may turn
PORT_REUSE_COST_PX = 60.0  # a searched route prefers a side of a box that is still free


class Port(StrEnum):
    """A side of a node where a line can attach."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


ANSWER_KINDS = {"yes": LabelKind.YES, "no": LabelKind.NO}  # a Yes or No chip keeps its colour
LABEL_KIND_OF_ROLE = {Role.YES: LabelKind.YES, Role.NO: LabelKind.NO, Role.BACK: LabelKind.BACK}


@dataclass(frozen=True)
class _Route:
    """A routed line: its points, the ports at both ends, and the channel it uses (if any)."""

    points: list[Point]
    leaves: Port
    arrives: Port
    channel: Port | None


@dataclass
class _Context:
    """What the router needs while it works: the nodes, the rules, and what is taken."""

    nodes: dict[str, Node]
    rules: LayoutRules
    used_ports: set[tuple[str, Port]]
    channels_used: dict[Port, int]
    caption_port: Port = Port.BOTTOM
    slots: dict[SpecEdge, tuple[float, float]] = field(default_factory=dict)
    lines: list[tuple[Point, Point]] = field(default_factory=list)


def _attach(node: Node, port: Port, caption_port: Port = Port.BOTTOM) -> Point:
    """Return the point in the middle of one side of a node.

    Args:
        node: The node.
        port: The side.
        caption_port: The side the caption hangs from: the bottom of the page, which is the right
            of the node when the layout is transposed. A line leaves that side beyond the caption.

    Returns:
        The attach point.
    """
    reach = load_theme().layout.caption_height if node.caption and port is caption_port else 0.0
    center_x, center_y = node.x + node.width / 2, node.y + node.height / 2
    return {
        Port.TOP: (center_x, node.y),
        Port.BOTTOM: (center_x, node.y + node.height + reach),
        Port.LEFT: (node.x, center_y),
        Port.RIGHT: (node.x + node.width + reach, center_y),
    }[port]


def _caption_box(node: Node, caption_port: Port) -> tuple[float, float, float, float] | None:
    """Return the box a caption covers, as left, top, right, bottom, in layout space."""
    if not node.caption:
        return None
    reach = load_theme().layout.caption_height
    half = CAPTION_WIDTH_PX / 2
    if caption_port is Port.RIGHT:
        center_y = node.y + node.height / 2
        return (node.x + node.width, center_y - half, node.x + node.width + reach, center_y + half)
    center_x = node.x + node.width / 2
    return (center_x - half, node.y + node.height, center_x + half, node.y + node.height + reach)


def _hits(node: Node, start: Point, end: Point) -> bool:
    """Tell whether an horizontal or vertical segment passes through a node, with clearance."""
    low_x, high_x = sorted((start[0], end[0]))
    low_y, high_y = sorted((start[1], end[1]))
    return (
        low_x < node.x + node.width + CLEARANCE_PX
        and high_x > node.x - CLEARANCE_PX
        and low_y < node.y + node.height + CLEARANCE_PX
        and high_y > node.y - CLEARANCE_PX
    )


def _hits_caption(node: Node, start: Point, end: Point, caption_port: Port) -> bool:
    """Tell whether a segment passes over the caption of a node."""
    box = _caption_box(node, caption_port)
    if box is None:
        return False
    low_x, high_x = sorted((start[0], end[0]))
    low_y, high_y = sorted((start[1], end[1]))
    left, top, right, bottom = box
    return low_x < right and high_x > left and low_y < bottom and high_y > top


def _is_clear(points: list[Point], context: _Context, ends: tuple[str, str]) -> bool:
    """Tell whether a route stays away from every node it passes.

    The first segment may touch the source and the last segment may touch the target, because
    that is where the line attaches; any other contact with them counts as passing through.

    Args:
        points: The route.
        context: The router state.
        ends: The ids of the source and the target.

    Returns:
        True when the route passes through no node.
    """
    source_id, target_id = ends
    last = len(points) - 2
    for index, (start, end) in enumerate(pairwise(points)):
        for node_id, node in context.nodes.items():
            attaches = (node_id == source_id and index == 0) or (
                node_id == target_id and index == last
            )
            if not attaches and _hits(node, start, end):
                return False
            if _hits_caption(node, start, end, context.caption_port):
                return False
    return True


def _center(node: Node) -> Point:
    """Return the centre of a node."""
    return node.x + node.width / 2, node.y + node.height / 2


def _goes_down(source: Node, target: Node) -> bool:
    """Tell whether a line between two nodes runs from one row to a lower one."""
    return _center(target)[1] - _center(source)[1] > SAME_LINE_TOLERANCE_PX


def _spread(positions: list[tuple[SpecEdge, float]], node: Node) -> dict[SpecEdge, float]:
    """Spread the points where several lines meet one side of a node, in the order of ``positions``.

    Args:
        positions: The edges and the x of their far end, in any order.
        node: The node whose side the lines meet.

    Returns:
        Edge to the x where it meets the node: the middle for a single line, otherwise evenly
        spaced across the width and ordered like the far ends, so that the lines do not cross.
    """
    ordered = sorted(positions, key=lambda item: item[1])
    count = len(ordered)
    return {
        edge: node.x + node.width * (index + 1) / (count + 1) if count > 1 else _center(node)[0]
        for index, (edge, _) in enumerate(ordered)
    }


def _centered(positions: list[tuple[SpecEdge, float]], node: Node) -> dict[SpecEdge, float]:
    """Meet the middle of a side of a node with every line, so that lines that merge share it."""
    return {edge: _center(node)[0] for edge, _ in positions}


def _leaves_by_side(edge: SpecEdge, down: list[SpecEdge], nodes: dict[str, Node]) -> bool:
    """Tell whether a dashed line should leave the side of its source, not share the bottom.

    A dashed line (a message) that would share the bottom of a node with a solid line goes to
    the side instead, so that the two kinds are not drawn on top of each other.
    """
    if not edge.dashed:
        return False
    source_x, target_x = _center(nodes[edge.source])[0], _center(nodes[edge.target])[0]
    if abs(source_x - target_x) < SAME_LINE_TOLERANCE_PX:
        return False
    return any(other.source == edge.source and not other.dashed for other in down)


def _fanned(edges: list[SpecEdge], nodes: dict[str, Node]) -> set[SpecEdge]:
    """Pick the exits of a multi-way decision that leave by a side of the diamond.

    A decision with three or more exits fans them out: the middle one leaves the bottom and the
    others leave the left and the right, each by its own corner of the diamond.
    """
    exits: dict[str, list[SpecEdge]] = {}
    for edge in edges:
        if nodes[edge.source].shape is Shape.DECISION:
            exits.setdefault(edge.source, []).append(edge)
    return {
        edge
        for group in exits.values()
        if len(group) >= MULTIWAY_EXITS
        for edge in group
        if abs(_center(nodes[edge.target])[0] - _center(nodes[edge.source])[0])
        > SAME_LINE_TOLERANCE_PX
    }


def _slots(edges: list[SpecEdge], nodes: dict[str, Node]) -> dict[SpecEdge, tuple[float, float]]:
    """Choose where each downward line leaves its source and where it enters its target.

    Args:
        edges: The forward edges.
        nodes: The placed nodes.

    Returns:
        Edge to ``(exit x, entry x)``, only for lines that run to a lower row.
    """
    down = [e for e in edges if _goes_down(nodes[e.source], nodes[e.target])]
    down = [e for e in down if not _leaves_by_side(e, down, nodes)]
    down = [e for e in down if e not in _fanned(edges, nodes)]
    leaving: dict[str, list[tuple[SpecEdge, float]]] = {}
    arriving: dict[str, list[tuple[SpecEdge, float]]] = {}
    for edge in down:
        leaving.setdefault(edge.source, []).append((edge, _center(nodes[edge.target])[0]))
        arriving.setdefault(edge.target, []).append((edge, _center(nodes[edge.source])[0]))
    exit_x: dict[SpecEdge, float] = {}
    entry_x: dict[SpecEdge, float] = {}
    for name, group in leaving.items():
        needs_room = any(edge.tail in SYMBOL_HEADS for edge, _ in group)
        exit_x.update(_spread(group, nodes[name]) if needs_room else _centered(group, nodes[name]))
    for name, group in arriving.items():
        needs_room = any(edge.head in SYMBOL_HEADS for edge, _ in group)
        entry_x.update(_spread(group, nodes[name]) if needs_room else _centered(group, nodes[name]))
    return _pin_to_bars(down, nodes, exit_x, entry_x)


def _pin_to_bars(
    down: list[SpecEdge],
    nodes: dict[str, Node],
    exit_x: dict[SpecEdge, float],
    entry_x: dict[SpecEdge, float],
) -> dict[SpecEdge, tuple[float, float]]:
    """Make each line that meets a split or join bar drop straight from, or onto, the bar.

    A line at the far end of the bar's reach has no place on it; it leaves by the end of the bar
    and is routed without a slot.

    Args:
        down: The lines that run to a lower row.
        nodes: The placed nodes.
        exit_x: Where each line leaves its source, by default.
        entry_x: Where each line enters its target, by default.

    Returns:
        Edge to ``(exit x, entry x)``.
    """
    slots = {}
    for edge in down:
        source, target = nodes[edge.source], nodes[edge.target]
        leave, enter = exit_x[edge], entry_x[edge]
        if source.shape is Shape.FORK:
            leave = enter = _center(target)[0]
        elif target.shape is Shape.FORK:
            leave = enter = _center(source)[0]
        bar = source if source.shape is Shape.FORK else target
        if bar.shape is Shape.FORK and not is_inside(bar, leave):
            continue
        slots[edge] = (leave, enter)
    return slots


def _forward_points(
    source: Node, target: Node, slot: tuple[float, float] | None, caption_port: Port
) -> tuple[list[Point], Port]:
    """Return the direct route between two nodes and the port it leaves from.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        slot: Where the line leaves the bottom of the source and enters the top of the target,
            when it runs to a lower row.
        caption_port: The side the captions hang from.

    Returns:
        The points, and the port of the source that the line leaves from.
    """
    (source_x, source_y), (target_x, target_y) = _center(source), _center(target)
    same_row = abs(source_y - target_y) < SAME_LINE_TOLERANCE_PX
    if slot is not None and not (source.shape is Shape.DECISION and source_x != slot[0]):
        exit_x, entry_x = slot
        start, end = (exit_x, _attach(source, Port.BOTTOM, caption_port)[1]), (entry_x, target.y)
        if abs(exit_x - entry_x) < SAME_LINE_TOLERANCE_PX:
            return [start, end], Port.BOTTOM
        bus_y = max(start[1] + BUS_BELOW_SOURCE_PX, end[1] - BUS_ABOVE_TARGET_PX)
        return [start, (exit_x, bus_y), (entry_x, bus_y), end], Port.BOTTOM
    leaving = Port.RIGHT if target_x > source_x else Port.LEFT
    if same_row:
        arriving = Port.LEFT if leaving is Port.RIGHT else Port.RIGHT
        return [
            _attach(source, leaving, caption_port),
            _attach(target, arriving, caption_port),
        ], leaving
    corner = (target_x, source_y)
    return [_attach(source, leaving, caption_port), corner, _attach(target, Port.TOP)], leaving


def _peek_channel_x(side: Port, rows: tuple[float, float], context: _Context) -> float:
    """Return the x of the next free vertical channel on one side of the flow.

    Args:
        side: ``RIGHT`` for a channel to the right of the nodes, ``LEFT`` for the left.
        rows: The top and bottom y of the stretch the line has to travel.
        context: The router state; it is not changed.

    Returns:
        The x of the channel.
    """
    top, bottom = rows
    spanned = [n for n in context.nodes.values() if n.y < bottom and n.y + n.height > top]
    index = context.channels_used.get(side, 0)
    distance = context.rules.channel_offset + context.rules.channel_step * index
    if side is Port.RIGHT:
        return max(node.x + node.width for node in spanned) + distance
    return min(node.x for node in spanned) - distance


def _channel_route(source: Node, target: Node, side: Port, context: _Context) -> _Route:
    """Build a route that leaves one side of the source, runs in a channel, and enters the target.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        side: ``RIGHT`` or ``LEFT``; both ends attach to that side.
        context: The router state.

    Returns:
        The route.
    """
    start = _attach(source, side, context.caption_port)
    end = _attach(target, side, context.caption_port)
    channel = _peek_channel_x(side, (min(start[1], end[1]), max(start[1], end[1])), context)
    points = [start, (channel, start[1]), (channel, end[1]), end]
    return _Route(points, leaves=side, arrives=side, channel=side)


def _arc_route(source: Node, target: Node, side: Port, context: _Context) -> _Route:
    """Build a route that leaves one side of the source, arcs over or under the flow, and enters.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        side: ``TOP`` to arc over the flow, ``BOTTOM`` to arc under it; both ends attach there.
        context: The router state.

    Returns:
        The route; it needs no channel.
    """
    start = _attach(source, side, context.caption_port)
    end = _attach(target, side, context.caption_port)
    offset = context.rules.channel_offset
    ridge = min(start[1], end[1]) - offset if side is Port.TOP else max(start[1], end[1]) + offset
    points = [start, (start[0], ridge), (end[0], ridge), end]
    return _Route(points, leaves=side, arrives=side, channel=None)


def _returning_route(source: Node, target: Node, context: _Context) -> _Route:
    """Choose the route of a line that loops back to an earlier step.

    The candidates are tried in order: a channel on the right, a channel on the left, an arc
    over the top, and an arc under the bottom. The first one that is clear of other nodes and
    uses ports that are still free wins; failing that, the first clear one; failing that, the
    first.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        context: The router state; the winning channel is marked as used.

    Returns:
        The chosen route.
    """
    candidates = [
        _channel_route(source, target, Port.RIGHT, context),
        _channel_route(source, target, Port.LEFT, context),
        _arc_route(source, target, Port.TOP, context),
        _arc_route(source, target, Port.BOTTOM, context),
    ]
    ends = (source.id, target.id)
    clear = [route for route in candidates if _is_clear(route.points, context, ends)]
    free = [
        route
        for route in clear
        if (source.id, route.leaves) not in context.used_ports
        and (target.id, route.arrives) not in context.used_ports
    ]
    chosen = (free or clear or candidates)[0]
    if chosen.channel is not None:
        context.channels_used[chosen.channel] = context.channels_used.get(chosen.channel, 0) + 1
    context.used_ports.add((target.id, chosen.arrives))
    return chosen


def _segment_length(segment: tuple[Point, Point]) -> float:
    """Return the length of a horizontal or vertical segment."""
    (start_x, start_y), (end_x, end_y) = segment
    return abs(end_x - start_x) + abs(end_y - start_y)


def _label_at(points: list[Point], role: Role, rules: LayoutRules) -> Point:
    """Choose where a label sits: on its line, or beside it when the line is vertical.

    Args:
        points: The route.
        role: The line role; a returning line has its label centred on the line.
        rules: The layout rules.

    Returns:
        The centre of the label chip.
    """
    start, end = max(pairwise(points), key=_segment_length)
    middle = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    is_vertical = abs(start[0] - end[0]) < SAME_LINE_TOLERANCE_PX
    if is_vertical and role is not Role.BACK:
        return middle[0] + rules.label_offset, middle[1]
    return middle


def _label_kind(spec_edge: SpecEdge) -> LabelKind:
    """Choose the colour of a label: by the role of its line, else by a Yes or No it says."""
    named = LABEL_KIND_OF_ROLE.get(spec_edge.role)
    if named is not None:
        return named
    answer = (spec_edge.label or "").strip().lower()
    return ANSWER_KINDS.get(answer, LabelKind.PLAIN)


def _end_labels(spec_edge: SpecEdge, points: list[Point]) -> tuple[EdgeLabel, ...]:
    """Build the small labels at the two ends of a line, such as multiplicities."""
    found = []
    for text, near, toward in (
        (spec_edge.start_label, points[0], points[1]),
        (spec_edge.end_label, points[-1], points[-2]),
    ):
        if text:
            length = max(math.dist(near, toward), 1.0)
            along = (toward[0] - near[0]) / length
            across = (toward[1] - near[1]) / length
            at = (
                near[0] + along * END_LABEL_ALONG_PX - across * END_LABEL_ACROSS_PX,
                near[1] + across * END_LABEL_ALONG_PX + along * END_LABEL_ACROSS_PX,
            )
            found.append(EdgeLabel(text=text, at=at, kind=LabelKind.TEXT))
    return tuple(found)


OUTWARD = {
    Port.TOP: (0.0, -1.0),
    Port.BOTTOM: (0.0, 1.0),
    Port.LEFT: (-1.0, 0.0),
    Port.RIGHT: (1.0, 0.0),
}


def _obstacles(context: _Context) -> tuple[tuple[float, float, float, float], ...]:
    """Return every node and every caption as a box grown by the search margin."""
    boxes = []
    for node in context.nodes.values():
        left, top, right, bottom = node.x, node.y, node.x + node.width, node.y + node.height
        boxes.append((left, top, right, bottom))
        caption = _caption_box(node, context.caption_port)
        if caption is not None:
            boxes.append(caption)
    return tuple(
        (
            left - SEARCH_MARGIN_PX,
            top - SEARCH_MARGIN_PX,
            right + SEARCH_MARGIN_PX,
            bottom + SEARCH_MARGIN_PX,
        )
        for left, top, right, bottom in boxes
    )


def _stub(node: Node, port: Port, caption_port: Port) -> Point:
    """Return the point just outside a node, straight out from one of its sides."""
    x, y = _attach(node, port, caption_port)
    out_x, out_y = OUTWARD[port]
    return (x + out_x * STUB_PX, y + out_y * STUB_PX)


def _facing(source: Node, target: Node) -> list[Port]:
    """Return the sides of a node that look towards another node."""
    (source_x, source_y), (target_x, target_y) = _center(source), _center(target)
    delta = (target_x - source_x, target_y - source_y)
    return [
        port
        for port, (out_x, out_y) in OUTWARD.items()
        if out_x * delta[0] + out_y * delta[1] > SAME_LINE_TOLERANCE_PX
    ]


def _search_route(source: Node, target: Node, context: _Context) -> _Route | None:
    """Search for a route around the boxes and the lines already drawn.

    The sides that face the other node are tried first; every side is tried only when those
    find no route, because each pair of sides costs a search.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        context: The router state; it is not changed.

    Returns:
        The cheapest route found, or None when no pair of sides can be joined.
    """
    space = SearchSpace(_obstacles(context), tuple(context.lines))
    pairs = [
        (leave, arrive) for leave in _facing(source, target) for arrive in _facing(target, source)
    ]
    best = _best_of(pairs, (source, target), space, context)
    if best is None:
        pairs = [(leave, arrive) for leave in Port for arrive in Port]
        best = _best_of(pairs, (source, target), space, context)
    return None if best is None else best[1]


def _best_of(
    pairs: list[tuple[Port, Port]],
    ends: tuple[Node, Node],
    space: SearchSpace,
    context: _Context,
) -> tuple[float, _Route] | None:
    """Search each pair of sides and return the cheapest route with its cost, or None."""
    source, target = ends
    best: tuple[float, _Route] | None = None
    for leave, arrive in pairs:
        found = find_route(
            space,
            _stub(source, leave, context.caption_port),
            _stub(target, arrive, context.caption_port),
        )
        if found is None:
            continue
        cost = found.cost + _reuse_cost(source, target, (leave, arrive), context)
        points = [
            _attach(source, leave, context.caption_port),
            *found.points,
            _attach(target, arrive, context.caption_port),
        ]
        if best is None or cost < best[0]:
            best = (cost, _Route(points, leaves=leave, arrives=arrive, channel=None))
    return best


def _reuse_cost(source: Node, target: Node, ports: tuple[Port, Port], context: _Context) -> float:
    """Return the extra cost of attaching to a side of a box that another line already uses."""
    leave, arrive = ports
    used = (source.id, leave) in context.used_ports, (target.id, arrive) in context.used_ports
    return PORT_REUSE_COST_PX * sum(used)


def _route_one(spec_edge: SpecEdge, returning: bool, context: _Context) -> list[Point]:
    """Route one edge, registering the ports it uses.

    Args:
        spec_edge: The edge to route.
        returning: Whether the edge loops back, which forces a route around the flow.
        context: The router state.

    Returns:
        The points of the route.
    """
    source, target = context.nodes[spec_edge.source], context.nodes[spec_edge.target]
    points, port = _forward_points(
        source, target, context.slots.get(spec_edge), context.caption_port
    )
    route = _Route(points, leaves=port, arrives=Port.TOP, channel=None)
    if returning:
        route = _returning_route(source, target, context)
    elif not _is_clear(points, context, (source.id, target.id)):
        route = _search_route(source, target, context) or _returning_route(source, target, context)
    context.used_ports.add((source.id, route.leaves))
    context.used_ports.add((target.id, route.arrives))
    context.lines.extend(pairwise(route.points))
    return route.points


def route_across(
    nodes: dict[str, Node], ends: tuple[str, str], lines: list[tuple[Point, Point]], port: Port
) -> list[Point]:
    """Route one line between two placed nodes by searching around every box.

    Used when nodes have been moved after the first routing, so a line has to be drawn again.

    Args:
        nodes: Every node at its final place.
        ends: The ids of the source and the target.
        lines: The segments already drawn, which the route should avoid.
        port: The side the captions hang from.

    Returns:
        The points of the route; a plain right-angled path when the search finds none.
    """
    rules = load_theme().layout
    context = _Context(nodes, rules, set(), {}, port)
    context.lines.extend(lines)
    source, target = nodes[ends[0]], nodes[ends[1]]
    route = _search_route(source, target, context)
    if route is not None:
        return route.points
    start, end = _center(source), _center(target)
    return [start, (start[0], end[1]), end]


def route_edges(spec: Spec, grid: Grid, placement: Placement, rules: LayoutRules) -> list[Edge]:
    """Route every edge of a flowchart and place its label.

    Args:
        spec: The flowchart description.
        grid: Which edges go forward and which return.
        placement: The nodes at their pixel positions.
        rules: The layout rules.

    Returns:
        One scene edge per spec edge, in spec order. Forward edges are routed first so that
        the returning ones take the ports that are left.
    """
    caption_port = Port.RIGHT if spec.direction is Direction.RIGHT else Port.BOTTOM
    context = _Context(placement.nodes, rules, set(), {}, caption_port)
    returning = set(grid.returning)
    context.slots = _slots(list(grid.forward), placement.nodes)
    order = sorted(spec.edges, key=lambda edge: edge in returning)
    routed = {edge: _route_one(edge, edge in returning, context) for edge in order}
    edges = []
    for index, spec_edge in enumerate(spec.edges, start=1):
        points = routed[spec_edge]
        label = None
        if spec_edge.label:
            at = _label_at(points, spec_edge.role, rules)
            kind = _label_kind(spec_edge)
            label = EdgeLabel(text=spec_edge.label, at=at, kind=kind)
        edges.append(
            Edge(
                id=f"e{index}",
                role=spec_edge.role,
                points=tuple(points),
                label=label,
                source=spec_edge.source,
                target=spec_edge.target,
                head=spec_edge.head,
                tail=spec_edge.tail,
                dashed=spec_edge.dashed,
                extras=_end_labels(spec_edge, points),
            )
        )
    return edges
