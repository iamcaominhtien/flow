"""Part the two arrows between a frame and a decision right above or below it.

A frame and a decision in one column join by straight vertical arrows. When the arrows run both
ways (``Sign up`` to ``Sign-up ok?`` and the ``rejected`` exit back), both meet the decision's
one top or bottom tip, so they run on top of each other and make a hook. Here the arrow that
leaves the decision is drawn from a free side tip instead: out sideways, then into the frame,
and the arrow into the decision is made straight.
"""

from collections import defaultdict

from ..model import Node, Point, Shape
from .screen_plan import Plan, RouteType

OUT_PX = 36  # how far beside the decision the parted arrow runs
INTO_SIDE = 0.75  # where on a frame's side the parted arrow enters, from its top, when it must

Routed = tuple[Plan, tuple[Point, ...]]


def part_tip_pairs(routes: list[Routed], nodes: dict[str, Node], clear: float) -> list[Routed]:
    """Redraw each pair of vertical arrows that share a decision's tip.

    Args:
        routes: Every arrow with its route.
        nodes: The placed nodes.
        clear: How far from a frame's corner an arrow may enter its top or bottom.

    Returns:
        The routes, with the pairs parted; every other route as it was.
    """
    pairs: dict[frozenset[str], list[int]] = defaultdict(list)
    for number, (plan, _) in enumerate(routes):
        ends = (plan.transition.source, plan.transition.target)
        is_decision = [nodes[end].shape is Shape.DECISION for end in ends]
        if plan.route is RouteType.VERTICAL and is_decision[0] != is_decision[1]:
            pairs[frozenset(ends)].append(number)
    parted = list(routes)
    used = _used_tips(routes, nodes)
    for numbers in pairs.values():
        outgoing = [
            n for n in numbers if nodes[routes[n][0].transition.source].shape is Shape.DECISION
        ]
        incoming = [n for n in numbers if n not in outgoing]
        if not outgoing or not incoming:
            continue
        decision = nodes[routes[outgoing[0]][0].transition.source]
        frame = nodes[routes[outgoing[0]][0].transition.target]
        side = _free_side(decision, used)
        if side is None:
            continue
        used.add((decision.id, side))
        plan = routes[outgoing[0]][0]
        parted[outgoing[0]] = (plan, _side_route(decision, frame, (side, clear)))
        for number in incoming:
            parted[number] = (routes[number][0], _straight(frame, decision))
    return parted


def _used_tips(routes: list[Routed], nodes: dict[str, Node]) -> set[tuple[str, int]]:
    """Return the side tips of decisions that arrows already use: (id, -1 west or 1 east)."""
    used = set()
    for plan, points in routes:
        for node_id, point in (
            (plan.transition.source, points[0]),
            (plan.transition.target, points[-1]),
        ):
            node = nodes[node_id]
            if node.shape is not Shape.DECISION:
                continue
            middle = node.x + node.width / 2
            if abs(point[1] - (node.y + node.height / 2)) < 1 and abs(point[0] - middle) > 1:
                used.add((node_id, 1 if point[0] > middle else -1))
    return used


def _free_side(decision: Node, used: set[tuple[str, int]]) -> int | None:
    """Return a side tip of the decision that no arrow uses, east first."""
    return next((side for side in (1, -1) if (decision.id, side) not in used), None)


def _side_route(decision: Node, frame: Node, where: tuple[int, float]) -> tuple[Point, ...]:
    """Draw an arrow out of a decision's side tip and into the frame above or below it."""
    side, clear = where
    middle_y = decision.y + decision.height / 2
    tip = (decision.x + decision.width / 2 + side * decision.width / 2, middle_y)
    out_x = tip[0] + side * OUT_PX
    is_above = frame.y < decision.y
    edge_y = frame.y + frame.height if is_above else frame.y
    if frame.x + clear <= out_x <= frame.x + frame.width - clear:
        return (tip, (out_x, middle_y), (out_x, edge_y))
    side_x = frame.x + frame.width if side > 0 else frame.x
    entry_y = frame.y + frame.height * (INTO_SIDE if is_above else 1 - INTO_SIDE)
    beside_x = side_x + side * OUT_PX
    return (tip, (beside_x, middle_y), (beside_x, entry_y), (side_x, entry_y))


def _straight(frame: Node, decision: Node) -> tuple[Point, ...]:
    """Draw the arrow from a frame straight down or up into the decision's facing tip."""
    middle_x = decision.x + decision.width / 2
    if frame.y < decision.y:
        return ((middle_x, frame.y + frame.height), (middle_x, decision.y))
    return ((middle_x, frame.y), (middle_x, decision.y + decision.height))
