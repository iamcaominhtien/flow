"""Draw the lines of a scene as draw.io edges: waypoints, ports, heads, animation and labels."""

import math
import xml.etree.ElementTree as ET
from itertools import pairwise

from .drawio_common import (
    FLOW_ROLE_KEY,
    FONT_BOLD,
    LAYER_CELL_ID,
    add_geometry,
    add_vertex,
    font_style,
    style_string,
)
from .drawio_screen import TONE_STYLE_KEY, chip_value
from .markup import esc, fmt
from .model import (
    MONO_LABEL_KINDS,
    SYMBOL_HEADS,
    Edge,
    EdgeLabel,
    Head,
    LabelKind,
    Node,
    Point,
    Role,
)
from .theme import LineStyle, Theme

CHIP_SPACING_PX = 3  # room around the text of a label chip
ARROW_SIZE_PER_STROKE = 3  # ``endSize`` per pixel of line width, tuned by eye against the HTML
NO_COLOR = "none"
DEFAULT_DASH = "6 5"  # for a line that is dashed by choice, not by its role
HEAD_ARROWS = {
    Head.NONE: "none",
    Head.FILLED: "block",
    Head.OPEN: "open",
    Head.DOT: "oval",
    Head.CIRCLE: "oval",
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
BOLD_CHIP_KINDS = (LabelKind.USER, LabelKind.SYSTEM, LabelKind.CODE)
FILLED_HEADS = (Head.FILLED, Head.DOT, Head.DIAMOND_FILLED)
SYMBOL_HEAD_SIZE_PX = 12
PLANNING_ROLES = (
    Role.GRID,
    Role.TODAY,
    Role.REPORTS,
    Role.WORKS_WITH,
    Role.BRANCH,
    Role.TWIG,
    Role.LINK,
    Role.KEY,
)
CURVE_SAMPLES = (0.25, 0.5, 0.75)  # where on a Bezier curve the waypoints of a draw.io curve lie
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


def drawio_width(line: LineStyle, theme: Theme) -> float:
    """Return the draw.io ``strokeWidth`` of a line role.

    An animated line takes the width of its tier (design 01 section 6.3); any other line takes
    the entry of the weight table for its canvas width, and keeps that width when the table has
    no entry for it.

    Args:
        line: The role's line style, whose width is in canvas pixels.
        theme: The design tokens, which hold the table and the tiers.

    Returns:
        The stroke width to write.
    """
    if line.animation:
        return theme.animations[line.animation].drawio_width
    return theme.drawio_weights.get(line.width, line.width)


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
        "fontSize": fmt(theme.type_scale.edge.size),
        "fontStyle": font_style(theme.type_scale.edge.weight),
        "spacing": CHIP_SPACING_PX,
    }
    if chip.background != NO_COLOR:
        style["labelBackgroundColor"] = chip.background
    if edge.label.kind in MONO_LABEL_KINDS:
        style["fontFamily"] = theme.fonts.mono
        style["fontSize"] = fmt(theme.type_scale.mono.size)
    if edge.label.kind in BOLD_CHIP_KINDS:
        style["fontStyle"] = FONT_BOLD
    if edge.label.kind is LabelKind.CODE:
        style["labelBorderColor"] = chip.foreground
    return style


def _edge_style(edge: Edge, nodes: dict[str, Node], theme: Theme) -> str:
    """Return the style of an edge cell: line, heads, ports, animation and label."""
    line = theme.roles[edge.role]
    style: dict[str, object] = {
        "html": 1,
        "rounded": 0,
        "strokeColor": theme.planning.accents[edge.tone] if edge.tone else line.color,
        "strokeWidth": fmt(drawio_width(line, theme)),
        **_end_style(edge, line),
        "fontFamily": theme.fonts.sans,
    }
    if edge.role in PLANNING_ROLES:
        style[FLOW_ROLE_KEY] = edge.role.value
    if edge.tone is not None:
        style[TONE_STYLE_KEY] = edge.tone.value
    if edge.is_curved:
        style["curved"] = 1
    dash = line.dash or (DEFAULT_DASH if edge.dashed else None)
    if dash:
        style["dashed"] = 1
        style["dashPattern"] = _dash_pattern(dash, drawio_width(line, theme))
    if line.animation:
        style["flowAnimation"] = 1
        speed = theme.animations[line.animation]
        style["flowAnimationDuration"] = speed.drawio_duration_ms
    style.update(_port_style(edge, nodes))
    style.update(_label_style(edge, theme))
    return style_string(style)


def _label_value(edge: Edge, theme: Theme) -> str:
    """Return the label of an edge as HTML: the step number in bold, then the icon and the text."""
    if edge.label is None:
        return ""
    number = f"<b>{esc(edge.label.number)}</b>&nbsp;" if edge.label.number else ""
    return number + chip_value(edge.label, theme)


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
        "value": _label_value(edge, theme),
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
    for x, y in _waypoints(edge):
        ET.SubElement(interior, "mxPoint", {"x": fmt(x), "y": fmt(y)})
    if offset != (0.0, 0.0):
        ET.SubElement(
            geometry, "mxPoint", {"x": fmt(offset[0]), "y": fmt(offset[1]), "as": "offset"}
        )
    for index, extra in enumerate(edge.extras, start=1):
        _add_extra(root, f"edge-{edge.id}-end{index}", extra, theme)


def _bezier_point(points: tuple[Point, ...], at: float) -> Point:
    """Return the point of a cubic Bezier curve at a fraction of its parameter.

    Args:
        points: The four points of the curve.
        at: A number from 0 (the start) to 1 (the end).

    Returns:
        The point on the curve.
    """
    keep = 1 - at
    weights = (keep**3, 3 * keep**2 * at, 3 * keep * at**2, at**3)
    return (
        sum(weight * x for weight, (x, _) in zip(weights, points, strict=True)),
        sum(weight * y for weight, (_, y) in zip(weights, points, strict=True)),
    )


def _waypoints(edge: Edge) -> list[Point]:
    """Return the waypoints draw.io keeps: the inner points, or samples of a curve."""
    if edge.is_curved:
        return [_bezier_point(edge.points, at) for at in CURVE_SAMPLES]
    return list(edge.points[1:-1])


def _add_extra(root: ET.Element, cell_id: str, extra: EdgeLabel, theme: Theme) -> None:
    """Add a small free-standing text next to the end of a line, such as a multiplicity."""
    chip = theme.chips[extra.kind]
    family = theme.fonts.sans if extra.kind is LabelKind.EFFECT else theme.fonts.mono
    style = style_string(
        {
            "text": "",
            "html": 1,
            "align": "center",
            "verticalAlign": "middle",
            "strokeColor": "none",
            "fillColor": "none",
            "fontSize": fmt(theme.type_scale.mono.size),
            "fontStyle": font_style(theme.type_scale.mono.weight),
            "fontColor": chip.foreground,
            "fontFamily": family,
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
