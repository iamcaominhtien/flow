"""The frame of a Gantt chart: its grid, its header, the line of today and the legend."""

import calendar
from dataclasses import dataclass, replace
from datetime import timedelta

from ..model import (
    DEFAULT_FONT_SIZE_PX,
    Edge,
    EdgeLabel,
    Frame,
    FrameVariant,
    Head,
    LabelKind,
    Node,
    PlanView,
    Point,
    Role,
    Shape,
    Status,
    Tone,
)
from ..sizing import estimate_text_width
from ..theme import GanttRules, Theme
from .gantt_spec import DAYS_PER_WEEK, Axis, TimeMode

STATUS_ORDER = (Status.DONE, Status.IN_PROGRESS, Status.PLANNED, Status.BLOCKED)
STATUS_NAMES = {
    Status.DONE: "Done",
    Status.IN_PROGRESS: "In progress",
    Status.PLANNED: "Planned",
    Status.BLOCKED: "Blocked",
}
CRITICAL_NAME = "Critical path"
LEGEND_PROGRESS = 0.5  # how far the swatch of an in-progress bar is filled
LEGEND_TEXT_GAP_PX = 10  # between a swatch and its text
LEGEND_FONT_PX = 11
THURSDAY = 3  # days after a Monday
TEXT_INSET_PX = 4  # a text box is this much smaller than its cell on every side
MONTH_PAD_PX = 12  # the name of a month starts this far from the line of its month
TEXT_SLACK_PX = 6  # extra width of a legend text, because the width is only estimated
Cell = tuple[str, float, float]  # a month: its name, and its left and right edge in columns


@dataclass(frozen=True)
class Grid:
    """Where the columns and the rows are: the left edge of the chart and the top of the rows."""

    rules: GanttRules
    left: float
    top: float
    columns: int

    @property
    def right(self) -> float:
        """Return the x of the right edge of the last column."""
        return self.left + self.columns * self.rules.week_width

    def x_at(self, position: float) -> float:
        """Return the x of a position counted in columns from the left edge."""
        return self.left + position * self.rules.week_width


def header_height(axis: Axis, rules: GanttRules) -> float:
    """Return the height of the header: two rows when the chart is read in dates, else one."""
    if axis.mode is TimeMode.DATES:
        return rules.month_height + rules.week_height
    return rules.week_height


def header_parts(
    axis: Axis, grid: Grid, header_top: float
) -> tuple[list[Frame], list[Node], list[Edge]]:
    """Draw the header: a white panel with a month row and a week row, and the lines inside it.

    Args:
        axis: The columns of the chart.
        grid: Where the columns are.
        header_top: The y of the top of the header.

    Returns:
        The panel, the labels and the lines.
    """
    rules = grid.rules
    panel = Frame(
        "header", grid.left, header_top, grid.right - grid.left, header_height(axis, rules),
        None, Tone.GRAY, FrameVariant.PANEL,
    )  # fmt: skip
    months = _months(axis, grid.columns)
    week_top = header_top + (rules.month_height if months else 0)
    nodes = _week_labels(axis, grid, week_top) + _month_labels(months, grid, header_top)
    return [panel], nodes, _header_lines(months, grid, (header_top, week_top))


def _months(axis: Axis, columns: int) -> list[Cell]:
    """Return the month cells of a chart read in dates; there are none for any other chart.

    A week belongs to the month its Thursday is in (the rule of ISO weeks), so a month cell
    always starts and ends on a week line.
    """
    if axis.start is None:
        return []
    thursdays = [
        axis.start + timedelta(days=DAYS_PER_WEEK * index + THURSDAY) for index in range(columns)
    ]
    shows_year = thursdays[0].year != thursdays[-1].year
    cells: list[Cell] = []
    for index, thursday in enumerate(thursdays):
        name = calendar.month_name[thursday.month] + (f" {thursday.year}" if shows_year else "")
        if cells and cells[-1][0] == name:
            cells[-1] = (name, cells[-1][1], index + 1)
        else:
            cells.append((name, index, index + 1))
    return cells


def _inset_box(cell: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Return a box a little smaller than a cell, so that two texts never touch."""
    x, y, width, height = cell
    return (
        x + TEXT_INSET_PX,
        y + TEXT_INSET_PX,
        width - 2 * TEXT_INSET_PX,
        height - 2 * TEXT_INSET_PX,
    )


def _text(identifier: str, text: str, box: tuple[float, float, float, float]) -> Node:
    """Build a plain text node in a box."""
    x, y, width, height = box
    return Node(
        identifier, Shape.LABEL, x, y, width, height, (text,), None, None, None,
        DEFAULT_FONT_SIZE_PX, plan=PlanView(),
    )  # fmt: skip


def _week_labels(axis: Axis, grid: Grid, top: float) -> list[Node]:
    """Draw the name of each column, centred in it."""
    rules = grid.rules
    nodes = []
    for index in range(axis.count):
        name = axis.labels[index] if axis.labels else f"W{index + 1}"
        box = _inset_box((grid.x_at(index), top, rules.week_width, rules.week_height))
        nodes.append(
            replace(
                _text(f"week-{index}", name, box), is_centered=True, font_size=rules.week_font_size
            )
        )
    return nodes


def _month_labels(months: list[Cell], grid: Grid, top: float) -> list[Node]:
    """Draw the name of each month at the left of its cell, in bold."""
    rules = grid.rules
    nodes = []
    for index, (name, left, right) in enumerate(months):
        x = grid.x_at(left) + MONTH_PAD_PX - TEXT_INSET_PX
        cell = (x, top, grid.x_at(right) - x - MONTH_PAD_PX, rules.month_height)
        node = _text(f"month-{index}", name, _inset_box(cell))
        nodes.append(replace(node, font_size=rules.month_font_size, plan=PlanView(is_bold=True)))
    return nodes


def _line(identifier: str, ends: tuple[Point, Point]) -> Edge:
    """Build a thin grid line between two points."""
    return Edge(identifier, Role.GRID, ends, None, None, None, head=Head.NONE)


def _header_lines(months: list[Cell], grid: Grid, tops: tuple[float, float]) -> list[Edge]:
    """Draw the line between the month row and the week row, and the lines between months."""
    header_top, week_top = tops
    if not months:
        return []
    lines = [_line("header-rule", ((grid.left, week_top), (grid.right, week_top)))]
    for index, (_, left, _right) in enumerate(months[1:], start=1):
        x = grid.x_at(left)
        lines.append(_line(f"month-line-{index}", ((x, header_top), (x, week_top))))
    return lines


def grid_lines(axis: Axis, grid: Grid, header_top: float, bottom: float) -> list[Edge]:
    """Draw the thin vertical line at every column edge, from the header down to the last row.

    Args:
        axis: The columns of the chart.
        grid: Where the columns are.
        header_top: The y of the top of the header.
        bottom: The y of the bottom of the last row.

    Returns:
        One line per column edge. Inside the header the lines run between the week names only;
        the two outer lines start under the header.
    """
    rules = grid.rules
    header_bottom = header_top + header_height(axis, rules)
    week_top = header_bottom - rules.week_height
    lines = []
    for index in range(axis.count + 1):
        top = header_bottom if index in (0, axis.count) else week_top
        x = grid.x_at(index)
        lines.append(_line(f"grid-{index}", ((x, top), (x, bottom))))
    return lines


def today_line(position: float, grid: Grid, ends: tuple[float, float]) -> Edge:
    """Draw the red dashed line of today, with its red pill under it.

    Args:
        position: Where today is, in columns from the left edge.
        grid: Where the columns are.
        ends: The y where the line starts (the bottom of the header) and the bottom of the rows.

    Returns:
        The line; it runs a little below the last row, and its pill is centred on its end.
    """
    rules = grid.rules
    x = grid.x_at(position)
    pill_height = rules.today_pill[1]
    end = ends[1] + rules.today_gap
    label = EdgeLabel("Today", (x, end + pill_height / 2), LabelKind.TODAY)
    return Edge("today", Role.TODAY, ((x, ends[0]), (x, end)), label, None, None, head=Head.NONE)


def legend_parts(
    statuses: set[Status], has_critical: bool, origin: Point, theme: Theme
) -> tuple[list[Node], list[Edge]]:
    """Draw the legend: a swatch and a name for each status in use, and the critical path.

    Args:
        statuses: The statuses the chart uses; only those are listed.
        has_critical: Whether the chart has a critical path.
        origin: The left end and the vertical middle of the legend.
        theme: The design tokens.

    Returns:
        The swatches and names, and the sample of the critical path.
    """
    rules = theme.planning.gantt
    swatch_width, swatch_height = rules.legend_swatch
    x, middle = origin
    nodes: list[Node] = []
    edges: list[Edge] = []
    entries = [(status, STATUS_NAMES[status]) for status in STATUS_ORDER if status in statuses]
    if has_critical:
        entries.append((None, CRITICAL_NAME))
    for index, (status, name) in enumerate(entries):
        if status is None:
            ends = ((x, middle), (x + swatch_width, middle))
            edges.append(Edge("legend-critical", Role.KEY, ends, None, None, None, head=Head.NONE))
        else:
            nodes.append(_swatch(f"legend-{status.value}", status, (x, middle), rules))
        text_x = x + swatch_width + LEGEND_TEXT_GAP_PX
        width = estimate_text_width(name, theme.layout, LEGEND_FONT_PX) + TEXT_SLACK_PX
        label = _text(
            f"legend-text-{index}", name, (text_x, middle - swatch_height, width, 2 * swatch_height)
        )
        nodes.append(replace(label, font_size=LEGEND_FONT_PX))
        x = text_x + width + rules.legend_item_gap
    return nodes, edges


def _swatch(identifier: str, status: Status, origin: Point, rules: GanttRules) -> Node:
    """Build the small bar that shows what a status looks like."""
    width, height = rules.legend_swatch
    view = PlanView(status=status, progress=LEGEND_PROGRESS)
    return Node(
        identifier, Shape.PLAN_BAR, origin[0], origin[1] - height / 2, width, height, (), None,
        None, None, DEFAULT_FONT_SIZE_PX, plan=view,
    )  # fmt: skip
