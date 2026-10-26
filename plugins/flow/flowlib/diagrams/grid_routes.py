"""Route the lines of a diagram that sits on a grid: straight or orthogonal, at most two bends.

Data flow, C4, cloud and architecture diagrams all use it.

Two flows that run between the same two boxes, one each way, are drawn side by side, 60 px
apart. Flows that share one side of a box are spread along it the same way. A flow that cannot
go straight is tried on every pair of sides and on a few channel positions; the route that
crosses the fewest lines and passes through no box wins.
"""

from dataclasses import dataclass, field, replace
from typing import Protocol

from ..check import Rect, node_rect
from ..model import Node, Point
from ..orthogonal import (
    HORIZONTAL,
    Facing,
)
from ..route_search import Plan, Search, best_route

SAME_ROW_FRACTION = 0.25  # boxes whose centres are this close, in rows, are in one row
SIDE_MARGIN_PX = 8  # a line keeps this far from the corners of a box side


class RouteRules(Protocol):
    """The spacing a diagram gives to its lines; every grid diagram's rules have these."""

    @property
    def row_pitch(self) -> float:
        """Return the distance between two rows."""

    @property
    def column_pitch(self) -> float:
        """Return the distance between two columns."""

    @property
    def pair_gap(self) -> float:
        """Return the distance between two lines that share a side of a box."""

    @property
    def channel_step(self) -> float:
        """Return the step in which a channel is moved to find a free route."""

    @property
    def channel_clearance(self) -> float:
        """Return how far a U goes round a box."""


class Link(Protocol):
    """A line to route: the ids of the box or frame at each end."""

    @property
    def source(self) -> str:
        """Return the id where the line starts."""

    @property
    def target(self) -> str:
        """Return the id where the line ends."""


@dataclass(frozen=True)
class GridSpacing:
    """The spacing of a diagram whose rules do not carry the names ``RouteRules`` asks for."""

    row_pitch: float
    column_pitch: float
    pair_gap: float
    channel_step: float
    channel_clearance: float


@dataclass(frozen=True)
class Extras:
    """What a diagram adds to its boxes: frames a line may start or end on, and areas to avoid.

    ``frames`` holds the frame of each id as a node of its size. A line that ends on a frame
    ignores the boxes inside it. ``blocked`` are rectangles no line may cross, such as the pill
    that names a frame.
    """

    frames: dict[str, Node] = field(default_factory=dict)
    blocked: list[Rect] = field(default_factory=list)


def route_flows(
    nodes: dict[str, Node],
    flows: tuple[Link, ...],
    rules: RouteRules,
    extras: Extras | None = None,
) -> list[list[Point]]:
    """Route every line.

    Args:
        nodes: The boxes by element id.
        flows: The lines, in the order they are drawn. A frame may be an end: put it in ``nodes``
            as a node of its size.
        rules: The spacing of the diagram.
        extras: Frames that are line ends and areas to avoid; none by default.

    Returns:
        One route per flow, in the same order.
    """
    extras = extras or Extras()
    ends = {**nodes, **extras.frames}
    plans = _spread([_plan(flow, ends, rules) for flow in flows], rules)
    routes = _route_all(plans, nodes, (rules, extras))
    settled = _spread(
        [replace(p, sides=_sides_of(r, p)) for p, r in zip(plans, routes, strict=True)], rules
    )
    return _route_all(settled, nodes, (rules, extras))


def _route_all(
    plans: list[Plan], nodes: dict[str, Node], setting: tuple[RouteRules, Extras]
) -> list[list[Point]]:
    """Route the flows one after the other, each avoiding the lines drawn before it."""
    rules, extras = setting
    bounds = _bounds(list(nodes.values()))
    routes: list[list[Point]] = []
    for plan in plans:
        ends = [node_rect(plan.source), node_rect(plan.target)]
        obstacles = [
            node_rect(node)
            for node in nodes.values()
            if node.id not in (plan.source.id, plan.target.id)
            and not any(_is_inside(node_rect(node), end) for end in ends)
        ]
        search = Search(
            obstacles + extras.blocked, routes, bounds, rules.channel_step, rules.channel_clearance
        )
        routes.append(best_route(plan, search))
    return routes


def _is_inside(inner: Rect, outer: Rect) -> bool:
    """Tell whether a rectangle lies wholly inside another."""
    return (
        outer.left <= inner.left
        and outer.top <= inner.top
        and inner.right <= outer.right
        and inner.bottom <= outer.bottom
    )


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


def _plan(flow: Link, nodes: dict[str, Node], rules: RouteRules) -> Plan:
    """Choose the first-choice sides of a flow from where its two boxes are."""
    source, target = nodes[flow.source], nodes[flow.target]
    delta_x = (target.x + target.width / 2) - (source.x + source.width / 2)
    delta_y = (target.y + target.height / 2) - (source.y + source.height / 2)
    across, down = abs(delta_x) / rules.column_pitch, abs(delta_y) / rules.row_pitch
    if down < SAME_ROW_FRACTION or (across > down and across >= 1):
        sides = (Facing.EAST, Facing.WEST) if delta_x > 0 else (Facing.WEST, Facing.EAST)
    else:
        sides = (Facing.SOUTH, Facing.NORTH) if delta_y > 0 else (Facing.NORTH, Facing.SOUTH)
    return Plan(source, target, sides)


def _spread(plans: list[Plan], rules: RouteRules) -> list[Plan]:
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


def _slot(node: Node, facing: Facing, place: tuple[int, int], rules: RouteRules) -> float:
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
