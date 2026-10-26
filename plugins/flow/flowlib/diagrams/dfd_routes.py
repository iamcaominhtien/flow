"""Route the flows of a data flow diagram: straight or orthogonal, at most two bends.

Two flows that run between the same two boxes, one each way, are drawn side by side, 60 px
apart. Flows that share one side of a box are spread along it the same way. A flow that cannot
go straight is tried on every pair of sides and on a few channel positions; the route that
crosses the fewest lines and passes through no box wins.
"""

from dataclasses import replace

from ..check import Rect, node_rect
from ..model import Node, Point
from ..orthogonal import (
    HORIZONTAL,
    Facing,
)
from ..route_search import Plan, Search, best_route
from ..theme import DfdRules
from .dfd_spec import Flow

SAME_ROW_FRACTION = 0.25  # boxes whose centres are this close, in rows, are in one row
SIDE_MARGIN_PX = 8  # a line keeps this far from the corners of a box side


def route_flows(
    nodes: dict[str, Node], flows: tuple[Flow, ...], rules: DfdRules
) -> list[list[Point]]:
    """Route every flow.

    Args:
        nodes: The boxes by element id.
        flows: The flows, in the order they are drawn.
        rules: The sizes of the data flow diagram.

    Returns:
        One route per flow, in the same order.
    """
    plans = _spread([_plan(flow, nodes, rules) for flow in flows], rules)
    routes = _route_all(plans, nodes, rules)
    settled = _spread(
        [replace(p, sides=_sides_of(r, p)) for p, r in zip(plans, routes, strict=True)], rules
    )
    return _route_all(settled, nodes, rules)


def _route_all(plans: list[Plan], nodes: dict[str, Node], rules: DfdRules) -> list[list[Point]]:
    """Route the flows one after the other, each avoiding the lines drawn before it."""
    bounds = _bounds(list(nodes.values()))
    routes: list[list[Point]] = []
    for plan in plans:
        obstacles = [
            node_rect(node)
            for node in nodes.values()
            if node.id not in (plan.source.id, plan.target.id)
        ]
        search = Search(obstacles, routes, bounds, rules.channel_step, rules.channel_clearance)
        routes.append(best_route(plan, search))
    return routes


def _sides_of(route: list[Point], plan: Plan) -> tuple[Facing, Facing]:
    """Return the sides of its two boxes that a routed flow really uses."""
    return (_side_at(plan.source, route[0]), _side_at(plan.target, route[-1]))


def _side_at(node: Node, point: Point) -> Facing:
    """Return the side of a node that a point on its border is on."""
    distances = {
        Facing.WEST: abs(point[0] - node.x),
        Facing.EAST: abs(point[0] - node.x - node.width),
        Facing.NORTH: abs(point[1] - node.y),
        Facing.SOUTH: abs(point[1] - node.y - node.height),
    }
    return min(distances, key=lambda side: distances[side])


def _plan(flow: Flow, nodes: dict[str, Node], rules: DfdRules) -> Plan:
    """Choose the first-choice sides of a flow from where its two boxes are."""
    source, target = nodes[flow.source], nodes[flow.target]
    delta_x = (target.x + target.width / 2) - (source.x + source.width / 2)
    delta_y = (target.y + target.height / 2) - (source.y + source.height / 2)
    if abs(delta_y) < rules.row_pitch * SAME_ROW_FRACTION:
        sides = (Facing.EAST, Facing.WEST) if delta_x > 0 else (Facing.WEST, Facing.EAST)
    elif abs(delta_x) < rules.column_pitch * SAME_ROW_FRACTION:
        sides = (Facing.SOUTH, Facing.NORTH) if delta_y > 0 else (Facing.NORTH, Facing.SOUTH)
    else:
        sides = (Facing.SOUTH, Facing.NORTH) if delta_y > 0 else (Facing.NORTH, Facing.SOUTH)
    return Plan(source, target, sides)


def _spread(plans: list[Plan], rules: DfdRules) -> list[Plan]:
    """Spread the flows that use the same side of a box along that side, 60 px apart."""
    groups: dict[tuple[str, Facing], list[tuple[int, bool, float]]] = {}
    for index, plan in enumerate(plans):
        source_key = (plan.source.id, plan.sides[0])
        target_key = (plan.target.id, plan.sides[1])
        groups.setdefault(source_key, []).append((index, True, _along(plan.target, plan.sides[0])))
        groups.setdefault(target_key, []).append((index, False, _along(plan.source, plan.sides[1])))
    offsets: dict[tuple[int, bool], float] = {}
    nodes = {plan.source.id: plan.source for plan in plans}
    nodes.update({plan.target.id: plan.target for plan in plans})
    for (node_id, facing), members in groups.items():
        for rank, (index, is_start, _) in enumerate(sorted(members, key=lambda m: (m[2], m[0]))):
            offsets[(index, is_start)] = _slot(nodes[node_id], facing, (rank, len(members)), rules)
    return [
        Plan(p.source, p.target, p.sides, offsets[(i, True)], offsets[(i, False)])
        for i, p in enumerate(plans)
    ]


def _along(other: Node, facing: Facing) -> float:
    """Return where the other end of a flow is along the side it leaves, to order the flows."""
    if facing in HORIZONTAL:
        return other.y + other.height / 2
    return other.x + other.width / 2


def _slot(node: Node, facing: Facing, place: tuple[int, int], rules: DfdRules) -> float:
    """Return how far the ``rank``-th of ``count`` flows is from the middle of a side."""
    rank, count = place
    length = node.height if facing in HORIZONTAL else node.width
    gap = min(rules.pair_gap, (length - 2 * SIDE_MARGIN_PX) / max(count - 1, 1))
    return (rank - (count - 1) / 2) * gap


def _bounds(nodes: list[Node]) -> Rect:
    """Return the rectangle that holds every box."""
    rects = [node_rect(node) for node in nodes]
    return Rect(
        min(r.left for r in rects),
        min(r.top for r in rects),
        max(r.right for r in rects),
        max(r.bottom for r in rects),
    )
