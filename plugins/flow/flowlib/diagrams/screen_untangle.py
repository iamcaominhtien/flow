"""Swap the ports, or the channels, of two arrows when the swap removes crossings.

``screen_routes`` orders the ports of a side by where each arrow heads. That guess does not know
the channel each arrow runs in, so two arrows that turn into one side from different heights
can cross just before the frame. Likewise the planner orders the channels of a gap between rows
without knowing where the ports are, so an arrow that leaves a frame or a decision down and one
that leaves the frame or decision below it up can run on top of each other.

Here every swap of two ports on one side, and of two channels of one gap, is tried, and
every move of one of them to another place in the order; a swap is
kept when the arrows it moves cross fewer lines, or run on fewer, and the passes repeat until
no swap helps. The set of ports of a side does not change, so the id chip stays clear.
"""

from collections.abc import Callable, Iterator
from itertools import combinations, pairwise, permutations

from ..model import Point

MAX_PASSES = 4
TOUCH_PX = 1.0  # segments closer than this at an end meet there; they do not cross
OVERLAP_WEIGHT = 2  # a shared stretch reads worse than a crossing
MOVE_MIN = 2  # a move of one place is a swap, already tried

Key = tuple[int, str]  # an arrow's index and which end, or which choice, such as its channel
Route = Callable[[int, dict[Key, float]], tuple[Point, ...]]
Segment = tuple[Point, Point]


def untangle(groups: list[list[Key]], offsets: dict[Key, float], route: Route) -> dict[Key, float]:
    """Return the port offsets with the swaps that lower the crossings.

    Args:
        groups: The choices that may trade values: the arrow ends of each frame side that has
            two or more (a decision's tips are left out, since each has one point), and the
            channels of each gap that has two or more.
        offsets: The value of each choice: where an arrow end sits on its side, or the channel
            an arrow runs in.
        route: Draws one arrow, by index, from a set of values.

    Returns:
        New values; the input is not changed.
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
    """Try every swap and every move once, keeping the good ones; tell whether any was kept."""
    improved = False
    for group in groups:
        for trial in _trials(group, current):
            moved = {key[0] for key in group if trial[key] != current[key]}
            redrawn = {index: route(index, trial) for index in moved}
            if _cost(moved, {**routes, **redrawn}) < _cost(moved, routes):
                current.update(trial)
                routes.update(redrawn)
                improved = True
    return improved


def _trials(group: list[Key], current: dict[Key, float]) -> Iterator[dict[Key, float]]:
    """Yield the new values to try for one group: each swap of two, then each move of one.

    A move takes one choice out of the order and puts it back at another place, so the others
    keep their order: an arrow can jump over several channels without upsetting them. The values
    are read from ``current`` when each trial is made, so a kept change counts for the next.
    """
    for first, second in combinations(group, 2):
        if current[first] != current[second]:
            yield {**current, first: current[second], second: current[first]}
    for start, end in permutations(range(len(group)), 2):
        if abs(start - end) < MOVE_MIN:
            continue
        order = sorted(group, key=lambda key: current[key])
        values = [current[key] for key in order]
        order.insert(end, order.pop(start))
        yield {**current, **dict(zip(order, values, strict=True))}


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
    return sum(segment_clash(one, two) for one in pairwise(first) for two in pairwise(second))


def segment_clash(one: Segment, two: Segment) -> int:
    """Return how badly two segments meet: 1 for a crossing, more for a shared stretch, else 0.

    Args:
        one: A horizontal or vertical segment.
        two: Another.

    Returns:
        The score; ``OVERLAP_WEIGHT`` when they run on one line.
    """
    if _crosses(one, two):
        return 1
    return OVERLAP_WEIGHT if shares(one, two) else 0


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


def shares(one: Segment, two: Segment) -> bool:
    """Tell whether two segments run on the same line for more than a touch.

    Args:
        one: A segment.
        two: Another.

    Returns:
        True when both are horizontal, or both vertical, on one line, and overlap.
    """
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
