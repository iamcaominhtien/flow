"""Turn grid positions into pixel positions: node sizes, column widths, row heights, gaps."""

from collections import defaultdict
from dataclasses import dataclass, replace

from .layered import Grid
from .model import DEFAULT_FONT_SIZE_PX, Direction, Frame, FrameVariant, Node, Point, Shape
from .screen_parts import screen_size
from .sizing import FittedNode, NodeContent, fit_card, fit_node, fit_table, fit_table_card
from .spec import Spec, SpecEdge, SpecNode
from .theme import LayoutRules, load_theme
from .zones import zone_frames

# Marks keep their own size: stretching a circle to the width of its column would make an ellipse.
FIXED_WIDTH_SHAPES = {
    Shape.START,
    Shape.END,
    Shape.INTERMEDIATE,
    Shape.CONNECTOR,
    Shape.ACTOR,
    Shape.FORK,
    Shape.SCREEN,
}


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


def _crosses_label(previous: int, index: int, labelled: set[int]) -> bool:
    """Tell whether a labelled edge crosses any gap between two positions."""
    return any(boundary in labelled for boundary in range(previous, index))


def _centers(
    sizes: dict[int, float], labelled: set[int], gaps: tuple[float, float], start: float
) -> dict[int, float]:
    """Return the centre line of each column (or row), in order, with the right gap between.

    Positions need not be consecutive: an empty column or row does not add a gap.

    Args:
        sizes: Position index to the width (or height) of that column (or row).
        labelled: The gaps that a labelled edge crosses, which need extra room.
        gaps: The gap between two neighbours, plain and labelled.
        start: Where the first column (or row) starts.

    Returns:
        Position index to the coordinate of its centre line.
    """
    plain_gap, labelled_gap = gaps
    centers: dict[int, float] = {}
    edge = start
    previous: int | None = None
    for index in sorted(sizes):
        if previous is not None:
            edge += labelled_gap if _crosses_label(previous, index, labelled) else plain_gap
        centers[index] = edge + sizes[index] / 2
        edge += sizes[index]
        previous = index
    return centers


def rules_for(spec: Spec, rules: LayoutRules) -> LayoutRules:
    """Return the rules to lay out with, in layout space.

    For a left-to-right flow the gaps along and across the flow swap, because layout space is
    mirrored: the design's horizontal gap must apply along the flow. With zones, the gaps grow
    so that the frames of two neighbouring zones do not touch.

    Args:
        spec: The description, which gives the direction and the zones.
        rules: The layout rules.

    Returns:
        The rules, adjusted.
    """
    if spec.direction is Direction.RIGHT:
        rules = replace(
            rules,
            gap_vertical=rules.gap_horizontal,
            gap_vertical_labelled=rules.gap_horizontal_labelled,
            gap_horizontal=rules.gap_vertical,
            gap_horizontal_labelled=rules.gap_vertical_labelled,
        )
    if spec.zones:
        room = 2 * rules.zone_padding
        rules = replace(
            rules,
            gap_vertical=max(rules.gap_vertical, room + rules.zone_label_room),
            gap_vertical_labelled=max(rules.gap_vertical_labelled, room + rules.zone_label_room),
            gap_horizontal=max(rules.gap_horizontal, room + rules.zone_padding / 2),
            gap_horizontal_labelled=max(rules.gap_horizontal_labelled, room + rules.zone_padding),
        )
    return rules


def fit_content(node: SpecNode, rules: LayoutRules) -> FittedNode:
    """Fit one node to its content: a table to its rows, any other shape to its text."""
    has_icon = node.icon is not None
    fixed = _fit_fixed(node, rules)
    if fixed is not None:
        return fixed
    if node.kind is Shape.TABLE:
        if node.card:
            return fit_table_card(node.text, node.sections, rules)
        return fit_table(node.text, node.sections, has_icon, rules)
    if node.card:
        return fit_card(NodeContent(node.text, node.detail, has_icon), rules)
    return fit_node(node.kind, NodeContent(node.text, node.detail, has_icon), rules)


def _fit_fixed(node: SpecNode, rules: LayoutRules) -> FittedNode | None:
    """Return the size of a node that does not grow with its text, or None for any other."""
    if node.view is not None:
        width, height = screen_size(node.view, load_theme())
        return FittedNode(width, height, (node.text,))
    if node.kind is Shape.FORK:
        return FittedNode(*rules.min_sizes[Shape.FORK], ())
    if node.kind is Shape.CONNECTOR:
        return _fit_connector(node, rules)
    return None


def _fit_connector(node: SpecNode, rules: LayoutRules) -> FittedNode:
    """Keep a connector a small circle: its letter is the text and its note hangs beside it."""
    width, height = rules.min_sizes[Shape.CONNECTOR]
    return FittedNode(width, height, (node.text,), (node.detail,) if node.detail else ())


def _layout_sizes(spec: Spec, rules: LayoutRules) -> dict[str, FittedNode]:
    """Fit every node to its content and, for a left-to-right chart, swap width and height."""
    fitted = {node.id: fit_content(node, rules) for node in spec.nodes}
    if spec.direction is Direction.DOWN:
        return fitted
    bars = {node.id for node in spec.nodes if node.kind is Shape.FORK}
    return {
        node_id: size if node_id in bars else replace(size, width=size.height, height=size.width)
        for node_id, size in fitted.items()
    }


def _lane_frames(
    spec: Spec, bands: dict[int, tuple[float, float]], rows: tuple[float, float], rules: LayoutRules
) -> tuple[Frame, ...]:
    """Build one frame per swimlane, covering the whole length of the flow.

    Args:
        spec: The flowchart description, with its lanes.
        bands: Lane index to the left edge and the width of its band.
        rows: The top and bottom of the nodes along the flow.
        rules: The layout rules: the space kept between the nodes and the end of a lane, and
            the room for the tab that holds the lane's name at the start of the flow.

    Returns:
        The frames, in lane order.
    """
    top, bottom = rows
    pad, tab = rules.lane_padding, rules.lane_tab
    return tuple(
        Frame(
            id=f"lane-{lane.id}",
            x=bands[index][0],
            y=top - pad - tab,
            width=bands[index][1],
            height=bottom - top + 2 * pad + tab,
            label=lane.label,
            tone=lane.tone,
            variant=FrameVariant.LANE,
        )
        for index, lane in enumerate(spec.lanes)
    )


def page_origin(spec: Spec, rules: LayoutRules) -> tuple[float, float]:
    """Return the left and top of the first column and row, leaving room for the title.

    The title sits at the top of the page. In layout space the page top is the top for a
    top-to-bottom chart, and the left for a left-to-right chart.
    """
    title = rules.title_block_height if spec.title else 0
    is_down = spec.direction is Direction.DOWN
    lane_room = rules.lane_padding + rules.lane_tab if spec.lanes else 0
    return rules.margin + (0 if is_down else title), rules.margin + (
        title if is_down else 0
    ) + lane_room


def _node_width(node: SpecNode, size: FittedNode, column_width: float, spec: Spec) -> float:
    """Return the drawn width: the column's, except for a mark or in a swimlane chart."""
    if spec.lanes or node.kind in FIXED_WIDTH_SHAPES:
        return size.width
    return column_width


def make_node(node: SpecNode, size: FittedNode, center: Point, width: float) -> Node:
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
        detail=size.detail,
        caption=node.caption,
        sections=node.sections,
        card=node.card,
        dashed=node.dashed,
        screen=node.view,
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
    rules = rules_for(spec, base_rules)
    fitted = _layout_sizes(spec, base_rules)
    widths = _column_widths(fitted, grid.column)
    bands: dict[int, tuple[float, float]] = {}
    if spec.lanes and grid.lane_columns:
        center_x, bands = _lane_positions(spec, grid, fitted, rules)
    else:
        center_x = _column_centers(spec, grid, fitted, rules)
    if spec.lanes and not bands:
        bands = {
            index: (center_x[index] - size / 2, size)
            for index, size in _lane_widths(widths, spec, rules).items()
        }
    heights: dict[int, float] = defaultdict(float)
    for node_id, size in fitted.items():
        heights[grid.rank[node_id]] = max(heights[grid.rank[node_id]], size.height)
    top = page_origin(spec, rules)[1]
    row_gaps = (rules.gap_vertical, rules.gap_vertical_labelled)
    labelled_rows = _labelled_boundaries(grid.forward, grid.rank)
    center_y = _centers(dict(heights), labelled_rows, row_gaps, top)
    nodes = {
        node.id: make_node(
            node,
            fitted[node.id],
            (
                center_x[grid.column[node.id]],
                _node_center_y(
                    node,
                    fitted[node.id],
                    (center_y[grid.rank[node.id]], heights[grid.rank[node.id]]),
                ),
            ),
            _node_width(node, fitted[node.id], widths[grid.column[node.id]], spec),
        )
        for node in spec.nodes
    }
    return _with_frames(spec, nodes, bands, rules)


def _node_center_y(node: SpecNode, size: FittedNode, row: tuple[float, float]) -> float:
    """Return the centre y of a node: the row's centre, or for a table a top-aligned centre.

    Tables of different heights in one row line up at their tops, as in the design's ER pages.

    Args:
        node: The node.
        size: Its fitted size.
        row: The centre y and the height of the row the node is in.

    Returns:
        The y of the middle of the node.
    """
    centre, height = row
    if node.kind is not Shape.TABLE:
        return centre
    return centre - height / 2 + size.height / 2


def lane_floor(spec: Spec, rules: LayoutRules) -> float:
    """Return the least size of a lane across the flow.

    A flowchart follows its page: 210 px with plain nodes and 240 px when a card is drawn.
    Other types that draw lanes keep the general minimum.
    """
    if not spec.is_flowchart:
        return rules.lane_min_size
    has_cards = any(node.card for node in spec.nodes)
    return rules.lane_size_card if has_cards else rules.lane_size_plain


def _lane_widths(widths: dict[int, float], spec: Spec, rules: LayoutRules) -> dict[int, float]:
    """Return the width of the lane of each column: the widest node plus padding, or a minimum."""
    floor = lane_floor(spec, rules)
    return {index: max(floor, width + 2 * rules.lane_padding) for index, width in widths.items()}


def _column_centers(
    spec: Spec, grid: Grid, fitted: dict[str, FittedNode], rules: LayoutRules
) -> dict[int, float]:
    """Return the centre x of each column when the columns are not lane-owned."""
    widths = _column_widths(fitted, grid.column)
    if spec.lanes:
        widths = _lane_widths(widths, spec, rules)
    column_gaps = (
        (0.0, 0.0) if spec.lanes else (rules.gap_horizontal, rules.gap_horizontal_labelled)
    )
    labelled_columns = _labelled_boundaries(grid.forward, grid.column)
    return _centers(widths, labelled_columns, column_gaps, page_origin(spec, rules)[0])


def _lane_positions(
    spec: Spec, grid: Grid, fitted: dict[str, FittedNode], rules: LayoutRules
) -> tuple[dict[int, float], dict[int, tuple[float, float]]]:
    """Place the columns of each swimlane inside its band, and size the bands.

    A lane with several columns (side-by-side branches) keeps ``gap_horizontal`` between them
    and ``lane_padding`` at both ends; a lane is never narrower than ``lane_min_size``, and its
    columns are centred in it.

    Args:
        spec: The description, with its lanes.
        grid: The columns, and which columns each lane owns.
        fitted: The size of each node.
        rules: The layout rules, in layout space.

    Returns:
        The centre x of each column, and each lane's left edge and width.
    """
    column_width: dict[int, float] = defaultdict(float)
    for node_id, size in fitted.items():
        column_width[grid.column[node_id]] = max(column_width[grid.column[node_id]], size.width)
    left = page_origin(spec, rules)[0]
    centers: dict[int, float] = {}
    bands: dict[int, tuple[float, float]] = {}
    for lane, columns in grid.lane_columns.items():
        content = sum(column_width[c] for c in columns) + rules.gap_horizontal * (len(columns) - 1)
        width = max(lane_floor(spec, rules), content + 2 * rules.lane_padding)
        edge = left + (width - content) / 2
        for column in columns:
            centers[column] = edge + column_width[column] / 2
            edge += column_width[column] + rules.gap_horizontal
        bands[lane] = (left, width)
        left += width
    return centers, bands


def _with_frames(
    spec: Spec,
    nodes: dict[str, Node],
    bands: dict[int, tuple[float, float]],
    rules: LayoutRules,
) -> Placement:
    """Add the swimlane and zone frames to placed nodes, and measure the area they cover.

    Args:
        spec: The description.
        nodes: The placed nodes.
        bands: Each lane's left edge and width; empty when there are no lanes.
        rules: The layout rules.

    Returns:
        The finished placement.
    """
    right = max(node.x + node.width for node in nodes.values())
    bottom = max(node.y + node.height for node in nodes.values())
    frames: tuple[Frame, ...] = ()
    if spec.lanes:
        row_span = (min(node.y for node in nodes.values()), bottom)
        frames = _lane_frames(spec, bands, row_span, rules)
    if spec.zones:
        frames = frames + zone_frames(spec, nodes, rules)
    if frames:
        right = max([right, *(frame.x + frame.width for frame in frames)])
        bottom = max([bottom, *(frame.y + frame.height for frame in frames)])
    return Placement(nodes=nodes, frames=frames, right=right, bottom=bottom)
