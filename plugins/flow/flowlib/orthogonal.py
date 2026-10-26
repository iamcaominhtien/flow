"""Right-angled routes between two points that leave and enter a box through a given side.

A route has at most two bends. For two sides that face each other it is a straight line or a Z;
for two sides that face the same way it is a U; for one horizontal and one vertical side it is
an L. A caller lists the pairs of sides it would accept, best first, and gets the first route
that does not pass through a box.
"""

from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

from .check import Rect
from .model import Node, Point

SAME_LINE_PX = 0.5  # two coordinates this close are the same line
CLEARANCE_PX = 2.0  # a segment this close to a box counts as touching it
MIN_ROUTE_POINTS = 2


class Facing(StrEnum):
    """The side of a box a line leaves or enters through."""

    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"


HORIZONTAL = (Facing.EAST, Facing.WEST)
OUTWARD: dict[Facing, Point] = {
    Facing.NORTH: (0, -1),
    Facing.EAST: (1, 0),
    Facing.SOUTH: (0, 1),
    Facing.WEST: (-1, 0),
}


@dataclass(frozen=True)
class Anchor:
    """A point on the border of a box and the side it is on."""

    point: Point
    facing: Facing


def anchor_on(node: Node, facing: Facing, offset: float = 0.0) -> Anchor:
    """Return the point in the middle of one side of a node, moved along that side by ``offset``.

    Args:
        node: The box.
        facing: Which side.
        offset: How far to move from the middle: right on a horizontal side, down on a vertical.

    Returns:
        The anchor.
    """
    middle_x, middle_y = node.x + node.width / 2, node.y + node.height / 2
    points = {
        Facing.NORTH: (middle_x + offset, node.y),
        Facing.SOUTH: (middle_x + offset, node.y + node.height),
        Facing.WEST: (node.x, middle_y + offset),
        Facing.EAST: (node.x + node.width, middle_y + offset),
    }
    return Anchor(points[facing], facing)


def path_between(start: Anchor, end: Anchor, shift: float, reach: float) -> list[Point] | None:
    """Return the route between two anchors, or None when their sides do not suit each other.

    Args:
        start: Where the line leaves.
        end: Where the line arrives.
        shift: Moves the middle channel of a Z, or the outer channel of a U, by this much.
        reach: How far a U goes beyond the farther of its two ends.

    Returns:
        The points of the route, the start and the end included.
    """
    start_horizontal = start.facing in HORIZONTAL
    end_horizontal = end.facing in HORIZONTAL
    route: list[Point] | None = None
    if start_horizontal != end_horizontal:
        route = _elbow(start, end)
    elif _are_opposite(start.facing, end.facing):
        route = _across(start, end, shift)
    elif start.facing is end.facing:
        route = _around(start, end, shift, reach)
    return route if route and _is_proper(simplify(route), start, end) else None


def best_route(
    pairs: list[tuple[Anchor, Anchor]],
    obstacles: list[Rect],
    shift: float = 0.0,
    reach: float = 40.0,
) -> list[Point]:
    """Return the first route of a list of anchor pairs that passes through no obstacle.

    Args:
        pairs: The ends to try, best first.
        obstacles: The boxes the line must not cross; the two boxes it joins are left out.
        shift: Moves the channel of a Z or a U, to keep parallel lines apart.
        reach: How far a U goes beyond its farther end.

    Returns:
        The route. When every route is blocked, the first one that exists; when none exists, a
        direct line between the first pair.
    """
    found = [route for pair in pairs if (route := path_between(*pair, shift, reach))]
    for route in found:
        if is_clear(route, obstacles):
            return simplify(route)
    return simplify(found[0]) if found else [pairs[0][0].point, pairs[0][1].point]


def is_clear(route: list[Point], obstacles: list[Rect]) -> bool:
    """Tell whether no segment of a route passes through an obstacle."""
    return not any(
        _segment_rect(start, end).overlaps(obstacle, -CLEARANCE_PX)
        for start, end in pairwise(route)
        for obstacle in obstacles
    )


def simplify(route: list[Point]) -> list[Point]:
    """Drop repeated points and points in the middle of a straight run."""
    points: list[Point] = []
    for point in route:
        if points and _same(points[-1], point):
            continue
        points.append(point)
    kept = points[:1]
    for before, here, after in zip(points, points[1:], points[2:], strict=False):
        if not _collinear(before, here, after):
            kept.append(here)
    return [*kept, *points[-1:]] if len(points) > 1 else points


def bend_count(route: list[Point]) -> int:
    """Count the corners of a route."""
    return max(len(simplify(route)) - 2, 0)


def _is_proper(route: list[Point], start: Anchor, end: Anchor) -> bool:
    """Tell whether a route leaves its first box outward and arrives at its last from outside."""
    if len(route) < MIN_ROUTE_POINTS:
        return False
    first = (route[1][0] - route[0][0], route[1][1] - route[0][1])
    last = (route[-2][0] - route[-1][0], route[-2][1] - route[-1][1])
    leaves = first[0] * OUTWARD[start.facing][0] + first[1] * OUTWARD[start.facing][1]
    arrives = last[0] * OUTWARD[end.facing][0] + last[1] * OUTWARD[end.facing][1]
    return leaves > 0 and arrives > 0


def _same(first: Point, second: Point) -> bool:
    """Tell whether two points are the same, within a tolerance."""
    return abs(first[0] - second[0]) < SAME_LINE_PX and abs(first[1] - second[1]) < SAME_LINE_PX


def _collinear(before: Point, here: Point, after: Point) -> bool:
    """Tell whether three points lie on one horizontal or vertical line."""
    on_row = abs(before[1] - here[1]) < SAME_LINE_PX and abs(here[1] - after[1]) < SAME_LINE_PX
    on_column = abs(before[0] - here[0]) < SAME_LINE_PX and abs(here[0] - after[0]) < SAME_LINE_PX
    return on_row or on_column


def _segment_rect(start: Point, end: Point) -> Rect:
    """Return the thin rectangle that covers a horizontal or vertical segment."""
    return Rect(
        min(start[0], end[0]), min(start[1], end[1]), max(start[0], end[0]), max(start[1], end[1])
    )


def _are_opposite(first: Facing, second: Facing) -> bool:
    """Tell whether two sides face each other, such as the east side and the west side."""
    return OUTWARD[first][0] == -OUTWARD[second][0] and OUTWARD[first][1] == -OUTWARD[second][1]


def _elbow(start: Anchor, end: Anchor) -> list[Point] | None:
    """Return the L between a horizontal side and a vertical side, or None when it is backwards."""
    (start_x, start_y), (end_x, end_y) = start.point, end.point
    corner = (end_x, start_y) if start.facing in HORIZONTAL else (start_x, end_y)
    if not _leaves_forward(start, corner) or not _arrives_forward(end, corner):
        return None
    return [start.point, corner, end.point]


def _leaves_forward(start: Anchor, corner: Point) -> bool:
    """Tell whether the first segment goes out of the box and not back into it."""
    direction = OUTWARD[start.facing]
    moved = (corner[0] - start.point[0]) * direction[0] + (corner[1] - start.point[1]) * direction[
        1
    ]
    return moved > SAME_LINE_PX


def _arrives_forward(end: Anchor, corner: Point) -> bool:
    """Tell whether the last segment comes in from outside the box and not from inside it."""
    direction = OUTWARD[end.facing]
    moved = (corner[0] - end.point[0]) * direction[0] + (corner[1] - end.point[1]) * direction[1]
    return moved > SAME_LINE_PX


def _across(start: Anchor, end: Anchor, shift: float) -> list[Point] | None:
    """Return a straight line or a Z between two sides that face each other."""
    (start_x, start_y), (end_x, end_y) = start.point, end.point
    if start.facing in HORIZONTAL:
        if (end_x - start_x) * OUTWARD[start.facing][0] <= SAME_LINE_PX:
            return None
        channel = (start_x + end_x) / 2 + shift
        return [start.point, (channel, start_y), (channel, end_y), end.point]
    if (end_y - start_y) * OUTWARD[start.facing][1] <= SAME_LINE_PX:
        return None
    channel = (start_y + end_y) / 2 + shift
    return [start.point, (start_x, channel), (end_x, channel), end.point]


def _around(start: Anchor, end: Anchor, shift: float, reach: float) -> list[Point]:
    """Return a U between two sides that face the same way, going past the farther end."""
    (start_x, start_y), (end_x, end_y) = start.point, end.point
    direction = OUTWARD[start.facing]
    if start.facing in HORIZONTAL:
        edge = max(start_x * direction[0], end_x * direction[0])
        channel = (edge + reach + shift) * direction[0]
        return [start.point, (channel, start_y), (channel, end_y), end.point]
    edge = max(start_y * direction[1], end_y * direction[1])
    channel = (edge + reach + shift) * direction[1]
    return [start.point, (start_x, channel), (end_x, channel), end.point]


def route_length(route: list[Point]) -> float:
    """Return the total length of a route in pixels."""
    return sum(abs(end[0] - start[0]) + abs(end[1] - start[1]) for start, end in pairwise(route))


def count_crossings(route: list[Point], others: list[list[Point]]) -> int:
    """Count the places where a route crosses a segment of other routes at a right angle."""
    count = 0
    for start, end in pairwise(route):
        for other in others:
            count += sum(_cross(start, end, a, b) for a, b in pairwise(other))
    return count


def shared_length(route: list[Point], others: list[list[Point]]) -> float:
    """Return how many pixels of a route run on top of other routes."""
    total = 0.0
    for start, end in pairwise(route):
        for other in others:
            total += sum(_overlap(start, end, a, b) for a, b in pairwise(other))
    return total


def _cross(first_start: Point, first_end: Point, second_start: Point, second_end: Point) -> bool:
    """Tell whether a horizontal and a vertical segment cross, not counting their end points."""
    first = (first_start, first_end)
    second = (second_start, second_end)
    first_is_row = abs(first_start[1] - first_end[1]) < SAME_LINE_PX
    second_is_row = abs(second_start[1] - second_end[1]) < SAME_LINE_PX
    if first_is_row == second_is_row:
        return False
    row, column = (first, second) if first_is_row else (second, first)
    return _strictly_between(column[0][0], row[0][0], row[1][0]) and _strictly_between(
        row[0][1], column[0][1], column[1][1]
    )


def _strictly_between(value: float, end: float, other_end: float) -> bool:
    """Tell whether a value lies inside a span, not on its ends."""
    return min(end, other_end) + SAME_LINE_PX < value < max(end, other_end) - SAME_LINE_PX


def _overlap(first_start: Point, first_end: Point, second_start: Point, second_end: Point) -> float:
    """Return the length two parallel segments share on one line, or zero."""
    for axis, other in ((0, 1), (1, 0)):
        on_one_line = (
            abs(first_start[other] - first_end[other]) < SAME_LINE_PX
            and abs(second_start[other] - second_end[other]) < SAME_LINE_PX
            and abs(first_start[other] - second_start[other]) < SAME_LINE_PX
        )
        if on_one_line:
            low = max(
                min(first_start[axis], first_end[axis]), min(second_start[axis], second_end[axis])
            )
            high = min(
                max(first_start[axis], first_end[axis]), max(second_start[axis], second_end[axis])
            )
            return max(high - low, 0.0)
    return 0.0
