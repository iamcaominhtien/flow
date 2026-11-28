"""The sides of a node where lines attach, and how the ends of lines that meet there are spread.

A reader tells lines apart by their kind: their role (colour) and their dash. Lines of one kind
that meet a node at one point merge there, as a trunk does; lines of different kinds would draw
two arrowheads, or two starts, on top of each other. ``spread_ends`` moves those apart along the
side. Both the flowchart router and the author kit (``untangle``) use it.
"""

from collections import defaultdict
from collections.abc import Callable, Hashable
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from typing import Protocol, TypeVar

from .model import Node, Point, Role, Shape

END_GAP_PX: float = 24.0  # lines of different kinds meeting one point of a side are this far apart
SAME_LINE_TOLERANCE_PX: float = 1.0  # two coordinates closer than this count as one
CLEARANCE_PX: float = 4.0  # how far a line must stay from a node it passes
SEARCH_MARGIN_PX: float = 12.0  # how far a searched route keeps from every box
STUB_PX: float = 16.0  # a searched route leaves a box straight for this far before it may turn


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
UPRIGHT_SIDES: tuple[Port, ...] = (Port.LEFT, Port.RIGHT)  # a line meets these going sideways


class Line(Protocol):
    """What spreading needs to know of a line besides its points: its kind and its ends."""

    role: Role
    dashed: bool
    source: str | None
    target: str | None


LineKey = TypeVar("LineKey", bound=Hashable)
ClearTest = Callable[[list[Point], tuple[str, str]], bool]


@dataclass(frozen=True)
class _End:
    """One end of a line at a node: the line, and whether it is the line's start."""

    line: Hashable
    at_start: bool


@dataclass(frozen=True)
class _Rules:
    """What a move of ends must respect: no new node in the way, and lines that must stay."""

    is_clear: ClearTest
    keep: frozenset[Hashable]


def spread_ends(
    routes: dict[LineKey, list[Point]],
    nodes: dict[str, Node],
    is_clear: ClearTest,
    keep: frozenset[LineKey] = frozenset(),
) -> dict[LineKey, list[Point]]:
    """Move apart the ends of lines of different kinds that meet a node at one point.

    The ends are put in groups of one kind coming from one way along the side, and each group
    takes a place of its own, in the order they come from, so their last stretches do not
    cross. A group moves as one, so a trunk stays one trunk. A group with a straight line, or a
    line in ``keep``, holds its place and the others move round it; a group is not moved when
    that would take one of its lines through a node it did not pass through before. A move may
    add a crossing: two arrowheads on one point hide a line, a crossing does not.

    Args:
        routes: Each line (anything with a role, a dash and its two ends) to its points.
        nodes: Every node, by id.
        is_clear: Tells whether points between two nodes pass through no other node.
        keep: Lines whose points must not change.

    Returns:
        Each line's points, some with an end moved along its side.
    """
    meeting: dict[tuple[str, Point], list[_End]] = defaultdict(list)
    for line, points in routes.items():
        meeting[(line.source, points[0])].append(_End(line, True))
        meeting[(line.target, points[-1])].append(_End(line, False))
    moved = dict(routes)
    for (node_id, _), ends in meeting.items():
        if len({kind_of(end.line) for end in ends}) > 1:
            groups = _groups(ends, moved)
            _place_groups(groups, nodes[node_id], moved, _Rules(is_clear, keep))
    return moved


def kind_of(line: Line) -> tuple[Role, bool]:
    """Return what tells a line apart on the page: its role and its dash.

    Args:
        line: The line.

    Returns:
        Its role and whether it is dashed.
    """
    return line.role, line.dashed


def end_side(points: list[Point], at_start: bool) -> Port:
    """Return the side of its node that a route leaves or enters by.

    Args:
        points: The route.
        at_start: True for the side it leaves by, False for the side it enters by.

    Returns:
        The side.
    """
    end, inner = (points[0], points[1]) if at_start else (points[-1], points[-2])
    if abs(inner[0] - end[0]) > abs(inner[1] - end[1]):
        return Port.LEFT if inner[0] < end[0] else Port.RIGHT
    return Port.TOP if inner[1] < end[1] else Port.BOTTOM


def attach(node: Node, port: Port) -> Point:
    """Return the point in the middle of one side of a node: a tip, on a decision.

    Args:
        node: The node.
        port: The side.

    Returns:
        The point.
    """
    center_x, center_y = node.x + node.width / 2, node.y + node.height / 2
    return {
        Port.TOP: (center_x, node.y),
        Port.BOTTOM: (center_x, node.y + node.height),
        Port.LEFT: (node.x, center_y),
        Port.RIGHT: (node.x + node.width, center_y),
    }[port]


def hits(node: Node, start: Point, end: Point) -> bool:
    """Tell whether a horizontal or vertical segment passes through a node, with clearance.

    Args:
        node: The node.
        start: One end of the segment.
        end: The other end.

    Returns:
        True when the segment comes closer to the node than the clearance.
    """
    low_x, high_x = sorted((start[0], end[0]))
    low_y, high_y = sorted((start[1], end[1]))
    return (
        low_x < node.x + node.width + CLEARANCE_PX
        and high_x > node.x - CLEARANCE_PX
        and low_y < node.y + node.height + CLEARANCE_PX
        and high_y > node.y - CLEARANCE_PX
    )


def simplify(points: list[Point]) -> list[Point]:
    """Drop repeated points and points in the middle of a straight stretch.

    Args:
        points: A right-angled route.

    Returns:
        The same route with only its ends and its bends.
    """
    kept = [points[0]]
    for here in points[1:]:
        if _same(here, kept[-1]):
            continue
        if len(kept) > 1 and _in_line(kept[-2], kept[-1], here):
            kept[-1] = here
        else:
            kept.append(here)
    if len(kept) == 1:
        kept.append(points[-1])
    return kept


def run_from_end(points: list[Point], at_start: bool) -> int:
    """Return how many points from one end lie on the straight stretch that meets the node.

    Args:
        points: The route.
        at_start: True for the start, False for the end.

    Returns:
        The count, at least 1; all the points when the route has no bend.
    """
    ordered = points if at_start else points[::-1]
    across = 1 if end_side(ordered, True) in UPRIGHT_SIDES else 0
    count = 1
    while count < len(ordered) and _near(ordered[count][across], ordered[0][across]):
        count += 1
    return count


def _same(first: Point, second: Point) -> bool:
    """Tell whether two points are one.

    Args:
        first: One point.
        second: The other.

    Returns:
        True when they are closer than the tolerance on both axes.
    """
    return _near(first[0], second[0]) and _near(first[1], second[1])


def _near(first: float, second: float) -> bool:
    """Tell whether two coordinates are one.

    Args:
        first: One coordinate.
        second: The other.

    Returns:
        True when they are closer than the tolerance.
    """
    return abs(first - second) < SAME_LINE_TOLERANCE_PX


def _in_line(before: Point, here: Point, after: Point) -> bool:
    """Tell whether three points lie on one horizontal or vertical line.

    Args:
        before: The point before.
        here: The point in the middle.
        after: The point after.

    Returns:
        True when the middle point adds no bend.
    """
    flat = _near(before[1], here[1]) and _near(here[1], after[1])
    upright = _near(before[0], here[0]) and _near(here[0], after[0])
    return flat or upright


def _way(points: list[Point], at_start: bool) -> tuple[int, float]:
    """Return which way a line comes from along its side, and how far its bend is from it.

    The way is -1 from the top (or left), 1 from the bottom (or right), and 0 for a line with
    no bend, which comes straight in.

    Args:
        points: The route.
        at_start: True for its start, False for its end.

    Returns:
        The way, and the distance of the bend from the node.
    """
    ordered = points if at_start else points[::-1]
    run = run_from_end(ordered, True)
    if run >= len(ordered):
        return 0, 0.0
    along = 1 if end_side(ordered, True) in UPRIGHT_SIDES else 0
    bend, far = ordered[run - 1], ordered[run]
    distance = abs(bend[1 - along] - ordered[0][1 - along])
    return (1 if far[along] > ordered[0][along] else -1), distance


def _groups(ends: list[_End], routes: dict[LineKey, list[Point]]) -> list[list[_End]]:
    """Group the ends by kind and way, and order the groups along the side.

    Groups from the top (or left) come first, then straight ones, then those from the bottom;
    within one way, the group whose bend is nearest the node takes the outermost place, so its
    last stretch passes no other group's bend.

    Args:
        ends: The ends that meet one point.
        routes: Each line's points.

    Returns:
        The groups, in their order along the side.
    """
    grouped: dict[tuple[tuple[Role, bool], int], list[_End]] = defaultdict(list)
    nearest: dict[tuple[tuple[Role, bool], int], float] = {}
    for end in ends:
        way, distance = _way(routes[end.line], end.at_start)
        key = (kind_of(end.line), way)
        grouped[key].append(end)
        nearest[key] = min(nearest.get(key, distance), distance)

    def place(key: tuple[tuple[Role, bool], int]) -> tuple[int, float]:
        """Return where a group goes: its way first, then outermost when its bend is nearest.

        Args:
            key: The kind and way of a group.

        Returns:
            The way, then the place within it.
        """
        way = key[1]
        return way, nearest[key] if way < 0 else -nearest[key]

    return [grouped[key] for key in sorted(grouped, key=place)]


def _place_groups(
    groups: list[list[_End]],
    node: Node,
    routes: dict[LineKey, list[Point]],
    rules: "_Rules",
) -> None:
    """Give each group of ends its place along the side; ``routes`` is changed in place.

    Args:
        groups: The groups of ends, in their order along the side.
        node: The node they meet.
        routes: Each line's points; changed in place.
        rules: The test of whether a route is clear of nodes, and the lines that must not move.
    """
    is_clear, keep = rules.is_clear, rules.keep
    first = groups[0][0]
    step = _end_step(node, end_side(routes[first.line], first.at_start), len(groups))
    fixed = [
        index
        for index, group in enumerate(groups)
        if any(end.line in keep or not _can_shift(routes, end) for end in group)
    ]
    anchor = fixed[0] if fixed else (len(groups) - 1) / 2
    for index, group in enumerate(groups):
        if index in fixed:
            continue
        offset = (index - anchor) * step
        shifted = {end.line: _shift_end(routes[end.line], end, node, offset) for end in group}
        if not any(
            _newly_blocked(routes[line], points, line, is_clear) for line, points in shifted.items()
        ):
            routes.update(shifted)


def _can_shift(routes: dict[LineKey, list[Point]], end: _End) -> bool:
    """Tell whether an end can slide along its side: its route bends somewhere.

    Args:
        routes: Each line's points.
        end: The end.

    Returns:
        True when the route has a bend.
    """
    points = routes[end.line]
    return run_from_end(points, end.at_start) < len(points)


def _newly_blocked(
    before: list[Point], after: list[Point], line: Line, is_clear: ClearTest
) -> bool:
    """Tell whether moving a line takes it through a node it did not pass through before.

    Args:
        before: The route before the move.
        after: The route after it.
        line: The line, for its two ends.
        is_clear: Tells whether a route is clear of nodes.

    Returns:
        True when the move takes the line through a node.
    """
    ends = (line.source, line.target)
    return not is_clear(after, ends) and is_clear(before, ends)


def _end_step(node: Node, side: Port, count: int) -> float:
    """Return the distance between ends spread along one side, so all of them fit on it.

    Args:
        node: The node.
        side: The side the ends meet.
        count: How many places are needed.

    Returns:
        The distance, at most the end gap.
    """
    length = node.height if side in UPRIGHT_SIDES else node.width
    return min(END_GAP_PX, length / (count + 1))


def _shift_end(points: list[Point], end: _End, node: Node, offset: float) -> list[Point]:
    """Slide one end of a route along its side, with the straight stretch that comes into it.

    Every point of that stretch moves, so the stretch stays straight and the bend at its far
    end absorbs the move. A route with no bend is returned as it is.

    Args:
        points: The route.
        end: Which end slides.
        node: The node the end meets.
        offset: How far it slides, along the side.

    Returns:
        A new route; the input itself when it has no bend or the offset is 0.
    """
    run = run_from_end(points, end.at_start)
    if run == len(points) or not offset:
        return points
    moved = list(points) if end.at_start else list(reversed(points))
    side = end_side(moved, True)
    across = 1 if side in UPRIGHT_SIDES else 0
    for index in range(run):
        point = list(moved[index])
        point[across] += offset
        moved[index] = (point[0], point[1])
    moved[0] = _on_border(node, side, moved[0])
    return moved if end.at_start else list(reversed(moved))


def _on_border(node: Node, side: Port, point: Point) -> Point:
    """Move a point that was slid along a side of a diamond back onto its slanted border.

    Args:
        node: The node.
        side: The side the point was slid along.
        point: The slid point.

    Returns:
        The point on the border; the point itself for any other shape.
    """
    if node.shape is not Shape.DECISION:
        return point
    center_x, center_y = node.x + node.width / 2, node.y + node.height / 2
    half_width, half_height = node.width / 2, node.height / 2
    if side in UPRIGHT_SIDES:
        inset = abs(point[1] - center_y) * half_width / half_height
        return (point[0] + (inset if side is Port.LEFT else -inset), point[1])
    inset = abs(point[0] - center_x) * half_height / half_width
    return (point[0], point[1] + (inset if side is Port.TOP else -inset))


def middle(points: list[Point]) -> Point:
    """Return the middle of the longest stretch of a route, where its label goes.

    Args:
        points: The route.

    Returns:
        The point.
    """
    start, end = max(
        pairwise(points),
        key=lambda pair: abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1]),
    )
    return (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
