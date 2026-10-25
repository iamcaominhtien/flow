"""Find a right-angled route between two points that goes around boxes and avoids other lines.

The search runs on a grid whose lines are the edges of the (inflated) boxes, the middle of each
gap between boxes, and the two ends. A step costs its length; a bend, a crossing of another line
and a stretch along another line cost extra, so the cheapest route is short, straight and clear.
"""

import heapq
from dataclasses import dataclass
from itertools import count, pairwise

from .model import Point

Rect = tuple[float, float, float, float]  # left, top, right, bottom
Segment = tuple[Point, Point]

BEND_COST_PX = 30.0
CROSSING_COST_PX = 60.0
OVERLAP_COST_PER_PX = 3.0
OUTSIDE_MARGIN_PX = 40.0
MIN_CORRIDOR_PX = 8.0  # a gap narrower than this gets no middle line
SAME_LINE_PX = 2.0
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


def _blocked(space: SearchSpace, start: Point, end: Point) -> bool:
    """Tell whether an axis-aligned segment passes through the inside of an obstacle."""
    low_x, high_x = sorted((start[0], end[0]))
    low_y, high_y = sorted((start[1], end[1]))
    return any(
        low_x < right and high_x > left and low_y < bottom and high_y > top
        for left, top, right, bottom in space.obstacles
    )


def _corridors(edges: set[float]) -> list[float]:
    """Return the grid lines on one axis: the given edges and the middle of each wide gap."""
    ordered = sorted(edges)
    lines = set(ordered)
    for low, high in pairwise(ordered):
        if high - low > MIN_CORRIDOR_PX:
            lines.add((low + high) / 2)
    return sorted(lines)


def _grid(space: SearchSpace, ends: tuple[Point, Point]) -> tuple[list[float], list[float]]:
    """Build the grid lines of the search: x lines and y lines."""
    xs = {point[0] for point in ends}
    ys = {point[1] for point in ends}
    for left, top, right, bottom in space.obstacles:
        xs.update((left, right))
        ys.update((top, bottom))
    xs.update((min(xs) - OUTSIDE_MARGIN_PX, max(xs) + OUTSIDE_MARGIN_PX))
    ys.update((min(ys) - OUTSIDE_MARGIN_PX, max(ys) + OUTSIDE_MARGIN_PX))
    return _corridors(xs), _corridors(ys)


def _line_cost(space: SearchSpace, start: Point, end: Point) -> float:
    """Return the extra cost of a step: along another line, or across one."""
    extra = 0.0
    horizontal = abs(start[1] - end[1]) < SAME_LINE_PX
    low, high = sorted((start[0], end[0]) if horizontal else (start[1], end[1]))
    fixed = start[1] if horizontal else start[0]
    for first, second in space.lines:
        other_horizontal = abs(first[1] - second[1]) < SAME_LINE_PX
        other_low, other_high = sorted(
            (first[0], second[0]) if other_horizontal else (first[1], second[1])
        )
        other_fixed = first[1] if other_horizontal else first[0]
        if other_horizontal == horizontal:
            if abs(other_fixed - fixed) < SAME_LINE_PX:
                extra += OVERLAP_COST_PER_PX * max(0.0, min(high, other_high) - max(low, other_low))
        elif low < other_fixed < high and other_low < fixed < other_high:
            extra += CROSSING_COST_PX
    return extra


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
        self.xs, self.ys = _grid(space, (start, end))
        self.goal = (self.xs.index(end[0]), self.ys.index(end[1]))
        self.first: State = (self.xs.index(start[0]), self.ys.index(start[1]), -1)
        self.best: dict[State, float] = {self.first: 0.0}
        self.parent: dict[State, State] = {}
        self.ticket = count()
        self.queue = [(0.0, next(self.ticket), self.first)]

    def point(self, column: int, row: int) -> Point:
        """Return the coordinates of a grid crossing."""
        return (self.xs[column], self.ys[row])

    def expand(self, state: State) -> None:
        """Push every step that can be taken from a state."""
        column, row, heading = state
        for direction, (step_x, step_y) in enumerate(DIRECTIONS):
            target = (column + step_x, row + step_y)
            if not (0 <= target[0] < len(self.xs) and 0 <= target[1] < len(self.ys)):
                continue
            here, there = self.point(column, row), self.point(*target)
            if _blocked(self.space, here, there):
                continue
            bend = BEND_COST_PX if heading not in (-1, direction) else 0.0
            step = abs(there[0] - here[0]) + abs(there[1] - here[1])
            cost = self.best[state] + step + bend + _line_cost(self.space, here, there)
            key = (target[0], target[1], direction)
            if cost < self.best.get(key, float("inf")):
                self.best[key] = cost
                self.parent[key] = state
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
