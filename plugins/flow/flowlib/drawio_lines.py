"""Draw the lines of a scene as draw.io edges: waypoints, ports, heads, animation and labels."""

import math
import xml.etree.ElementTree as ET
from itertools import pairwise

from .drawio_common import FONT_BOLD, LAYER_CELL_ID, add_geometry, add_vertex, style_string
from .markup import esc, fmt
from .model import SYMBOL_HEADS, Edge, EdgeLabel, Head, Node, Point
from .theme import LineStyle, Theme

CHIP_FONT_SIZE_PX = 11
CHIP_SPACING_PX = 3  # room around the text of a label chip
MILLISECONDS_PER_SECOND = 1000
DRAWIO_CYCLE_PX = 16  # draw.io spends ``flowAnimationDuration`` ms per 16 px of dash cycle
ARROW_SIZE_PER_STROKE = 3  # ``endSize`` per pixel of line width, tuned by eye against the HTML
NO_COLOR = "none"
DEFAULT_DASH = "6 5"  # for a line that is dashed by choice, not by its role
HEAD_ARROWS = {
    Head.NONE: "none",
    Head.FILLED: "block",
    Head.OPEN: "open",
    Head.DOT: "oval",
    Head.TRIANGLE: "block",
    Head.DIAMOND: "diamond",
    Head.DIAMOND_FILLED: "diamond",
    Head.ONE: "ERone",
    Head.MANY: "ERmany",
    Head.ONE_ONLY: "ERmandOne",
    Head.ZERO_ONE: "ERzeroToOne",
    Head.ZERO_MANY: "ERzeroToMany",
    Head.ONE_MANY: "ERoneToMany",
}
FILLED_HEADS = (Head.FILLED, Head.DOT, Head.DIAMOND_FILLED)
SYMBOL_HEAD_SIZE_PX = 12
EXTRA_LABEL_WIDTH_PX = 60
EXTRA_LABEL_HEIGHT_PX = 20


def _port(node: Node, point: Point) -> tuple[float, float]:
    """Return where a point on the border of a node lies, as fractions of its width and height."""
    return (point[0] - node.x) / node.width, (point[1] - node.y) / node.height


def _nearest_on_segment(start: Point, end: Point, target: Point) -> tuple[float, Point]:
    """Find the point of a segment that is nearest to ``target``.

    Args:
        start: One end of the segment.
        end: The other end.
        target: Any point.

    Returns:
        The fraction of the segment at which the nearest point lies, and that point.
    """
    run_x, run_y = end[0] - start[0], end[1] - start[1]
    length_squared = run_x**2 + run_y**2
    if length_squared == 0:
        return 0.0, start
    along = ((target[0] - start[0]) * run_x + (target[1] - start[1]) * run_y) / length_squared
    ratio = max(0.0, min(1.0, along))
    return ratio, (start[0] + run_x * ratio, start[1] + run_y * ratio)


def _project_on_path(points: tuple[Point, ...], target: Point) -> tuple[float, Point]:
    """Find the point of a path that is nearest to ``target``.

    Args:
        points: The path, at least two points.
        target: Any point.

    Returns:
        The fraction of the path length at which the nearest point lies (0 at the start, 1 at
        the end), and that point.
    """
    total = sum(math.dist(start, end) for start, end in pairwise(points))
    best: tuple[float, Point, float] = (math.inf, points[0], 0.0)
    travelled = 0.0
    for start, end in pairwise(points):
        ratio, nearest = _nearest_on_segment(start, end, target)
        distance = math.dist(nearest, target)
        if distance < best[0]:
            best = (distance, nearest, travelled + math.dist(start, end) * ratio)
        travelled += math.dist(start, end)
    return best[2] / total, best[1]


def _dash_pattern(dash: str, width: float) -> str:
    """Convert a dash pattern in pixels to draw.io's, which is in multiples of the line width.

    Args:
        dash: Space-separated dash and gap lengths in pixels, such as ``"6 5"``.
        width: The line width in pixels.

    Returns:
        The same pattern in units of the line width.
    """
    return " ".join(fmt(float(length) / width) for length in dash.split())


def _flow_duration_ms(dash: str | None, seconds: float) -> int:
    """Return the ``flowAnimationDuration`` that makes a line move as fast as in the HTML page.

    draw.io runs one dash cycle in ``duration * cycle / DRAWIO_CYCLE_PX`` milliseconds, while the
    page runs one cycle in ``seconds``; this solves for ``duration``.

    Args:
        dash: The dash pattern in pixels, such as ``"10 8"``; None is not animated.
        seconds: How long one dash cycle lasts in the HTML page.

    Returns:
        The duration in milliseconds.
    """
    cycle = sum(float(length) for length in (dash or "").split())
    return round(seconds * MILLISECONDS_PER_SECOND * DRAWIO_CYCLE_PX / cycle)


def _end_style(edge: Edge, line: LineStyle) -> dict[str, object]:
    """Return the style pairs for the arrowhead and the tail of an edge."""
    arrow_size = fmt(line.head_size * ARROW_SIZE_PER_STROKE / 2)
    return {
        "endArrow": HEAD_ARROWS[edge.head],
        "endFill": int(edge.head in FILLED_HEADS),
        "endSize": SYMBOL_HEAD_SIZE_PX if edge.head in SYMBOL_HEADS else arrow_size,
        "startArrow": HEAD_ARROWS[edge.tail],
        "startFill": int(edge.tail in FILLED_HEADS),
        "startSize": SYMBOL_HEAD_SIZE_PX if edge.tail in SYMBOL_HEADS else arrow_size,
    }


def _port_style(edge: Edge, nodes: dict[str, Node]) -> dict[str, object]:
    """Return the style pairs that pin both ends of an edge to the points where it attaches."""
    style: dict[str, object] = {}
    for end, point, prefix in (
        (edge.source, edge.points[0], "exit"),
        (edge.target, edge.points[-1], "entry"),
    ):
        if end in nodes:
            across, down = _port(nodes[end], point)
            style.update({f"{prefix}X": fmt(across), f"{prefix}Y": fmt(down), f"{prefix}Dx": 0})
            style[f"{prefix}Dy"] = 0
    return style


def _label_style(edge: Edge, theme: Theme) -> dict[str, object]:
    """Return the style pairs for the label of an edge: colours and size."""
    if edge.label is None:
        return {}
    chip = theme.chips[edge.label.kind]
    style: dict[str, object] = {
        "fontColor": chip.foreground,
        "fontSize": CHIP_FONT_SIZE_PX,
        "fontStyle": FONT_BOLD,
        "spacing": CHIP_SPACING_PX,
    }
    if chip.background != NO_COLOR:
        style["labelBackgroundColor"] = chip.background
    return style


def _edge_style(edge: Edge, nodes: dict[str, Node], theme: Theme) -> str:
    """Return the style of an edge cell: line, heads, ports, animation and label."""
    line = theme.roles[edge.role]
    style: dict[str, object] = {
        "html": 1,
        "rounded": 0,
        "strokeColor": line.color,
        "strokeWidth": fmt(line.width),
        **_end_style(edge, line),
        "fontFamily": theme.fonts.sans,
    }
    dash = line.dash or (DEFAULT_DASH if edge.dashed else None)
    if dash:
        style["dashed"] = 1
        style["dashPattern"] = _dash_pattern(dash, line.width)
    if line.animation:
        style["flowAnimation"] = 1
        speed = theme.animations[line.animation]
        style["flowAnimationDuration"] = _flow_duration_ms(line.dash, speed.seconds)
    style.update(_port_style(edge, nodes))
    style.update(_label_style(edge, theme))
    return style_string(style)


def _label_value(edge: Edge) -> str:
    """Return the label of an edge as HTML: the step number in bold, then the text."""
    if edge.label is None:
        return ""
    number = f"<b>{esc(edge.label.number)}</b>&nbsp;" if edge.label.number else ""
    return number + esc(edge.label.text)


def add_edge(root: ET.Element, edge: Edge, nodes: dict[str, Node], theme: Theme) -> None:
    """Add an edge with its waypoints, and its label placed along the line.

    Args:
        root: The ``root`` element of the diagram.
        edge: The line to add.
        nodes: Node id to node, to find the cells the edge joins.
        theme: The design tokens.
    """
    attributes = {
        "id": f"edge-{edge.id}",
        "value": _label_value(edge),
        "style": _edge_style(edge, nodes, theme),
        "edge": "1",
        "parent": LAYER_CELL_ID,
    }
    if edge.source in nodes:
        attributes["source"] = f"node-{edge.source}"
    if edge.target in nodes:
        attributes["target"] = f"node-{edge.target}"
    cell = ET.SubElement(root, "mxCell", attributes)
    geometry_attributes = {"relative": "1", "as": "geometry"}
    offset = (0.0, 0.0)
    if edge.label:
        along, nearest = _project_on_path(edge.points, edge.label.at)
        geometry_attributes["x"] = fmt(round(2 * along - 1, 4))
        offset = (edge.label.at[0] - nearest[0], edge.label.at[1] - nearest[1])
    geometry = ET.SubElement(cell, "mxGeometry", geometry_attributes)
    for name, (x, y) in (("sourcePoint", edge.points[0]), ("targetPoint", edge.points[-1])):
        ET.SubElement(geometry, "mxPoint", {"x": fmt(x), "y": fmt(y), "as": name})
    interior = ET.SubElement(geometry, "Array", {"as": "points"})
    for x, y in edge.points[1:-1]:
        ET.SubElement(interior, "mxPoint", {"x": fmt(x), "y": fmt(y)})
    if offset != (0.0, 0.0):
        ET.SubElement(
            geometry, "mxPoint", {"x": fmt(offset[0]), "y": fmt(offset[1]), "as": "offset"}
        )
    for index, extra in enumerate(edge.extras, start=1):
        _add_extra(root, f"edge-{edge.id}-end{index}", extra, theme)


def _add_extra(root: ET.Element, cell_id: str, extra: EdgeLabel, theme: Theme) -> None:
    """Add a small free-standing text next to the end of a line, such as a multiplicity."""
    chip = theme.chips[extra.kind]
    style = style_string(
        {
            "text": "",
            "html": 1,
            "align": "center",
            "verticalAlign": "middle",
            "strokeColor": "none",
            "fillColor": "none",
            "fontSize": CHIP_FONT_SIZE_PX,
            "fontStyle": FONT_BOLD,
            "fontColor": chip.foreground,
            "fontFamily": theme.fonts.mono,
        }
    )
    cell = add_vertex(root, cell_id, esc(extra.text), style)
    x, y = extra.at
    half_width, half_height = EXTRA_LABEL_WIDTH_PX / 2, EXTRA_LABEL_HEIGHT_PX / 2
    add_geometry(
        cell, (x - half_width, y - half_height, EXTRA_LABEL_WIDTH_PX, EXTRA_LABEL_HEIGHT_PX)
    )


def add_divider(root: ET.Element, cell_id: str, ends: tuple[Point, Point], color: str) -> None:
    """Add a dashed horizontal line, drawn as an edge without arrowheads.

    Args:
        root: The ``root`` element of the diagram.
        cell_id: A unique cell id.
        ends: The left end and the right end of the line.
        color: The line colour.
    """
    style = style_string(
        {"endArrow": "none", "html": 1, "dashed": 1, "strokeColor": color, "strokeWidth": 1}
    )
    attributes = {"id": cell_id, "value": "", "style": style, "edge": "1"}
    attributes["parent"] = LAYER_CELL_ID
    cell = ET.SubElement(root, "mxCell", attributes)
    geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    for name, (x, y) in zip(("sourcePoint", "targetPoint"), ends, strict=True):
        ET.SubElement(geometry, "mxPoint", {"x": fmt(x), "y": fmt(y), "as": name})
