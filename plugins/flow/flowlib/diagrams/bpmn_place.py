"""Place the elements, the pools and the lanes of a BPMN diagram on the page.

Every pool starts 64 px from the left edge with a coloured band 38 px wide that carries its
name. Lanes are at least 200 px high and pools are stacked 40 px apart. The elements of one
column share one x, so a message flow between two pools can run straight up and down. The
smallest gap between two columns is 56 px, and 100 px where a flow into the next column
carries a label.
"""

from dataclasses import dataclass, replace

from ..check import Rect
from ..model import Frame, FrameVariant, Node, Shape, Tone
from ..sizing import wrap_text
from ..text_area import text_area_width
from ..theme import BpmnRules, LayoutRules, Theme
from .bpmn_grid import Grid
from .bpmn_spec import LOOKS, BpmnSpec, Item, Link, LinkStyle, Pool

CAPTIONED_SHAPES = (Shape.START, Shape.END, Shape.INTERMEDIATE, Shape.DECISION, Shape.CYLINDER)
LABELLED_STYLES = (LinkStyle.SEQUENCE, LinkStyle.RETURN)
FILLED_SHAPES = (Shape.TASK, Shape.DOCUMENT)  # drawn in the tone of their lane
MIN_POOL_WIDTH_PX = 640
SAME_COLUMN_PX = 60  # a neighbour this close across is in the same column
VERTICAL_TOLERANCE_PX = 20  # a neighbour this much lower or higher is not on the same line
FONT_SIZE_PX = 12
LaneKey = tuple[str | None, str | None]


@dataclass(frozen=True)
class Placed:
    """The result of placing a diagram: its nodes, its frames and the rectangle of each pool."""

    nodes: dict[str, Node]
    frames: tuple[Frame, ...]
    pools: dict[str, Rect]


@dataclass(frozen=True)
class _LaneBox:
    """A lane on the page: where it starts, how high it is and which row is at its top."""

    key: LaneKey
    top: float
    height: float
    first_row: int
    last_row: int
    pitch: float


def place(spec: BpmnSpec, grid: Grid, theme: Theme) -> Placed:
    """Place every element, pool and lane.

    Args:
        spec: The checked spec.
        grid: The column and row of every element.
        theme: The design tokens.

    Returns:
        The nodes (a boundary event after its task), the pool and lane frames, and the pool
        rectangles that sequence flows must stay inside.
    """
    rules = theme.bpmn
    sizes = {item.id: _size(item, rules) for item in spec.items}
    left = theme.layout.margin + _band_depth(spec, rules)
    centers = _column_centers(spec, grid, sizes, (left + rules.content_pad, rules))
    lanes = _lane_boxes(spec, grid, theme)
    nodes = _build_nodes(spec, grid, (centers, sizes), (lanes, theme.layout))
    nodes = _with_boundaries(spec, nodes, (rules, theme.layout))
    width = _pool_width(spec, nodes, rules, theme)
    frames, pools = _frames(spec, lanes, (width, rules, theme))
    return Placed(_with_captions(spec, nodes, pools), frames, pools)


def _band_depth(spec: BpmnSpec, rules: BpmnRules) -> float:
    """Return how much room the deepest pool needs for its bands, at the left of the elements."""
    depths = [
        (2 if pool.lanes and pool.label else 1) * rules.band_width
        for pool in spec.pools
        if not pool.is_black_box
    ]
    return max(depths, default=0.0)


def _size(item: Item, rules: BpmnRules) -> tuple[float, float]:
    """Return the size of an element: an event is a circle, a gateway a diamond, a task a box."""
    shape = LOOKS[item.kind].shape
    if item.attached_to is not None:
        return (2 * rules.boundary_radius, 2 * rules.boundary_radius)
    if shape in (Shape.START, Shape.END, Shape.INTERMEDIATE):
        return (2 * rules.event_radius, 2 * rules.event_radius)
    if shape is Shape.DECISION:
        return (rules.gateway_width, rules.gateway_width)
    if shape is Shape.CYLINDER:
        return rules.data_store_size
    return rules.task_size


def _column_centers(
    spec: BpmnSpec,
    grid: Grid,
    sizes: dict[str, tuple[float, float]],
    where: tuple[float, BpmnRules],
) -> dict[int, float]:
    """Return the x of the middle of each column, with the gaps the labels need."""
    start, rules = where
    widths: dict[int, float] = {}
    for item in spec.items:
        if item.attached_to is None:
            column = grid.columns[item.id]
            widths[column] = max(widths.get(column, 0.0), sizes[item.id][0])
    labelled = {grid.columns[link.target] for link in _labelled_forward(spec, grid)}
    centers: dict[int, float] = {}
    previous: int | None = None
    for column in sorted(widths):
        if previous is None:
            centers[column] = start + widths[column] / 2
        else:
            gap = rules.gap_labelled if column in labelled else rules.gap_plain
            centers[column] = centers[previous] + (widths[previous] + widths[column]) / 2 + gap
        previous = column
    return centers


def _labelled_forward(spec: BpmnSpec, grid: Grid) -> list[Link]:
    """Return the labelled sequence flows that lead into a later column."""
    return [
        link
        for link in spec.links
        if link.label
        and link.style in LABELLED_STYLES
        and link.source in grid.columns
        and link.target in grid.columns
        and grid.columns[link.source] < grid.columns[link.target]
    ]


def _lane_boxes(spec: BpmnSpec, grid: Grid, theme: Theme) -> dict[LaneKey, _LaneBox]:
    """Return every lane with its top and its height, pools stacked from the top of the page."""
    rules = theme.bpmn
    rows: dict[LaneKey, list[int]] = {}
    for item in spec.items:
        rows.setdefault((item.pool, item.lane), []).append(grid.rows[item.id])
    boxes: dict[LaneKey, _LaneBox] = {}
    top = theme.layout.title_block_height + theme.layout.margin
    for key in _lane_order(spec, rows):
        first, last = (min(rows[key]), max(rows[key])) if key in rows else (0, 0)
        height = _lane_height(spec, key, (first, last), rules)
        boxes[key] = _LaneBox(key, top, height, first, last, rules.row_pitch)
        top += height + (rules.pool_gap if _ends_pool(spec, key) else 0)
    return boxes


def _lane_order(spec: BpmnSpec, rows: dict[LaneKey, list[int]]) -> list[LaneKey]:
    """List the lanes top to bottom: pool by pool, lane by lane; a flat diagram has one."""
    if not spec.pools:
        return [(None, None)]
    order: list[LaneKey] = []
    for pool in spec.pools:
        order.extend([(pool.id, lane.id) for lane in pool.lanes] or [(pool.id, None)])
    return order


def _ends_pool(spec: BpmnSpec, key: LaneKey) -> bool:
    """Tell whether a lane is the last one of its pool."""
    pool = next((p for p in spec.pools if p.id == key[0]), None)
    if pool is None or not pool.lanes:
        return True
    return pool.lanes[-1].id == key[1]


def _lane_height(spec: BpmnSpec, key: LaneKey, span: tuple[int, int], rules: BpmnRules) -> float:
    """Return the height of a lane: 200 px at least, more when it holds several rows."""
    pool = next((p for p in spec.pools if p.id == key[0]), None)
    if pool is not None and pool.is_black_box:
        return rules.black_box_height
    needed = (span[1] - span[0]) * rules.row_pitch + 2 * rules.lane_pad
    return max(rules.lane_min_height, needed) if spec.pools else needed


def _build_nodes(
    spec: BpmnSpec,
    grid: Grid,
    placed: tuple[dict[int, float], dict[str, tuple[float, float]]],
    where: tuple[dict[LaneKey, _LaneBox], LayoutRules],
) -> dict[str, Node]:
    """Build the node of every element that is not a boundary event, on its column and row."""
    centers, sizes = placed
    lanes, layout = where
    nodes: dict[str, Node] = {}
    for item in spec.items:
        if item.attached_to is not None:
            continue
        width, height = sizes[item.id]
        middle_y = _row_y(lanes[(item.pool, item.lane)], grid.rows[item.id])
        x = centers[grid.columns[item.id]] - width / 2
        nodes[item.id] = _node(spec, item, (x, middle_y - height / 2, width, height), layout)
    return nodes


def _row_y(box: _LaneBox, row: int) -> float:
    """Return the y of the middle of a row of a lane: the rows of the lane are centred in it."""
    return box.top + box.height / 2 + (row - (box.first_row + box.last_row) / 2) * box.pitch


def _node(
    spec: BpmnSpec, item: Item, box: tuple[float, float, float, float], layout: LayoutRules
) -> Node:
    """Build the node of an element at a position and size; a task wraps its name in lines."""
    shape = LOOKS[item.kind].shape
    x, y, width, height = box
    is_captioned = shape in CAPTIONED_SHAPES
    return Node(
        id=item.id,
        shape=shape,
        x=x,
        y=y,
        width=width,
        height=height,
        text=() if is_captioned else _lines(item.label, shape, (width, layout)),
        icon=None,
        tone=_tone(spec, item) if shape in FILLED_SHAPES else item.tone,
        number=item.number,
        font_size=FONT_SIZE_PX,
        caption=item.label if is_captioned and item.label else None,
        dashed=item.attached_to is not None and not item.is_interrupting,
        markers=item.markers,
        host=item.attached_to,
    )


def _lines(label: str, shape: Shape, size: tuple[float, LayoutRules]) -> tuple[str, ...]:
    """Break the name of a task into lines that fit its width."""
    width, layout = size
    room = text_area_width(shape, width, has_icon=False)
    return tuple(wrap_text(label, layout, room, FONT_SIZE_PX)) if label else ()


def _tone(spec: BpmnSpec, item: Item) -> Tone | None:
    """Return the tone of a task: its own, else its lane's, else its pool's."""
    if item.tone is not None:
        return item.tone
    pool = next((p for p in spec.pools if p.id == item.pool), None)
    if pool is None:
        return None
    lane = next((lane for lane in pool.lanes if lane.id == item.lane), None)
    return lane.tone if lane is not None else pool.tone


def _with_boundaries(
    spec: BpmnSpec, nodes: dict[str, Node], where: tuple[BpmnRules, LayoutRules]
) -> dict[str, Node]:
    """Add the boundary events, each on the bottom edge of its task."""
    rules, layout = where
    result = dict(nodes)
    hosts: dict[str, list[Item]] = {}
    for item in spec.items:
        if item.attached_to is not None:
            hosts.setdefault(item.attached_to, []).append(item)
    for host_id, events in hosts.items():
        host = nodes[host_id]
        for index, event in enumerate(events):
            x = _boundary_x(host, index, len(events), rules)
            size = 2 * rules.boundary_radius
            box = (x - size / 2, host.y + host.height - size / 2, size, size)
            result[event.id] = _node(spec, event, box, layout)
    return result


def _boundary_x(host: Node, index: int, count: int, rules: BpmnRules) -> float:
    """Return the x of the ``index``-th of ``count`` boundary events along a task's bottom edge."""
    if count == 1:
        return host.x + rules.boundary_inset
    span = host.width - 2 * rules.boundary_inset
    return host.x + rules.boundary_inset + index * span / (count - 1)


def _pool_width(spec: BpmnSpec, nodes: dict[str, Node], rules: BpmnRules, theme: Theme) -> float:
    """Return the width every pool has: it holds the farthest element, with room to spare."""
    right = max((node.x + node.width for node in nodes.values()), default=0.0)
    return max(MIN_POOL_WIDTH_PX, right + rules.pool_right_pad - theme.layout.margin)


def _frames(
    spec: BpmnSpec, lanes: dict[LaneKey, _LaneBox], where: tuple[float, BpmnRules, Theme]
) -> tuple[tuple[Frame, ...], dict[str, Rect]]:
    """Build the frames of the pools and lanes, and the rectangle of each pool."""
    width, rules, theme = where
    left = theme.layout.margin
    frames: list[Frame] = []
    pools: dict[str, Rect] = {}
    for pool in spec.pools:
        keys = [(pool.id, lane.id) for lane in pool.lanes] or [(pool.id, None)]
        top, bottom = lanes[keys[0]].top, lanes[keys[-1]].top + lanes[keys[-1]].height
        pools[pool.id] = Rect(left, top, left + width, bottom)
        frames.extend(_pool_frames(pool, (left, width, rules), (top, bottom, lanes)))
    return tuple(frames), pools


def _pool_frames(
    pool: Pool, across: tuple[float, float, BpmnRules], down: tuple[float, float, dict]
) -> list[Frame]:
    """Build the frames of one pool: a black-box bar, one pool frame, or a pool frame with lanes."""
    left, width, rules = across
    top, bottom, lanes = down
    if pool.is_black_box:
        return [
            Frame(
                pool.id,
                left,
                top,
                width,
                bottom - top,
                pool.label,
                pool.tone,
                FrameVariant.BLACK_BOX,
            )
        ]
    if not pool.lanes:
        return [
            Frame(pool.id, left, top, width, bottom - top, pool.label, pool.tone, FrameVariant.POOL)
        ]
    frames = []
    inner = left
    if pool.label:
        frames.append(
            Frame(pool.id, left, top, width, bottom - top, pool.label, pool.tone, FrameVariant.POOL)
        )
        inner = left + rules.band_width
    for lane in pool.lanes:
        box = lanes[(pool.id, lane.id)]
        frames.append(
            Frame(
                lane.id,
                inner,
                box.top,
                width - (inner - left),
                box.height,
                lane.label,
                lane.tone,
                FrameVariant.POOL,
            )
        )
    return frames


def _with_captions(
    spec: BpmnSpec, nodes: dict[str, Node], pools: dict[str, Rect]
) -> dict[str, Node]:
    """Hang each caption above its node when a line leaves its bottom, else below."""
    result = dict(nodes)
    for node in nodes.values():
        if node.caption is None:
            continue
        lower, higher = _neighbours(spec, node, nodes, pools)
        if lower and not higher:
            result[node.id] = replace(node, caption_above=True)
    hosts = {item.id: item for item in spec.items}
    return {
        name: result[name]
        for name in sorted(result, key=lambda n: hosts[n].attached_to is not None)
    }


def _neighbours(
    spec: BpmnSpec, node: Node, nodes: dict[str, Node], pools: dict[str, Rect]
) -> tuple[bool, bool]:
    """Tell whether a line is likely to use the bottom of a node, and whether one uses its top.

    A line uses the top or bottom of a node when it goes to a message partner, to an element in
    its own column, back to an earlier column, or, for a gateway, to an element on another row.
    """
    middle_x, middle_y = node.x + node.width / 2, node.y + node.height / 2
    lower = higher = False
    for link in spec.links:
        if node.id not in (link.source, link.target):
            continue
        other = link.target if link.source == node.id else link.source
        if other in nodes:
            other_x = nodes[other].x + nodes[other].width / 2
            other_y = nodes[other].y + nodes[other].height / 2
        elif other in pools:
            other_x, other_y = middle_x, (pools[other].top + pools[other].bottom) / 2
        else:
            continue
        is_back = (link.target == node.id and other_x > middle_x) or (
            link.source == node.id and other_x < middle_x
        )
        is_vertical = (
            link.style is LinkStyle.MESSAGE
            or abs(other_x - middle_x) < SAME_COLUMN_PX
            or node.shape is Shape.DECISION
            or is_back
        )
        lower |= is_vertical and other_y > middle_y + VERTICAL_TOLERANCE_PX
        higher |= is_vertical and other_y < middle_y - VERTICAL_TOLERANCE_PX
    return lower, higher
