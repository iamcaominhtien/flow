"""Render a scene as a draw.io file (an uncompressed ``mxfile``) that stays editable.

Nodes are vertices, lines are edges that keep their routed waypoints, and the labels of lines
are edge labels placed at their position along the line. Icons are small image cells inside
their node, so they move with it. Animated lines use draw.io's ``flowAnimation`` style.
"""

import base64
import math
import xml.etree.ElementTree as ET
from collections.abc import Callable
from itertools import pairwise

from .markup import esc, fmt
from .model import ArrowEnd, Edge, Frame, Node, Point, Scene, Shape
from .shapes import BOX_CORNER_RADIUS_PX, STROKE_WIDTH_PX, SUBPROCESS_BAR_INSET_PX
from .text_area import ICON_TEXT_RESERVE_PX
from .theme import Theme, load_icons, load_theme

Bounds = tuple[float, float, float, float]  # x, y, width, height

ROOT_CELL_ID = "0"
LAYER_CELL_ID = "1"
FONT_BOLD = 1  # the draw.io ``fontStyle`` bit for bold
ICON_SIZE_PX = 18
ICON_STROKE_WIDTH = 2
ICON_LEFT_PX = 14
ICON_VIEW_BOX = "0 0 24 24"
BADGE_HEIGHT_PX = 20
BADGE_MIN_WIDTH_PX = 22
BADGE_OVERHANG_LEFT_PX = 6
BADGE_OVERHANG_TOP_PX = 10
BADGE_FONT_SIZE_PX = 11
TITLE_LEFT_PX = 64
TITLE_TOP_PX = 48
TITLE_FONT_SIZE_PX = 24
TITLE_HEIGHT_PX = 34
DESCRIPTION_FONT_SIZE_PX = 13
DESCRIPTION_HEIGHT_PX = 44
DESCRIPTION_MAX_WIDTH_PX = 900
CHIP_FONT_SIZE_PX = 11
MILLISECONDS_PER_SECOND = 1000
DRAWIO_CYCLE_PX = 16  # draw.io spends ``flowAnimationDuration`` ms per 16 px of dash cycle
CHIP_SPACING_PX = 3  # room around the text of a label chip
FRAME_CORNER_PERCENT = 6
PARALLELOGRAM_SLANT_MAX_PX = 18
PARALLELOGRAM_SLANT_DIVISOR = 6
HEXAGON_SLANT_MAX_PX = 20
HEXAGON_SLANT_DIVISOR = 5
DOCUMENT_WAVE_FRACTION = 0.2
PILL_ARC_PERCENT = 50
ARROW_SIZE_PER_STROKE = 3  # ``endSize`` per pixel of line width, tuned by eye against the HTML


def _style(parts: dict[str, object]) -> str:
    """Join style pairs into a draw.io style string, which ends with a semicolon.

    A pair whose value is empty is written as a bare key (``rhombus;``), which is how draw.io
    writes a shape name or a flag.
    """
    return "".join(f"{key}={value};" if value != "" else f"{key};" for key, value in parts.items())


def _pill_style(node: Node) -> dict[str, object]:
    """Style pairs for a rounded rectangle with fully round ends."""
    return {"rounded": 1, "arcSize": PILL_ARC_PERCENT}


def _box_style(node: Node) -> dict[str, object]:
    """Style pairs for a rectangle with rounded corners."""
    return {"rounded": 1, "absoluteArcSize": 1, "arcSize": 2 * BOX_CORNER_RADIUS_PX}


def _subprocess_style(node: Node) -> dict[str, object]:
    """Style pairs for the process shape: a box with two vertical bars."""
    bar_fraction = SUBPROCESS_BAR_INSET_PX / node.width
    return {"shape": "process", "backgroundOutline": 1, "size": fmt(bar_fraction)}


def _diamond_style(node: Node) -> dict[str, object]:
    """Style pairs for a diamond."""
    return {"rhombus": ""}


def _parallelogram_style(node: Node) -> dict[str, object]:
    """Style pairs for a parallelogram whose slant is fixed in pixels."""
    slant = min(PARALLELOGRAM_SLANT_MAX_PX, node.width / PARALLELOGRAM_SLANT_DIVISOR)
    return {
        "shape": "parallelogram",
        "perimeter": "parallelogramPerimeter",
        "fixedSize": 1,
        "size": fmt(slant),
    }


def _document_style(node: Node) -> dict[str, object]:
    """Style pairs for a document: a box with a wavy bottom edge."""
    return {"shape": "document", "boundedLbl": 1, "size": DOCUMENT_WAVE_FRACTION}


def _hexagon_style(node: Node) -> dict[str, object]:
    """Style pairs for a hexagon with pointed left and right ends."""
    slant = min(HEXAGON_SLANT_MAX_PX, node.width / HEXAGON_SLANT_DIVISOR)
    return {
        "shape": "hexagon",
        "perimeter": "hexagonPerimeter2",
        "fixedSize": 1,
        "size": fmt(slant),
    }


def _circle_style(node: Node) -> dict[str, object]:
    """Style pairs for an ellipse, which is a circle when the node is square."""
    return {"ellipse": ""}


SHAPE_STYLES: dict[Shape, Callable[[Node], dict[str, object]]] = {
    Shape.TERMINATOR: _pill_style,
    Shape.FAIL: _pill_style,
    Shape.PROCESS: _box_style,
    Shape.SUBPROCESS: _subprocess_style,
    Shape.DECISION: _diamond_style,
    Shape.IO: _parallelogram_style,
    Shape.DOCUMENT: _document_style,
    Shape.PREPARATION: _hexagon_style,
    Shape.CONNECTOR: _circle_style,
}


def _node_style(node: Node, theme: Theme) -> str:
    """Return the full style of a node cell: outline, colours and text."""
    colors = theme.shapes[node.shape]
    fill = theme.tones[node.tone].box if node.tone else colors.fill
    style = {
        **SHAPE_STYLES[node.shape](node),
        "html": 1,
        "whiteSpace": "wrap",
        "fillColor": fill,
        "strokeColor": colors.stroke,
        "strokeWidth": STROKE_WIDTH_PX,
        "fontColor": theme.ink,
        "fontSize": fmt(node.font_size),
        "fontStyle": FONT_BOLD,
        "fontFamily": theme.fonts.sans,
    }
    if node.icon:
        style["spacingLeft"] = ICON_TEXT_RESERVE_PX
    return _style(style)


def _label_value(lines: tuple[str, ...]) -> str:
    """Join text lines with ``<br>``, escaping each so that markup in the text stays text."""
    return "<br>".join(esc(line) for line in lines)


def _geometry(parent: ET.Element, bounds: Bounds) -> None:
    """Add the rectangle of a vertex cell, given as ``(x, y, width, height)``."""
    x, y, width, height = bounds
    ET.SubElement(
        parent,
        "mxGeometry",
        {"x": fmt(x), "y": fmt(y), "width": fmt(width), "height": fmt(height), "as": "geometry"},
    )


def _vertex(root: ET.Element, cell_id: str, value: str, style: str) -> ET.Element:
    """Add a vertex cell to the diagram's layer and return it, so that its geometry can be added.

    Args:
        root: The ``root`` element of the diagram.
        cell_id: A unique cell id.
        value: The label, already escaped for HTML.
        style: The draw.io style string.

    Returns:
        The new ``mxCell`` element.
    """
    attributes = {"id": cell_id, "value": value, "style": style, "vertex": "1"}
    attributes["parent"] = LAYER_CELL_ID
    return ET.SubElement(root, "mxCell", attributes)


def _icon_data_uri(name: str, stroke: str) -> str:
    """Build the ``image`` style value for an icon: a base64 SVG with no ``base64`` keyword.

    draw.io splits styles at semicolons, so the usual ``;base64,`` of a data URI cannot be used.
    """
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{ICON_VIEW_BOX}" fill="none" '
        f'stroke="{stroke}" stroke-width="{ICON_STROKE_WIDTH}" stroke-linecap="round" '
        f'stroke-linejoin="round">{load_icons()[name]}</svg>'
    )
    return "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()


def _add_node(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add a node, its icon (as a child cell) and its number badge."""
    cell = _vertex(root, f"node-{node.id}", _label_value(node.text), _node_style(node, theme))
    _geometry(cell, (node.x, node.y, node.width, node.height))
    if node.icon:
        icon_style = _style(
            {"shape": "image", "image": _icon_data_uri(node.icon, theme.shapes[node.shape].stroke)}
        )
        icon = _vertex(root, f"icon-{node.id}", "", icon_style)
        icon.set("parent", f"node-{node.id}")  # a child cell moves with its node
        icon_top = (node.height - ICON_SIZE_PX) / 2
        _geometry(icon, (ICON_LEFT_PX, icon_top, ICON_SIZE_PX, ICON_SIZE_PX))
    if node.number:
        _add_badge(root, node, theme)


def _add_badge(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the number badge at the top-left corner of a node."""
    style = _style(
        {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "html": 1,
            "fillColor": theme.badge.background,
            "strokeColor": "none",
            "fontColor": theme.badge.foreground,
            "fontSize": BADGE_FONT_SIZE_PX,
            "fontStyle": FONT_BOLD,
            "fontFamily": theme.fonts.mono,
        }
    )
    cell = _vertex(root, f"badge-{node.id}", esc(node.number), style)
    corner_x, corner_y = node.x - BADGE_OVERHANG_LEFT_PX, node.y - BADGE_OVERHANG_TOP_PX
    _geometry(cell, (corner_x, corner_y, BADGE_MIN_WIDTH_PX, BADGE_HEIGHT_PX))


def _add_frame(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a frame as a dashed, tinted container with its label at the top left."""
    tone = theme.tones[frame.tone]
    style = _style(
        {
            "rounded": 1,
            "arcSize": FRAME_CORNER_PERCENT,
            "dashed": 1,
            "container": 1,
            "collapsible": 0,
            "html": 1,
            "verticalAlign": "top",
            "align": "left",
            "spacingLeft": 16,
            "spacingTop": 8,
            "fillColor": tone.box,
            "strokeColor": tone.pill,
            "fontColor": theme.ink,
            "fontStyle": FONT_BOLD,
            "fontFamily": theme.fonts.sans,
        }
    )
    cell = _vertex(root, f"frame-{frame.id}", esc(frame.label or ""), style)
    _geometry(cell, (frame.x, frame.y, frame.width, frame.height))


def _add_title(root: ET.Element, scene: Scene, theme: Theme) -> None:
    """Add the title and the description as plain text cells."""
    if not scene.title:
        return
    common = {"text": "", "html": 1, "align": "left", "verticalAlign": "top", "strokeColor": "none"}
    title_style = _style(
        {
            **common,
            "fontSize": TITLE_FONT_SIZE_PX,
            "fontStyle": FONT_BOLD,
            "fontColor": theme.ink,
            "fontFamily": theme.fonts.sans,
        }
    )
    title = _vertex(root, "title", esc(scene.title), title_style)
    title_width = scene.width - 2 * TITLE_LEFT_PX
    _geometry(title, (TITLE_LEFT_PX, TITLE_TOP_PX, title_width, TITLE_HEIGHT_PX))
    if scene.description:
        description_style = _style(
            {
                **common,
                "whiteSpace": "wrap",
                "fontSize": DESCRIPTION_FONT_SIZE_PX,
                "fontColor": theme.slate,
                "fontFamily": theme.fonts.sans,
            }
        )
        description = _vertex(root, "description", esc(scene.description), description_style)
        width = min(scene.width - 2 * TITLE_LEFT_PX, DESCRIPTION_MAX_WIDTH_PX)
        top = TITLE_TOP_PX + TITLE_HEIGHT_PX
        _geometry(description, (TITLE_LEFT_PX, top, width, DESCRIPTION_HEIGHT_PX))


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


def _edge_style(edge: Edge, nodes: dict[str, Node], theme: Theme) -> str:
    """Return the style of an edge cell: line, arrowhead, ports, animation and label chip."""
    line = theme.roles[edge.role]
    style: dict[str, object] = {
        "html": 1,
        "rounded": 0,
        "strokeColor": line.color,
        "strokeWidth": fmt(line.width),
        "endArrow": "block" if edge.arrow is ArrowEnd.END else "none",
        "endFill": 1,
        "endSize": fmt(line.head_size * ARROW_SIZE_PER_STROKE / 2),
        "fontFamily": theme.fonts.sans,
    }
    if line.dash:
        style["dashed"] = 1
        style["dashPattern"] = _dash_pattern(line.dash, line.width)
    if line.animation:
        style["flowAnimation"] = 1
        speed = theme.animations[line.animation]
        style["flowAnimationDuration"] = _flow_duration_ms(line.dash, speed.seconds)
    for end, point, prefix in (
        (edge.source, edge.points[0], "exit"),
        (edge.target, edge.points[-1], "entry"),
    ):
        if end in nodes:
            across, down = _port(nodes[end], point)
            style.update({f"{prefix}X": fmt(across), f"{prefix}Y": fmt(down), f"{prefix}Dx": 0})
            style[f"{prefix}Dy"] = 0
    if edge.label:
        chip = theme.chips[edge.label.kind]
        style.update(
            {
                "labelBackgroundColor": chip.background,
                "fontColor": chip.foreground,
                "fontSize": CHIP_FONT_SIZE_PX,
                "fontStyle": FONT_BOLD,
                "spacing": CHIP_SPACING_PX,
            }
        )
    return _style(style)


def _add_edge(root: ET.Element, edge: Edge, nodes: dict[str, Node], theme: Theme) -> None:
    """Add an edge with its waypoints, and its label placed along the line."""
    value = esc(edge.label.text) if edge.label else ""
    attributes = {
        "id": f"edge-{edge.id}",
        "value": value,
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


def render(scene: Scene) -> str:
    """Return the text of a draw.io file for a scene.

    Args:
        scene: A scene from ``scene.parse`` or from ``build.layout``.

    Returns:
        An uncompressed ``mxfile`` document.
    """
    theme = load_theme()
    nodes = {node.id: node for node in scene.nodes}
    mxfile = ET.Element("mxfile", {"host": "flow", "type": "device"})
    diagram = ET.SubElement(
        mxfile, "diagram", {"id": "flow-diagram", "name": scene.title or "Diagram"}
    )
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "0",
            "dy": "0",
            "grid": "0",
            "page": "0",
            "background": theme.canvas,
            "pageWidth": fmt(scene.width),
            "pageHeight": fmt(scene.height),
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": ROOT_CELL_ID})
    ET.SubElement(root, "mxCell", {"id": LAYER_CELL_ID, "parent": ROOT_CELL_ID})
    _add_title(root, scene, theme)
    for frame in scene.frames:
        _add_frame(root, frame, theme)
    for node in scene.nodes:
        _add_node(root, node, theme)
    for edge in scene.edges:
        _add_edge(root, edge, nodes, theme)
    ET.indent(mxfile)
    return ET.tostring(mxfile, encoding="unicode") + "\n"
