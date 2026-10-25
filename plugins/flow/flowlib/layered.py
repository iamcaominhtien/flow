"""Place the nodes of a flowchart on a grid of ranks (rows) and columns.

The happy path runs straight down one column. A branch that is not the main continuation
leaves sideways. Lines that return to an earlier step are kept out of the placement and
are routed around the flow later.
"""

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field

from .model import Role, Side
from .spec import Spec, SpecEdge

CONTINUATION_ORDER = {Role.MAIN: 0, Role.YES: 0, Role.NEXT: 0, Role.DATA: 1, Role.NO: 2}
LATE_ORDER = 3  # roles not listed above are placed after the others
SIDEWAYS_ROLES = (Role.NO,)  # a "no" exit stays on the row of its decision ...
CONTINUING_ROLES = (Role.YES, Role.NEXT, Role.MAIN)  # ... when another exit continues the flow


@dataclass(frozen=True)
class Grid:
    """Where every node sits: its row, its column, and which edges loop back."""

    rank: dict[str, int]
    column: dict[str, int]
    forward: tuple[SpecEdge, ...]
    returning: tuple[SpecEdge, ...]
    lane_columns: dict[int, tuple[int, ...]] = field(default_factory=dict)


def split_returning(spec: Spec) -> tuple[list[SpecEdge], list[SpecEdge]]:
    """Separate the edges that go forward from the ones that loop back.

    An edge loops back when its role is ``back`` or when it closes a cycle that the earlier
    edges already form.

    Args:
        spec: The flowchart description.

    Returns:
        The forward edges and the returning edges, each in spec order.
    """
    forward: list[SpecEdge] = []
    returning: list[SpecEdge] = []
    for edge in spec.edges:
        closes_cycle = edge.source in _descendants(edge.target, forward)
        if edge.role is Role.BACK or closes_cycle:
            returning.append(edge)
        else:
            forward.append(edge)
    return forward, returning


def _descendants(start: str, edges: list[SpecEdge]) -> set[str]:
    """Return every node reachable from ``start``, including ``start`` itself."""
    children: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        children[edge.source].append(edge.target)
    seen = {start}
    pending = [start]
    while pending:
        for child in children[pending.pop()]:
            if child not in seen:
                seen.add(child)
                pending.append(child)
    return seen


def sideways_edges(forward: list[SpecEdge]) -> set[SpecEdge]:
    """Pick the exits that leave sideways instead of continuing down.

    A "no" exit leaves sideways only when its node has another exit that continues the flow;
    when it is the only forward exit, it is the continuation and goes down.

    Args:
        forward: The forward edges.

    Returns:
        The edges that are placed beside their source, on the same row.
    """
    continuing = {edge.source for edge in forward if edge.role in CONTINUING_ROLES}
    return {edge for edge in forward if edge.role in SIDEWAYS_ROLES and edge.source in continuing}


def assign_ranks(
    spec: Spec,
    forward: list[SpecEdge],
    sideways: set[SpecEdge],
    minimum: dict[str, int] | None = None,
) -> dict[str, int]:
    """Give each node the row of its longest forward path from a start node.

    A sideways exit does not move its target down, so it lands on the row of its source.

    Args:
        spec: The flowchart description.
        forward: The forward edges, without cycles.
        sideways: The edges that stay on the row of their source.
        minimum: A row below which a node may not be placed; used to separate nodes that
            would otherwise share a lane and a row.

    Returns:
        Node id to row number, starting at 0.
    """
    rank = {node.id: (minimum or {}).get(node.id, 0) for node in spec.nodes}
    for _ in spec.nodes:
        for edge in forward:
            step = 0 if edge in sideways else 1
            rank[edge.target] = max(rank[edge.target], rank[edge.source] + step)
    return rank


def _children_in_order(node_id: str, forward: list[SpecEdge]) -> list[SpecEdge]:
    """Return the forward edges of a node, the main continuation first."""
    own = [edge for edge in forward if edge.source == node_id]
    return sorted(own, key=lambda edge: CONTINUATION_ORDER.get(edge.role, LATE_ORDER))


def _free_column(taken: set[tuple[int, int]], start: int, row: int, step: int) -> int:
    """Find the nearest column from ``start``, moving by ``step``, that is free in ``row``."""
    column = start
    while (row, column) in taken:
        column += step
    return column


def assign_columns(
    spec: Spec, rank: dict[str, int], forward: list[SpecEdge], sideways: set[SpecEdge]
) -> dict[str, int]:
    """Choose a column for every node.

    A node's main continuation stays in its column; other exits take the nearest free column
    on the requested side (right by default). Start nodes are spread to the right.

    Args:
        spec: The flowchart description.
        rank: Node id to row, from ``assign_ranks``.
        forward: The forward edges.
        sideways: The edges that leave beside their source.

    Returns:
        Node id to column; columns may be negative when a branch asks for the left side.
    """
    sides = {node.id: node.side for node in spec.nodes}
    has_parent = {edge.target for edge in forward}
    column: dict[str, int] = {}
    taken: set[tuple[int, int]] = set()

    def place(node_id: str, wanted: int, step: int) -> None:
        """Put a node in the nearest free column at or after ``wanted``."""
        chosen = _free_column(taken, wanted, rank[node_id], step)
        column[node_id] = chosen
        taken.add((rank[node_id], chosen))

    roots = [node.id for node in spec.nodes if node.id not in has_parent]
    for position, root in enumerate(roots):
        place(root, position, 1)
    waiting = Counter(edge.target for edge in forward)
    wants: dict[str, list[int]] = defaultdict(list)
    pending = deque(roots)
    while pending:
        node_id = pending.popleft()
        for index, edge in enumerate(_children_in_order(node_id, forward)):
            step = -1 if sides[edge.target] is Side.LEFT else 1
            offset = 0 if index == 0 and edge not in sideways else step
            wants[edge.target].append(column[node_id] + offset)
            waiting[edge.target] -= 1
            if waiting[edge.target] == 0:
                average = sum(wants[edge.target]) / len(wants[edge.target])
                place(edge.target, round(average), step)
                pending.append(edge.target)
    return column


def separate_lane_cells(
    spec: Spec,
    forward: list[SpecEdge],
    column: dict[str, int],
) -> dict[str, int]:
    """Give every node its own row within its lane, pushing later nodes down.

    Two nodes of one lane may reach the same row by different paths; the one that comes later
    in the spec moves down a row, and what follows it moves with it.

    Args:
        spec: The flowchart description.
        forward: The forward edges.
        column: Node id to its lane's column.

    Returns:
        Node id to row, with at most one node per lane and row.
    """
    minimum: dict[str, int] = {}
    while True:
        rank = assign_ranks(spec, forward, set(), minimum)
        taken: dict[tuple[int, int], str] = {}
        clash = None
        for node in spec.nodes:
            cell = (rank[node.id], column[node.id])
            if cell in taken:
                clash = node.id
                break
            taken[cell] = node.id
        if clash is None:
            return rank
        minimum[clash] = rank[clash] + 1


def assign_lane_columns(spec: Spec) -> dict[str, int]:
    """Give each node the column of its swimlane.

    Args:
        spec: A flowchart description whose nodes all name a lane.

    Returns:
        Node id to the position of its lane in ``spec.lanes``.
    """
    position = {lane.id: index for index, lane in enumerate(spec.lanes)}
    return {node.id: position[node.lane] for node in spec.nodes if node.lane is not None}


def split_lane_columns(
    spec: Spec, rank: dict[str, int]
) -> tuple[dict[str, int], dict[int, tuple[int, ...]]]:
    """Give each lane as many columns as its busiest row has nodes, and spread the nodes over them.

    Args:
        spec: A flowchart description whose nodes all name a lane.
        rank: Node id to row; several nodes of one lane may share a row.

    Returns:
        Node id to its column, and each lane's position to the columns it owns, in order.
    """
    lane_of = assign_lane_columns(spec)
    in_cell: dict[tuple[int, int], list[str]] = defaultdict(list)
    for node in spec.nodes:
        in_cell[(rank[node.id], lane_of[node.id])].append(node.id)
    width = dict.fromkeys(range(len(spec.lanes)), 1)
    for (_, lane), members in in_cell.items():
        width[lane] = max(width[lane], len(members))
    first, columns = 0, {}
    lane_columns = {}
    for lane in range(len(spec.lanes)):
        lane_columns[lane] = tuple(range(first, first + width[lane]))
        first += width[lane]
    for (_, lane), members in in_cell.items():
        for position, node_id in enumerate(members):
            columns[node_id] = lane_columns[lane][position]
    return columns, lane_columns


def build_grid(spec: Spec) -> Grid:
    """Place every node of a flowchart on the grid.

    With explicit grid cells (``at``), the cells are used as given. With swimlanes, a node's
    column is its lane and no exit leaves sideways; without them, the happy path takes one
    column and branches take the columns beside it.

    Args:
        spec: The flowchart description.

    Returns:
        The rows, the columns, and the edges split into forward and returning ones.
    """
    forward, returning = split_returning(spec)
    if any(node.at is not None for node in spec.nodes):
        rank = {node.id: node.at[0] for node in spec.nodes if node.at is not None}
        column = {node.id: node.at[1] for node in spec.nodes if node.at is not None}
        return Grid(rank=rank, column=column, forward=tuple(forward), returning=tuple(returning))
    if spec.lanes and spec.side_by_side:
        rank = assign_ranks(spec, forward, set())
        column, lane_columns = split_lane_columns(spec, rank)
        return Grid(rank, column, tuple(forward), tuple(returning), lane_columns)
    if spec.lanes:
        column = assign_lane_columns(spec)
        rank = separate_lane_cells(spec, forward, column)
        return Grid(rank=rank, column=column, forward=tuple(forward), returning=tuple(returning))
    sideways = sideways_edges(forward)
    rank = assign_ranks(spec, forward, sideways)
    column = assign_columns(spec, rank, forward, sideways)
    return Grid(rank=rank, column=column, forward=tuple(forward), returning=tuple(returning))
