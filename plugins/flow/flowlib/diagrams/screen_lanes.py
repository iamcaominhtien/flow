"""Find routes for the arrows of a screen flow that run in free lanes (design 02, Layout).

A lane is a free line between two rows (horizontal) or between two columns (vertical). No frame
sits in a lane, so a route made of lane runs never crosses a frame. An arrow leaves a side of its
source, runs in the lanes and enters a side of its target. Lanes meet at crossings; the search
goes from crossing to crossing and charges for length, for bends, for the outer lanes and for lanes
that other arrows already use. Each run then gets a slot of its lane, so that two arrows never
share a line.
"""

import heapq
from collections import defaultdict
from dataclasses import dataclass, replace
from enum import StrEnum

Cell = tuple[int, int]
State = tuple[int, int, bool]  # gap of the horizontal lane, gap of the vertical lane, runs along x

BEND_COST = 0.7  # a turn, in rows or columns of length
OUTER_COST = 1.5  # per row, for a lane outside the first or the last column
CONGESTION_COST = 0.4  # per arrow that already runs in the lane
CROSS_COST = 1.0  # per line of another arrow that a move crosses
STUB_COST = 0.6  # per empty column a stub runs through
SIDE_COST = 0.6  # per arrow that already meets the side of the frame
DECISION_SIDE_FACTOR = 2.0  # a decision has one tip per side, so it is charged more
HALF = 0.5  # a lane is half a cell from the cells next to it
OVERLAP_MARGIN = 0.25  # runs closer than this, in cells, need slots of their own


class PortSide(StrEnum):
    """Which side of a frame an arrow meets."""

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


@dataclass(frozen=True)
class Run:
    """One straight stretch of a route, in a lane.

    For a horizontal run ``lane`` is the gap between rows that holds it; for a vertical run it is
    the gap between the columns of ``band``, counted over the columns that are present there.
    ``low`` and ``high`` are its ends along the lane, in cells.
    """

    is_horizontal: bool
    lane: int
    band: int
    low: float
    high: float
    bias: int = 0  # -1 when it is fed from above or from the left, 1 from below or the right
    slot: int = 0


@dataclass(frozen=True)
class LanePath:
    """A route in lanes: the sides it meets and its runs, from the source to the target."""

    start_side: PortSide
    end_side: PortSide
    runs: tuple[Run, ...]
    start_toward: tuple[float, float]  # where the first run heads, as (row, column) in cells
    end_toward: tuple[float, float]


@dataclass(frozen=True)
class LaneMap:
    """The lanes of a grid: its size and how column gaps map to lanes in each band."""

    rows: int
    columns: int
    row_band: list[int]
    lane_of: list[list[int]]  # band, then column gap, to the lane among the present columns
    occupied: frozenset[Cell] = frozenset()  # the cells that hold an item

    def reach(self, cell: Cell, side: PortSide) -> list[tuple[int, int]]:
        """List the vertical lanes a stub from the east or west side of a cell can reach.

        The stub may run on through the empty cells of its row; each lane comes with how many
        columns the stub is long.
        """
        row, column = cell
        is_east = side is PortSide.EAST
        step = 1 if is_east else -1
        vertical = column + 1 if is_east else column
        lanes = []
        while 0 <= vertical <= self.columns:
            lanes.append((vertical, abs(vertical - column - is_east)))
            beyond = vertical if is_east else vertical - 1
            if (row, beyond) in self.occupied:
                break
            vertical += step
        return lanes

    def lane_count(self, band: int) -> int:
        """Return the number of lanes between and around the columns present in a band."""
        return self.lane_of[band][self.columns] + 1


@dataclass
class Load:
    """What routes already use: arrows per lane and per frame side."""

    lanes: dict[tuple[bool, int, int], int]
    sides: dict[tuple[str, PortSide], int]
    verticals: dict[tuple[int, int], int]  # (gap, column): lines that cross a gap in a column
    horizontals: dict[tuple[int, int], int]  # (row, column gap): lines that cross a row there
    runs_across: dict[tuple[bool, int, int], int]  # crossings that a route passes straight over


@dataclass(frozen=True)
class Request:
    """An arrow to route: its two cells and the ids of its two frames."""

    source: Cell
    target: Cell
    ends: tuple[str, str]
    decisions: frozenset[str]
    entries: frozenset[str]  # frames that an arrow leaves by the east side only


@dataclass(frozen=True)
class Found:
    """A route found by the search: the crossings it visits and the sides it meets."""

    sides: tuple[PortSide, PortSide]
    crossings: tuple[tuple[int, int], ...]


def make_lane_map(
    size: tuple[int, int], bands: list[range], present: list[list[bool]], occupied: frozenset[Cell]
) -> LaneMap:
    """Build the lane map from the bands and the columns each one holds.

    Args:
        size: The number of rows and of columns.
        bands: The bands of rows that have columns of their own.
        present: For each band, whether each column holds an item there.
        occupied: The cells that hold an item.

    Returns:
        The map.
    """
    rows, columns = size
    row_band = [index for index, band in enumerate(bands) for _ in band]
    lane_of = []
    for flags in present:
        lanes, count = [], 0
        for column in range(columns + 1):
            lanes.append(count)
            count += flags[column] if column < columns else 0
        lane_of.append(lanes)
    return LaneMap(rows, columns, row_band, lane_of, occupied)


def new_load() -> Load:
    """Return an empty load."""
    return Load(
        defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
    )


def find_path(request: Request, lanes: LaneMap, load: Load) -> LanePath | None:
    """Find the cheapest route in lanes for one arrow, and add it to the load.

    Args:
        request: The arrow.
        lanes: The lanes of the grid.
        load: What other routes use; this route is added to it.

    Returns:
        The route, with its runs not yet given a slot; None when no route exists.
    """
    found = _cheapest(request, lanes, load)
    if found is None:
        return None
    path = _path_of(found, request, lanes)
    _charge(load, path, request, found.crossings)
    return path


def _charge(
    load: Load, path: LanePath, request: Request, crossings: tuple[tuple[int, int], ...]
) -> None:
    """Add a route to the load."""
    for run in path.runs:
        load.lanes[(run.is_horizontal, run.band, run.lane)] += 1
    for end, side in zip(request.ends, (path.start_side, path.end_side), strict=True):
        load.sides[(end, side)] += 1
    for crossing, is_horizontal in _passed(crossings):
        load.runs_across[(is_horizontal, *crossing)] += 1


def _passed(
    crossings: tuple[tuple[int, int], ...],
) -> list[tuple[tuple[int, int], bool]]:
    """List the crossings a route runs straight over, with whether it runs along x there."""
    passed = []
    for before, here, after in zip(crossings, crossings[1:], crossings[2:], strict=False):
        is_along_x = before[0] == here[0] == after[0]
        is_along_y = before[1] == here[1] == after[1]
        if is_along_x or is_along_y:
            passed.append((here, is_along_x))
    return passed


def _x_of(vertical_gap: int) -> float:
    """Return the x, in columns, of the lane between two columns."""
    return vertical_gap - HALF


def _y_of(horizontal_gap: int) -> float:
    """Return the y, in rows, of the lane between two rows."""
    return horizontal_gap - HALF


def _side_cost(load: Load, request: Request, which: int, side: PortSide) -> float:
    """Charge for meeting a side that other arrows meet."""
    end = request.ends[which]
    factor = DECISION_SIDE_FACTOR if end in request.decisions else 1.0
    return SIDE_COST * factor * load.sides.get((end, side), 0)


def _starts(request: Request, lanes: LaneMap, load: Load) -> list[tuple[float, State, PortSide]]:
    """List where a route can begin: a crossing on the lane next to a side of the source."""
    row, column = request.source
    starts: list[tuple[float, State, PortSide]] = []
    for side in PortSide:
        if request.ends[0] in request.entries and side is not PortSide.EAST:
            continue
        extra = _side_cost(load, request, 0, side)
        if side in (PortSide.NORTH, PortSide.SOUTH):
            gap = row if side is PortSide.NORTH else row + 1
            for vertical in range(lanes.columns + 1):
                distance = abs(column - _x_of(vertical))
                starts.append((distance + extra, (gap, vertical, True), side))
            continue
        for vertical, length in lanes.reach(request.source, side):
            for gap in (row, row + 1):
                starts.append((HALF + STUB_COST * length + extra, (gap, vertical, False), side))
    return starts


def _neighbours(state: State, lanes: LaneMap, load: Load) -> list[tuple[float, State]]:
    """List the crossings next to a crossing, with the cost of the move to each."""
    gap, vertical, is_horizontal = state
    moves: list[tuple[float, State]] = []
    for step in (-1, 1):
        next_vertical = vertical + step
        if 0 <= next_vertical <= lanes.columns:
            cost = 1.0 + CONGESTION_COST * load.lanes.get((True, 0, gap), 0)
            cost += CROSS_COST * load.verticals.get((gap, min(vertical, next_vertical)), 0)
            cost += CROSS_COST * load.runs_across.get((False, gap, next_vertical), 0)
            cost += 0.0 if is_horizontal else BEND_COST
            moves.append((cost, (gap, next_vertical, True)))
        next_gap = gap + step
        if 0 <= next_gap <= lanes.rows:
            row = min(gap, next_gap)
            band = lanes.row_band[row]
            lane = lanes.lane_of[band][vertical]
            cost = 1.0 + CONGESTION_COST * load.lanes.get((False, band, lane), 0)
            cost += CROSS_COST * load.horizontals.get((row, vertical), 0)
            cost += CROSS_COST * load.runs_across.get((True, next_gap, vertical), 0)
            if lane in (0, lanes.lane_count(band) - 1):
                cost += OUTER_COST
            cost += BEND_COST if is_horizontal else 0.0
            moves.append((cost, (next_gap, vertical, False)))
    return moves


def _dijkstra(
    starts: list[tuple[float, State, PortSide]], lanes: LaneMap, load: Load
) -> tuple[dict[State, float], dict[State, State | PortSide]]:
    """Run the search from every start; return the cost of each crossing and where it came from."""
    costs: dict[State, float] = {}
    came: dict[State, State | PortSide] = {}
    queue: list[tuple[float, int, State]] = []
    for order, (cost, state, side) in enumerate(starts):
        if cost < costs.get(state, float("inf")):
            costs[state], came[state] = cost, side
            heapq.heappush(queue, (cost, order, state))
    counter = len(starts)
    while queue:
        cost, _, state = heapq.heappop(queue)
        if cost > costs[state]:
            continue
        for step_cost, following in _neighbours(state, lanes, load):
            if cost + step_cost < costs.get(following, float("inf")):
                costs[following], came[following] = cost + step_cost, state
                counter += 1
                heapq.heappush(queue, (cost + step_cost, counter, following))
    return costs, came


def _finish_cost(
    state: State, request: Request, side: PortSide, setting: tuple[LaneMap, Load]
) -> float | None:
    """Return what it costs to end at a side of the target from a crossing; None if it cannot."""
    gap, vertical, is_horizontal = state
    lanes, load = setting
    row, column = request.target
    extra = _side_cost(load, request, 1, side)
    if side in (PortSide.NORTH, PortSide.SOUTH):
        wanted = row if side is PortSide.NORTH else row + 1
        if gap != wanted:
            return None
        bend = 0.0 if is_horizontal else BEND_COST
        across = CROSS_COST * load.runs_across.get((False, gap, vertical), 0) * is_horizontal
        return abs(column - _x_of(vertical)) + bend + extra + across
    if gap not in (row, row + 1):
        return None
    lengths = dict(lanes.reach(request.target, side))
    if vertical not in lengths:
        return None
    bend = BEND_COST if is_horizontal else 0.0
    across = CROSS_COST * load.runs_across.get((True, gap, vertical), 0) * (not is_horizontal)
    return HALF + STUB_COST * lengths[vertical] + bend + extra + across


def _cheapest(request: Request, lanes: LaneMap, load: Load) -> Found | None:
    """Search for the cheapest route, either through crossings or straight along one lane."""
    costs, came = _dijkstra(_starts(request, lanes, load), lanes, load)
    best: tuple[float, State, PortSide] | None = None
    for state, cost in costs.items():
        for side in PortSide:
            finish = _finish_cost(state, request, side, (lanes, load))
            if finish is not None and (best is None or cost + finish < best[0]):
                best = (cost + finish, state, side)
    straight = _straight(request, load)
    if straight is not None and (best is None or straight[0] <= best[0]):
        return Found(straight[1], ())
    if best is None:
        return None
    _, state, end_side = best
    crossings = [state]
    while not isinstance(came[crossings[-1]], PortSide):
        crossings.append(came[crossings[-1]])  # type: ignore[arg-type]
    start_side = came[crossings[-1]]
    assert isinstance(start_side, PortSide)
    return Found((start_side, end_side), tuple((g, v) for g, v, _ in reversed(crossings)))


def _straight(request: Request, load: Load) -> tuple[float, tuple[PortSide, PortSide]] | None:
    """Find a route that is one run: both ends on the same horizontal lane."""
    (row_a, column_a), (row_b, column_b) = request.source, request.target
    best = None
    if request.ends[0] in request.entries:
        return None
    for side_a, gap_a in ((PortSide.NORTH, row_a), (PortSide.SOUTH, row_a + 1)):
        for side_b, gap_b in ((PortSide.NORTH, row_b), (PortSide.SOUTH, row_b + 1)):
            if gap_a != gap_b:
                continue
            cost = abs(column_a - column_b)
            cost += _side_cost(load, request, 0, side_a) + _side_cost(load, request, 1, side_b)
            if best is None or cost < best[0]:
                best = (cost, (side_a, side_b))
    return best


@dataclass(frozen=True)
class _Leg:
    """A stretch of a route before its slot: orientation, lane, band and its two ends."""

    is_horizontal: bool
    lane: int
    band: int
    start: float
    end: float
    across: float  # the fixed coordinate: y of a horizontal leg, x of a vertical one
    bias: int = 0


def _path_of(found: Found, request: Request, lanes: LaneMap) -> LanePath:
    """Turn the crossings of a route into its runs."""
    start_side, end_side = found.sides
    legs = _legs(found, request, lanes)
    runs = _merged(legs)
    toward_start = _toward(runs[0], request.source)
    toward_end = _toward(runs[-1], request.target)
    return LanePath(start_side, end_side, tuple(runs), toward_start, toward_end)


def _toward(run: Run, cell: Cell) -> tuple[float, float]:
    """Return where a run heads from a cell, as a point in cells: it orders the ports of a side."""
    row, column = cell
    middle = (run.low + run.high) / 2
    if run.is_horizontal:
        return (row, middle if middle != column else column + HALF)
    return (middle if middle != row else row + HALF, column)


def _stub_leg(cell: Cell, side: PortSide, crossing: tuple[int, int], lanes: LaneMap) -> _Leg:
    """Make the first or last leg of a route: from a frame side to the nearest crossing."""
    row, column = cell
    gap, vertical = crossing
    if side in (PortSide.NORTH, PortSide.SOUTH):
        bias = -1 if side is PortSide.SOUTH else 1
        return _Leg(True, gap, 0, column, _x_of(vertical), _y_of(gap), bias)
    band = lanes.row_band[row]
    bias = -1 if side is PortSide.EAST else 1
    lane = lanes.lane_of[band][vertical]
    return _Leg(False, lane, band, row, _y_of(gap), _x_of(vertical), bias)


def _legs(found: Found, request: Request, lanes: LaneMap) -> list[_Leg]:
    """Break a route into legs: the stub at each end and one leg per move between crossings."""
    if not found.crossings:
        gap = request.source[0] + (found.sides[0] is PortSide.SOUTH)
        legs = [
            _Leg(True, gap, 0, request.source[1], request.target[1], _y_of(gap), 0),
        ]
        return legs
    first, last = found.crossings[0], found.crossings[-1]
    legs = [_stub_leg(request.source, found.sides[0], first, lanes)]
    for (gap_a, vertical_a), (gap_b, vertical_b) in zip(
        found.crossings, found.crossings[1:], strict=False
    ):
        legs.append(_move_leg((gap_a, vertical_a), (gap_b, vertical_b), lanes))
    end = _stub_leg(request.target, found.sides[1], last, lanes)
    legs.append(replace(end, start=end.end, end=end.start))
    return legs


def _move_leg(first: tuple[int, int], second: tuple[int, int], lanes: LaneMap) -> _Leg:
    """Make the leg of one move from a crossing to the next."""
    (gap_a, vertical_a), (gap_b, vertical_b) = first, second
    if gap_a == gap_b:
        return _Leg(True, gap_a, 0, _x_of(vertical_a), _x_of(vertical_b), _y_of(gap_a))
    band = lanes.row_band[min(gap_a, gap_b)]
    lane = lanes.lane_of[band][vertical_a]
    return _Leg(False, lane, band, _y_of(gap_a), _y_of(gap_b), _x_of(vertical_a))


def _merged(legs: list[_Leg]) -> list[Run]:
    """Join the legs that run along the same lane into runs, and bridge a change of band."""
    runs: list[Run] = []
    for leg in legs:
        previous = runs[-1] if runs else None
        if previous is not None and _is_same_lane(previous, leg):
            runs[-1] = _joined(previous, leg)
            continue
        if previous is not None and not previous.is_horizontal and not leg.is_horizontal:
            gap = round(leg.start + HALF)
            runs.append(Run(True, gap, 0, leg.across, leg.across))
        runs.append(
            Run(leg.is_horizontal, leg.lane, leg.band, *sorted((leg.start, leg.end)), leg.bias)
        )
    return runs


def _is_same_lane(run: Run, leg: _Leg) -> bool:
    """Tell whether a leg continues the lane of a run."""
    return (run.is_horizontal, run.lane, run.band) == (leg.is_horizontal, leg.lane, leg.band)


def _joined(run: Run, leg: _Leg) -> Run:
    """Extend a run with a leg of the same lane; it keeps a bias only when both agree."""
    low, high = min(run.low, leg.start, leg.end), max(run.high, leg.start, leg.end)
    bias = run.bias if run.bias == leg.bias else run.bias + leg.bias
    return replace(run, low=low, high=high, bias=max(-1, min(1, bias)))


def assign_slots(paths: dict[int, LanePath], first_slots: dict[int, int]) -> dict[int, LanePath]:
    """Give every run a slot in its lane, so that runs that overlap do not share one.

    A run that is fed from above (or from the left) takes the upper (left) slots of its lane and
    one fed from below (or from the right) the lower (right) ones, so that the short legs at the
    ends of a route do not cross the lanes of other routes.

    Args:
        paths: Arrow index to route, from the search.
        first_slots: Horizontal lane to the number of slots something else already holds there.

    Returns:
        The same routes with the slot of each run set.
    """
    groups: dict[tuple[bool, int, int], list[tuple[int, int]]] = defaultdict(list)
    for index, path in paths.items():
        for position, run in enumerate(path.runs):
            groups[(run.is_horizontal, run.band, run.lane)].append((index, position))
    slots: dict[tuple[int, int], int] = {}
    for key, members in groups.items():
        first = first_slots.get(key[2], 0) if key[0] else 0
        slots.update(_lane_slots(paths, members, first))
    return {
        index: replace(
            path,
            runs=tuple(
                replace(run, slot=slots[(index, position)])
                for position, run in enumerate(path.runs)
            ),
        )
        for index, path in paths.items()
    }


def _lane_slots(
    paths: dict[int, LanePath], members: list[tuple[int, int]], first: int
) -> dict[tuple[int, int], int]:
    """Give the runs of one lane their slots: by bias, then longest first, first fit."""
    slots: dict[tuple[int, int], int] = {}
    cursor = first
    for bias in (-1, 0, 1):
        chosen = [m for m in members if paths[m[0]].runs[m[1]].bias == bias]
        chosen.sort(key=lambda m: (-_length(paths[m[0]].runs[m[1]]), m))
        tracks: list[list[tuple[float, float]]] = []
        for member in chosen:
            run = paths[member[0]].runs[member[1]]
            track = _first_fit(tracks, run)
            slots[member] = cursor + track
        cursor += len(tracks)
    return slots


def _length(run: Run) -> float:
    """Return the length of a run in cells."""
    return run.high - run.low


def _first_fit(tracks: list[list[tuple[float, float]]], run: Run) -> int:
    """Return the first track where a run overlaps no other, adding a track when none is free."""
    for number, taken in enumerate(tracks):
        if all(
            run.high + OVERLAP_MARGIN < low or run.low - OVERLAP_MARGIN > high
            for low, high in taken
        ):
            taken.append((run.low, run.high))
            return number
    tracks.append([(run.low, run.high)])
    return len(tracks) - 1
