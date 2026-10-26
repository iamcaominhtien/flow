"""Decide how each arrow of a screen flow runs, and how much room the rows and columns need.

An arrow is one of five shapes. A straight line joins neighbours in a row or in a column. A
``ZIG`` leaves the bottom (or top) of a frame, runs along a channel in the gap between two rows and
enters the top (or bottom) of the target. A ``BEND`` leaves the side of a frame and turns once
into the target. A ``STRIP`` runs in the strip above a row, over the frames between its ends.
Channels are lines in the gap between rows; every arrow that needs one gets its own slot, so that
no two chips meet (design 02, Layout).
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from enum import StrEnum

from ..model import Device
from .screen_items import Cell
from .screen_spec import FlowSpec, ItemKind, Route, Transition, TransitionKind

ENTRY_ZONE_ID = "entries"
LOOP_GROUP = 2  # the key that keeps loops apart from strips and channels when slots are given
ENTRY_STACK_GAP_PX = 16  # between two entries that open screens in the same row


class RouteType(StrEnum):
    """The shape of an arrow."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    ZIG = "zig"
    BEND = "bend"
    ELBOW = "elbow"
    LOOP = "loop"
    STRIP = "strip"


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
    is_west: bool = True  # for a loop: which side of the band it runs along
    row: int = 0  # the row of its source


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
    plans = [_plan(index, t, grid) for index, t in enumerate(spec.transitions)]
    return _with_slots(plans)


def _is_clear_row(grid: Grid, row: int, columns: range) -> bool:
    """Tell whether no item sits in a row at the given columns."""
    return not any((row, column) in grid.occupied for column in columns)


def _is_clear_column(grid: Grid, column: int, rows: range) -> bool:
    """Tell whether no item sits in a column at the given rows."""
    return not any((row, column) in grid.occupied for row in rows)


def _between(first: int, second: int) -> range:
    """Return the numbers strictly between two numbers."""
    return range(min(first, second) + 1, max(first, second))


def _plan(index: int, transition: Transition, grid: Grid) -> Plan:
    """Choose the shape of one transition from where its two ends are."""
    source, target = grid.cells[transition.source], grid.cells[transition.target]
    (row_a, column_a), (row_b, column_b) = source, target
    span = abs(column_b - column_a)
    is_down = row_b >= row_a
    is_west = column_a <= (grid.columns - 1) / 2
    if row_a == row_b:
        route, gap = _same_row(transition, grid, (row_a, column_a, column_b))
    elif column_a == column_b and _is_clear_column(grid, column_a, _between(row_a, row_b)):
        route, gap = RouteType.VERTICAL, 0
    elif transition.route is Route.ELBOW:
        route, gap = RouteType.ELBOW, 0
    else:
        is_return = transition.kind in (TransitionKind.BACK, TransitionKind.RETRY)
        route, gap = _diagonal(grid, (source, target), is_return)
    return Plan(index, transition, route, gap, 0, span, is_down, is_west, row_a)


def _same_row(
    transition: Transition, grid: Grid, where: tuple[int, int, int]
) -> tuple[RouteType, int]:
    """Choose the shape of an arrow between two items of one row."""
    row, column_a, column_b = where
    is_back = transition.kind is TransitionKind.BACK and transition.route is not Route.DIRECT
    if is_back or not _is_clear_row(grid, row, _between(column_a, column_b)):
        return RouteType.STRIP, row
    return RouteType.HORIZONTAL, 0


def _diagonal(grid: Grid, ends: tuple[Cell, Cell], is_return: bool) -> tuple[RouteType, int]:
    """Choose the shape of an arrow between items in different rows and columns.

    A return (back or retry) that cannot turn once loops round the outside of the band.
    """
    source, target = ends
    (row_a, column_a), (row_b, column_b) = source, target
    rows_between = _between(row_a, row_b)
    if row_b < row_a and _bend_is_clear(grid, source, target):
        return RouteType.BEND, 0
    if row_b < row_a and is_return:
        return RouteType.LOOP, 0
    if row_b > row_a:
        if _is_clear_column(grid, column_b, rows_between):
            return RouteType.ZIG, row_a + 1
        return RouteType.ZIG, (
            row_b if _is_clear_column(grid, column_a, rows_between) else row_a + 1
        )
    if _is_clear_column(grid, column_b, rows_between):
        return RouteType.ZIG, row_a
    return RouteType.ZIG, (row_b + 1 if _is_clear_column(grid, column_a, rows_between) else row_a)


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


def _slot_order(plan: Plan) -> tuple[int, int, int]:
    """Sort key of the channels of one gap, top to bottom, so that arrows do not cross.

    Strips come first, longest on top so that they nest; then the arrows that go up, longest on
    top; then the ones that go down, shortest on top.
    """
    if plan.route is RouteType.LOOP:
        return (3, plan.span, plan.index)
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
        elif plan.route is RouteType.LOOP:
            groups[(LOOP_GROUP, int(plan.is_west))].append(plan)
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
    return [counts[gap] for gap in range(rows + 1)]


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
