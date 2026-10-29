"""Move apart two arrows that still run on top of each other after they are routed.

The ports of a frame side are spread from its middle, and so are those of the frame across the
gap. When a long leg leaves the top of one frame and another long leg the bottom of a frame in
the same column, the two can share an x, and then a stretch of the column holds two lines
drawn as one. Swapping ports (``screen_untangle``) cannot help when both sides use the same
spread. Here such a stretch of one of the arrows is moved sideways by a few pixels, with the
ends it shares with its neighbours, so that the two lines can be told apart.

A stretch at a decision's tip stays where it is, since a tip has one point; a stretch that ends
on a frame moves its port along the side, clear of the corners.
"""

from dataclasses import dataclass
from itertools import pairwise

from ..model import Node, Point, Shape
from .screen_plan import Plan
from .screen_untangle import TOUCH_PX, segment_clash, shares

STEP_PX = 8.0  # how far a stretch moves: half the room between two ports
TRIES = (1, -1, 2, -2, 3, -3)  # multiples of the step to try, nearest first
MIN_RUN_PX = 12.0  # the shortest a neighbouring stretch may become, so no jog appears

Routed = tuple[Plan, tuple[Point, ...]]


@dataclass(frozen=True)
class _Setting:
    """What a move must respect: the arrows' ends, the frames, and the corners' room."""

    routes: list[Routed]
    nodes: dict[str, Node]
    clear: float


def nudge_overlaps(routes: list[Routed], nodes: dict[str, Node], clear: float) -> list[Routed]:
    """Move apart the stretches of different arrows that run on the same line.

    Args:
        routes: Every arrow with its route.
        nodes: The placed nodes, whose sides the moved ports stay on.
        clear: How far from a frame's corner a port may sit.

    Returns:
        The routes, with an overlapping stretch moved where a move makes its arrow meet the
        others less; every other route as it was.
    """
    setting = _Setting(routes, nodes, clear)
    points = [list(route) for _, route in routes]
    for arrow, start in _overlapping(points):
        points[arrow] = _nudged((arrow, start), points, setting)
    return [(plan, tuple(moved)) for (plan, _), moved in zip(routes, points, strict=True)]


def _overlapping(points: list[list[Point]]) -> list[tuple[int, int]]:
    """List each stretch that shares a line with a stretch of an earlier arrow: (arrow, start)."""
    found: list[tuple[int, int]] = []
    for arrow, route in enumerate(points):
        earlier = [two for other in points[:arrow] for two in pairwise(other)]
        for start, segment in enumerate(pairwise(route)):
            if any(shares(segment, two) for two in earlier):
                found.append((arrow, start))
    return found


def _nudged(stretch: tuple[int, int], points: list[list[Point]], setting: _Setting) -> list[Point]:
    """Return the arrow's route with one stretch at the nearest place that meets others least."""
    arrow, _ = stretch
    route = points[arrow]
    others = [
        segment for i, other in enumerate(points) if i != arrow for segment in pairwise(other)
    ]
    best = (_score(route, others), route)
    for times in TRIES:
        moved = _moved(stretch, route, times * STEP_PX, setting)
        if moved is not None and _score(moved, others) < best[0]:
            best = (_score(moved, others), moved)
    return best[1]


def _score(route: list[Point], others: list[tuple[Point, Point]]) -> int:
    """Return how badly a route meets the other arrows: crossings, and shared stretches weighted."""
    return sum(segment_clash(one, two) for one in pairwise(route) for two in others)


def _moved(
    stretch: tuple[int, int], route: list[Point], distance: float, setting: _Setting
) -> list[Point] | None:
    """Return the route with one stretch moved across itself; None when the move is not allowed.

    A vertical stretch moves along x and a horizontal one along y. A neighbouring stretch must
    keep its direction and some length, and an end of the route that moves must stay on its
    frame side, clear of the corners, and must not be a decision's tip.
    """
    arrow, start = stretch
    axis = 0 if abs(route[start][0] - route[start + 1][0]) < TOUCH_PX else 1
    moved = list(route)
    for index in (start, start + 1):
        shifted = list(moved[index])
        shifted[axis] += distance
        moved[index] = (shifted[0], shifted[1])
    if not _keeps_neighbours(route, moved, (start, axis)):
        return None
    transition = setting.routes[arrow][0].transition
    ends = ((0, transition.source), (len(route) - 1, transition.target))
    for index, node_id in ends:
        if index in (start, start + 1) and not _stays_on_side(
            (route[index], moved[index]), setting.nodes[node_id], setting.clear
        ):
            return None
    return moved


def _keeps_neighbours(route: list[Point], moved: list[Point], where: tuple[int, int]) -> bool:
    """Tell whether the stretches next to a moved one keep their direction and some length."""
    start, axis = where
    for first, second in ((start - 1, start), (start + 1, start + 2)):
        if first < 0 or second >= len(route):
            continue
        before = route[second][axis] - route[first][axis]
        after = moved[second][axis] - moved[first][axis]
        if before * after <= 0 or abs(after) < MIN_RUN_PX:
            return False
    return True


def _stays_on_side(ends: tuple[Point, Point], node: Node, clear: float) -> bool:
    """Tell whether a moved end of a route is still on its frame's side, clear of the corners."""
    before, after = ends
    if node.shape is Shape.DECISION:
        return False
    bottom = node.y + node.height
    if abs(before[1] - node.y) < TOUCH_PX or abs(before[1] - bottom) < TOUCH_PX:
        return node.x + clear <= after[0] <= node.x + node.width - clear
    return node.y + clear <= after[1] <= bottom - clear
