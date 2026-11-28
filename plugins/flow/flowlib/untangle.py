"""Give every line a script drew by hand a way of its own where lines of different kinds meet.

A reader tells lines apart by their kind: their role (colour) and their dash. Two lines of
different kinds that leave one tip of a decision, run on top of each other, or end at one point
of a node cannot be told apart. The author kit runs these passes on the lines as drawn:

1. An exit of a decision that shares a tip with another kind moves to a free tip facing its
   target, when one is free.
2. A stretch that runs on top of another kind is pushed a track or two aside; when that fails,
   a new way is searched.
3. The ends that still meet at one point are spread along the side (``ports.spread_ends``).

Each move is weighed: it may pass through no new node, and it may add at most one crossing,
because a line on top of another hides it and a crossing does not.
"""

from dataclasses import dataclass, field, replace
from itertools import combinations, pairwise

from .model import Edge, Node, Point, Role, Shape
from .pathfind import SearchSpace, find_route, path_cost
from .ports import (
    OUTWARD,
    SAME_LINE_TOLERANCE_PX,
    SEARCH_MARGIN_PX,
    STUB_PX,
    Port,
    attach,
    end_side,
    hits,
    kind_of,
    middle,
    run_from_end,
    simplify,
    spread_ends,
)

MIN_OVERLAP_PX: float = 32.0  # a shorter shared stretch is a junction at a node, not an overlap
UNTANGLE_ROUNDS: int = 3  # times the lines still on top of another kind are tried again
NUDGE_OFFSETS_PX: tuple[float, ...] = (-16.0, 16.0, -32.0, 32.0)  # a track or two aside
CROSSINGS_A_PART_MAY_ADD: int = 1  # parting two lines is worth one more crossing


@dataclass
class _Lines:
    """The lines being untangled: their points, the nodes, and what may not move or was tried."""

    routes: dict[Edge, list[Point]]
    nodes: dict[str, Node]
    keep: frozenset[Edge]
    failed: set[tuple[Edge, tuple[Point, ...]]] = field(default_factory=set)

    def others(self, edge: Edge) -> list[tuple[Point, Point]]:
        """Return the stretches of every line but one.

        Args:
            edge: The line left out.

        Returns:
            The stretches.
        """
        return [
            stretch
            for other, points in self.routes.items()
            if other is not edge
            for stretch in pairwise(points)
        ]

    def is_clear(self, points: list[Point], ends: tuple[str, str]) -> bool:
        """Tell whether a route passes through no node; it may touch its ends where it attaches.

        Args:
            points: The route.
            ends: The ids of its source and its target.

        Returns:
            True when it passes through no other node.
        """
        last = len(points) - 2
        for index, (start, end) in enumerate(pairwise(points)):
            for node_id, node in self.nodes.items():
                attaches = (node_id == ends[0] and index == 0) or (
                    node_id == ends[1] and index == last
                )
                if not attaches and hits(node, start, end):
                    return False
        return True

    def take(self, edge: Edge, points: list[Point]) -> bool:
        """Put a new route in place when it is clear of new nodes and adds at most one crossing.

        Args:
            edge: The line.
            points: Its new route.

        Returns:
            Whether the route was taken.
        """
        old = self.routes[edge]
        ends = (edge.source, edge.target)
        if not self.is_clear(points, ends) and self.is_clear(old, ends):
            return False
        lines = self.others(edge)
        if _crossings(points, lines) > _crossings(old, lines) + CROSSINGS_A_PART_MAY_ADD:
            return False
        self.routes[edge] = points
        return True


@dataclass(frozen=True)
class _Ends:
    """The two nodes a searched line joins, and the sides of its source it may not leave by."""

    source: Node
    target: Node
    banned: frozenset[Port] = frozenset()


def untangle(edges: list[Edge], nodes: dict[str, Node]) -> list[Edge]:
    """Give each line its own tip, its own stretch and its own end point.

    A line that carries words (a screen flow arrow) keeps its route, because its words are
    placed along it by hand, but other lines keep clear of it. A moved line's label goes to the
    middle of its longest stretch.

    Args:
        edges: The lines as drawn.
        nodes: Every node, by id.

    Returns:
        The lines in the same order, some with new points.
    """
    joined = [edge for edge in edges if edge.source in nodes and edge.target in nodes]
    lines = _Lines(
        {edge: simplify(list(edge.points)) for edge in joined},
        nodes,
        frozenset(edge for edge in joined if edge.extras),
    )
    _free_tips(lines)
    _part_overlaps(lines)
    lines.routes = spread_ends(lines.routes, nodes, lines.is_clear, lines.keep)
    return [_moved(edge, lines.routes.get(edge)) for edge in edges]


def shared_length(first: list[Point], second: list[Point]) -> float:
    """Return the longest stretch two routes run on top of each other.

    Args:
        first: One route.
        second: The other.

    Returns:
        The length, 0 when they share no stretch.
    """
    return max(
        (_overlap(one, other) for one in pairwise(first) for other in pairwise(second)),
        default=0.0,
    )


def _free_tips(lines: _Lines) -> None:
    """Move an exit of a decision off a tip that a line of another kind leaves by.

    The kind of the first exit (the main path, when one leaves there) keeps the tip; a lone
    line of another kind searches from a tip that no line uses and that faces its target.
    Several lines of one kind on a tip are the branches of a switch: they stay together, and
    their trunk is moved along the border as one. When no tip is free, or the new way is not
    worth it, the line stays and its start is spread along the border.

    Args:
        lines: The lines; changed in place.
    """
    for (node_id, _), exits in _exits_by_tip(lines).items():
        exits.sort(key=lambda edge: edge.role is not Role.MAIN)
        for edge in exits:
            same_kind = [other for other in exits if kind_of(other) == kind_of(edge)]
            if edge in lines.keep or kind_of(edge) == kind_of(exits[0]) or len(same_kind) > 1:
                continue
            source, target = lines.nodes[node_id], lines.nodes[edge.target]
            in_use = _sides_in_use(lines.routes, node_id)
            free = {port for port in Port if port not in in_use and _faces(source, target, port)}
            if free:
                found = _search(
                    _Ends(source, target, frozenset(Port) - free), lines.others(edge), lines.nodes
                )
                if found is not None:
                    lines.take(edge, found)


def _exits_by_tip(lines: _Lines) -> dict[tuple[str, Port], list[Edge]]:
    """Return the exits of every decision, by the tip they leave from.

    Args:
        lines: The lines.

    Returns:
        Each decision's id and tip to the lines that leave by it.
    """
    by_tip: dict[tuple[str, Port], list[Edge]] = {}
    for edge, points in lines.routes.items():
        if lines.nodes[edge.source].shape is Shape.DECISION:
            by_tip.setdefault((edge.source, end_side(points, True)), []).append(edge)
    return by_tip


def _sides_in_use(routes: dict[Edge, list[Point]], node_id: str) -> frozenset[Port]:
    """Return the sides of a node that a line leaves or enters by.

    Args:
        routes: Each line's points.
        node_id: The node.

    Returns:
        The sides.
    """
    sides = {end_side(points, True) for edge, points in routes.items() if edge.source == node_id}
    sides |= {end_side(points, False) for edge, points in routes.items() if edge.target == node_id}
    return frozenset(sides)


def _part_overlaps(lines: _Lines) -> None:
    """Part the lines that run on top of a line of another kind, for a few rounds.

    Of the two, a line off the main path moves first, the one drawn later before the other;
    when it cannot move, the other one tries. A pair is looked at again before each move,
    because an earlier move may already have parted it. Two lines that only share the last
    stretch into a common point are left to ``spread_ends``.

    Args:
        lines: The lines; changed in place.
    """
    for _ in range(UNTANGLE_ROUNDS):
        pairs = _overlapping_pairs(lines)
        if not pairs:
            return
        for first, second in pairs:
            if not _overlap_beyond_ends(first, second, lines.routes):
                continue
            for mover in _movers(first, second, lines.keep):
                if _nudge(mover, lines) or _new_way(mover, lines):
                    break


def _overlapping_pairs(lines: _Lines) -> list[tuple[Edge, Edge]]:
    """Return the pairs of lines of different kinds that run on top of each other.

    Args:
        lines: The lines.

    Returns:
        The pairs, in the order the lines were drawn.
    """
    return [
        (first, second)
        for first, second in combinations(lines.routes, 2)
        if kind_of(first) != kind_of(second) and _overlap_beyond_ends(first, second, lines.routes)
    ]


def _movers(first: Edge, second: Edge, keep: frozenset[Edge]) -> list[Edge]:
    """Return the lines of a pair that may move, the one to try first first.

    Args:
        first: The line drawn first.
        second: The line drawn later.
        keep: The lines that must not move.

    Returns:
        The lines to try, in order.
    """
    order = [second, first] if second.role is not Role.MAIN else [first, second]
    return [edge for edge in order if edge not in keep]


def _nudge(edge: Edge, lines: _Lines) -> bool:
    """Push a stretch of a line that runs on top of another kind a track or two aside.

    Only a stretch between two bends moves; the bends absorb the move, so the line stays
    right-angled and keeps its ends. The push is kept when the line then runs on top of no line
    of another kind.

    Args:
        edge: The line to push.
        lines: The lines; changed when the push is kept.

    Returns:
        Whether the line was moved.
    """
    points = lines.routes[edge]
    for index in range(1, len(points) - 2):
        for offset in NUDGE_OFFSETS_PX:
            tried = _pushed(points, index, offset)
            if not _runs_on_other_kind(edge, tried, lines.routes) and lines.take(edge, tried):
                return True
    return False


def _new_way(edge: Edge, lines: _Lines) -> bool:
    """Search a new way for a line, kept when it costs less and runs on no other kind.

    A search that found nothing worth taking is not run again for the same route.

    Args:
        edge: The line to search again.
        lines: The lines; changed when the new way is kept.

    Returns:
        Whether the line was moved.
    """
    old = lines.routes[edge]
    attempt = (edge, tuple(old))
    if attempt in lines.failed:
        return False
    lines.failed.add(attempt)
    taken = {
        end_side(points, True)
        for other, points in lines.routes.items()
        if other.source == edge.source and other is not edge
    }
    source = lines.nodes[edge.source]
    banned = frozenset(taken) if source.shape is Shape.DECISION else frozenset()
    found = _search(
        _Ends(source, lines.nodes[edge.target], banned), lines.others(edge), lines.nodes
    )
    if found is None or _runs_on_other_kind(edge, found, lines.routes):
        return False
    space = SearchSpace((), tuple(lines.others(edge)))
    return path_cost(space, found) < path_cost(space, old) and lines.take(edge, found)


def _pushed(points: list[Point], index: int, offset: float) -> list[Point]:
    """Return a route with one inner stretch moved sideways by ``offset``.

    Args:
        points: The route.
        index: The first point of the stretch to move.
        offset: How far it moves, across the stretch.

    Returns:
        A new route.
    """
    start, end = points[index], points[index + 1]
    across = 0 if abs(start[0] - end[0]) < SAME_LINE_TOLERANCE_PX else 1
    pushed = list(points)
    for at in (index, index + 1):
        point = list(pushed[at])
        point[across] += offset
        pushed[at] = (point[0], point[1])
    return pushed


def _runs_on_other_kind(edge: Edge, points: list[Point], routes: dict[Edge, list[Point]]) -> bool:
    """Tell whether a route runs on top of a line of another kind, beyond shared end points.

    Args:
        edge: The line.
        points: The route to try for it.
        routes: Each line's points.

    Returns:
        True when it does.
    """
    trial = {**routes, edge: points}
    return any(
        kind_of(other) != kind_of(edge) and _overlap_beyond_ends(edge, other, trial)
        for other in routes
        if other is not edge
    )


def _overlap_beyond_ends(first: Edge, second: Edge, routes: dict[Edge, list[Point]]) -> bool:
    """Tell whether two lines run on top of each other other than into a point they share.

    Two lines into one point overlap along their last straight stretch; spreading their ends
    parts them, so that stretch is left out here.

    Args:
        first: One line.
        second: The other.
        routes: Each line's points.

    Returns:
        True when they share a stretch of at least the overlap length.
    """
    first_points, second_points = routes[first], routes[second]
    if first_points[0] == second_points[0]:
        first_points, second_points = _beyond(first_points, True), _beyond(second_points, True)
    if first_points[-1] == second_points[-1]:
        first_points, second_points = _beyond(first_points, False), _beyond(second_points, False)
    return shared_length(first_points, second_points) >= MIN_OVERLAP_PX


def _beyond(points: list[Point], at_start: bool) -> list[Point]:
    """Return a route without the straight stretch at one end, keeping the bend it ends at.

    Args:
        points: The route.
        at_start: True to drop the stretch at the start, False at the end.

    Returns:
        The shorter route; the route itself when it has no bend.
    """
    run = run_from_end(points, at_start)
    if run >= len(points):
        return points
    return points[run - 1 :] if at_start else points[: len(points) - run + 1]


def _crossings(points: list[Point], lines: list[tuple[Point, Point]]) -> int:
    """Return how many of the lines a route crosses in the middle of both.

    Args:
        points: The route.
        lines: The stretches of the other lines.

    Returns:
        The number of crossings.
    """
    return sum(_cross(stretch, line) for stretch in pairwise(points) for line in lines)


def _cross(first: tuple[Point, Point], second: tuple[Point, Point]) -> bool:
    """Tell whether a horizontal and a vertical segment cross inside both.

    Args:
        first: One segment.
        second: The other.

    Returns:
        True when they cross away from their ends.
    """
    for flat, upright in ((first, second), (second, first)):
        if (
            abs(flat[0][1] - flat[1][1]) < SAME_LINE_TOLERANCE_PX
            and abs(upright[0][0] - upright[1][0]) < SAME_LINE_TOLERANCE_PX
        ):
            low_x, high_x = sorted((flat[0][0], flat[1][0]))
            low_y, high_y = sorted((upright[0][1], upright[1][1]))
            x, y = upright[0][0], flat[0][1]
            return low_x < x < high_x and low_y < y < high_y
    return False


def _search(
    ends: _Ends, lines: list[tuple[Point, Point]], nodes: dict[str, Node]
) -> list[Point] | None:
    """Search the cheapest way between two nodes around every box and the lines drawn.

    The sides that face each other are tried first, every side only when those find nothing.

    Args:
        ends: The two nodes, and the sides the line may not leave by.
        lines: The stretches of the other lines.
        nodes: Every node, by id.

    Returns:
        The points, from a side of the source to a side of the target, or None.
    """
    space = SearchSpace(_obstacles(nodes), tuple(lines))
    leaving = [port for port in Port if port not in ends.banned]
    facing = [
        (leave, arrive)
        for leave in leaving
        for arrive in Port
        if _faces(ends.source, ends.target, leave) and _faces(ends.target, ends.source, arrive)
    ]
    every = [(leave, arrive) for leave in leaving for arrive in Port]
    return _best_way(facing, ends, space) or _best_way(every, ends, space)


def _best_way(
    pairs: list[tuple[Port, Port]], ends: _Ends, space: SearchSpace
) -> list[Point] | None:
    """Return the cheapest way found over the pairs of sides, or None.

    Args:
        pairs: The sides to leave and enter by.
        ends: The two nodes.
        space: The boxes and lines to keep off.

    Returns:
        The points of the cheapest way, or None.
    """
    best: tuple[float, list[Point]] | None = None
    for leave, arrive in pairs:
        found = find_route(space, _stub(ends.source, leave), _stub(ends.target, arrive))
        if found is None:
            continue
        points = simplify([attach(ends.source, leave), *found.points, attach(ends.target, arrive)])
        cost = path_cost(space, points)
        if best is None or cost < best[0]:
            best = (cost, points)
    return None if best is None else best[1]


def _faces(node: Node, other: Node, port: Port) -> bool:
    """Tell whether a side of a node looks towards another node.

    Args:
        node: The node.
        other: The node it should look towards.
        port: The side.

    Returns:
        True when the side points towards the other node.
    """
    out_x, out_y = OUTWARD[port]
    delta_x = other.x + other.width / 2 - (node.x + node.width / 2)
    delta_y = other.y + other.height / 2 - (node.y + node.height / 2)
    return out_x * delta_x + out_y * delta_y > SAME_LINE_TOLERANCE_PX


def _stub(node: Node, port: Port) -> Point:
    """Return the point straight out from one side of a node, past the search margin.

    Args:
        node: The node.
        port: The side.

    Returns:
        The point.
    """
    x, y = attach(node, port)
    out_x, out_y = OUTWARD[port]
    reach = SEARCH_MARGIN_PX + STUB_PX
    return (x + out_x * reach, y + out_y * reach)


def _obstacles(nodes: dict[str, Node]) -> tuple[tuple[float, float, float, float], ...]:
    """Return every node as a box grown by the search margin.

    Args:
        nodes: Every node, by id.

    Returns:
        The grown boxes.
    """
    margin = SEARCH_MARGIN_PX
    return tuple(
        (
            node.x - margin,
            node.y - margin,
            node.x + node.width + margin,
            node.y + node.height + margin,
        )
        for node in nodes.values()
    )


def _moved(edge: Edge, points: list[Point] | None) -> Edge:
    """Return a line with its new points, its label at the middle of its longest stretch.

    Args:
        edge: The line as drawn.
        points: Its untangled route, or None when it was left out.

    Returns:
        The line, changed only when its route changed.
    """
    if points is None or simplify(list(edge.points)) == points:
        return edge
    label = edge.label
    if label is not None:
        label = replace(label, at=middle(points))
    return replace(edge, points=tuple(points), label=label)


def _overlap(first: tuple[Point, Point], second: tuple[Point, Point]) -> float:
    """Return how long two horizontal or vertical segments run on one line together.

    Args:
        first: One segment.
        second: The other.

    Returns:
        The length, 0 when they are not on one line.
    """
    for along in (0, 1):
        across = 1 - along
        coordinates = (first[0][across], first[1][across], second[0][across], second[1][across])
        if max(coordinates) - min(coordinates) < SAME_LINE_TOLERANCE_PX:
            low = max(
                min(first[0][along], first[1][along]), min(second[0][along], second[1][along])
            )
            high = min(
                max(first[0][along], first[1][along]), max(second[0][along], second[1][along])
            )
            return max(0.0, high - low)
    return 0.0
