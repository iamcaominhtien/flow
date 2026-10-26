"""Work out where the rows, the columns and the channels of a screen flow are, in pixels.

Rows are shared by the whole diagram. Columns are laid out per band (the app flow, the web flow),
because frames of different devices do not have the same width. The gap between two columns is
130 px when an arrow between them carries a chip and 96 px otherwise; the gap between two rows
holds the channels of the arrows that run between them, one slot each, and the borders of the
zones that end or begin there.
"""

from dataclasses import dataclass

from ..model import Node
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
    strips: list[int]
    bands: list[range]
    top: float
    left: float


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
    strips: list[int]
    pitch: float
    chip_room: float
    loop_gap: float  # how far outside the first or last column a loop runs
    loop_step: float  # between two loops on one side

    def column_centre(self, row: int, column: int) -> float:
        """Return the x of the centre line of a column, as laid out in the band of a row."""
        band = self.row_band[row]
        return self.column_left[band][column] + self.column_width[band][column] / 2

    def row_centre(self, row: int) -> float:
        """Return the y of the centre line of a row."""
        return self.row_top[row] + self.row_height[row] / 2

    def channel_y(self, gap: int, slot: int) -> float:
        """Return the y of one channel line of a gap between rows."""
        used = self.channels[gap] * self.pitch
        top = self.region_top[gap] + (self.region_height[gap] - used) / 2
        return top + (slot + 0.5) * self.pitch

    def loop_x(self, row: int, is_west: bool, slot: int) -> float:
        """Return the x of the line a loop runs along, outside the columns of the band of a row."""
        band = self.row_band[row]
        columns = [
            (left, left + width)
            for left, width in zip(self.column_left[band], self.column_width[band], strict=True)
            if width > 0
        ]
        reach = slot * self.loop_step
        if is_west:
            return min(left for left, _ in columns) - self.loop_gap - reach
        return max(right for _, right in columns) + self.loop_gap + reach

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
    lefts, widths = [], []
    for band in sizing.bands:
        band_lefts, band_widths = _band_columns(sizing, band)
        lefts.append(band_lefts)
        widths.append(band_widths)
    row_band = [index for index, band in enumerate(sizing.bands) for _ in band]
    heights = _row_heights(sizing)
    region_top, region_height, row_top = _row_positions(sizing, heights)
    return Geometry(
        lefts,
        widths,
        row_band,
        row_top,
        heights,
        region_top,
        region_height,
        sizing.channels,
        sizing.strips,
        sizing.rules.channel_pitch,
        sizing.rules.chip_room,
        sizing.rules.zone_pad_x / 2,
        sizing.rules.port_pitch,
    )


def _band_columns(sizing: Sizing, band: range) -> tuple[list[float], list[float]]:
    """Return the left edge and the width of each column of a band.

    A column that holds nothing in the band takes no room and no gap.
    """
    columns = sizing.grid.columns
    widths = [0.0] * columns
    for item_id, (row, column) in sizing.grid.cells.items():
        if row in band:
            widths[column] = max(widths[column], sizing.nodes[item_id].width)
    present = [column for column in range(columns) if widths[column] > 0]
    lefts = [sizing.left] * columns
    cursor = sizing.left
    for position, column in enumerate(present):
        lefts[column] = cursor
        following = present[position + 1] if position + 1 < len(present) else None
        cursor += widths[column] + (
            _column_gap(sizing, band, (column, following)) if following else 0
        )
    return lefts, widths


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
    return gap + _column_zone_room(sizing, band, columns)


def _column_zone_room(sizing: Sizing, band: range, columns: tuple[int, int]) -> float:
    """Return the room between two columns for zone borders that end or begin there."""
    room = 0.0
    for extent in sizing.zones.values():
        if extent.first_row not in band:
            continue
        if extent.last_column == columns[0]:
            room += sizing.rules.zone_pad_x
        if extent.first_column == columns[1]:
            room += sizing.rules.zone_pad_x
    return room


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
    wanted = count * rules.channel_pitch + rules.channel_margin if count else 0.0
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
