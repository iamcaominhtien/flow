"""The Gantt chart: tasks over time, one row per task, drawn to design 08 section 2.

See ``gantt_spec`` for the spec. Time runs left to right in columns 88 px wide with a month
header above them; the names of the tasks are in a column on the left, each with the circle of
its owner. A phase is a grey band with its name, a milestone an amber diamond on its own row,
a dependency a thin arrow, and the critical path the one blue animated chain. ``gantt_axis``
draws the grid, the header, today and the legend; ``gantt_links`` the lines between tasks.
"""

from dataclasses import dataclass, replace

from ..canvas import fit_canvas
from ..model import (
    DEFAULT_FONT_SIZE_PX,
    Edge,
    Frame,
    FrameVariant,
    Node,
    PlanView,
    Scene,
    Shape,
    Tone,
)
from ..theme import Theme, load_theme
from .gantt_axis import Grid, grid_lines, header_height, header_parts, legend_parts, today_line
from .gantt_links import critical_links, dependency_edges
from .gantt_spec import GanttSpec, Milestone, Task, read_spec

HEADER_GAP_PX = 26  # between the title block and the header
LABEL_INSET_PX = 12  # a name is this much lower than the top of its row, so that rows do not touch
LABEL_SLACK_PX = 8  # least room between a task name and the chart
BAR_FONT_PX = 12
MIN_BAR_WIDTH_PX = 12
Box = tuple[float, float, float, float]  # x, y, width and height
BAR_SHAPES = (Shape.PLAN_BAR, Shape.MILESTONE)  # what a dependency line joins


@dataclass(frozen=True)
class _Row:
    """One row of the chart: a phase band, a task or a milestone. ``item`` is None for a band."""

    name: str
    item: Task | Milestone | None


def layout_raw(raw: object) -> Scene:
    """Lay out a Gantt chart from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``gantt`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(read_spec(raw))


def layout(spec: GanttSpec) -> Scene:
    """Place the header, the rows, the lines and the legend of a checked spec.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    rules = theme.layout
    rows = _rows(spec)
    header_top = rules.margin + (rules.title_block_height if spec.title else 0) + HEADER_GAP_PX
    gantt = theme.planning.gantt
    first_row = header_top + header_height(spec.axis, gantt) + gantt.grid_top_gap
    grid = Grid(gantt, rules.margin + gantt.label_column, first_row, spec.axis.count)
    bottom = first_row + len(rows) * gantt.row_height
    frames, nodes, edges = header_parts(spec.axis, grid, header_top)
    body_frames, body_nodes = _body(rows, grid, theme)
    by_id = {node.id: node for node in body_nodes if node.shape in BAR_SHAPES}
    edges += grid_lines(spec.axis, grid, header_top, bottom)
    edges += dependency_edges(spec, by_id, gantt.dependency_gap)
    if spec.today is not None:
        edges.append(today_line(spec.today, grid, (first_row - gantt.grid_top_gap, bottom)))
    legend_nodes, legend_edges = _legend(spec, grid, bottom, theme)
    scene = Scene(
        width=0,
        height=0,
        title=spec.title,
        description=spec.description,
        frames=tuple(frames + body_frames),
        nodes=tuple(nodes + body_nodes + legend_nodes),
        edges=tuple(edges + legend_edges),
    )
    return fit_canvas(scene)


def _rows(spec: GanttSpec) -> list[_Row]:
    """List the rows: for each group its band, its tasks and then its milestones."""
    groups: dict[str | None, list[Task | Milestone]] = {}
    for task in spec.tasks:
        groups.setdefault(task.group, []).append(task)
    for milestone in spec.milestones:
        groups.setdefault(_group_of(milestone, spec), []).append(milestone)
    rows = []
    for name, items in groups.items():
        if name is not None:
            rows.append(_Row(name, None))
        rows += [_Row(name or "", item) for item in items]
    return rows


def _group_of(milestone: Milestone, spec: GanttSpec) -> str | None:
    """Return the group a milestone is in: the one it names, else that of the task it follows."""
    if milestone.group is not None:
        return milestone.group
    followed = {task.id: task.group for task in spec.tasks}
    known = [followed[name] for name in milestone.after if name in followed]
    return known[0] if known else (spec.tasks[-1].group if spec.tasks else None)


def _body(rows: list[_Row], grid: Grid, theme: Theme) -> tuple[list[Frame], list[Node]]:
    """Place the bands, the names with their owners, the bars and the diamonds."""
    frames: list[Frame] = []
    nodes: list[Node] = []
    rules = grid.rules
    margin = theme.layout.margin
    for index, row in enumerate(rows):
        top = grid.top + index * rules.row_height
        if row.item is None:
            frames.append(_band(row.name, (margin, top), grid, len(frames)))
            continue
        nodes += _row_nodes(row.item, top, grid, theme)
    return frames, nodes


def _band(name: str, origin: tuple[float, float], grid: Grid, number: int) -> Frame:
    """Build the grey band of a phase, as wide as the label column and the chart together."""
    rules = grid.rules
    x, top = origin
    inset = (rules.row_height - rules.band_height) / 2
    return Frame(
        f"phase-{number}", x, top + inset, grid.right - x, rules.band_height, name, Tone.GRAY,
        FrameVariant.BAND,
    )  # fmt: skip


def _row_nodes(item: Task | Milestone, top: float, grid: Grid, theme: Theme) -> list[Node]:
    """Build the nodes of a task or milestone row: its name, its owner, and its bar or diamond."""
    rules = grid.rules
    margin = theme.layout.margin
    owner = item.owner if isinstance(item, Task) else None
    name_left = margin + rules.label_pad
    nodes = []
    if owner is not None:
        size = rules.person_size
        view = PlanView(initials=owner.initials, person_tone=owner.tone)
        nodes.append(
            _node(
                f"owner-{item.id}",
                Shape.PERSON,
                (name_left, top + (rules.row_height - size) / 2, size, size),
                ((owner.initials,), view),
            )
        )
        name_left += size + rules.person_gap
    inset = LABEL_INSET_PX
    box = (
        name_left,
        top + inset,
        grid.left - name_left - LABEL_SLACK_PX,
        rules.row_height - 2 * inset,
    )
    bold = isinstance(item, Milestone)
    label = _node(f"label-{item.id}", Shape.LABEL, box, ((item.label,), PlanView(is_bold=bold)))
    nodes.append(replace(label, font_size=rules.name_font_size))
    nodes.append(_mark(item, top, grid))
    return nodes


def _node(
    identifier: str, shape: Shape, box: Box, content: tuple[tuple[str, ...], PlanView]
) -> Node:
    """Build a planning node in a box, with its text and what it shows."""
    x, y, width, height = box
    text, view = content
    return Node(
        identifier, shape, x, y, width, height, text, None, None, None, DEFAULT_FONT_SIZE_PX,
        plan=view,
    )  # fmt: skip


def _mark(item: Task | Milestone, top: float, grid: Grid) -> Node:
    """Build the bar of a task, or the diamond of a milestone, on its row."""
    rules = grid.rules
    if isinstance(item, Milestone):
        size = rules.milestone_size
        box = (grid.x_at(item.at) - size / 2, top + (rules.row_height - size) / 2, size, size)
        return replace(_node(item.id, Shape.MILESTONE, box, ((), PlanView())), tone=Tone.AMBER)
    left = grid.x_at(item.start) + rules.bar_inset
    width = max(grid.x_at(item.end) - rules.bar_inset - left, MIN_BAR_WIDTH_PX)
    view = PlanView(status=item.status, progress=item.progress, reason=item.reason)
    box = (left, top + (rules.row_height - rules.bar_height) / 2, width, rules.bar_height)
    return replace(
        _node(item.id, Shape.PLAN_BAR, box, ((item.label,), view)), font_size=BAR_FONT_PX
    )


def _legend(
    spec: GanttSpec, grid: Grid, bottom: float, theme: Theme
) -> tuple[list[Node], list[Edge]]:
    """Place the legend under the chart, below the pill of today."""
    rules = grid.rules
    margin = theme.layout.margin
    middle = bottom + rules.today_gap + rules.today_pill[1] + rules.legend_gap
    statuses = {task.status for task in spec.tasks}
    return legend_parts(statuses, bool(critical_links(spec)), (margin, middle), theme)
