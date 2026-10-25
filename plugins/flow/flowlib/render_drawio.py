"""Render a scene as a draw.io file (an uncompressed ``mxfile``) that stays editable.

Nodes are vertices, lines are edges that keep their routed waypoints (see ``drawio_lines``), and
the labels of lines are edge labels placed at their position along the line. Icons are small
image cells inside their node, so they move with it. Animated lines use draw.io's
``flowAnimation`` style.
"""

import base64
import xml.etree.ElementTree as ET
from collections.abc import Callable

from .drawio_common import (
    FONT_BOLD,
    LAYER_CELL_ID,
    ROOT_CELL_ID,
    Bounds,
    add_geometry,
    add_vertex,
    style_string,
)
from .drawio_lines import add_divider, add_edge
from .markup import esc, fmt
from .model import Frame, FrameVariant, Node, Scene, Shape
from .shapes import BOX_CORNER_RADIUS_PX, STROKE_WIDTH_PX, SUBPROCESS_BAR_INSET_PX
from .text_area import ICON_TEXT_RESERVE_PX
from .theme import Theme, load_icons, load_theme

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
FRAME_CORNER_PERCENT = 6
PARALLELOGRAM_SLANT_MAX_PX = 18
PARALLELOGRAM_SLANT_DIVISOR = 6
HEXAGON_SLANT_MAX_PX = 20
HEXAGON_SLANT_DIVISOR = 5
DOCUMENT_WAVE_FRACTION = 0.2
PILL_ARC_PERCENT = 50
NOTE_FOLD_PX = 16
TABLE_ARC_PERCENT = 6
TABLE_TEXT_INSET_PX = 12
ROW_PADDING_PX = 12
CYLINDER_CAP_PX = 10
START_STROKE_WIDTH_PX = 2
END_STROKE_WIDTH_PX = 5
DETAIL_FONT_SIZE_PX = 11
BELOW = {
    "verticalLabelPosition": "bottom",
    "verticalAlign": "top",
}  # the label sits under the shape
BAR_STROKE_WIDTH_PX = 1.5
FRAGMENT_TAG_WIDTH_PX = 60
FRAGMENT_TAG_HEIGHT_PX = 18
FRAGMENT_FONT_SIZE_PX = 11
FRAGMENT_GUARD_GAP_PX = 8


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


def _bar_style(node: Node) -> dict[str, object]:
    """Style pairs for a thin rectangle with square corners."""
    return {"rounded": 0, "strokeWidth": BAR_STROKE_WIDTH_PX}


def _note_style(node: Node) -> dict[str, object]:
    """Style pairs for a rectangle with a folded corner and left-aligned text."""
    return {
        "shape": "note",
        "size": NOTE_FOLD_PX,
        "boundedLbl": 1,
        "align": "left",
        "spacingLeft": 8,
    }


def _cross_style(node: Node) -> dict[str, object]:
    """Style pairs for the X that ends a lifeline."""
    return {"shape": "umlDestroy"}


def _table_style(node: Node) -> dict[str, object]:
    """Style pairs for a table: a swimlane whose header is the title and whose rows are children."""
    return {
        "swimlane": "",
        "horizontal": 1,
        "collapsible": 0,
        "align": "left",
        "rounded": 1,
        "arcSize": TABLE_ARC_PERCENT,
    }


def _cylinder_style(node: Node) -> dict[str, object]:
    """Style pairs for a can, the symbol of a database."""
    return {"shape": "cylinder3", "boundedLbl": 1, "backgroundOutline": 1, "size": CYLINDER_CAP_PX}


def _entity_style(node: Node) -> dict[str, object]:
    """Style pairs for a rectangle with square corners."""
    return {"rounded": 0}


def _store_style(node: Node) -> dict[str, object]:
    """Style pairs for a box open on the right, the symbol of a data store."""
    return {"shape": "partialRectangle", "right": 0}


def _start_style(node: Node) -> dict[str, object]:
    """Style pairs for a thin circle."""
    return {"ellipse": "", "strokeWidth": START_STROKE_WIDTH_PX, **BELOW}


def _end_style(node: Node) -> dict[str, object]:
    """Style pairs for a thick circle."""
    return {"ellipse": "", "strokeWidth": END_STROKE_WIDTH_PX, **BELOW}


def _intermediate_style(node: Node) -> dict[str, object]:
    """Style pairs for a double circle."""
    return {"shape": "doubleEllipse", **BELOW}


def _actor_style(node: Node) -> dict[str, object]:
    """Style pairs for a stick figure whose name is written below it."""
    return {"shape": "umlActor", **BELOW}


def _ellipse_style(node: Node) -> dict[str, object]:
    """Style pairs for an ellipse."""
    return {"ellipse": ""}


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
    Shape.BAR: _bar_style,
    Shape.NOTE: _note_style,
    Shape.CROSS: _cross_style,
    Shape.TABLE: _table_style,
    Shape.CYLINDER: _cylinder_style,
    Shape.ENTITY: _entity_style,
    Shape.STORE: _store_style,
    Shape.START: _start_style,
    Shape.END: _end_style,
    Shape.INTERMEDIATE: _intermediate_style,
    Shape.ACTOR: _actor_style,
    Shape.ELLIPSE: _ellipse_style,
}


def _node_style(node: Node, theme: Theme) -> str:
    """Return the full style of a node cell: outline, colours and text."""
    colors = theme.shapes[node.shape]
    fill = theme.tones[node.tone].box if node.tone else colors.fill
    style = {
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
    style.update(SHAPE_STYLES[node.shape](node))
    if node.shape is Shape.NOTE:
        style.update({"fontStyle": 0, "fontColor": theme.slate})
    if node.shape is Shape.TABLE:
        icon_room = ICON_LEFT_PX + ICON_SIZE_PX if node.icon else 0
        style.update(
            {
                "startSize": theme.layout.table_header_height,
                "swimlaneFillColor": "#FFFFFF",
                "spacingLeft": TABLE_TEXT_INSET_PX + icon_room,
            }
        )
    if node.icon and node.shape is not Shape.TABLE:
        style["spacingLeft"] = ICON_TEXT_RESERVE_PX
    return style_string(style)


def _label_value(lines: tuple[str, ...]) -> str:
    """Join text lines with ``<br>``, escaping each so that markup in the text stays text."""
    return "<br>".join(esc(line) for line in lines)


def _node_value(node: Node, theme: Theme) -> str:
    """Return the label of a node: its caption, or its title followed by its detail lines."""
    if node.caption:
        return esc(node.caption)
    title = _label_value(node.text)
    if not node.detail:
        return title
    style = f"font-size:{DETAIL_FONT_SIZE_PX}px;font-weight:normal;color:{theme.slate}"
    return f'{title}<br><span style="{style}">{_label_value(node.detail)}</span>'


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
    cell = add_vertex(root, f"node-{node.id}", _node_value(node, theme), _node_style(node, theme))
    add_geometry(cell, (node.x, node.y, node.width, node.height))
    if node.shape is Shape.TABLE:
        _add_table_rows(root, node, theme)
    if node.icon:
        icon_style = style_string(
            {"shape": "image", "image": _icon_data_uri(node.icon, theme.shapes[node.shape].stroke)}
        )
        icon = add_vertex(root, f"icon-{node.id}", "", icon_style)
        icon.set("parent", f"node-{node.id}")  # a child cell moves with its node
        band = theme.layout.table_header_height if node.shape is Shape.TABLE else node.height
        icon_top = (band - ICON_SIZE_PX) / 2
        add_geometry(icon, (ICON_LEFT_PX, icon_top, ICON_SIZE_PX, ICON_SIZE_PX))
    if node.number:
        _add_badge(root, node, theme)


def _row_value(left: str, right: str) -> str:
    """Return a table row as a one-line HTML table with the name left and the note right."""
    return (
        '<table style="width:100%;border-collapse:collapse"><tr>'
        f'<td style="padding-left:{ROW_PADDING_PX}px">{esc(left)}</td>'
        f'<td align="right" style="padding-right:{ROW_PADDING_PX}px">{esc(right)}</td>'
        "</tr></table>"
    )


def _add_table_rows(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add each row of a table as a child cell, so that the rows move with the table."""
    rules = theme.layout
    style = style_string(
        {
            "text": "",
            "html": 1,
            "whiteSpace": "wrap",
            "overflow": "fill",
            "align": "left",
            "verticalAlign": "middle",
            "spacingLeft": 8,
            "spacingRight": 8,
            "strokeColor": "none",
            "fillColor": "none",
            "fontSize": DETAIL_FONT_SIZE_PX,
            "fontColor": theme.ink,
            "fontFamily": theme.fonts.mono,
        }
    )
    y = rules.table_header_height
    for section_index, section in enumerate(node.sections):
        if section_index:
            y += rules.table_section_gap
        for row_index, row in enumerate(section):
            cell = add_vertex(
                root,
                f"row-{node.id}-{section_index}-{row_index}",
                _row_value(row.left, row.right),
                style,
            )
            cell.set("parent", f"node-{node.id}")
            add_geometry(cell, (0, y, node.width, rules.table_row_height))
            y += rules.table_row_height


def _add_badge(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the number badge at the top-left corner of a node."""
    style = style_string(
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
    cell = add_vertex(root, f"badge-{node.id}", esc(node.number), style)
    corner_x, corner_y = node.x - BADGE_OVERHANG_LEFT_PX, node.y - BADGE_OVERHANG_TOP_PX
    add_geometry(cell, (corner_x, corner_y, BADGE_MIN_WIDTH_PX, BADGE_HEIGHT_PX))


def _add_frame(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a frame: a dashed, tinted container, or a fragment with a tag and a guard."""
    if frame.variant is FrameVariant.FRAGMENT:
        _add_fragment(root, frame, theme)
        return
    tone = theme.tones[frame.tone]
    style = style_string(
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
    cell = add_vertex(root, f"frame-{frame.id}", esc(frame.label or ""), style)
    add_geometry(cell, (frame.x, frame.y, frame.width, frame.height))


def _guard_style(theme: Theme) -> str:
    """Return the style of the small monospace text that holds a guard."""
    return style_string(
        {
            "text": "",
            "html": 1,
            "align": "left",
            "verticalAlign": "middle",
            "strokeColor": "none",
            "fillColor": "none",
            "fontSize": FRAGMENT_FONT_SIZE_PX,
            "fontColor": theme.slate,
            "fontFamily": theme.fonts.mono,
        }
    )


def _add_fragment(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a fragment frame as a draw.io frame shape, its guard, and its dividers."""
    tone = theme.tones[frame.tone]
    style = style_string(
        {
            "shape": "umlFrame",
            "whiteSpace": "wrap",
            "html": 1,
            "pointerEvents": 0,
            "width": FRAGMENT_TAG_WIDTH_PX,
            "height": FRAGMENT_TAG_HEIGHT_PX,
            "fillColor": tone.box,
            "strokeColor": tone.stroke,
            "fontColor": theme.ink,
            "fontStyle": FONT_BOLD,
            "fontSize": FRAGMENT_FONT_SIZE_PX,
            "fontFamily": theme.fonts.sans,
        }
    )
    cell = add_vertex(root, f"frame-{frame.id}", esc(frame.label or ""), style)
    add_geometry(cell, (frame.x, frame.y, frame.width, frame.height))

    def put_guard(cell_id: str, text: str, bounds: Bounds) -> None:
        """Add one guard text cell."""
        guard_cell = add_vertex(root, cell_id, esc(f"[{text}]"), _guard_style(theme))
        add_geometry(guard_cell, bounds)

    if frame.guard:
        left = frame.x + FRAGMENT_TAG_WIDTH_PX + FRAGMENT_GUARD_GAP_PX
        width = frame.width - FRAGMENT_TAG_WIDTH_PX
        put_guard(f"guard-{frame.id}", frame.guard, (left, frame.y, width, FRAGMENT_TAG_HEIGHT_PX))
    for index, divider in enumerate(frame.dividers):
        ends = ((frame.x, divider.y), (frame.x + frame.width, divider.y))
        add_divider(root, f"divider-{frame.id}-{index}", ends, tone.stroke)
        left = frame.x + FRAGMENT_GUARD_GAP_PX
        bounds = (left, divider.y, frame.width, FRAGMENT_TAG_HEIGHT_PX)
        put_guard(f"divider-guard-{frame.id}-{index}", divider.guard, bounds)


def _add_title(root: ET.Element, scene: Scene, theme: Theme) -> None:
    """Add the title and the description as plain text cells."""
    if not scene.title:
        return
    common = {"text": "", "html": 1, "align": "left", "verticalAlign": "top", "strokeColor": "none"}
    title_style = style_string(
        {
            **common,
            "fontSize": TITLE_FONT_SIZE_PX,
            "fontStyle": FONT_BOLD,
            "fontColor": theme.ink,
            "fontFamily": theme.fonts.sans,
        }
    )
    title = add_vertex(root, "title", esc(scene.title), title_style)
    title_width = scene.width - 2 * TITLE_LEFT_PX
    add_geometry(title, (TITLE_LEFT_PX, TITLE_TOP_PX, title_width, TITLE_HEIGHT_PX))
    if scene.description:
        description_style = style_string(
            {
                **common,
                "whiteSpace": "wrap",
                "fontSize": DESCRIPTION_FONT_SIZE_PX,
                "fontColor": theme.slate,
                "fontFamily": theme.fonts.sans,
            }
        )
        description = add_vertex(root, "description", esc(scene.description), description_style)
        width = min(scene.width - 2 * TITLE_LEFT_PX, DESCRIPTION_MAX_WIDTH_PX)
        top = TITLE_TOP_PX + TITLE_HEIGHT_PX
        add_geometry(description, (TITLE_LEFT_PX, top, width, DESCRIPTION_HEIGHT_PX))


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
        add_edge(root, edge, nodes, theme)
    ET.indent(mxfile)
    return ET.tostring(mxfile, encoding="unicode") + "\n"
