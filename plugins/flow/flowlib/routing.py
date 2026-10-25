"""Route the lines of a flowchart as horizontal and vertical segments, and place their labels.

A forward line runs straight when it can, in an L-shape when its ends are in different
columns, and around the flow when a node is in the way. A returning line always runs around
the flow, in a channel outside the nodes.
"""

import math
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import pairwise

from .layered import Grid
from .model import SYMBOL_HEADS, Edge, EdgeLabel, LabelKind, Node, Point, Role, Shape
from .placement import Placement
from .spec import Spec, SpecEdge
from .theme import LayoutRules, load_theme

END_LABEL_ALONG_PX = 24.0  # distance of an end label from the end of its line
END_LABEL_ACROSS_PX = 12.0  # and how far it sits to the side of the line
BUS_ABOVE_TARGET_PX = 28.0  # a line between columns turns this far above its target
BUS_BELOW_SOURCE_PX = 12.0  # but never closer than this to the bottom of its source
SAME_LINE_TOLERANCE_PX = 1.0  # two centres closer than this count as on one line
CLEARANCE_PX = 4.0  # how far a line must stay from a node it passes


class Port(StrEnum):
    """A side of a node where a line can attach."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


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
    slots: dict[SpecEdge, tuple[float, float]] = field(default_factory=dict)


def _bottom(node: Node) -> float:
    """Return where a line leaves the bottom of a node: under its caption when it has one."""
    caption = load_theme().layout.caption_height if node.caption else 0.0
    return node.y + node.height + caption


def _attach(node: Node, port: Port) -> Point:
    """Return the point in the middle of one side of a node."""
    center_x, center_y = node.x + node.width / 2, node.y + node.height / 2
    return {
        Port.TOP: (center_x, node.y),
        Port.BOTTOM: (center_x, _bottom(node)),
        Port.LEFT: (node.x, center_y),
        Port.RIGHT: (node.x + node.width, center_y),
    }[port]


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


def _slots(edges: list[SpecEdge], nodes: dict[str, Node]) -> dict[SpecEdge, tuple[float, float]]:
    """Choose where each downward line leaves its source and where it enters its target.

    Args:
        edges: The forward edges.
        nodes: The placed nodes.

    Returns:
        Edge to ``(exit x, entry x)``, only for lines that run to a lower row.
    """
    down = [e for e in edges if _goes_down(nodes[e.source], nodes[e.target])]
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
    return {edge: (exit_x[edge], entry_x[edge]) for edge in down}


def _forward_points(
    source: Node, target: Node, slot: tuple[float, float] | None
) -> tuple[list[Point], Port]:
    """Return the direct route between two nodes and the port it leaves from.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        slot: Where the line leaves the bottom of the source and enters the top of the target,
            when it runs to a lower row.

    Returns:
        The points, and the port of the source that the line leaves from.
    """
    (source_x, source_y), (target_x, target_y) = _center(source), _center(target)
    same_row = abs(source_y - target_y) < SAME_LINE_TOLERANCE_PX
    if slot is not None and not (source.shape is Shape.DECISION and source_x != slot[0]):
        exit_x, entry_x = slot
        start, end = (exit_x, _bottom(source)), (entry_x, target.y)
        if abs(exit_x - entry_x) < SAME_LINE_TOLERANCE_PX:
            return [start, end], Port.BOTTOM
        bus_y = max(start[1] + BUS_BELOW_SOURCE_PX, end[1] - BUS_ABOVE_TARGET_PX)
        return [start, (exit_x, bus_y), (entry_x, bus_y), end], Port.BOTTOM
    leaving = Port.RIGHT if target_x > source_x else Port.LEFT
    if same_row:
        arriving = Port.LEFT if leaving is Port.RIGHT else Port.RIGHT
        return [_attach(source, leaving), _attach(target, arriving)], leaving
    corner = (target_x, source_y)
    return [_attach(source, leaving), corner, _attach(target, Port.TOP)], leaving


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
    start, end = _attach(source, side), _attach(target, side)
    channel = _peek_channel_x(side, (min(start[1], end[1]), max(start[1], end[1])), context)
    points = [start, (channel, start[1]), (channel, end[1]), end]
    return _Route(points, leaves=side, arrives=side, channel=side)


def _arc_route(source: Node, target: Node, context: _Context) -> _Route:
    """Build a route that leaves the top of the source, arcs over the flow, and enters the target.

    Args:
        source: Where the line starts.
        target: Where the line ends.
        context: The router state.

    Returns:
        The route; it needs no channel.
    """
    start, end = _attach(source, Port.TOP), _attach(target, Port.TOP)
    ridge = min(start[1], end[1]) - context.rules.channel_offset
    points = [start, (start[0], ridge), (end[0], ridge), end]
    return _Route(points, leaves=Port.TOP, arrives=Port.TOP, channel=None)


def _returning_route(source: Node, target: Node, context: _Context) -> _Route:
    """Choose the route of a line that loops back to an earlier step.

    The candidates are tried in order: a channel on the right, a channel on the left, and an
    arc over the top. The first one that is clear of other nodes and uses ports that are still
    free wins; failing that, the first clear one; failing that, the first.

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
        _arc_route(source, target, context),
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
    points, port = _forward_points(source, target, context.slots.get(spec_edge))
    route = _Route(points, leaves=port, arrives=Port.TOP, channel=None)
    if returning or not _is_clear(points, context, (source.id, target.id)):
        route = _returning_route(source, target, context)
    context.used_ports.add((source.id, route.leaves))
    return route.points


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
    context = _Context(placement.nodes, rules, set(), {})
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
            kind = LABEL_KIND_OF_ROLE.get(spec_edge.role, LabelKind.PLAIN)
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
