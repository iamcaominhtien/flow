"""Work out where the rows, the columns and the channels of a screen flow are, in pixels.

Rows are shared by the whole diagram. Columns are laid out per band (the app flow, the web flow),
because frames of different devices do not have the same width. The gap between two columns is
130 px when an arrow between them carries a chip and 96 px otherwise; the gap between two rows
holds the channels of the arrows that run between them, one slot each, and the borders of the
zones that end or begin there. A gap between columns holds the vertical lanes of the arrows that
are routed in free lanes, one slot each, and grows to fit them.
"""

from dataclasses import dataclass

from ..model import Node, Shape
from ..theme import ScreenRules
from .screen_labels import Caption, caption_width
from .screen_plan import ENTRY_STACK_GAP_PX, Grid, Plan, RouteType, ZoneExtent

LABEL_ROOM_PX = 24  # kept free on both sides of a label that sits between two columns


@dataclass(frozen=True)
class Sizing:
    """What the geometry needs to know: the nodes, the grid, the plans, the zones and the rules."""

    nodes: dict[str, Node]
    grid: Grid
    plans: list[Plan]
    captions: dict[int, Caption]
    zones: dict[str, ZoneExtent]
    rules: ScreenRules
    channels: list[int]
    channel_zigs: list[int]  # how many of the channels of each gap are zigs, which need more room
    strips: list[int]
    bands: list[range]
    lane_slots: dict[tuple[int, int], int]  # (band, lane) to the slots of a vertical lane
    top: float
    left: float


@dataclass(frozen=True)
class BandColumns:
    """The columns of one band: left edges, widths, and where the first slot of each lane is."""

    lefts: list[float]
    widths: list[float]
    lane_first: list[float]


@dataclass(frozen=True)
class Geometry:
    """Where every row, column and channel is, in pixels."""

    column_left: list[list[float]]  # by band, then column
    column_width: list[list[float]]
    row_band: list[int]
    row_top: list[float]
    row_height: list[float]
    region_top: list[float]
    region_height: list[float]
    channels: list[int]
    channel_zigs: list[int]
    strips: list[int]
    lane_first: list[list[float]]  # by band, then lane: the x of its first slot
    pitch: float
    lane_pitch: float
    chip_room: float

    def column_centre(self, row: int, column: int) -> float:
        """Return the x of the centre line of a column, as laid out in the band of a row."""
        band = self.row_band[row]
        return self.column_left[band][column] + self.column_width[band][column] / 2

    def row_centre(self, row: int) -> float:
        """Return the y of the centre line of a row."""
        return self.row_top[row] + self.row_height[row] / 2

    def channel_y(self, gap: int, slot: int) -> float:
        """Return the y of one channel line of a gap between rows."""
        zigs = min(self.channel_zigs[gap], self.channels[gap])
        used = zigs * self.pitch + (self.channels[gap] - zigs) * self.lane_pitch
        top = self.region_top[gap] + (self.region_height[gap] - used) / 2
        if slot < zigs:
            return top + (slot + 0.5) * self.pitch
        return top + zigs * self.pitch + (slot - zigs + 0.5) * self.lane_pitch

    def lane_x(self, band: int, lane: int, slot: int) -> float:
        """Return the x of one slot of a vertical lane: a gap between the columns of a band."""
        return self.lane_first[band][lane] + slot * self.lane_pitch

    def strip_y(self, row: int, slot: int) -> float:
        """Return the y of one strip above a row, inside the top of the zone of that row."""
        floor = self.row_top[row] - self.chip_room
        return floor - (self.strips[row] - slot - 0.5) * self.pitch


def compute_geometry(sizing: Sizing) -> Geometry:
    """Place the rows, the columns and the channels.

    Args:
        sizing: The nodes, the grid, the plans and the rules.

    Returns:
        The geometry; node positions follow from it.
    """
    columns = [_band_columns(sizing, index) for index in range(len(sizing.bands))]
    row_band = [index for index, band in enumerate(sizing.bands) for _ in band]
    heights = _row_heights(sizing)
    region_top, region_height, row_top = _row_positions(sizing, heights)
    return Geometry(
        [band.lefts for band in columns],
        [band.widths for band in columns],
        row_band,
        row_top,
        heights,
        region_top,
        region_height,
        sizing.channels,
        sizing.channel_zigs,
        sizing.strips,
        [band.lane_first for band in columns],
        sizing.rules.channel_pitch,
        sizing.rules.lane_pitch,
        sizing.rules.chip_room,
    )


def _band_columns(sizing: Sizing, index: int) -> BandColumns:
    """Return the left edge and the width of each column of a band, and where its lanes are.

    A column that holds nothing in the band takes no room and no gap. A band with no entry
    point still starts right of the entries' column, so that its zones cannot reach over them.
    """
    band, rules = sizing.bands[index], sizing.rules
    columns = sizing.grid.columns
    widths = [0.0] * columns
    for item_id, (row, column) in sizing.grid.cells.items():
        if row in band:
            widths[column] = max(widths[column], sizing.nodes[item_id].width)
    present = [column for column in range(columns) if widths[column] > 0]
    outer = sizing.lane_slots.get((index, 0), 0)
    west_room = rules.lane_edge + outer * rules.lane_pitch if outer else 0.0
    west_room = max(west_room, _entry_room(sizing, widths))
    has_zone_pad = any(extent.first_column == 0 for extent in sizing.zones.values())
    lane_first = [sizing.left - (rules.zone_pad_x if has_zone_pad else 0.0) + rules.lane_edge / 2]
    lefts = [sizing.left + west_room] * columns
    cursor = sizing.left + west_room
    for position, column in enumerate(present):
        lefts[column] = cursor
        following = present[position + 1] if position + 1 < len(present) else None
        cursor += widths[column]
        if following is None:
            lane_first.append(cursor + rules.zone_pad_x + rules.lane_edge / 2)
            continue
        slots = sizing.lane_slots.get((index, position + 1), 0)
        gap = _column_gap(sizing, band, (column, following)) + slots * rules.lane_pitch
        lane_first.append(_first_lane_x(sizing, band, (column, following), (cursor, gap, slots)))
        cursor += gap
    return BandColumns(lefts, widths, lane_first)


def _entry_room(sizing: Sizing, widths: list[float]) -> float:
    """Return the room the entries' column takes in a band that has no entry, else 0."""
    entries = [
        (column, sizing.nodes[item_id].width)
        for item_id, (_, column) in sizing.grid.cells.items()
        if sizing.nodes[item_id].shape is Shape.TERMINATOR
    ]
    if not entries or any(widths[column] for column, _ in entries):
        return 0.0
    return max(width for _, width in entries) + sizing.rules.gap


def _first_lane_x(
    sizing: Sizing, band: range, columns: tuple[int, int], gap: tuple[float, float, int]
) -> float:
    """Return the x of the first slot of the lane in a gap between columns.

    The slots are centred between the borders of the zones that end or begin there.
    """
    left, width, slots = gap
    end_pad, begin_pad = _zone_pads(sizing, band, columns)
    middle = (left + end_pad + left + width - begin_pad) / 2
    return middle - (slots - 1) * sizing.rules.lane_pitch / 2


def _column_gap(sizing: Sizing, band: range, columns: tuple[int, int]) -> float:
    """Return the gap between two columns: 96 or 130, wider for a long label, plus zone borders."""
    rules = sizing.rules
    first, second = columns
    gap = rules.gap
    for plan in sizing.plans:
        caption = sizing.captions[plan.index]
        cells = [
            sizing.grid.cells[plan.transition.source],
            sizing.grid.cells[plan.transition.target],
        ]
        is_here = all(row in band for row, _ in cells)
        if not (is_here and plan.route is RouteType.HORIZONTAL and caption.has_text):
            continue
        if sorted(column for _, column in cells) == [first, second]:
            gap = max(gap, rules.gap_labelled, caption_width(caption) + 2 * LABEL_ROOM_PX)
    return gap + sum(_zone_pads(sizing, band, columns))


def _zone_pads(sizing: Sizing, band: range, columns: tuple[int, int]) -> tuple[float, float]:
    """Return the room between two columns for zone borders: that end there, that begin there."""
    ends = begins = 0.0
    for extent in sizing.zones.values():
        if extent.first_row not in band:
            continue
        if extent.last_column == columns[0]:
            ends = sizing.rules.zone_pad_x
        if extent.first_column == columns[1]:
            begins = sizing.rules.zone_pad_x
    return ends, begins


def _row_heights(sizing: Sizing) -> list[float]:
    """Return the height of each row: that of its tallest item, or of its stack of entries."""
    heights = [0.0] * sizing.grid.rows
    for cell, ids in sizing.grid.occupied.items():
        stack = sum(sizing.nodes[item_id].height for item_id in ids)
        stack += (len(ids) - 1) * ENTRY_STACK_GAP_PX
        heights[cell[0]] = max(heights[cell[0]], stack)
    return heights


def _row_positions(
    sizing: Sizing, heights: list[float]
) -> tuple[list[float], list[float], list[float]]:
    """Return the top of each gap's free band, its height, and the top of each row."""
    region_top, region_height, row_top = [], [], []
    cursor = sizing.top
    for gap in range(sizing.grid.rows + 1):
        above, below = _edge_room(sizing, gap)
        height = _region_height(sizing, gap)
        region_top.append(cursor + above)
        region_height.append(height)
        cursor += above + height + below
        if gap < sizing.grid.rows:
            row_top.append(cursor)
            cursor += heights[gap]
    return region_top, region_height, row_top


def _has_vertical_label(sizing: Sizing, gap: int) -> bool:
    """Tell whether a labelled arrow runs straight down through a gap between rows."""
    for plan in sizing.plans:
        if plan.route is not RouteType.VERTICAL or not sizing.captions[plan.index].has_text:
            continue
        ends = (plan.transition.source, plan.transition.target)
        rows = sorted(sizing.grid.cells[end][0] for end in ends)
        if rows[0] < gap <= rows[1]:
            return True
    return False


def _region_height(sizing: Sizing, gap: int) -> float:
    """Return the height of the free band of a gap, which holds its channels and its chips."""
    rules = sizing.rules
    count = sizing.channels[gap]
    zigs = min(sizing.channel_zigs[gap], count)
    lanes = (count - zigs) * rules.lane_pitch
    wanted = zigs * rules.channel_pitch + lanes + rules.channel_margin if count else 0.0
    if gap in (0, sizing.grid.rows):
        return wanted
    base = rules.gap_labelled if _has_vertical_label(sizing, gap) else rules.gap
    return max(base - rules.chip_room, wanted)


def _edge_room(sizing: Sizing, gap: int) -> tuple[float, float]:
    """Return the room above and below the free band of a gap: zone borders or chip room."""
    rules = sizing.rules
    ends = any(extent.last_row == gap - 1 for extent in sizing.zones.values())
    above = rules.zone_pad_bottom if ends and gap > 0 else 0.0
    if gap == sizing.grid.rows:
        return above, 0.0
    begins = any(extent.first_row == gap for extent in sizing.zones.values())
    strips = sizing.strips[gap] * rules.channel_pitch
    return above, (rules.zone_pad_top if begins else rules.chip_room) + strips
