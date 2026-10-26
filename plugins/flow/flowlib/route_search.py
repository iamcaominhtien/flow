"""Search the right-angled route of a line that costs least, over sides, reach and channels.

A caller describes a line as a ``Plan`` (two boxes, the sides to try first, where along those
sides to attach) and the scene as a ``Search`` (the boxes in the way, the lines already drawn).
``best_route`` tries every pair of sides and a few channel positions, scores each route, and
returns the cheapest: it passes through no box, crosses the fewest lines, runs on top of none,
has the fewest bends, and prefers the sides of the plan.
"""

from dataclasses import dataclass
from itertools import product

from .check import Rect
from .model import Node, Point
from .orthogonal import (
    Anchor,
    Facing,
    anchor_on,
    bend_count,
    count_crossings,
    is_clear,
    path_between,
    route_length,
    shared_length,
    simplify,
)

CHANNEL_STEPS = (0, 1, -1, 2, -2)  # in units of ``Search.channel_step``
BLOCKED_COST = 1000.0
OUTSIDE_COST = 800.0
OVERLAP_COST = 500.0
CROSSING_COST = 10.0
BEND_COST = 4.0
OTHER_SIDES_COST = 6.0
LENGTH_COST_PER_PX = 0.005


@dataclass(frozen=True)
class Plan:
    """The two boxes a line joins, the sides it is first tried on and where it attaches."""

    source: Node
    target: Node
    sides: tuple[Facing, Facing]
    start_offset: float = 0.0
    end_offset: float = 0.0


@dataclass(frozen=True)
class Search:
    """What a route is scored against.

    ``bounds`` is the rectangle of the whole diagram, which a U may go round. ``limit``, when
    set, is a rectangle the route must stay in, such as the pool a sequence flow belongs to.
    """

    obstacles: list[Rect]
    taken: list[list[Point]]
    bounds: Rect
    channel_step: float
    clearance: float
    limit: Rect | None = None


def best_route(plan: Plan, search: Search) -> list[Point]:
    """Return the cheapest route of a line.

    Args:
        plan: The line.
        search: The scene it is routed in.

    Returns:
        The points of the route, at most two bends when any such route exists; a direct line
        between the first-choice sides when none does.
    """
    best: tuple[float, list[Point]] | None = None
    for sides, step, is_far in product(product(Facing, Facing), CHANNEL_STEPS, (False, True)):
        route = _try(plan, sides, step * search.channel_step, (search, is_far))
        if route is None:
            continue
        cost = score_route(route, search, sides != plan.sides)
        if best is None or cost < best[0]:
            best = (cost, route)
    if best is None:
        return [
            anchor_on(plan.source, plan.sides[0]).point,
            anchor_on(plan.target, plan.sides[1]).point,
        ]
    return best[1]


def _try(
    plan: Plan, sides: tuple[Facing, Facing], shift: float, how: tuple[Search, bool]
) -> list[Point] | None:
    """Return the route of a line on a pair of sides with its channel moved by ``shift``."""
    search, is_far = how
    is_first_choice = sides == plan.sides
    start = anchor_on(plan.source, sides[0], plan.start_offset if is_first_choice else 0.0)
    end = anchor_on(plan.target, sides[1], plan.end_offset if is_first_choice else 0.0)
    reach = _reach(start, end, search) if is_far else search.clearance
    route = path_between(start, end, shift, reach)
    return simplify(route) if route else None


def _reach(start: Anchor, end: Anchor, search: Search) -> float:
    """Return how far a U must go to pass every box: past the farthest edge of the diagram."""
    bounds = search.limit or search.bounds
    (start_x, start_y), (end_x, end_y) = start.point, end.point
    past = {
        Facing.SOUTH: bounds.bottom - max(start_y, end_y),
        Facing.NORTH: min(start_y, end_y) - bounds.top,
        Facing.EAST: bounds.right - max(start_x, end_x),
        Facing.WEST: min(start_x, end_x) - bounds.left,
    }[start.facing]
    return max(past, 0.0) + search.clearance


def score_route(route: list[Point], search: Search, is_other_side: bool = False) -> float:
    """Score a route: a lower score is better."""
    cost = 0.0 if is_clear(route, search.obstacles) else BLOCKED_COST
    cost += OUTSIDE_COST * _leaves(route, search.limit)
    cost += OVERLAP_COST * (shared_length(route, search.taken) > 0)
    cost += CROSSING_COST * count_crossings(route, search.taken)
    cost += BEND_COST * bend_count(route)
    cost += OTHER_SIDES_COST * is_other_side
    return cost + LENGTH_COST_PER_PX * route_length(route)


def _leaves(route: list[Point], limit: Rect | None) -> bool:
    """Tell whether a route has a point outside the rectangle it must stay in."""
    if limit is None:
        return False
    return any(
        not (limit.left <= x <= limit.right and limit.top <= y <= limit.bottom) for x, y in route
    )
