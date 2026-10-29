"""Swap the ports of arrows that share a frame side when the swap removes crossings.

``screen_routes`` orders the ports of a side by where each arrow heads. That guess does not know
the channel each arrow runs in, so two arrows that turn into one side from different heights
can cross just before the frame. Here every swap of two ports on one side is tried; a swap is
kept when the arrows it moves cross fewer lines, or run on fewer, and the passes repeat until
no swap helps. The set of ports of a side does not change, so the id chip stays clear.
"""

from collections.abc import Callable
from itertools import combinations, pairwise

from ..model import Point

MAX_PASSES = 4
TOUCH_PX = 1.0  # segments closer than this at an end meet there; they do not cross
OVERLAP_WEIGHT = 2  # a shared stretch reads worse than a crossing

Key = tuple[int, str]  # an arrow's index and which end, as the routes module keys its ports
Route = Callable[[int, dict[Key, float]], tuple[Point, ...]]
Segment = tuple[Point, Point]


def untangle(groups: list[list[Key]], offsets: dict[Key, float], route: Route) -> dict[Key, float]:
    """Return the port offsets with the swaps that lower the crossings.

    Args:
        groups: The arrow ends of each frame side that has two or more; a decision's tips are
            left out, since each has one point.
        offsets: Where each arrow end sits on its side.
        route: Draws one arrow, by index, from a set of offsets.

    Returns:
        New offsets; the input is not changed.
    """
    current = dict(offsets)
    routes = {index: route(index, current) for index in {key[0] for key in current}}
    for _ in range(MAX_PASSES):
        if not _one_pass(groups, current, routes, route):
            break
    return current


def _one_pass(
    groups: list[list[Key]],
    current: dict[Key, float],
    routes: dict[int, tuple[Point, ...]],
    route: Route,
) -> bool:
    """Try every swap once, keeping the good ones in place; tell whether any was kept."""
    improved = False
    for group in groups:
        for first, second in combinations(group, 2):
            if current[first] == current[second]:
                continue
            trial = {**current, first: current[second], second: current[first]}
            moved = {first[0], second[0]}
            redrawn = {index: route(index, trial) for index in moved}
            if _cost(moved, {**routes, **redrawn}) < _cost(moved, routes):
                current.update(trial)
                routes.update(redrawn)
                improved = True
    return improved


def _cost(moved: set[int], routes: dict[int, tuple[Point, ...]]) -> int:
    """Count the crossings and shared stretches of the moved arrows with every other arrow."""
    total = 0
    for index in moved:
        for other, points in routes.items():
            if other == index or (other in moved and other < index):
                continue
            total += _clash(routes[index], points)
    return total


def _clash(first: tuple[Point, ...], second: tuple[Point, ...]) -> int:
    """Return how badly two routes meet: one per crossing, more per shared stretch."""
    score = 0
    for one in pairwise(first):
        for two in pairwise(second):
            if _crosses(one, two):
                score += 1
            elif _shares(one, two):
                score += OVERLAP_WEIGHT
    return score


def _crosses(one: Segment, two: Segment) -> bool:
    """Tell whether a horizontal and a vertical segment cross inside both."""
    horizontal, vertical = (one, two) if _is_flat(one) else (two, one)
    if not _is_flat(horizontal) or not _is_upright(vertical):
        return False
    row, column = horizontal[0][1], vertical[0][0]
    left, right = sorted((horizontal[0][0], horizontal[1][0]))
    top, bottom = sorted((vertical[0][1], vertical[1][1]))
    inside_row = left + TOUCH_PX < column < right - TOUCH_PX
    return inside_row and top + TOUCH_PX < row < bottom - TOUCH_PX


def _shares(one: Segment, two: Segment) -> bool:
    """Tell whether two segments run on the same line for more than a touch."""
    if _is_flat(one) != _is_flat(two) or not (_is_flat(one) or _is_upright(one)):
        return False
    axis = 1 if _is_flat(one) else 0
    if abs(one[0][axis] - two[0][axis]) > TOUCH_PX:
        return False
    along = 1 - axis
    low = max(min(one[0][along], one[1][along]), min(two[0][along], two[1][along]))
    high = min(max(one[0][along], one[1][along]), max(two[0][along], two[1][along]))
    return high - low > TOUCH_PX


def _is_flat(segment: Segment) -> bool:
    """Tell whether a segment is horizontal."""
    return abs(segment[0][1] - segment[1][1]) < TOUCH_PX


def _is_upright(segment: Segment) -> bool:
    """Tell whether a segment is vertical; a slanted one (a jump not yet cut) is neither."""
    return abs(segment[0][0] - segment[1][0]) < TOUCH_PX
