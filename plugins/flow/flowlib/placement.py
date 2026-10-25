"""Turn grid positions into pixel positions: node sizes, column widths, row heights, gaps."""

from collections import defaultdict
from dataclasses import dataclass

from .layered import Grid
from .model import DEFAULT_FONT_SIZE_PX, Node
from .sizing import FittedNode, fit_node
from .spec import Spec, SpecEdge
from .theme import LayoutRules


@dataclass(frozen=True)
class Placement:
    """The nodes of a flowchart at their pixel positions, and the room they take."""

    nodes: dict[str, Node]
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
    widths: dict[int, float], labelled: set[int], rules: LayoutRules
) -> dict[int, float]:
    """Return the x of each column's centre line, left to right, with the right gaps."""
    centers: dict[int, float] = {}
    left = rules.margin
    previous: int | None = None
    for index in sorted(widths):
        if previous is not None:
            wide = previous in labelled and previous + 1 == index
            left += rules.gap_horizontal_labelled if wide else rules.gap_horizontal
        centers[index] = left + widths[index] / 2
        left += widths[index]
        previous = index
    return centers


def _row_centers(
    heights: dict[int, float], labelled: set[int], top: float, rules: LayoutRules
) -> dict[int, float]:
    """Return the y of each row's centre line, top to bottom, with the right gaps."""
    centers: dict[int, float] = {}
    edge = top
    for index in sorted(heights):
        if index - 1 in heights:
            edge += rules.gap_vertical_labelled if index - 1 in labelled else rules.gap_vertical
        centers[index] = edge + heights[index] / 2
        edge += heights[index]
    return centers


def place_nodes(spec: Spec, grid: Grid, rules: LayoutRules) -> Placement:
    """Give every node its size and its position in pixels.

    Args:
        spec: The flowchart description.
        grid: The row and column of each node.
        rules: The layout rules.

    Returns:
        The nodes, and the right and bottom edge of the area they cover.
    """
    fitted = {
        node.id: fit_node(node.kind, node.text, node.icon is not None, rules) for node in spec.nodes
    }
    widths = _column_widths(fitted, grid.column)
    heights: dict[int, float] = defaultdict(float)
    for node_id, size in fitted.items():
        heights[grid.rank[node_id]] = max(heights[grid.rank[node_id]], size.height)
    top = rules.margin + (rules.title_block_height if spec.title else 0)
    across = _labelled_boundaries(grid.forward, grid.column)
    down = _labelled_boundaries(grid.forward, grid.rank)
    center_x = _column_centers(widths, across, rules)
    center_y = _row_centers(dict(heights), down, top, rules)
    nodes: dict[str, Node] = {}
    for node in spec.nodes:
        width = widths[grid.column[node.id]]
        height = fitted[node.id].height
        nodes[node.id] = Node(
            id=node.id,
            shape=node.kind,
            x=center_x[grid.column[node.id]] - width / 2,
            y=center_y[grid.rank[node.id]] - height / 2,
            width=width,
            height=height,
            text=fitted[node.id].lines,
            icon=node.icon,
            tone=node.tone,
            number=node.number,
            font_size=DEFAULT_FONT_SIZE_PX,
        )
    right = max(node.x + node.width for node in nodes.values())
    bottom = max(node.y + node.height for node in nodes.values())
    return Placement(nodes=nodes, right=right, bottom=bottom)
