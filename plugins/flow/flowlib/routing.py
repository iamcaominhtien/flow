"""Route the lines of a flowchart as horizontal and vertical segments, and place their labels.

A forward line runs straight when it can, in an L-shape when its ends are in different
columns, and around the nodes and lines in its way otherwise. A returning line runs around
the flow, in a channel outside the nodes, unless every way round is blocked. Two lines never
leave one tip of a decision, and lines of different kinds never meet a node at one point.
"""

import math
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import pairwise

from .forks import is_inside
from .html_nodes import CAPTION_WIDTH_PX
from .layered import Grid
from .model import SYMBOL_HEADS, Direction, Edge, EdgeLabel, LabelKind, Node, Point, Role, Shape
from .pathfind import SearchSpace, find_route, path_cost
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
REROUTE_ROUNDS: int = 3  # times each line that meets another is searched again once all are drawn
END_GAP_PX: float = 24.0  # lines of different kinds meeting one point of a side are this far apart


class Port(StrEnum):
    """A side of a node where a line can attach."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


SIDE_PORTS: tuple[Port, ...] = (Port.LEFT, Port.RIGHT)  # a side one line at most leaves from
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
    exits: set[tuple[str, Port]] = field(default_factory=set)  # the sides lines leave nodes by


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
) -> _Route:
    """Return the direct route between two nodes.

    A decision leaves by its bottom tip only towards the node straight below it; any other
    exit leaves by the side tip that faces its target, so two exits never share one tip.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        slot: Where the line leaves the bottom of the source and enters the top of the target,
            when it runs to a lower row.
        caption_port: The side the captions hang from.

    Returns:
        The route, with the ports it leaves and enters by.
    """
    (source_x, source_y), (target_x, target_y) = _center(source), _center(target)
    same_row = abs(source_y - target_y) < SAME_LINE_TOLERANCE_PX
    straight_below = abs(source_x - target_x) < SAME_LINE_TOLERANCE_PX
    by_side = source.shape is Shape.DECISION and not straight_below
    if slot is not None and not by_side:
        exit_x, entry_x = slot
        start, end = (exit_x, _attach(source, Port.BOTTOM, caption_port)[1]), (entry_x, target.y)
        if abs(exit_x - entry_x) < SAME_LINE_TOLERANCE_PX:
            return _Route([start, end], Port.BOTTOM, Port.TOP, None)
        bus_y = max(start[1] + BUS_BELOW_SOURCE_PX, end[1] - BUS_ABOVE_TARGET_PX)
        return _Route([start, (exit_x, bus_y), (entry_x, bus_y), end], Port.BOTTOM, Port.TOP, None)
    leaving = Port.RIGHT if target_x > source_x else Port.LEFT
    if same_row:
        arriving = Port.LEFT if leaving is Port.RIGHT else Port.RIGHT
        points = [_attach(source, leaving, caption_port), _attach(target, arriving, caption_port)]
        return _Route(points, leaving, arriving, None)
    corner = (target_x, source_y)
    points = [_attach(source, leaving, caption_port), corner, _attach(target, Port.TOP)]
    return _Route(points, leaving, Port.TOP, None)


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
    over the top, and an arc under the bottom. The first one that is clear of other nodes, uses
    ports that are still free and runs along no line already drawn wins; failing that, a route
    searched around every node and line; failing that, the first clear one, or the first.

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
    apart = [route for route in free or clear if not _follows_line(route.points, context.lines)]
    if not apart:
        found = _search_route(source, target, context)
        apart = [found] if found is not None else []
    chosen = (apart or free or clear or candidates)[0]
    if chosen.channel is not None:
        context.channels_used[chosen.channel] = context.channels_used.get(chosen.channel, 0) + 1
    context.used_ports.add((target.id, chosen.arrives))
    return chosen


def _follows_line(points: list[Point], lines: list[tuple[Point, Point]]) -> bool:
    """Tell whether a route runs on top of a line already drawn for more than a junction.

    A line that meets the route at one of its ends is left out: two lines into one point are
    moved apart once all are drawn (``_spread_ends``).
    """
    ends = {points[0], points[-1]}
    return any(
        _overlap(stretch, line) > SAME_LINE_TOLERANCE_PX
        for stretch in pairwise(points)
        for line in lines
        if not ends & set(line)
    )


def _overlap(first: tuple[Point, Point], second: tuple[Point, Point]) -> float:
    """Return how long two horizontal or vertical segments run on one line together."""
    for along in (0, 1):
        across = 1 - along
        coordinates = (first[0][across], first[1][across], second[0][across], second[1][across])
        if max(coordinates) - min(coordinates) < SAME_LINE_TOLERANCE_PX:
            low = max(
                min(first[0][along], first[1][along]), min(second[0][along], second[1][along])
            )
            high = min(
                max(first[0][along], first[1][along]), max(second[0][along], second[1][along])
            )
            return max(0.0, high - low)
    return 0.0


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
    find no route, because each pair of sides costs a search. A tip of a decision that another
    line already uses is never tried, so two lines never leave one tip.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        context: The router state; it is not changed.

    Returns:
        The cheapest route found, or None when no pair of sides can be joined.
    """
    space = SearchSpace(_obstacles(context), tuple(context.lines))
    sides = [port for port in Port if not _is_taken_tip(source, port, context)]
    facing = [port for port in _facing(source, target) if port in sides]
    pairs = [(leave, arrive) for leave in facing for arrive in _facing(target, source)]
    best = _best_of(pairs, (source, target), space, context)
    if best is None:
        pairs = [(leave, arrive) for leave in sides for arrive in Port]
        best = _best_of(pairs, (source, target), space, context)
    return None if best is None else best[1]


def _is_taken_tip(node: Node, port: Port, context: _Context) -> bool:
    """Tell whether a line may not leave this side: a tip another exit of a decision leaves by.

    A line that enters by that tip does not take it: the exit has the tip, and the two ends are
    moved apart once all lines are drawn.
    """
    return node.shape is Shape.DECISION and (node.id, port) in context.exits


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
    if returning:
        route = _returning_route(source, target, context)
    else:
        direct = _forward_points(source, target, context.slots.get(spec_edge), context.caption_port)
        route = _forward_route(source, target, direct, context)
    context.used_ports.add((source.id, route.leaves))
    context.used_ports.add((target.id, route.arrives))
    context.exits.add((source.id, route.leaves))
    context.lines.extend(pairwise(route.points))
    return route.points


def _forward_route(source: Node, target: Node, direct: _Route, context: _Context) -> _Route:
    """Keep the direct route when it is clear, else take a searched one when that costs less.

    The direct route is clear when it passes through no node, leaves by a side that no other
    line leaves from, and crosses, follows or runs beside no line already drawn.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        direct: The route ``_forward_points`` gives.
        context: The router state; it is not changed.

    Returns:
        The route to draw.
    """
    misses_nodes = _is_clear(direct.points, context, (source.id, target.id))
    side_taken = (source.id, direct.leaves) in context.used_ports and direct.leaves in SIDE_PORTS
    side_taken = side_taken or _is_taken_tip(source, direct.leaves, context)
    if misses_nodes and not side_taken and not _meets_lines(direct.points, context.lines):
        return direct
    found = _search_route(source, target, context)
    if found is None:
        return direct if misses_nodes else _returning_route(source, target, context)
    if (
        misses_nodes
        and not side_taken
        and _cost(direct.points, context.lines) <= _cost(found.points, context.lines)
    ):
        return direct
    return found


def _cost(points: list[Point], lines: list[tuple[Point, Point]]) -> float:
    """Return what a route costs among the lines drawn: length, bends, crossings, stretches."""
    return path_cost(SearchSpace((), tuple(lines)), points)


def _meets_lines(points: list[Point], lines: list[tuple[Point, Point]]) -> bool:
    """Tell whether a route crosses, follows or runs close beside one of the lines."""
    return _cost(points, lines) > _cost(points, [])


def _reroute_meeting(
    routed: dict[SpecEdge, list[Point]], returning: set[SpecEdge], context: _Context
) -> dict[SpecEdge, list[Point]]:
    """Search again every forward line that meets another, now that all are drawn.

    A line drawn early could not avoid the lines drawn after it, nor see which tip of a decision
    a later line took. Each is searched with every other line in place and replaced when the new
    route costs less, or when it shares a decision's tip with another line, for a few rounds. A
    returning line keeps its way round the flow.

    Args:
        routed: Each edge's route.
        returning: The edges that loop back.
        context: The router state; its lines and ports describe every route when this returns.

    Returns:
        Each edge's route, some replaced.
    """
    routes = dict(routed)
    for _ in range(REROUTE_ROUNDS):
        changed = False
        for edge in [edge for edge in routes if edge not in returning]:
            changed = _reroute_one(edge, routes, context) or changed
        if not changed:
            break
    context.lines = [segment for drawn in routes.values() for segment in pairwise(drawn)]
    context.used_ports = _ports_of(routes, None)
    context.exits = {(edge.source, _end_side(drawn, True)) for edge, drawn in routes.items()}
    return routes


def _reroute_one(edge: SpecEdge, routes: dict[SpecEdge, list[Point]], context: _Context) -> bool:
    """Search one line again among all the others; replace its route and return True if better.

    Args:
        edge: The line to search again.
        routes: Each edge's route; the edge's entry is replaced when a better route is found.
        context: The router state; its lines and ports are set to those of the other routes.

    Returns:
        Whether the route was replaced.
    """
    points = routes[edge]
    context.lines = [
        segment
        for other, drawn in routes.items()
        if other is not edge
        for segment in pairwise(drawn)
    ]
    context.used_ports = _ports_of(routes, edge)
    context.exits = {
        (other.source, _end_side(drawn, True))
        for other, drawn in routes.items()
        if other is not edge
    }
    source, target = context.nodes[edge.source], context.nodes[edge.target]
    clashes = _is_taken_tip(source, _end_side(points, True), context)
    if not clashes and not _meets_lines(points, context.lines):
        return False
    found = _search_route(source, target, context)
    if found is None or not (
        clashes or _cost(found.points, context.lines) < _cost(points, context.lines)
    ):
        return False
    routes[edge] = found.points
    return True


def _ports_of(routes: dict[SpecEdge, list[Point]], skip: SpecEdge | None) -> set[tuple[str, Port]]:
    """Return the sides of nodes that the routes leave or enter by, but those of ``skip``."""
    ports = set()
    for edge, points in routes.items():
        if edge is not skip:
            ports.add((edge.source, _end_side(points, True)))
            ports.add((edge.target, _end_side(points, False)))
    return ports


def _spread_ends(
    routes: dict[SpecEdge, list[Point]], context: _Context
) -> dict[SpecEdge, list[Point]]:
    """Move apart the ends of lines of different kinds that meet a node at one point.

    Lines of one kind (role and dash) that meet at one point merge there, as a trunk does; lines
    of different kinds would draw two arrowheads, or two starts, on top of each other. They are
    spread along the side, in the order they come from, so that they do not cross. A straight
    line has no bend to absorb a move, so it keeps its place and the others move round it; a
    move that would take a line through a node is not made.

    Args:
        routes: Each edge's route.
        context: The router state.

    Returns:
        Each edge's route, some with an end moved along its side.
    """
    meeting: dict[tuple[str, Point], list[tuple[SpecEdge, bool]]] = defaultdict(list)
    for edge, points in routes.items():
        meeting[(edge.source, points[0])].append((edge, True))
        meeting[(edge.target, points[-1])].append((edge, False))
    moved = dict(routes)
    for (node_id, _), ends in meeting.items():
        if len({(edge.role, edge.dashed) for edge, _ in ends}) > 1:
            _spread_group(ends, context.nodes[node_id], moved, context)
    return moved


def _spread_group(
    ends: list[tuple[SpecEdge, bool]],
    node: Node,
    moved: dict[SpecEdge, list[Point]],
    context: _Context,
) -> None:
    """Spread the ends that meet one point of a node; ``moved`` is changed in place.

    Args:
        ends: Each edge with True when its start is at the point, False when its end is.
        node: The node they meet.
        moved: Each edge's route.
        context: The router state.
    """
    ends.sort(key=lambda end: _approach(moved[end[0]], end[1]))
    step = _end_step(node, _end_side(moved[ends[0][0]], ends[0][1]), len(ends))
    offsets = [index * step for index in range(len(ends))]
    fixed = [i for i, (edge, at_start) in enumerate(ends) if not _can_shift(moved[edge], at_start)]
    anchor = offsets[fixed[0]] if fixed else (offsets[0] + offsets[-1]) / 2
    for (edge, at_start), offset in zip(ends, offsets, strict=True):
        shifted = _shift_end(moved[edge], at_start, node, offset - anchor)
        if _is_clear(shifted, context, (edge.source, edge.target)):
            moved[edge] = shifted


def _end_side(points: list[Point], at_start: bool) -> Port:
    """Return the side of its node that a route leaves (``at_start``) or enters by."""
    end, inner = (points[0], points[1]) if at_start else (points[-1], points[-2])
    if abs(inner[0] - end[0]) > abs(inner[1] - end[1]):
        return Port.LEFT if inner[0] < end[0] else Port.RIGHT
    return Port.TOP if inner[1] < end[1] else Port.BOTTOM


def _approach(points: list[Point], at_start: bool) -> float:
    """Return where a route goes after it leaves its side, to order the ends along that side."""
    ordered = points if at_start else points[::-1]
    far = ordered[min(2, len(ordered) - 1)]
    return far[1] if _end_side(points, at_start) in (Port.LEFT, Port.RIGHT) else far[0]


def _end_step(node: Node, side: Port, count: int) -> float:
    """Return the distance between ends spread along one side, so all of them fit on it."""
    length = node.height if side in (Port.LEFT, Port.RIGHT) else node.width
    return min(END_GAP_PX, length / (count + 1))


def _run_from_end(points: list[Point], at_start: bool) -> int:
    """Return how many points from one end lie on the straight stretch that meets the node."""
    ordered = points if at_start else points[::-1]
    side = _end_side(ordered, True)
    across = 1 if side in (Port.LEFT, Port.RIGHT) else 0
    count = 1
    while count < len(ordered) and abs(ordered[count][across] - ordered[0][across]) < (
        SAME_LINE_TOLERANCE_PX
    ):
        count += 1
    return count


def _can_shift(points: list[Point], at_start: bool) -> bool:
    """Tell whether an end can slide along its side: the route bends somewhere."""
    return _run_from_end(points, at_start) < len(points)


def _shift_end(points: list[Point], at_start: bool, node: Node, offset: float) -> list[Point]:
    """Slide one end of a route along its side, with the straight stretch that comes into it.

    Every point of that stretch moves, so the stretch stays straight and the bend at its far
    end absorbs the move. A route with no bend is returned as it is.
    """
    run = _run_from_end(points, at_start)
    if run == len(points) or not offset:
        return points
    moved = list(points) if at_start else list(reversed(points))
    side = _end_side(moved, True)
    across = 1 if side in (Port.LEFT, Port.RIGHT) else 0
    for index in range(run):
        point = list(moved[index])
        point[across] += offset
        moved[index] = (point[0], point[1])
    moved[0] = _on_border(node, side, moved[0])
    return moved if at_start else list(reversed(moved))


def _on_border(node: Node, side: Port, point: Point) -> Point:
    """Move a point that was slid along a side of a diamond back onto its slanted border."""
    if node.shape is not Shape.DECISION:
        return point
    center_x, center_y = _center(node)
    half_width, half_height = node.width / 2, node.height / 2
    if side in (Port.LEFT, Port.RIGHT):
        inset = abs(point[1] - center_y) * half_width / half_height
        return (point[0] + (inset if side is Port.LEFT else -inset), point[1])
    inset = abs(point[0] - center_x) * half_height / half_width
    return (point[0], point[1] + (inset if side is Port.TOP else -inset))


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
    routed = _spread_ends(_reroute_meeting(routed, returning, context), context)
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
