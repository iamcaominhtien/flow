"""Render a scene as a draw.io file (an uncompressed ``mxfile``) that stays editable.

Nodes are vertices, lines are edges that keep their routed waypoints (see ``drawio_lines``), and
the labels of lines are edge labels placed at their position along the line. Icons are small
image cells inside their node, so they move with it. Animated lines use draw.io's
``flowAnimation`` style.
"""

import base64
import xml.etree.ElementTree as ET
from collections.abc import Callable

from .cards import card_parts
from .drawio_common import (
    FONT_BOLD,
    FRAME_LABEL_PREFIX,
    LAYER_CELL_ID,
    ROOT_CELL_ID,
    Bounds,
    add_geometry,
    add_vertex,
    style_string,
)
from .drawio_lines import add_divider, add_edge
from .drawio_notation import (
    add_band_frame,
    add_dfd_parts,
    add_marks,
    dfd_style,
    dfd_value,
    marks_style,
)
from .drawio_screen import add_node_chip, add_screen_parts, screen_style
from .html_dfd import is_dfd_node
from .html_frames import BAND_VARIANTS
from .markup import esc, fmt
from .model import KEY_FLAG_TONES, REF_FRAGMENT, Frame, FrameVariant, Node, Row, Scene, Shape, Tone
from .shapes import SUBPROCESS_BAR_INSET_PX
from .sizing import estimate_text_width, key_room
from .text_area import ICON_TEXT_RESERVE_PX
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg, load_theme

ICON_SIZE_PX = 18
CONNECTOR_NOTE_GAP_PX = 10  # the note beside an off-page connector, as in the HTML page
CONNECTOR_NOTE_WIDTH_PX = 140
CONNECTOR_NOTE_FONT_SIZE_PX = 11
ICON_STROKE_WIDTH = 2
ICON_LEFT_PX = 14
CENTERED_ICON_SHAPES = (Shape.INTERMEDIATE, Shape.DECISION)  # the icon is a marker in the middle
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
BADGE_HEIGHT_PX = 20
BADGE_MIN_WIDTH_PX = 22
BADGE_OVERHANG_LEFT_PX = 6
BADGE_OVERHANG_TOP_PX = 10
BADGE_FONT_SIZE_PX = 11
TITLE_LEFT_PX = 64
TITLE_TOP_PX = 48
TITLE_HEIGHT_PX = 34
DESCRIPTION_FONT_SIZE_PX = 13
DESCRIPTION_HEIGHT_PX = 44
DESCRIPTION_MAX_WIDTH_PX = 900
FRAME_CORNER_PERCENT = 6
LANE_TAB_FONT_SIZE = 13
FRAME_DASH_PATTERN = "4 3"  # design 01 section 3: the container
FRAME_STROKE_WIDTH_PX = 1.5
FRAME_PILL_LEFT_PX = 16
FRAME_PILL_TOP_PX = 12
FRAME_PILL_HEIGHT_PX = 22
FRAME_PILL_PADDING_PX = 12
ROUNDED_SHAPES = (
    Shape.PROCESS,
    Shape.TASK,
    Shape.DFD_PROCESS,
)  # boxes whose corner radius is in pixels
SHADOW_SHAPES = (  # the rounded boxes of design 01 section 3 carry ``shadow=1``
    Shape.TERMINATOR,
    Shape.FAIL,
    Shape.PROCESS,
    Shape.TASK,
    Shape.SUBPROCESS,
    Shape.IO,
    Shape.DOCUMENT,
    Shape.PREPARATION,
    Shape.DECISION,
    Shape.CYLINDER,
    Shape.ELLIPSE,
)
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
DASH_PATTERN = "6 4"
CHIP_FONT_SIZE_PX = 10
TABLE_PILL_HEIGHT_PX = 28  # the name pill in the header of an illustrated table
TABLE_CARD_ICON_PX = 52
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
FLAG_POINT_PX = 16


def _pill_style(node: Node) -> dict[str, object]:
    """Style pairs for a rounded rectangle with fully round ends."""
    return {"rounded": 1, "arcSize": PILL_ARC_PERCENT}


def _box_style(node: Node) -> dict[str, object]:
    """Style pairs for a rectangle with rounded corners."""
    return {"rounded": 1, "absoluteArcSize": 1}


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


def _fork_style(node: Node) -> dict[str, object]:
    """Style pairs for the solid bar of a split or join; ``flowFork`` lets the importer know it."""
    return {"rounded": 1, "arcSize": PILL_ARC_PERCENT, "flowFork": 1, "strokeWidth": 0}


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


def _flag_style(node: Node) -> dict[str, object]:
    """Style pairs for a flag: a step shape with a notch on the left and a point on the right."""
    return {"shape": "step", "perimeter": "stepPerimeter", "fixedSize": 1, "size": FLAG_POINT_PX}


def _text_style(node: Node) -> dict[str, object]:
    """Style pairs for free text: no outline, no fill, left aligned."""
    return {"text": "", "align": "left", "verticalAlign": "middle", "spacingLeft": 0}


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
    Shape.FORK: _fork_style,
    Shape.HEADER: _box_style,
    Shape.NOTE: _note_style,
    Shape.TEXT: _text_style,
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
    Shape.SCREEN: _box_style,
    Shape.FLAG: _flag_style,
    Shape.TASK: _box_style,
    Shape.DFD_PROCESS: _box_style,
    Shape.DFD_STORE: _store_style,
}


def _theme_pairs(node: Node, theme: Theme) -> dict[str, object]:
    """Return the style pairs a theme decides: the corner radius and the shadow of a box."""
    pairs: dict[str, object] = {}
    if node.shape in ROUNDED_SHAPES:
        pairs["arcSize"] = 2 * theme.shapes[node.shape].radius
    if theme.style.shadow and node.shape in SHADOW_SHAPES:
        pairs["shadow"] = 1
    return pairs


def _base_pairs(node: Node, theme: Theme) -> dict[str, object]:
    """Return the style pairs every node has: its colours, its outline and its text."""
    colors = theme.shapes[node.shape]
    fill = theme.tones[node.tone].box if node.tone else colors.fill
    if node.shape is Shape.TABLE and node.card:
        fill = theme.tones[node.tone or Tone.GRAY].pill
    return {
        "html": 1,
        "whiteSpace": "wrap",
        "fillColor": fill,
        "strokeColor": colors.stroke,
        "strokeWidth": fmt(colors.stroke_width),
        "fontColor": theme.ink,
        "fontSize": fmt(node.font_size),
        "fontStyle": FONT_BOLD,
        "fontFamily": theme.fonts.sans,
    }


def _kind_pairs(node: Node, theme: Theme) -> dict[str, object]:
    """Return the style pairs of a note, a table, a card or a node with an icon."""
    if node.shape in (Shape.NOTE, Shape.TEXT):
        return {"fontStyle": 0, "fontColor": theme.slate}
    if node.shape is Shape.TABLE:
        icon_room = ICON_LEFT_PX + ICON_SIZE_PX if node.icon else 0
        return {
            "startSize": _table_header_height(node, theme),
            "swimlaneFillColor": theme.paper,
            "spacingLeft": TABLE_TEXT_INSET_PX + icon_room,
        }
    if node.card:
        return _card_text_style(node, theme)
    if node.icon:
        return {"spacingLeft": ICON_TEXT_RESERVE_PX}
    return {}


def _node_style(node: Node, theme: Theme) -> str:
    """Return the full style of a node cell: outline, colours and text."""
    if node.screen is not None:
        return screen_style(node, theme)
    style = _base_pairs(node, theme)
    style.update(SHAPE_STYLES[node.shape](node))
    style.update(_theme_pairs(node, theme))
    if node.dashed:
        style.update({"dashed": 1, "dashPattern": DASH_PATTERN})
    style.update(marks_style(node))
    if is_dfd_node(node):
        style.update(dfd_style(node, theme))
    else:
        style.update(_kind_pairs(node, theme))
    return style_string(style)


def _card_text_style(node: Node, theme: Theme) -> dict[str, object]:
    """Style pairs that put the detail text at the bottom of an illustrated card."""
    return {
        "verticalAlign": "bottom",
        "spacingBottom": theme.layout.card_padding / 2,
        "fontStyle": 0,
        "fontSize": theme.layout.detail_font_size,
        "fontColor": theme.slate,
    }


def _shadow_pair(theme: Theme) -> dict[str, object]:
    """Return ``shadow=1`` when the theme has shadows, else no pair."""
    return {"shadow": 1} if theme.style.shadow else {}


def _label_value(lines: tuple[str, ...]) -> str:
    """Join text lines with ``<br>``, escaping each so that markup in the text stays text."""
    return "<br>".join(esc(line) for line in lines)


def _node_value(node: Node, theme: Theme) -> str:
    """Return the label of a node: its caption, or its title followed by its detail lines."""
    if node.screen is not None or (node.shape is Shape.TABLE and node.card):
        return ""
    if is_dfd_node(node):
        return dfd_value(node, theme)
    if node.caption:
        return esc(node.caption)
    if node.card:
        return _label_value(node.detail)
    title = _label_value(node.text)
    if not node.detail or node.shape is Shape.CONNECTOR:
        return title
    style = f"font-size:{DETAIL_FONT_SIZE_PX}px;font-weight:normal;color:{theme.slate}"
    return f'{title}<br><span style="{style}">{_label_value(node.detail)}</span>'


def _icon_data_uri(name: str, stroke: str, size: float = ICON_SIZE_PX) -> str:
    """Build the ``image`` style value for an icon: a base64 SVG with no ``base64`` keyword.

    draw.io splits styles at semicolons, so the usual ``;base64,`` of a data URI cannot be used.
    """
    svg = icon_svg(name, size, stroke, f'xmlns="{SVG_NAMESPACE}"')
    return "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()


def _detailed_data_uri(name: str, stroke: str, size: float) -> str:
    """Build the ``image`` style value for an icon in its detailed form."""
    svg = detailed_icon_svg(name, size, stroke, f'xmlns="{SVG_NAMESPACE}"')
    return "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()


def add_node(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add a node, its icon (as a child cell) and its number badge."""
    cell = add_vertex(root, f"node-{node.id}", _node_value(node, theme), _node_style(node, theme))
    add_geometry(cell, (node.x, node.y, node.width, node.height))
    if node.screen is not None:
        add_screen_parts(root, node, theme)
    if node.chip is not None:
        add_node_chip(root, node, theme)
    if node.shape is Shape.TABLE:
        _add_table_rows(root, node, theme)
    if is_dfd_node(node):
        add_dfd_parts(root, node, theme)
    elif node.shape is Shape.TABLE and node.card:
        _add_table_card_parts(root, node, theme)
    elif node.card:
        _add_card_parts(root, node, theme)
    elif node.icon:
        icon_style = style_string(
            {"shape": "image", "image": _icon_data_uri(node.icon, theme.shapes[node.shape].stroke)}
        )
        icon = add_vertex(root, f"icon-{node.id}", "", icon_style)
        icon.set("parent", f"node-{node.id}")  # a child cell moves with its node
        band = _table_header_height(node, theme) if node.shape is Shape.TABLE else node.height
        icon_top = (band - ICON_SIZE_PX) / 2
        is_marker = node.shape in CENTERED_ICON_SHAPES and not node.text
        icon_left = (node.width - ICON_SIZE_PX) / 2 if is_marker else ICON_LEFT_PX
        add_geometry(icon, (icon_left, icon_top, ICON_SIZE_PX, ICON_SIZE_PX))
    add_marks(root, node, theme)
    _add_badge_and_note(root, node, theme)


def _add_badge_and_note(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add what hangs on the outside of a node: its number badge and a connector's note."""
    if node.number and not is_dfd_node(node):
        _add_badge(root, node, theme)
    if node.shape is Shape.CONNECTOR and node.detail:
        _add_connector_note(root, node, theme)


def _add_connector_note(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the note that says where an off-page connector continues, beside its circle."""
    style = style_string(
        {
            "text": "",
            "html": 1,
            "whiteSpace": "wrap",
            "align": "left",
            "verticalAlign": "middle",
            "strokeColor": "none",
            "fillColor": "none",
            "fontSize": CONNECTOR_NOTE_FONT_SIZE_PX,
            "fontColor": theme.slate,
            "fontFamily": theme.fonts.sans,
        }
    )
    cell = add_vertex(root, f"note-{node.id}", _label_value(node.detail), style)
    left = node.x + node.width + CONNECTOR_NOTE_GAP_PX
    add_geometry(cell, (left, node.y, CONNECTOR_NOTE_WIDTH_PX, node.height))


def _add_card_disc(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the tinted disc and the enlarged flat icon of an illustrated card."""
    rules = theme.layout
    tone = theme.tones[node.tone or Tone.BLUE]
    parent = f"node-{node.id}"
    disc_left = (node.width - rules.card_disc) / 2
    disc_style = style_string({"ellipse": "", "strokeColor": "none", "fillColor": tone.pill})
    disc = add_vertex(root, f"disc-{node.id}", "", disc_style)
    disc.set("parent", parent)
    top = card_parts(node, theme).icon_top
    add_geometry(disc, (disc_left, top, rules.card_disc, rules.card_disc))
    size = rules.card_disc * rules.card_icon_fraction
    inset = (rules.card_disc - size) / 2
    image = _icon_data_uri(node.icon or "", tone.stroke, size)
    icon = add_vertex(root, f"icon-{node.id}", "", style_string({"shape": "image", "image": image}))
    icon.set("parent", parent)
    add_geometry(icon, (disc_left + inset, top + inset, size, size))


def _add_detailed_icon(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the detailed icon of an illustrated card, which needs no disc."""
    rules = theme.layout
    tone = theme.tones[node.tone or Tone.BLUE]
    image = _detailed_data_uri(node.icon or "", tone.stroke, rules.card_disc)
    icon = add_vertex(root, f"icon-{node.id}", "", style_string({"shape": "image", "image": image}))
    icon.set("parent", f"node-{node.id}")
    left = (node.width - rules.card_disc) / 2
    top = card_parts(node, theme).icon_top
    add_geometry(icon, (left, top, rules.card_disc, rules.card_disc))


def _add_card_parts(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the icon and the name pill of an illustrated card as child cells."""
    rules = theme.layout
    tone = theme.tones[node.tone or Tone.BLUE]
    parent = f"node-{node.id}"
    if has_detailed_icon(node.icon or ""):
        _add_detailed_icon(root, node, theme)
    else:
        _add_card_disc(root, node, theme)
    pill_width = (
        estimate_text_width(" ".join(node.text), rules, node.font_size)
        + 2 * rules.card_pill_padding
    )
    pill_style = style_string(
        {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "html": 1,
            "strokeColor": "none",
            "fillColor": tone.pill,
            "fontColor": theme.ink,
            "fontSize": fmt(node.font_size),
            "fontStyle": FONT_BOLD,
            "fontFamily": theme.fonts.sans,
        }
    )
    pill = add_vertex(root, f"pill-{node.id}", esc(" ".join(node.text)), pill_style)
    pill.set("parent", parent)
    parts = card_parts(node, theme)
    add_geometry(
        pill, ((node.width - pill_width) / 2, parts.pill_top, pill_width, parts.pill_height)
    )


def _chip_value(flag: str, theme: Theme) -> str:
    """Return one key chip as an HTML span with the tint of its kind."""
    tone = theme.tones[KEY_FLAG_TONES.get(flag, Tone.GRAY)]
    style = (
        f"background:{tone.pill};color:{tone.label};border-radius:4px;padding:1px 5px;"
        f"font-size:{CHIP_FONT_SIZE_PX}px;font-weight:bold;font-family:{theme.fonts.sans}"
    )
    return f'<span style="{style}">{esc(flag)}</span>'


def _row_value(row: Row, key_width: float, theme: Theme) -> str:
    """Return a table row as a one-line HTML table: chips, name and type in three cells.

    The first cell has the width of the key column of the table, so that the names of rows
    with and without chips start at the same x.
    """
    chips = "&nbsp;".join(_chip_value(flag, theme) for flag in row.flags)
    name = f"<b>{esc(row.left)}</b>" if "PK" in row.flags else esc(row.left)
    key_cell = f'<td style="width:{key_width}px;padding-left:{ROW_PADDING_PX}px">{chips}</td>'
    left = key_cell if key_width else ""
    pad = "" if key_width else f"padding-left:{ROW_PADDING_PX}px"
    return (
        f'<table style="width:100%;border-collapse:collapse"><tr>{left}'
        f'<td style="{pad}">{name}</td>'
        f'<td align="right" style="padding-right:{ROW_PADDING_PX}px;color:{theme.slate};'
        f'font-family:{theme.fonts.mono};font-size:{DETAIL_FONT_SIZE_PX}px">'
        f"{esc(row.right)}</td></tr></table>"
    )


def _table_header_height(node: Node, theme: Theme) -> float:
    """Return the height of a table header: tall when the table is illustrated."""
    if node.card:
        return theme.layout.table_card_header_height
    return theme.layout.table_header_height


def _add_table_card_parts(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the name pill and the large icon in the header of an illustrated table."""
    rules = theme.layout
    tone = theme.tones[node.tone or Tone.GRAY]
    parent = f"node-{node.id}"
    pill_width = (
        estimate_text_width(" ".join(node.text), rules, node.font_size)
        + 2 * rules.card_pill_padding
    )
    pill_style = style_string(
        {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "html": 1,
            "strokeColor": theme.shapes[node.shape].stroke,
            "strokeWidth": fmt(theme.shapes[node.shape].stroke_width),
            "fillColor": tone.box,
            "fontColor": theme.ink,
            "fontSize": fmt(node.font_size),
            "fontStyle": FONT_BOLD,
            "fontFamily": theme.fonts.sans,
            **_shadow_pair(theme),
        }
    )
    pill = add_vertex(root, f"pill-{node.id}", esc(" ".join(node.text)), pill_style)
    pill.set("parent", parent)
    top = (rules.table_card_header_height - TABLE_PILL_HEIGHT_PX) / 2
    add_geometry(pill, (TABLE_TEXT_INSET_PX, top, pill_width, TABLE_PILL_HEIGHT_PX))
    if not node.icon:
        return
    make = _detailed_data_uri if has_detailed_icon(node.icon) else _icon_data_uri
    image = make(node.icon, tone.stroke, TABLE_CARD_ICON_PX)
    icon = add_vertex(root, f"icon-{node.id}", "", style_string({"shape": "image", "image": image}))
    icon.set("parent", parent)
    left = node.width - TABLE_TEXT_INSET_PX - TABLE_CARD_ICON_PX
    icon_top = (rules.table_card_header_height - TABLE_CARD_ICON_PX) / 2
    add_geometry(icon, (left, icon_top, TABLE_CARD_ICON_PX, TABLE_CARD_ICON_PX))


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
            "fontSize": fmt(rules.table_name_font_size),
            "fontColor": theme.ink,
            "fontFamily": theme.fonts.sans,
        }
    )
    key_width = key_room(node.sections, rules)
    y = _table_header_height(node, theme)
    for section_index, section in enumerate(node.sections):
        if section_index:
            y += rules.table_section_gap
        for row_index, row in enumerate(section):
            cell = add_vertex(
                root,
                f"row-{node.id}-{section_index}-{row_index}",
                _row_value(row, key_width, theme),
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
    if frame.variant is FrameVariant.LANE:
        _add_lane(root, frame, theme)
        return
    if frame.variant in BAND_VARIANTS:
        add_band_frame(root, frame, theme)
        return
    tone = theme.tones[frame.tone]
    style = style_string(
        {
            "rounded": 1,
            "arcSize": FRAME_CORNER_PERCENT,
            "dashed": 1,
            "dashPattern": FRAME_DASH_PATTERN,
            "container": 1,
            "collapsible": 0,
            "html": 1,
            "verticalAlign": "top",
            "fillColor": tone.box,
            "strokeColor": tone.pill,
            "strokeWidth": FRAME_STROKE_WIDTH_PX,
        }
    )
    cell = add_vertex(root, f"frame-{frame.id}", "", style)
    add_geometry(cell, (frame.x, frame.y, frame.width, frame.height))
    if frame.label:
        _add_frame_pill(root, frame, theme)


def _add_frame_pill(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add the pill with the name of a frame, in the style of design 01 section 3."""
    tone = theme.tones[frame.tone]
    pill = theme.type_scale.pill
    style = style_string(
        {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "whiteSpace": "wrap",
            "html": 1,
            "fillColor": tone.pill,
            "strokeColor": "none",
            "fontColor": theme.ink,
            "fontStyle": FONT_BOLD,
            "fontSize": fmt(pill.size),
            "fontFamily": theme.fonts.sans,
        }
    )
    label = frame.label or ""
    width = estimate_text_width(label, theme.layout, pill.size) + 2 * FRAME_PILL_PADDING_PX
    cell = add_vertex(root, f"{FRAME_LABEL_PREFIX}frame-{frame.id}", esc(label), style)
    left, top = frame.x + FRAME_PILL_LEFT_PX, frame.y + FRAME_PILL_TOP_PX
    add_geometry(cell, (left, top, width, FRAME_PILL_HEIGHT_PX))


def _add_lane(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a swimlane: a lightly tinted band and, on top of it, a dark tab with the lane's name."""
    tone = theme.tones[frame.tone]
    band = style_string(
        {
            "rounded": 0,
            "html": 1,
            "fillColor": tone.lane,
            "strokeColor": tone.pill,
            "strokeWidth": 1,
        }
    )
    add_geometry(
        add_vertex(root, f"frame-{frame.id}", "", band),
        (frame.x, frame.y, frame.width, frame.height),
    )
    tab_size = load_theme().layout.lane_tab
    is_row = frame.width >= frame.height
    tab = style_string(
        {
            "rounded": 0,
            "html": 1,
            "fillColor": tone.accent,
            "strokeColor": "none",
            "fontColor": theme.on_accent,
            "fontStyle": FONT_BOLD,
            "fontSize": LANE_TAB_FONT_SIZE,
            "fontFamily": theme.fonts.sans,
            "horizontal": 0 if is_row else 1,
            "whiteSpace": "wrap",
        }
    )
    size = (tab_size, frame.height) if is_row else (frame.width, tab_size)
    cell = add_vertex(root, f"tab-{frame.id}", esc(frame.label or ""), tab)
    add_geometry(cell, (frame.x, frame.y, *size))


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
            "fillColor": tone.lane,
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

    if frame.guard and frame.label == REF_FRAGMENT:
        _add_ref_name(root, frame, theme)
    elif frame.guard:
        left = frame.x + FRAGMENT_TAG_WIDTH_PX + FRAGMENT_GUARD_GAP_PX
        width = frame.width - FRAGMENT_TAG_WIDTH_PX
        put_guard(f"guard-{frame.id}", frame.guard, (left, frame.y, width, FRAGMENT_TAG_HEIGHT_PX))
    for index, divider in enumerate(frame.dividers):
        ends = ((frame.x, divider.y), (frame.x + frame.width, divider.y))
        add_divider(root, f"divider-{frame.id}-{index}", ends, tone.stroke)
        left = frame.x + FRAGMENT_GUARD_GAP_PX
        bounds = (left, divider.y, frame.width, FRAGMENT_TAG_HEIGHT_PX)
        if divider.guard:
            put_guard(f"divider-guard-{frame.id}-{index}", divider.guard, bounds)


def _add_ref_name(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add the name of the diagram a ``ref`` frame points to, centred in the frame."""
    style = style_string(
        {
            "text": "",
            "html": 1,
            "align": "center",
            "verticalAlign": "middle",
            "strokeColor": "none",
            "fillColor": "none",
            "fontStyle": FONT_BOLD,
            "fontSize": fmt(theme.type_scale.node.size),
            "fontColor": theme.ink,
            "fontFamily": theme.fonts.sans,
        }
    )
    cell = add_vertex(root, f"ref-name-{frame.id}", esc(frame.guard or ""), style)
    add_geometry(cell, (frame.x, frame.y, frame.width, frame.height))


def _add_title(root: ET.Element, scene: Scene, theme: Theme) -> None:
    """Add the title and the description as plain text cells."""
    if not scene.title:
        return
    common = {"text": "", "html": 1, "align": "left", "verticalAlign": "top", "strokeColor": "none"}
    title_style = style_string(
        {
            **common,
            "fontSize": fmt(theme.type_scale.title.size),
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
    theme = load_theme(scene.theme)
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
        add_node(root, node, theme)
    for edge in scene.edges:
        add_edge(root, edge, nodes, theme)
    ET.indent(mxfile)
    return ET.tostring(mxfile, encoding="unicode") + "\n"
