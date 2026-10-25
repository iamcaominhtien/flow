"""Turn grid positions into pixel positions: node sizes, column widths, row heights, gaps."""

from collections import defaultdict
from dataclasses import dataclass, replace

from .layered import Grid
from .model import DEFAULT_FONT_SIZE_PX, Direction, Frame, Node, Point
from .sizing import FittedNode, fit_node
from .spec import Spec, SpecEdge, SpecNode
from .theme import LayoutRules


@dataclass(frozen=True)
class Placement:
    """The nodes and frames of a flowchart at their pixel positions, and the room they take.

    Positions are in layout space, where the flow always runs top to bottom; ``build.layout``
    mirrors them back for a left-to-right chart.
    """

    nodes: dict[str, Node]
    frames: tuple[Frame, ...]
    right: float
    bottom: float


def _labelled_boundaries(edges: tuple[SpecEdge, ...], position: dict[str, int]) -> set[int]:
    """Return the gaps that a labelled edge crosses, which need extra room for the label.

    Args:
        edges: The forward edges.
        position: Node id to its row (or its column).

    Returns:
        The numbers ``b`` such that the gap between ``b`` and ``b + 1`` is crossed by a
        labelled edge.
    """
    crossed: set[int] = set()
    for edge in edges:
        if not edge.label:
            continue
        low, high = sorted((position[edge.source], position[edge.target]))
        crossed.update(boundary for boundary in range(low, high))
    return crossed


def _column_widths(fitted: dict[str, FittedNode], column: dict[str, int]) -> dict[int, float]:
    """Give every node in a column the width of the widest one, as the design asks."""
    widths: dict[int, float] = defaultdict(float)
    for node_id, size in fitted.items():
        widths[column[node_id]] = max(widths[column[node_id]], size.width)
    return dict(widths)


def _column_centers(
    widths: dict[int, float], labelled: set[int], gaps: tuple[float, float], left: float
) -> dict[int, float]:
    """Return the x of each column's centre line, left to right.

    Args:
        widths: Column index to its width.
        labelled: The columns whose right-hand gap a labelled edge crosses.
        gaps: The gap between two columns, plain and labelled.
        left: The x where the first column starts.

    Returns:
        Column index to the x of its centre line.
    """
    plain_gap, labelled_gap = gaps
    centers: dict[int, float] = {}
    previous: int | None = None
    for index in sorted(widths):
        if previous is not None:
            wide = previous in labelled and previous + 1 == index
            left += labelled_gap if wide else plain_gap
        centers[index] = left + widths[index] / 2
        left += widths[index]
        previous = index
    return centers


def _row_centers(
    heights: dict[int, float], labelled: set[int], gaps: tuple[float, float], top: float
) -> dict[int, float]:
    """Return the y of each row's centre line, top to bottom.

    Args:
        heights: Row index to its height.
        labelled: The rows whose following gap a labelled edge crosses.
        gaps: The gap between two rows, plain and labelled.
        top: The y where the first row starts.

    Returns:
        Row index to the y of its centre line.
    """
    plain_gap, labelled_gap = gaps
    centers: dict[int, float] = {}
    edge = top
    for index in sorted(heights):
        if index - 1 in heights:
            edge += labelled_gap if index - 1 in labelled else plain_gap
        centers[index] = edge + heights[index] / 2
        edge += heights[index]
    return centers


def rules_for(direction: Direction, rules: LayoutRules) -> LayoutRules:
    """Return the rules to lay out with, in layout space.

    For a left-to-right flow the gaps along and across the flow swap, because layout space
    is mirrored: the design's horizontal gap must apply along the flow.

    Args:
        direction: The direction of the flow.
        rules: The layout rules.

    Returns:
        The same rules, or a copy with the vertical and horizontal gaps exchanged.
    """
    if direction is Direction.DOWN:
        return rules
    return replace(
        rules,
        gap_vertical=rules.gap_horizontal,
        gap_vertical_labelled=rules.gap_horizontal_labelled,
        gap_horizontal=rules.gap_vertical,
        gap_horizontal_labelled=rules.gap_vertical_labelled,
    )


def _layout_sizes(spec: Spec, rules: LayoutRules) -> dict[str, FittedNode]:
    """Fit every node to its text and, for a left-to-right chart, swap width and height."""
    fitted = {
        node.id: fit_node(node.kind, node.text, node.icon is not None, rules) for node in spec.nodes
    }
    if spec.direction is Direction.DOWN:
        return fitted
    return {
        node_id: FittedNode(size.height, size.width, size.lines) for node_id, size in fitted.items()
    }


def _lane_frames(
    spec: Spec, bands: dict[int, tuple[float, float]], rows: tuple[float, float], pad: float
) -> tuple[Frame, ...]:
    """Build one frame per swimlane, covering the whole length of the flow.

    Args:
        spec: The flowchart description, with its lanes.
        bands: Lane index to the left edge and the width of its band.
        rows: The top and bottom of the nodes along the flow.
        pad: Space kept between the nodes and the end of a lane.

    Returns:
        The frames, in lane order.
    """
    top, bottom = rows
    return tuple(
        Frame(
            id=f"lane-{lane.id}",
            x=bands[index][0],
            y=top - pad,
            width=bands[index][1],
            height=bottom - top + 2 * pad,
            label=lane.label,
            tone=lane.tone,
        )
        for index, lane in enumerate(spec.lanes)
    )


def _origin(spec: Spec, rules: LayoutRules) -> tuple[float, float]:
    """Return the left and top of the first column and row, leaving room for the title.

    The title sits at the top of the page. In layout space the page top is the top for a
    top-to-bottom chart, and the left for a left-to-right chart.
    """
    title = rules.title_block_height if spec.title else 0
    is_down = spec.direction is Direction.DOWN
    lane_room = rules.lane_padding if spec.lanes else 0
    return rules.margin + (0 if is_down else title), rules.margin + (
        title if is_down else 0
    ) + lane_room


def _make_node(node: SpecNode, size: FittedNode, center: Point, width: float) -> Node:
    """Build a scene node from its spec, its fitted size and the centre it is placed at."""
    return Node(
        id=node.id,
        shape=node.kind,
        x=center[0] - width / 2,
        y=center[1] - size.height / 2,
        width=width,
        height=size.height,
        text=size.lines,
        icon=node.icon,
        tone=node.tone,
        number=node.number,
        font_size=DEFAULT_FONT_SIZE_PX,
    )


def place_nodes(spec: Spec, grid: Grid, base_rules: LayoutRules) -> Placement:
    """Give every node its size and its position in pixels, in layout space.

    Args:
        spec: The flowchart description.
        grid: The row and column of each node.
        base_rules: The layout rules, before they are adjusted for the direction.

    Returns:
        The nodes, the swimlane frames, and the right and bottom edge of the area they cover.
    """
    rules = rules_for(spec.direction, base_rules)
    fitted = _layout_sizes(spec, base_rules)
    widths = _column_widths(fitted, grid.column)
    if spec.lanes:
        pad = rules.lane_padding
        widths = {
            index: max(rules.lane_min_size, width + 2 * pad) for index, width in widths.items()
        }
    heights: dict[int, float] = defaultdict(float)
    for node_id, size in fitted.items():
        heights[grid.rank[node_id]] = max(heights[grid.rank[node_id]], size.height)
    left, top = _origin(spec, rules)
    column_gaps = (
        (0.0, 0.0) if spec.lanes else (rules.gap_horizontal, rules.gap_horizontal_labelled)
    )
    labelled_columns = _labelled_boundaries(grid.forward, grid.column)
    center_x = _column_centers(widths, labelled_columns, column_gaps, left)
    row_gaps = (rules.gap_vertical, rules.gap_vertical_labelled)
    labelled_rows = _labelled_boundaries(grid.forward, grid.rank)
    center_y = _row_centers(dict(heights), labelled_rows, row_gaps, top)
    nodes = {
        node.id: _make_node(
            node,
            fitted[node.id],
            (center_x[grid.column[node.id]], center_y[grid.rank[node.id]]),
            fitted[node.id].width if spec.lanes else widths[grid.column[node.id]],
        )
        for node in spec.nodes
    }
    right = max(node.x + node.width for node in nodes.values())
    bottom = max(node.y + node.height for node in nodes.values())
    frames: tuple[Frame, ...] = ()
    if spec.lanes:
        bands = {index: (center_x[index] - widths[index] / 2, widths[index]) for index in widths}
        row_span = (min(node.y for node in nodes.values()), bottom)
        frames = _lane_frames(spec, bands, row_span, rules.lane_padding)
        right = max(frame.x + frame.width for frame in frames)
        bottom = max(frame.y + frame.height for frame in frames)
    return Placement(nodes=nodes, frames=frames, right=right, bottom=bottom)
