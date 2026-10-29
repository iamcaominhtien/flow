"""Decide how each arrow of a screen flow runs, and how much room the rows and columns need.

An arrow is one of a few shapes. A straight line joins neighbours in a row or in a column. A
``ZIG`` leaves the bottom (or top) of a frame, runs along a channel in the gap between two rows and
enters the top (or bottom) of the target. A ``BEND`` leaves the side of a frame and turns once
into the target. A ``STRIP`` runs in the strip above a row, over the frames between its ends.
A ``ROUTED`` arrow, for a return or a far target that none of these can reach without crossing a
frame, runs in the free lanes between rows and columns (``screen_lanes``). Channels are lines in
the gap between rows; every arrow that needs one gets its own slot, so that
no two chips meet (design 02, Layout).
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from enum import StrEnum

from ..model import Device
from .screen_items import Cell
from .screen_lanes import (
    LaneMap,
    LanePath,
    Load,
    PortSide,
    Request,
    assign_slots,
    find_path,
    make_lane_map,
    new_load,
)
from .screen_spec import FlowSpec, ItemKind, Route, Transition, TransitionKind

ENTRY_ZONE_ID = "entries"
ENTRY_STACK_GAP_PX = 16  # between two entries that open screens in the same row


class RouteType(StrEnum):
    """The shape of an arrow."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    ZIG = "zig"
    BEND = "bend"
    ELBOW = "elbow"
    ROUTED = "routed"
    STRIP = "strip"
    JUMP = "jump"  # two short arrows and a pair of lettered circles, for a very long return


CHANNEL_ROUTES = (RouteType.ZIG, RouteType.STRIP)  # the shapes that run in a channel


@dataclass(frozen=True)
class Plan:
    """How one transition is drawn: its shape and, for a channel, where."""

    index: int
    transition: Transition
    route: RouteType
    gap: int = 0  # the gap between rows that holds its channel
    slot: int = 0  # which of the channels of that gap it takes, from the top
    span: int = 0  # how many columns it crosses
    is_down: bool = True
    lanes: LanePath | None = None  # for a routed arrow: its runs in the free lanes


@dataclass(frozen=True)
class Grid:
    """Where the items are: their cells, the size of the grid and who sits in which cell."""

    cells: dict[str, Cell]
    rows: int
    columns: int
    occupied: dict[Cell, list[str]]


@dataclass(frozen=True)
class ZoneExtent:
    """The rows and columns a zone covers."""

    first_row: int
    last_row: int
    first_column: int
    last_column: int


def make_grid(cells: dict[str, Cell], rows: int, columns: int) -> Grid:
    """Build the grid from the cells of the items."""
    occupied: dict[Cell, list[str]] = defaultdict(list)
    for item_id, cell in cells.items():
        occupied[cell].append(item_id)
    return Grid(cells, rows, columns, dict(occupied))


def plan_routes(spec: FlowSpec, grid: Grid) -> list[Plan]:
    """Choose the shape of every transition and give each channel its slot.

    Args:
        spec: The parsed spec.
        grid: The cells of the items.

    Returns:
        One plan per transition, in the order of the spec.
    """
    entries = frozenset(item.id for item in spec.items if item.kind is ItemKind.ENTRY)
    decisions = frozenset(item.id for item in spec.items if item.kind is ItemKind.DECISION)
    plans = [_plan(index, t, grid, entries) for index, t in enumerate(spec.transitions)]
    plans, closed = _part_decision_legs(plans, grid, decisions)
    return _with_lanes(_with_slots(plans), spec, grid, closed)


def _part_decision_legs(
    plans: list[Plan], grid: Grid, decisions: frozenset[str]
) -> tuple[list[Plan], set[tuple[str, PortSide]]]:
    """Send to the free lanes a zig whose leg would run on the leg of another decision.

    A decision has one point per tip, so its legs run down the middle of its column. Two
    decisions in one column, such as the route guards of two entry points, then draw their legs
    on one line when both reach into the gap between them. The later arrow is routed instead,
    and the tip that faces the clash is closed to it.

    Args:
        plans: The plans, in the order of the spec.
        grid: The cells of the items.
        decisions: The ids of the decisions.

    Returns:
        The plans, with the clashing zigs routed, and the decision tips the lanes must not use.
    """
    taken: dict[tuple[int, int], str] = {}  # (column, gap) to the decision whose leg is there
    closed: set[tuple[str, PortSide]] = set()
    parted = []
    for plan in plans:
        legs = _decision_legs(plan, grid, decisions)
        clashes = [leg for leg in legs if taken.get(leg.spot, leg.owner) != leg.owner]
        if clashes:
            parted.append(replace(plan, route=RouteType.ROUTED, gap=0))
            closed.update((leg.owner, leg.side) for leg in clashes)
            continue
        taken.update((leg.spot, leg.owner) for leg in legs)
        parted.append(plan)
    return parted, closed


@dataclass(frozen=True)
class _DecisionLeg:
    """A stretch of a zig at a decision's tip, where it crosses one gap between rows."""

    owner: str  # the decision
    side: PortSide  # the tip it leaves or enters by
    spot: tuple[int, int]  # the column, and the gap between rows


def _decision_legs(plan: Plan, grid: Grid, decisions: frozenset[str]) -> list[_DecisionLeg]:
    """Return the gaps between rows that the legs of a zig at a decision run through."""
    if plan.route is not RouteType.ZIG:
        return []
    ends = (plan.transition.source, plan.transition.target)
    cells = (grid.cells[ends[0]], grid.cells[ends[1]])
    legs = _vertical_legs(plan, (cells[0][0], cells[1][0]))
    return [
        _DecisionLeg(end, PortSide.SOUTH if gap > cell[0] else PortSide.NORTH, (cell[1], gap))
        for end, cell, gaps in zip(ends, cells, legs, strict=True)
        if end in decisions
        for gap in gaps
    ]


def _is_clear_row(grid: Grid, row: int, columns: range) -> bool:
    """Tell whether no item sits in a row at the given columns."""
    return not any((row, column) in grid.occupied for column in columns)


def _is_clear_column(grid: Grid, column: int, rows: range) -> bool:
    """Tell whether no item sits in a column at the given rows."""
    return not any((row, column) in grid.occupied for row in rows)


def _between(first: int, second: int) -> range:
    """Return the numbers strictly between two numbers."""
    return range(min(first, second) + 1, max(first, second))


def _plan(index: int, transition: Transition, grid: Grid, entries: frozenset[str]) -> Plan:
    """Choose the shape of one transition from where its two ends are."""
    source, target = grid.cells[transition.source], grid.cells[transition.target]
    (row_a, column_a), (row_b, column_b) = source, target
    span = abs(column_b - column_a)
    is_down = row_b >= row_a
    if transition.route is Route.JUMP:
        route, gap = RouteType.JUMP, 0
    elif transition.source in entries and not _is_clear_row(
        grid, row_a, range(column_a + 1, column_b)
    ):
        route, gap = RouteType.ROUTED, 0
    elif row_a == row_b:
        route, gap = _same_row(transition, grid, (row_a, column_a, column_b))
    elif column_a == column_b and _is_clear_column(grid, column_a, _between(row_a, row_b)):
        route, gap = RouteType.VERTICAL, 0
    elif transition.route is Route.ELBOW and _elbow_is_clear(grid, source, target):
        route, gap = RouteType.ELBOW, 0
    else:
        route, gap = _diagonal(grid, (source, target))
        if _is_return(transition) and route is not RouteType.BEND:
            route, gap = RouteType.ROUTED, 0
    return Plan(index, transition, route, gap, 0, span, is_down)


def _is_return(transition: Transition) -> bool:
    """Tell a back or retry arrow: it runs in the free lanes unless it can turn once."""
    return transition.kind in (TransitionKind.BACK, TransitionKind.RETRY)


def _same_row(
    transition: Transition, grid: Grid, where: tuple[int, int, int]
) -> tuple[RouteType, int]:
    """Choose the shape of an arrow between two items of one row."""
    row, column_a, column_b = where
    is_back = transition.kind is TransitionKind.BACK and transition.route is not Route.DIRECT
    if is_back or not _is_clear_row(grid, row, _between(column_a, column_b)):
        return RouteType.STRIP, row
    return RouteType.HORIZONTAL, 0


def _diagonal(grid: Grid, ends: tuple[Cell, Cell]) -> tuple[RouteType, int]:
    """Choose the shape of an arrow between items in different rows and columns.

    The first shape whose lines cross no frame is taken; when none does the arrow is routed in
    the free lanes.
    """
    source, target = ends
    (row_a, column_a), (row_b, column_b) = source, target
    rows_between = _between(row_a, row_b)
    is_target_clear = _is_clear_column(grid, column_b, rows_between)
    is_source_clear = _is_clear_column(grid, column_a, rows_between)
    if row_b < row_a and _bend_is_clear(grid, source, target):
        return RouteType.BEND, 0
    if row_b > row_a and is_target_clear:
        return RouteType.ZIG, row_a + 1
    if row_b > row_a and is_source_clear:
        return RouteType.ZIG, row_b
    if row_b < row_a and is_target_clear:
        return RouteType.ZIG, row_a
    if row_b < row_a and is_source_clear:
        return RouteType.ZIG, row_b + 1
    return RouteType.ROUTED, 0


def _elbow_is_clear(grid: Grid, source: Cell, target: Cell) -> bool:
    """Tell whether an arrow can leave the top or bottom of the source and turn into the target."""
    (row_a, column_a), (row_b, column_b) = source, target
    if column_a < column_b:
        columns = range(column_a, column_b)
    else:
        columns = range(column_b + 1, column_a + 1)
    return _is_clear_column(grid, column_a, _between(row_a, row_b)) and _is_clear_row(
        grid, row_b, columns
    )


def _bend_is_clear(grid: Grid, source: Cell, target: Cell) -> bool:
    """Tell whether an arrow can leave the side of the source and turn once into the target."""
    (row_a, column_a), (row_b, column_b) = source, target
    if column_a < column_b:
        columns = range(column_a + 1, column_b + 1)
    else:
        columns = range(column_b, column_a)
    return _is_clear_row(grid, row_a, columns) and _is_clear_column(
        grid, column_b, _between(row_a, row_b)
    )


def sides_of(plan: Plan, cells: tuple[Cell, Cell]) -> tuple[PortSide, PortSide]:
    """Return the side an arrow leaves and the side it enters.

    Args:
        plan: The plan of the arrow.
        cells: The cells of its source and its target.

    Returns:
        The source side and the target side.
    """
    (row_a, column_a), (row_b, column_b) = cells
    goes_right = column_b > column_a
    goes_down = row_b > row_a
    sideways = PortSide.EAST if goes_right else PortSide.WEST
    opposite = PortSide.WEST if goes_right else PortSide.EAST
    vertical = PortSide.SOUTH if goes_down else PortSide.NORTH
    facing = PortSide.NORTH if goes_down else PortSide.SOUTH
    if plan.lanes is not None:
        return plan.lanes.start_side, plan.lanes.end_side
    is_jump_in_row = plan.route is RouteType.JUMP and row_a == row_b
    if plan.route is RouteType.HORIZONTAL or is_jump_in_row:
        return sideways, opposite
    if plan.route is RouteType.STRIP:
        return PortSide.NORTH, PortSide.NORTH
    if plan.route is RouteType.BEND:
        return sideways, facing
    if plan.route is RouteType.ELBOW:
        return vertical, opposite
    return vertical, facing


def _lane_map(grid: Grid, bands: list[range]) -> LaneMap:
    """Build the lane map: which columns each band holds."""
    present = [[False] * grid.columns for _ in bands]
    for row, column in grid.cells.values():
        band = next(index for index, rows in enumerate(bands) if row in rows)
        present[band][column] = True
    return make_lane_map((grid.rows, grid.columns), bands, present, frozenset(grid.cells.values()))


def _with_lanes(
    plans: list[Plan], spec: FlowSpec, grid: Grid, closed: set[tuple[str, PortSide]]
) -> list[Plan]:
    """Route the arrows that need the free lanes and give each of their runs a slot."""
    routed = [plan for plan in plans if plan.route is RouteType.ROUTED]
    if not routed:
        return plans
    lane_map = _lane_map(grid, split_bands(spec, grid))
    load = new_load()
    load.closed.update(closed)
    for plan in plans:
        if plan.route is not RouteType.ROUTED:
            _count_sides(load.sides, plan, grid)
            _count_crossings(load, plan, grid)
    decisions = frozenset(i.id for i in spec.items if i.kind is ItemKind.DECISION)
    entries = frozenset(i.id for i in spec.items if i.kind is ItemKind.ENTRY)
    paths: dict[int, LanePath] = {}
    for plan in sorted(routed, key=lambda p: _distance(p, grid)):
        transition = plan.transition
        ends = (transition.source, transition.target)
        request = Request(grid.cells[ends[0]], grid.cells[ends[1]], ends, decisions, entries)
        path = find_path(request, lane_map, load)
        if path is not None:
            paths[plan.index] = path
    zigs = Counter(plan.gap for plan in plans if plan.route is RouteType.ZIG)
    slotted = assign_slots(paths, dict(zigs))
    return [_with_path(plan, slotted) for plan in plans]


def _with_path(plan: Plan, paths: dict[int, LanePath]) -> Plan:
    """Give a routed plan its path; one with no path in the lanes falls back to an elbow."""
    if plan.route is not RouteType.ROUTED:
        return plan
    if plan.index in paths:
        return replace(plan, lanes=paths[plan.index])
    return replace(plan, route=RouteType.ELBOW)


def _count_crossings(load: Load, plan: Plan, grid: Grid) -> None:
    """Note the gaps and the rows that a plan that is not routed runs across, for the search."""
    (row_a, column_a) = grid.cells[plan.transition.source]
    (row_b, column_b) = grid.cells[plan.transition.target]
    if plan.route is RouteType.HORIZONTAL:
        for gap in range(min(column_a, column_b) + 1, max(column_a, column_b) + 1):
            load.horizontals[(row_a, gap)] += 1
    if plan.route is RouteType.ZIG:
        for vertical in range(min(column_a, column_b) + 1, max(column_a, column_b) + 1):
            load.runs_across[(True, plan.gap, vertical)] += 1
    legs = _vertical_legs(plan, (row_a, row_b))
    for gaps, column in zip(legs, (column_a, column_b), strict=True):
        for gap in gaps:
            load.verticals[(gap, column)] += 1


def _vertical_legs(plan: Plan, rows: tuple[int, int]) -> tuple[range, range]:
    """Return the gaps between rows that the legs at the source and at the target run through."""
    row_a, row_b = rows
    empty = range(0)
    if plan.route is RouteType.VERTICAL:
        return range(min(rows) + 1, max(rows) + 1), empty
    if plan.route is RouteType.BEND:
        return empty, range(min(rows) + 1, max(rows) + 1)
    if plan.route is not RouteType.ZIG:
        return empty, empty
    if row_b > row_a:
        return range(row_a + 1, plan.gap + 1), range(plan.gap, row_b + 1)
    return range(plan.gap, row_a + 1), range(row_b + 1, plan.gap + 1)


def _count_sides(sides: dict[tuple[str, PortSide], int], plan: Plan, grid: Grid) -> None:
    """Count the frame sides a plan that is not routed meets."""
    transition = plan.transition
    ends = (transition.source, transition.target)
    met = sides_of(plan, (grid.cells[ends[0]], grid.cells[ends[1]]))
    for end, side in zip(ends, met, strict=True):
        sides[(end, side)] += 1


def _distance(plan: Plan, grid: Grid) -> int:
    """Return how far apart the two ends of an arrow are, in cells."""
    (row_a, column_a) = grid.cells[plan.transition.source]
    (row_b, column_b) = grid.cells[plan.transition.target]
    return abs(row_a - row_b) + abs(column_a - column_b)


def _slot_order(plan: Plan) -> tuple[int, int, int]:
    """Sort key of the channels of one gap, top to bottom, so that arrows do not cross.

    Strips come first, longest on top so that they nest; then the arrows that go up, longest on
    top; then the ones that go down, shortest on top.
    """
    if plan.route is RouteType.STRIP:
        return (0, -plan.span, plan.index)
    if not plan.is_down:
        return (1, -plan.span, plan.index)
    return (2, plan.span, plan.index)


def _with_slots(plans: list[Plan]) -> list[Plan]:
    """Give each arrow that runs in a channel the slot of its gap that suits it."""
    groups: dict[tuple[int, int], list[Plan]] = defaultdict(list)
    for plan in plans:
        if plan.route in CHANNEL_ROUTES:
            groups[(int(plan.route is RouteType.STRIP), plan.gap)].append(plan)
    slots = {}
    for group in groups.values():
        for slot, plan in enumerate(sorted(group, key=_slot_order)):
            slots[plan.index] = slot
    return [replace(plan, slot=slots.get(plan.index, 0)) for plan in plans]


def channel_counts(plans: list[Plan], rows: int, extra: dict[int, int]) -> list[int]:
    """Count the channels each gap between rows needs, buses included.

    Args:
        plans: The plans of the transitions.
        rows: The number of rows.
        extra: Gap to the number of channels taken by something that is not a transition.

    Returns:
        One count per gap, ``rows + 1`` of them.
    """
    counts = Counter(plan.gap for plan in plans if plan.route is RouteType.ZIG)
    for gap, more in extra.items():
        counts[gap] += more
    for plan in plans:
        for run in plan.lanes.runs if plan.lanes else ():
            if run.is_horizontal:
                counts[run.lane] = max(counts[run.lane], run.slot + 1)
    return [counts[gap] for gap in range(rows + 1)]


def zig_counts(plans: list[Plan], rows: int) -> list[int]:
    """Count the zigs in each gap between rows: each takes a channel with room for its words."""
    counts = Counter(plan.gap for plan in plans if plan.route is RouteType.ZIG)
    return [counts[gap] for gap in range(rows + 1)]


def lane_counts(plans: list[Plan]) -> dict[tuple[int, int], int]:
    """Count the slots each vertical lane needs: the lane is a band and a gap between columns.

    Args:
        plans: The plans of the transitions.

    Returns:
        ``(band, lane)`` to the number of slots; a lane no arrow uses is absent.
    """
    counts: dict[tuple[int, int], int] = {}
    for plan in plans:
        for run in plan.lanes.runs if plan.lanes else ():
            if not run.is_horizontal:
                key = (run.band, run.lane)
                counts[key] = max(counts.get(key, 0), run.slot + 1)
    return counts


def strip_counts(plans: list[Plan], rows: int, extra: dict[int, int]) -> list[int]:
    """Count the strips above each row: they run inside the top of the zone of that row.

    Args:
        plans: The plans of the transitions.
        rows: The number of rows.
        extra: Row to the number of strips taken by something that is not a transition.

    Returns:
        One count per row, and one for the gap below the last row.
    """
    counts = Counter(plan.gap for plan in plans if plan.route is RouteType.STRIP)
    for row, more in extra.items():
        counts[row] += more
    return [counts[row] for row in range(rows + 1)]


def zone_extents(spec: FlowSpec, grid: Grid) -> dict[str, ZoneExtent]:
    """Return the rows and columns each zone covers, with the entries as a zone of their own."""
    members: dict[str, list[Cell]] = defaultdict(list)
    for item in spec.items:
        zone = ENTRY_ZONE_ID if item.kind is ItemKind.ENTRY else item.zone
        if zone:
            members[zone].append(grid.cells[item.id])
    return {
        zone: ZoneExtent(
            min(r for r, _ in cells),
            max(r for r, _ in cells),
            min(c for _, c in cells),
            max(c for _, c in cells),
        )
        for zone, cells in members.items()
    }


def split_bands(spec: FlowSpec, grid: Grid) -> list[range]:
    """Split the rows into bands that each get their own columns.

    A web flow is drawn below the app flow with frames of another size, so its columns are laid
    out on their own: a band is a run of rows whose screens are all desktop, or none are.

    Args:
        spec: The parsed spec.
        grid: The cells of the items.

    Returns:
        The bands, top to bottom; together they cover every row.
    """
    desktop = [False] * grid.rows
    others = [False] * grid.rows
    for item in spec.items:
        if item.view is None:
            continue
        row = grid.cells[item.id][0]
        is_desktop = item.view.device is Device.DESKTOP
        desktop[row] = desktop[row] or is_desktop
        others[row] = others[row] or not is_desktop
    classes: list[bool] = []
    for row in range(grid.rows):
        known = desktop[row] != others[row]
        classes.append(desktop[row] if known else (classes[-1] if classes else False))
    bands, start = [], 0
    for row in range(1, grid.rows + 1):
        if row == grid.rows or classes[row] != classes[start]:
            bands.append(range(start, row))
            start = row
    return bands
