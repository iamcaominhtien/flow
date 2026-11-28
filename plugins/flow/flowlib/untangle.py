"""Give every drawn line a way of its own where lines of different kinds meet.

A reader tells lines apart by their role (colour) and their dash. Two lines of different kinds
that run on top of each other, that leave one tip of a decision, or that end at one point of a
node cannot be told apart. These passes fix that on lines already drawn, whoever placed them:
the flowchart router spreads the ends of its lines, and the author kit runs all three passes
on the lines a script drew by hand.
"""

from collections import defaultdict
from collections.abc import Callable, Hashable
from dataclasses import dataclass, replace
from enum import StrEnum
from itertools import combinations, pairwise
from typing import Protocol, TypeVar

from .model import Edge, Node, Point, Role, Shape
from .pathfind import SearchSpace, find_route, path_cost

END_GAP_PX: float = 24.0  # lines of different kinds meeting one point of a side are this far apart
SAME_LINE_TOLERANCE_PX: float = 1.0  # two coordinates closer than this count as one
MIN_OVERLAP_PX: float = 32.0  # a shorter shared stretch is a junction at a node, not an overlap
SEARCH_MARGIN_PX: float = 12.0  # how far a searched route keeps from every box
STUB_PX: float = 16.0  # a searched route leaves a box straight for this far before it may turn
CLEARANCE_PX: float = 4.0  # how far a line must stay from a node it passes
UNTANGLE_ROUNDS: int = 3  # times the overlapping lines are searched again
SPREAD_ORDER_SPAN_PX: float = 1e6  # larger than any page: keeps the two ways apart in the order
NUDGE_OFFSETS_PX: tuple[float, ...] = (-16.0, 16.0, -32.0, 32.0)  # a track or two aside


class Port(StrEnum):
    """A side of a node where a line can attach."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


OUTWARD: dict[Port, tuple[float, float]] = {
    Port.TOP: (0.0, -1.0),
    Port.BOTTOM: (0.0, 1.0),
    Port.LEFT: (-1.0, 0.0),
    Port.RIGHT: (1.0, 0.0),
}


class Line(Protocol):
    """What the passes need to know of a line besides its points: its kind and its ends."""

    role: Role
    dashed: bool
    source: str | None
    target: str | None


LineKey = TypeVar("LineKey", bound=Hashable)
ClearTest = Callable[[list[Point], tuple[str, str]], bool]


@dataclass(frozen=True)
class _Ends:
    """The two nodes a searched line joins, and the sides of its source it may not leave by."""

    source: Node
    target: Node
    banned: frozenset[Port] = frozenset()


def untangle(edges: list[Edge], nodes: dict[str, Node]) -> list[Edge]:
    """Give each line its own tip, its own stretch and its own end point.

    A line that carries words (a screen flow arrow) keeps its route: its words are placed along
    it by hand. A moved line's label goes to the middle of its longest stretch.

    Args:
        edges: The lines as drawn.
        nodes: Every node, by id.

    Returns:
        The lines in the same order, some with new points.
    """
    routes = {
        edge: list(edge.points)
        for edge in edges
        if edge.source in nodes and edge.target in nodes and not edge.extras
    }
    routes = _free_tips(routes, nodes)
    routes = _part_overlaps(routes, nodes)
    routes = spread_ends(routes, nodes, _clear_of(nodes))
    return [_moved(edge, routes.get(edge)) for edge in edges]


def spread_ends(
    routes: dict[LineKey, list[Point]], nodes: dict[str, Node], is_clear: ClearTest
) -> dict[LineKey, list[Point]]:
    """Move apart the ends of lines of different kinds that meet a node at one point.

    Lines of one kind that meet at one point merge there, as a trunk does; lines of different
    kinds would draw two arrowheads, or two starts, on top of each other. They are spread along
    the side, in the order they come from, so that they do not cross. A straight line has no
    bend to absorb a move, so it keeps its place and the others move round it; a move that
    would take a line through a node is not made. A move may add a crossing: two arrowheads on
    one point hide a line, a crossing does not.

    Args:
        routes: Each line (anything with a role, a dash and its two ends) to its points.
        nodes: Every node, by id.
        is_clear: Tells whether points between two nodes pass through no other node.

    Returns:
        Each line's points, some with an end moved along its side.
    """
    meeting: dict[tuple[str, Point], list[tuple[LineKey, bool]]] = defaultdict(list)
    for line, points in routes.items():
        meeting[(line.source, points[0])].append((line, True))
        meeting[(line.target, points[-1])].append((line, False))
    moved = dict(routes)
    for (node_id, _), ends in meeting.items():
        if len({_kind(line) for line, _ in ends}) > 1:
            _spread_group(ends, nodes[node_id], moved, is_clear)
    return moved


def end_side(points: list[Point], at_start: bool) -> Port:
    """Return the side of its node that a route leaves (``at_start``) or enters by."""
    end, inner = (points[0], points[1]) if at_start else (points[-1], points[-2])
    if abs(inner[0] - end[0]) > abs(inner[1] - end[1]):
        return Port.LEFT if inner[0] < end[0] else Port.RIGHT
    return Port.TOP if inner[1] < end[1] else Port.BOTTOM


def attach(node: Node, port: Port) -> Point:
    """Return the point in the middle of one side of a node: a tip, on a decision."""
    center_x, center_y = node.x + node.width / 2, node.y + node.height / 2
    return {
        Port.TOP: (center_x, node.y),
        Port.BOTTOM: (center_x, node.y + node.height),
        Port.LEFT: (node.x, center_y),
        Port.RIGHT: (node.x + node.width, center_y),
    }[port]


def shared_length(first: list[Point], second: list[Point]) -> float:
    """Return the longest stretch two routes run on top of each other."""
    return max(
        (_overlap(a, b) for a in pairwise(first) for b in pairwise(second)),
        default=0.0,
    )


def _kind(line: Line) -> tuple[Role, bool]:
    """Return what tells a line apart on the page: its role and its dash."""
    return line.role, line.dashed


def _free_tips(routes: dict[Edge, list[Point]], nodes: dict[str, Node]) -> dict[Edge, list[Point]]:
    """Search a new way for a line that leaves a decision by a tip a line of another kind uses.

    The kind of the first exit (the main path, when one leaves there) keeps the tip; a line of
    another kind searches from a tip that no line uses and that faces its target. Lines of one
    kind may leave one tip together, as the branches of a switch do. When no such tip is free,
    the line stays, and its start is moved along the tip's border later.
    """
    moved = dict(routes)
    by_tip: dict[tuple[str, Port], list[Edge]] = defaultdict(list)
    for edge, points in routes.items():
        if nodes[edge.source].shape is Shape.DECISION:
            by_tip[(edge.source, end_side(points, True))].append(edge)
    for (node_id, _), exits in by_tip.items():
        exits.sort(key=lambda edge: edge.role is not Role.MAIN)
        for edge in exits:
            if _kind(edge) == _kind(exits[0]):
                continue
            source, target = nodes[node_id], nodes[edge.target]
            free = {
                port
                for port in Port
                if port not in _sides_in_use(moved, node_id) and _faces(source, target, port)
            }
            if free:
                ends = _Ends(source, target, frozenset(Port) - free)
                moved[edge] = _search(ends, _others(moved, edge), nodes) or moved[edge]
    return moved


def _sides_in_use(routes: dict[Edge, list[Point]], node_id: str) -> frozenset[Port]:
    """Return the sides of a node that a line leaves or enters by."""
    sides = {end_side(points, True) for edge, points in routes.items() if edge.source == node_id}
    sides |= {end_side(points, False) for edge, points in routes.items() if edge.target == node_id}
    return frozenset(sides)


def _part_overlaps(
    routes: dict[Edge, list[Point]], nodes: dict[str, Node]
) -> dict[Edge, list[Point]]:
    """Part a line that runs on top of a line of another kind, for a few rounds.

    Of the two, a line on the main path keeps its way; otherwise the one drawn later moves: the
    stretch on top is first pushed a track aside, and only when that fails is a new way
    searched. The new way is kept when it runs on top of no line of another kind. Two lines
    that only share the last stretch into a common point are left to ``spread_ends``.
    """
    moved = dict(routes)
    for _ in range(UNTANGLE_ROUNDS):
        pairs = [
            (first, second)
            for first, second in combinations(moved, 2)
            if _kind(first) != _kind(second) and _overlap_beyond_ends(first, second, moved)
        ]
        if not pairs:
            break
        for first, second in pairs:
            mover = first if second.role is Role.MAIN and first.role is not Role.MAIN else second
            if not _nudge(mover, moved, nodes):
                _try_new_way(mover, moved, nodes)
    return moved


def _nudge(edge: Edge, moved: dict[Edge, list[Point]], nodes: dict[str, Node]) -> bool:
    """Push the stretches of a line that run on top of another kind a track or two aside.

    Only a stretch between two bends moves; the bends at its ends absorb the move, so the line
    stays right-angled and keeps its ends. A move is made when the line then runs on top of no
    line of another kind, passes through no new node and crosses no more lines.

    Returns:
        Whether the line was moved.
    """
    points = moved[edge]
    lines = _others(moved, edge)
    is_clear = _clear_of(nodes)
    for index in range(1, len(points) - 2):
        for offset in NUDGE_OFFSETS_PX:
            tried = _pushed(points, index, offset)
            if (
                not _runs_on_other_kind(edge, tried, moved)
                and not _newly_blocked(points, tried, edge, is_clear)
                and _crossings(tried, lines) <= _crossings(points, lines)
            ):
                moved[edge] = tried
                return True
    return False


def _pushed(points: list[Point], index: int, offset: float) -> list[Point]:
    """Return a route with one inner stretch moved sideways by ``offset``."""
    start, end = points[index], points[index + 1]
    across = 0 if abs(start[0] - end[0]) < SAME_LINE_TOLERANCE_PX else 1
    pushed = list(points)
    for at in (index, index + 1):
        point = list(pushed[at])
        point[across] += offset
        pushed[at] = (point[0], point[1])
    return pushed


def _runs_on_other_kind(edge: Edge, points: list[Point], routes: dict[Edge, list[Point]]) -> bool:
    """Tell whether a route runs on top of a line of another kind, beyond shared end points."""
    trial = {**routes, edge: points}
    return any(
        _kind(other) != _kind(edge) and _overlap_beyond_ends(edge, other, trial)
        for other in routes
        if other is not edge
    )


def _overlap_beyond_ends(first: Edge, second: Edge, routes: dict[Edge, list[Point]]) -> bool:
    """Tell whether two lines run on top of each other other than into a point they share.

    Two lines into one point overlap along their last straight stretch; moving their ends
    apart (``spread_ends``) parts them, so that stretch is left out here.
    """
    first_points, second_points = routes[first], routes[second]
    if first_points[0] == second_points[0]:
        first_points, second_points = _beyond(first_points, True), _beyond(second_points, True)
    if first_points[-1] == second_points[-1]:
        first_points, second_points = _beyond(first_points, False), _beyond(second_points, False)
    return shared_length(first_points, second_points) >= MIN_OVERLAP_PX


def _beyond(points: list[Point], at_start: bool) -> list[Point]:
    """Return a route without the straight stretch at one end, keeping the bend it ends at."""
    run = _run_from_end(points, at_start)
    if run >= len(points):
        return points
    return points[run - 1 :] if at_start else points[: len(points) - run + 1]


def _try_new_way(edge: Edge, moved: dict[Edge, list[Point]], nodes: dict[str, Node]) -> None:
    """Replace a line's points with a searched way that costs less and overlaps no other kind.

    The cost counts length, bends, crossings and stretches along other lines; and a new way
    that crosses more lines than the old one is not taken either, because a line drawn by hand
    was placed with the whole picture in mind and a detour across it costs more than it shows.
    """
    taken = frozenset(
        end_side(moved[other], True)
        for other in moved
        if other.source == edge.source and other is not edge
    )
    banned = taken if nodes[edge.source].shape is Shape.DECISION else frozenset()
    found = _search(
        _Ends(nodes[edge.source], nodes[edge.target], banned), _others(moved, edge), nodes
    )
    if found is None:
        return
    lines = _others(moved, edge)
    space = SearchSpace((), tuple(lines))
    if path_cost(space, found) >= path_cost(space, moved[edge]):
        return
    if _crossings(found, lines) > _crossings(moved[edge], lines):
        return
    clashes = any(
        _kind(other) != _kind(edge) and shared_length(found, points) >= MIN_OVERLAP_PX
        for other, points in moved.items()
        if other is not edge
    )
    if not clashes:
        moved[edge] = found


def _crossings(points: list[Point], lines: list[tuple[Point, Point]]) -> int:
    """Return how many of the lines a route crosses in the middle of both."""
    return sum(_cross(stretch, line) for stretch in pairwise(points) for line in lines)


def _cross(first: tuple[Point, Point], second: tuple[Point, Point]) -> bool:
    """Tell whether a horizontal and a vertical segment cross inside both."""
    for flat, upright in ((first, second), (second, first)):
        if (
            abs(flat[0][1] - flat[1][1]) < SAME_LINE_TOLERANCE_PX
            and abs(upright[0][0] - upright[1][0]) < SAME_LINE_TOLERANCE_PX
        ):
            low_x, high_x = sorted((flat[0][0], flat[1][0]))
            low_y, high_y = sorted((upright[0][1], upright[1][1]))
            x, y = upright[0][0], flat[0][1]
            return low_x < x < high_x and low_y < y < high_y
    return False


def _others(routes: dict[LineKey, list[Point]], edge: LineKey) -> list[tuple[Point, Point]]:
    """Return the stretches of every line but one."""
    return [
        segment
        for other, points in routes.items()
        if other is not edge
        for segment in pairwise(points)
    ]


def _search(
    ends: _Ends, lines: list[tuple[Point, Point]], nodes: dict[str, Node]
) -> list[Point] | None:
    """Search the cheapest way between two nodes around every box and the lines drawn.

    The sides that face each other are tried first, every side only when those find nothing.

    Returns:
        The points, from a side of the source to a side of the target, or None.
    """
    space = SearchSpace(_obstacles(nodes), tuple(lines))
    leaving = [port for port in Port if port not in ends.banned]
    for first_try in (True, False):
        pairs = [
            (leave, arrive)
            for leave in leaving
            for arrive in Port
            if not first_try
            or (
                _faces(ends.source, ends.target, leave) and _faces(ends.target, ends.source, arrive)
            )
        ]
        best = _best_way(pairs, ends, space)
        if best is not None:
            return best
    return None


def _best_way(
    pairs: list[tuple[Port, Port]], ends: _Ends, space: SearchSpace
) -> list[Point] | None:
    """Return the cheapest way found over the pairs of sides, or None."""
    best: tuple[float, list[Point]] | None = None
    for leave, arrive in pairs:
        found = find_route(space, _stub(ends.source, leave), _stub(ends.target, arrive))
        if found is None:
            continue
        points = [attach(ends.source, leave), *found.points, attach(ends.target, arrive)]
        cost = path_cost(space, points)
        if best is None or cost < best[0]:
            best = (cost, points)
    return None if best is None else best[1]


def _faces(node: Node, other: Node, port: Port) -> bool:
    """Tell whether a side of a node looks towards another node."""
    out_x, out_y = OUTWARD[port]
    delta_x = other.x + other.width / 2 - (node.x + node.width / 2)
    delta_y = other.y + other.height / 2 - (node.y + node.height / 2)
    return out_x * delta_x + out_y * delta_y > SAME_LINE_TOLERANCE_PX


def _stub(node: Node, port: Port) -> Point:
    """Return the point straight out from one side of a node, past the search margin."""
    x, y = attach(node, port)
    out_x, out_y = OUTWARD[port]
    reach = SEARCH_MARGIN_PX + STUB_PX
    return (x + out_x * reach, y + out_y * reach)


def _obstacles(nodes: dict[str, Node]) -> tuple[tuple[float, float, float, float], ...]:
    """Return every node as a box grown by the search margin."""
    margin = SEARCH_MARGIN_PX
    return tuple(
        (
            node.x - margin,
            node.y - margin,
            node.x + node.width + margin,
            node.y + node.height + margin,
        )
        for node in nodes.values()
    )


def _clear_of(nodes: dict[str, Node]) -> ClearTest:
    """Return a test of whether points pass through no node but their two ends."""

    def is_clear(points: list[Point], ends: tuple[str, str]) -> bool:
        """Tell whether a route passes through no node; it may touch its ends where it attaches."""
        last = len(points) - 2
        for index, (start, end) in enumerate(pairwise(points)):
            for node_id, node in nodes.items():
                attaches = (node_id == ends[0] and index == 0) or (
                    node_id == ends[1] and index == last
                )
                if not attaches and _hits(node, start, end):
                    return False
        return True

    return is_clear


def _hits(node: Node, start: Point, end: Point) -> bool:
    """Tell whether a horizontal or vertical segment passes through a node, with clearance."""
    low_x, high_x = sorted((start[0], end[0]))
    low_y, high_y = sorted((start[1], end[1]))
    return (
        low_x < node.x + node.width + CLEARANCE_PX
        and high_x > node.x - CLEARANCE_PX
        and low_y < node.y + node.height + CLEARANCE_PX
        and high_y > node.y - CLEARANCE_PX
    )


def _moved(edge: Edge, points: list[Point] | None) -> Edge:
    """Return a line with its new points, its label at the middle of its longest stretch."""
    if points is None or tuple(points) == edge.points:
        return edge
    label = edge.label
    if label is not None:
        label = replace(label, at=_middle(points))
    return replace(edge, points=tuple(points), label=label)


def _middle(points: list[Point]) -> Point:
    """Return the middle of the longest stretch of a route."""
    start, end = max(
        pairwise(points),
        key=lambda pair: abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1]),
    )
    return (start[0] + end[0]) / 2, (start[1] + end[1]) / 2


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


def _spread_group(
    ends: list[tuple[LineKey, bool]],
    node: Node,
    moved: dict[LineKey, list[Point]],
    is_clear: ClearTest,
) -> None:
    """Spread the ends that meet one point of a node, one place per kind; ``moved`` changes.

    The lines of one kind move together, so a trunk they share stays one trunk. A kind with a
    straight line keeps its place, and the others move round it. A kind is not moved when that
    would take one of its lines through a node it did not pass through before.

    Args:
        ends: Each line with True when its start is at the point, False when its end is.
        node: The node they meet.
        moved: Each line's points.
        is_clear: Tells whether points between two nodes pass through no other node.
    """
    kinds: dict[tuple[Role, bool], list[tuple[LineKey, bool]]] = defaultdict(list)
    for end in ends:
        kinds[_kind(end[0])].append(end)
    groups = sorted(
        kinds.values(),
        key=lambda group: (
            sum(_approach(moved[line], at_start) for line, at_start in group) / len(group)
        ),
    )
    step = _end_step(node, end_side(moved[ends[0][0]], ends[0][1]), len(groups))
    offsets = [index * step for index in range(len(groups))]
    fixed = [
        index
        for index, group in enumerate(groups)
        if any(not _can_shift(moved[line], at_start) for line, at_start in group)
    ]
    anchor = offsets[fixed[0]] if fixed else (offsets[0] + offsets[-1]) / 2
    for group, offset in zip(groups, offsets, strict=True):
        shifted = {
            line: _shift_end(moved[line], at_start, node, offset - anchor)
            for line, at_start in group
        }
        if not any(
            _newly_blocked(moved[line], points, line, is_clear) for line, points in shifted.items()
        ):
            moved.update(shifted)


def _newly_blocked(
    before: list[Point], after: list[Point], line: Line, is_clear: ClearTest
) -> bool:
    """Tell whether moving a line takes it through a node it did not pass through before."""
    ends = (line.source, line.target)
    return not is_clear(after, ends) and is_clear(before, ends)


def _approach(points: list[Point], at_start: bool) -> float:
    """Return where an end belongs along its side, so the ends spread there do not cross.

    Lines that come from one way along the side take the places on that way; among them, the
    one whose bend is nearest the node takes the outermost place, so its last stretch passes
    no other line's bend. A line with no bend sits in the middle.
    """
    ordered = points if at_start else points[::-1]
    run = _run_from_end(ordered, True)
    if run >= len(ordered):
        return 0.0
    along = 1 if end_side(ordered, True) in (Port.LEFT, Port.RIGHT) else 0
    bend, far = ordered[run - 1], ordered[run]
    distance = abs(bend[1 - along] - ordered[0][1 - along])
    way = 1.0 if far[along] > ordered[0][along] else -1.0
    return way * (SPREAD_ORDER_SPAN_PX - distance)


def _end_step(node: Node, side: Port, count: int) -> float:
    """Return the distance between ends spread along one side, so all of them fit on it."""
    length = node.height if side in (Port.LEFT, Port.RIGHT) else node.width
    return min(END_GAP_PX, length / (count + 1))


def _run_from_end(points: list[Point], at_start: bool) -> int:
    """Return how many points from one end lie on the straight stretch that meets the node."""
    ordered = points if at_start else points[::-1]
    side = end_side(ordered, True)
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
    side = end_side(moved, True)
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
    center_x, center_y = node.x + node.width / 2, node.y + node.height / 2
    half_width, half_height = node.width / 2, node.height / 2
    if side in (Port.LEFT, Port.RIGHT):
        inset = abs(point[1] - center_y) * half_width / half_height
        return (point[0] + (inset if side is Port.LEFT else -inset), point[1])
    inset = abs(point[0] - center_x) * half_height / half_width
    return (point[0], point[1] + (inset if side is Port.TOP else -inset))
