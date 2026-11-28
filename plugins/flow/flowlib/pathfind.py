"""Find a right-angled route between two points that goes around boxes and avoids other lines.

The search runs on a grid whose lines are the edges of the (inflated) boxes, the middle of each
gap between boxes, and the two ends. A step costs its length; a bend, a crossing of another line
and a stretch along another line cost extra, so the cheapest route is short, straight and clear.
"""

import heapq
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from itertools import count, pairwise

from .model import Point

Rect = tuple[float, float, float, float]  # left, top, right, bottom
Segment = tuple[Point, Point]

BEND_COST_PX = 30.0
CROSSING_COST_PX = 60.0
OVERLAP_COST_PER_PX = 6.0
BESIDE_COST_PER_PX: float = 3.0  # running closer than a track gap beside a line reads as touching
TRACK_GAP_PX = 16.0  # a route may run this far beside a line already drawn, and no closer
TRACK_REACH_PX = 150.0  # but only for lines that pass this close to an end of the route
OUTSIDE_MARGIN_PX = 40.0
MIN_CORRIDOR_PX = 8.0  # a gap narrower than this gets no middle line
SAME_LINE_PX = 2.0
INDEX_CELL_PX: float = 200.0  # the side of a cell of the box index
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True)
class SearchSpace:
    """What a route must avoid: boxes it may not cross, and lines it should not run along."""

    obstacles: tuple[Rect, ...]
    lines: tuple[Segment, ...] = ()


@dataclass(frozen=True)
class Found:
    """A route and what it cost."""

    points: list[Point]
    cost: float


def _inside(rect: Rect, point: Point) -> bool:
    """Tell whether a point lies strictly inside a rectangle."""
    left, top, right, bottom = rect
    return left < point[0] < right and top < point[1] < bottom


class _BoxIndex:
    """The obstacles, filed by the square cells of the page they touch, for lookups.

    A step of the search is short and meets only the boxes near it.
    """

    def __init__(self, obstacles: tuple[Rect, ...]) -> None:
        """File every obstacle under each cell it touches.

        Args:
            obstacles: The boxes a route may not cross.
        """
        self.cells: dict[tuple[int, int], list[Rect]] = {}
        for rect in obstacles:
            for cell in _cells(rect):
                self.cells.setdefault(cell, []).append(rect)

    def blocks(self, start: Point, end: Point) -> bool:
        """Tell whether an axis-aligned segment passes through the inside of an obstacle."""
        low_x, high_x = sorted((start[0], end[0]))
        low_y, high_y = sorted((start[1], end[1]))
        return any(
            low_x < right and high_x > left and low_y < bottom and high_y > top
            for cell in _cells((low_x, low_y, high_x, high_y))
            for left, top, right, bottom in self.cells.get(cell, ())
        )


def _cells(rect: Rect) -> list[tuple[int, int]]:
    """Return the cells of the box index that a rectangle touches."""
    left, top, right, bottom = (int(value // INDEX_CELL_PX) for value in rect)
    return [(x, y) for x in range(left, right + 1) for y in range(top, bottom + 1)]


def _corridors(edges: set[float]) -> list[float]:
    """Return the grid lines on one axis: the given edges and the middle of each wide gap."""
    ordered = sorted(edges)
    lines = set(ordered)
    for low, high in pairwise(ordered):
        if high - low > MIN_CORRIDOR_PX:
            lines.add((low + high) / 2)
    return sorted(lines)


def _near(first: Point, second: Point, end: Point) -> bool:
    """Tell whether a segment passes within reach of an end of the route."""
    low_x, high_x = sorted((first[0], second[0]))
    low_y, high_y = sorted((first[1], second[1]))
    return (
        low_x - TRACK_REACH_PX < end[0] < high_x + TRACK_REACH_PX
        and low_y - TRACK_REACH_PX < end[1] < high_y + TRACK_REACH_PX
    )


def _grid(space: SearchSpace, ends: tuple[Point, Point]) -> tuple[list[float], list[float]]:
    """Build the grid lines of the search: x lines and y lines."""
    xs = {point[0] for point in ends}
    ys = {point[1] for point in ends}
    for left, top, right, bottom in space.obstacles:
        xs.update((left, right))
        ys.update((top, bottom))
    for first, second in space.lines:
        if not any(_near(first, second, end) for end in ends):
            continue
        if abs(first[0] - second[0]) < SAME_LINE_PX:
            xs.update((first[0] - TRACK_GAP_PX, first[0] + TRACK_GAP_PX))
        else:
            ys.update((first[1] - TRACK_GAP_PX, first[1] + TRACK_GAP_PX))
    xs.update((min(xs) - OUTSIDE_MARGIN_PX, max(xs) + OUTSIDE_MARGIN_PX))
    ys.update((min(ys) - OUTSIDE_MARGIN_PX, max(ys) + OUTSIDE_MARGIN_PX))
    return _corridors(xs), _corridors(ys)


class _LineIndex:
    """The lines drawn, split by direction and sorted by the coordinate they keep, for lookups.

    A step of the search only meets the lines near it, so finding them by bisection keeps a
    search fast when hundreds of lines are drawn.
    """

    def __init__(self, lines: tuple[Segment, ...]) -> None:
        """Sort every line under its direction: 0 for horizontal, 1 for vertical.

        Args:
            lines: The segments already drawn.
        """
        by_axis: dict[int, list[tuple[float, float, float]]] = {0: [], 1: []}
        for first, second in lines:
            along = 0 if abs(first[1] - second[1]) < SAME_LINE_PX else 1
            low, high = sorted((first[along], second[along]))
            by_axis[along].append((first[1 - along], low, high))
        self.lines = {along: sorted(found) for along, found in by_axis.items()}
        self.keys = {along: [line[0] for line in found] for along, found in self.lines.items()}

    def between(self, along: int, low: float, high: float) -> list[tuple[float, float, float]]:
        """Return the lines of one direction whose kept coordinate lies from ``low`` to ``high``."""
        keys = self.keys[along]
        return self.lines[along][bisect_left(keys, low) : bisect_right(keys, high)]


def _line_cost(index: _LineIndex, start: Point, end: Point) -> float:
    """Return the extra cost of a step: along another line, beside one, or across one.

    A line that the step reaches counts as crossed, and one it leaves from does not, so a
    crossing is paid once even though the grid always has a line on the crossed one.
    """
    extra = 0.0
    along = 0 if abs(start[1] - end[1]) < SAME_LINE_PX else 1
    low, high = sorted((start[along], end[along]))
    fixed = start[1 - along]
    for other_fixed, other_low, other_high in index.between(
        along, fixed - TRACK_GAP_PX, fixed + TRACK_GAP_PX
    ):
        shared = max(0.0, min(high, other_high) - max(low, other_low))
        extra += shared * _beside_cost(abs(other_fixed - fixed))
    for other_fixed, other_low, other_high in index.between(1 - along, low, high):
        if other_low < fixed < other_high and _reaches(start[along], end[along], other_fixed):
            extra += CROSSING_COST_PX
    return extra


def _beside_cost(gap: float) -> float:
    """Return the cost per pixel of running this far from a parallel line."""
    if gap < SAME_LINE_PX:
        return OVERLAP_COST_PER_PX
    if gap < TRACK_GAP_PX - SAME_LINE_PX:
        return BESIDE_COST_PER_PX
    return 0.0


def _reaches(start: float, end: float, mark: float) -> bool:
    """Tell whether a step from ``start`` to ``end`` passes or stops on ``mark``, not leaves it."""
    if end > start:
        return start < mark <= end
    return end <= mark < start


def path_cost(space: SearchSpace, points: list[Point]) -> float:
    """Return what a drawn route costs by the measure the search uses.

    Args:
        space: The lines the route should stay off; obstacles are not looked at.
        points: The route, at least two points.

    Returns:
        Its length, plus the cost of every bend, crossing and stretch along or beside a line.
    """
    steps = [(start, end) for start, end in pairwise(points) if start != end]
    cost = sum(abs(end[0] - start[0]) + abs(end[1] - start[1]) for start, end in steps)
    index = _LineIndex(space.lines)
    cost += sum(_line_cost(index, start, end) for start, end in steps)
    return cost + BEND_COST_PX * max(0, len(steps) - 1)


def _simplify(points: list[Point]) -> list[Point]:
    """Drop the points that lie in the middle of a straight stretch."""
    kept = [points[0]]
    for index in range(1, len(points) - 1):
        before, here, after = points[index - 1], points[index], points[index + 1]
        straight = (before[0] == here[0] == after[0]) or (before[1] == here[1] == after[1])
        if not straight:
            kept.append(here)
    kept.append(points[-1])
    return kept


State = tuple[
    int, int, int
]  # grid column, grid row, heading (index into DIRECTIONS, -1 at the start)


class _Search:
    """One run of the search: the grid, the best cost to each state and how each was reached."""

    def __init__(self, space: SearchSpace, start: Point, end: Point) -> None:
        """Build the grid and put the start on the queue.

        Args:
            space: The obstacles and the lines to avoid.
            start: Where the route begins.
            end: Where the route ends.
        """
        self.space = space
        self.index = _LineIndex(space.lines)
        self.boxes = _BoxIndex(space.obstacles)
        self.xs, self.ys = _grid(space, (start, end))
        self.goal = (self.xs.index(end[0]), self.ys.index(end[1]))
        self.first: State = (self.xs.index(start[0]), self.ys.index(start[1]), -1)
        self.best: dict[State, float] = {self.first: 0.0}
        self.parent: dict[State, State] = {}
        self.steps: dict[tuple[tuple[int, int], tuple[int, int]], float | None] = {}
        self.ticket = count()
        self.queue = [(0.0, next(self.ticket), self.first)]

    def point(self, column: int, row: int) -> Point:
        """Return the coordinates of a grid crossing."""
        return (self.xs[column], self.ys[row])

    def step_cost(self, here: tuple[int, int], there: tuple[int, int]) -> float | None:
        """Return the cost of one step between neighbouring grid crossings, None when blocked.

        The answer does not depend on how the step is reached, so it is kept.
        """
        key = (here, there)
        if key not in self.steps:
            start, end = self.point(*here), self.point(*there)
            if self.boxes.blocks(start, end):
                self.steps[key] = None
            else:
                length = abs(end[0] - start[0]) + abs(end[1] - start[1])
                self.steps[key] = length + _line_cost(self.index, start, end)
        return self.steps[key]

    def expand(self, state: State) -> None:
        """Push every step that can be taken from a state."""
        column, row, heading = state
        for direction, (step_x, step_y) in enumerate(DIRECTIONS):
            target = (column + step_x, row + step_y)
            if not (0 <= target[0] < len(self.xs) and 0 <= target[1] < len(self.ys)):
                continue
            step = self.step_cost((column, row), target)
            if step is None:
                continue
            bend = BEND_COST_PX if heading not in (-1, direction) else 0.0
            cost = self.best[state] + step + bend
            key = (target[0], target[1], direction)
            if cost < self.best.get(key, float("inf")):
                self.best[key] = cost
                self.parent[key] = state
                there = self.point(*target)
                goal = self.point(*self.goal)
                guess = abs(goal[0] - there[0]) + abs(goal[1] - there[1])
                heapq.heappush(self.queue, (cost + guess, next(self.ticket), key))

    def run(self) -> Found | None:
        """Search until the goal is reached, or the queue is empty."""
        while self.queue:
            _, _, state = heapq.heappop(self.queue)
            if (state[0], state[1]) == self.goal:
                points = _trace(self.parent, state, self.xs, self.ys)
                return Found(_simplify(points), self.best[state])
            self.expand(state)
        return None


def find_route(space: SearchSpace, start: Point, end: Point) -> Found | None:
    """Find the cheapest right-angled route from one point to another.

    Args:
        space: The obstacles to go around and the lines to stay off.
        start: Where the route begins; it must not lie inside an obstacle.
        end: Where the route ends; it must not lie inside an obstacle.

    Returns:
        The route and its cost, or None when there is no route.
    """
    if any(_inside(rect, point) for rect in space.obstacles for point in (start, end)):
        return None
    return _Search(space, start, end).run()


def _trace(
    parent: dict[State, State],
    state: State,
    xs: list[float],
    ys: list[float],
) -> list[Point]:
    """Walk back from the goal to the start and return the points in order."""
    points = []
    current: State | None = state
    while current is not None:
        points.append((xs[current[0]], ys[current[1]]))
        current = parent.get(current)
    points.reverse()
    return points
