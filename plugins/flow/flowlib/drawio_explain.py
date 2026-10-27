"""The draw.io cells of an explainer: cards, rows, cells, pills, remarks and bands (design 07).

Each node is one cell whose style carries ``flowShape``; what sits on it (icon, name pill, text,
chips) is a child cell that moves with it. The positions come from ``explain_parts``, so the HTML
page and the draw.io file agree.
"""

import xml.etree.ElementTree as ET

from .drawio_common import (
    FLOW_FRAME_KEY,
    FLOW_SHAPE_KEY,
    FONT_BOLD,
    FRAME_LABEL_PREFIX,
    add_geometry,
    add_vertex,
    style_string,
)
from .drawio_plan_parts import image_style, rounded_pairs
from .explain_parts import (
    COMPOSITE_SHAPES,
    PILL_RADIUS_PX,
    Part,
    PartKind,
    badge_box,
    band_fill,
    explain_parts,
    outline_of,
    pill_width,
)
from .markup import esc, fmt
from .model import Frame, Node, Shape
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
PILL_ARC_PERCENT = 50
TEXT_PAIRS = {
    "text": "",
    "html": 1,
    "whiteSpace": "wrap",
    "strokeColor": "none",
    "fillColor": "none",
}
SMALL_FONT_STYLE = "font-weight:normal;color:"
HEAD_TEXT_LEFT_PX = 46
SECTION_HEAD_GAP_PX = 10


def add_explain_node(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add a node of an explainer as a cell, with its parts as child cells and its badge.

    Args:
        root: The ``root`` element of the diagram.
        node: A node whose shape is one of ``explain_parts.EXPLAIN_SHAPES``.
        theme: The design tokens.
    """
    cell = add_vertex(root, f"node-{node.id}", _value(node, theme), _style(node, theme))
    add_geometry(cell, (node.x, node.y, node.width, node.height))
    for part in explain_parts(node, theme):
        if part.kind is PartKind.CIRCLE:
            _add_circle(root, node, part)
        else:
            _add_part(root, node, part, theme)
    _add_badge(root, node, theme)


def add_strip_frame(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a band: a tinted strip and, on it, the pill that names it.

    Args:
        root: The ``root`` element of the diagram.
        frame: A frame whose variant is ``STRIP``.
        theme: The design tokens.
    """
    rules = theme.explainer
    style = {
        FLOW_FRAME_KEY: frame.variant.value,
        **rounded_pairs(rules.band_radius),
        "html": 1,
        "fillColor": band_fill(frame.tone, theme),
        "strokeColor": "none",
    }
    cell = add_vertex(root, f"frame-{frame.id}", "", style_string(style))
    add_geometry(cell, (frame.x, frame.y, frame.width, frame.height))
    if not frame.label:
        return
    label = frame.label
    pill = _pill_pairs(theme.tones[frame.tone].pill, rules.band_pill_font, theme)
    width = pill_width(label, rules.band_pill_font, theme)
    pill_cell = add_vertex(
        root, f"{FRAME_LABEL_PREFIX}frame-{frame.id}", esc(label), style_string(pill)
    )
    left, top = frame.x + rules.band_pill_left, frame.y + rules.band_pill_top
    add_geometry(pill_cell, (left, top, width, rules.band_pill_height))


def _pill_pairs(fill: str, font_size: float, theme: Theme) -> dict[str, object]:
    """Return the style pairs of a pill: a tint, an ink outline and bold text."""
    return {
        "rounded": 1,
        "arcSize": PILL_ARC_PERCENT,
        "html": 1,
        "whiteSpace": "nowrap",
        "fillColor": fill,
        "strokeColor": theme.ink,
        "strokeWidth": fmt(theme.explainer.border_width),
        "fontColor": theme.ink,
        "fontStyle": FONT_BOLD,
        "fontSize": fmt(font_size),
        "fontFamily": theme.fonts.sans,
    }


def _value(node: Node, theme: Theme) -> str:
    """Return the text written on the cell of a node that is one box; parts carry the rest."""
    if node.shape in COMPOSITE_SHAPES and node.shape is not Shape.SECTION_HEAD:
        return ""
    if node.shape is Shape.REMARK:
        return _remark_value(node, theme)
    return "<br>".join(esc(line) for line in node.text)


def _remark_value(node: Node, theme: Theme) -> str:
    """Return the label of a remark: bold lines, then the detail small and grey."""
    bold = "<br>".join(esc(line) for line in node.text)
    grey = "<br>".join(esc(line) for line in node.detail)
    if not node.detail:
        return bold
    detail = f'<span style="{SMALL_FONT_STYLE}{theme.slate}">{grey}</span>'
    return f"{bold}<br>{detail}" if bold else detail


def _style(node: Node, theme: Theme) -> str:
    """Return the style of the cell of a node."""
    pairs: dict[str, object] = {
        FLOW_SHAPE_KEY: node.shape.value,
        "html": 1,
        "whiteSpace": "wrap",
        "fontFamily": theme.fonts.sans,
        "fontColor": theme.ink,
        "fontSize": fmt(node.font_size),
    }
    outline = outline_of(node, theme)
    if outline is None:
        pairs.update(_text_pairs(node, theme))
        return style_string(pairs)
    radius = PILL_RADIUS_PX if node.shape is Shape.PILL_LABEL else outline.radius
    pairs.update(
        {
            **rounded_pairs(min(radius, node.height / 2)),
            "fillColor": outline.fill,
            "strokeColor": theme.ink,
            "strokeWidth": fmt(theme.explainer.border_width),
        }
    )
    pairs.update(_box_text_pairs(node, theme))
    return style_string(pairs)


def _box_text_pairs(node: Node, theme: Theme) -> dict[str, object]:
    """Return the style pairs of the text of a cell or a pill label."""
    if node.shape is Shape.PILL_LABEL:
        color = theme.on_accent if node.tone is None else theme.ink
        return {"fontStyle": FONT_BOLD, "fontColor": color}
    if node.shape is Shape.CELL:
        return {"align": "left", "spacingLeft": theme.explainer.cell_pad - 2, "fontStyle": 0}
    return {}


def _text_pairs(node: Node, theme: Theme) -> dict[str, object]:
    """Return the style pairs of a remark or a section heading: free text, no outline."""
    if node.shape is Shape.SECTION_HEAD:
        return {
            **TEXT_PAIRS,
            "align": "left",
            "verticalAlign": "middle",
            "spacingLeft": HEAD_TEXT_LEFT_PX - SECTION_HEAD_GAP_PX + SECTION_HEAD_GAP_PX,
            "fontSize": fmt(theme.explainer.section_head_font),
            "fontStyle": FONT_BOLD,
        }
    has_title = bool(node.text and node.detail)
    return {
        **TEXT_PAIRS,
        "align": "center" if node.is_centered else "left",
        "verticalAlign": "top" if has_title else "middle",
        "spacingLeft": 0,
        "fontStyle": FONT_BOLD if node.text else 0,
        "fontColor": theme.ink if node.text else theme.slate,
    }


def _child(root: ET.Element, node: Node, name: str, style: dict[str, object]) -> ET.Element:
    """Add a child cell of a node; its id is a prefix and the id of the node."""
    cell = add_vertex(root, f"{name}-{node.id}", "", style_string(style))
    cell.set("parent", f"node-{node.id}")
    return cell


def _add_part(root: ET.Element, node: Node, part: Part, theme: Theme) -> None:
    """Add one part of a node: its icon, a pill or a text."""
    if part.kind is PartKind.ICON:
        cell = _child(root, node, part.name, image_style(_icon_svg(part)))
    elif part.kind is PartKind.PILL:
        cell = _child(root, node, part.name, _part_pill_pairs(part, theme))
        cell.set("value", esc(part.text))
    else:
        cell = _child(root, node, part.name, _part_text_pairs(part, theme))
        cell.set("value", esc(part.text))
    add_geometry(cell, part.box)


def _icon_svg(part: Part) -> str:
    """Return the SVG of the icon of a part, detailed when it has a detailed drawing."""
    name = part.icon or ""
    attrs = f'xmlns="{SVG_NAMESPACE}"'
    size = part.box[2]
    if has_detailed_icon(name):
        return detailed_icon_svg(name, size, part.color, attrs)
    return icon_svg(name, size, part.color, attrs)


def _part_pill_pairs(part: Part, theme: Theme) -> dict[str, object]:
    """Return the style pairs of a pill part, set in mono when it is a chip."""
    pairs = _pill_pairs(part.fill, part.font_size, theme)
    if part.is_mono:
        pairs["fontFamily"] = theme.fonts.mono
    return pairs


def _part_text_pairs(part: Part, theme: Theme) -> dict[str, object]:
    """Return the style pairs of a text part."""
    return {
        **TEXT_PAIRS,
        "align": "center" if part.is_centered else "left",
        "verticalAlign": "top",
        "spacingLeft": 0,
        "spacingTop": 0,
        "fontSize": fmt(part.font_size),
        "fontColor": part.color,
        "fontStyle": FONT_BOLD if part.is_bold else 0,
        "fontFamily": theme.fonts.mono if part.is_mono else theme.fonts.sans,
    }


def _circle_pairs(part: Part) -> dict[str, object]:
    """Return the style pairs of a dark circle that holds a number or a letter."""
    return {
        "ellipse": "",
        "html": 1,
        "fillColor": part.fill,
        "strokeColor": "none",
        "fontColor": part.color,
        "fontStyle": FONT_BOLD,
        "fontSize": fmt(part.font_size),
    }


def _add_circle(root: ET.Element, node: Node, part: Part) -> None:
    """Add the letter circle of a section heading; it is read back as the number of the node."""
    cell = add_vertex(root, f"badge-{node.id}", esc(part.text), style_string(_circle_pairs(part)))
    left, top, width, height = part.box
    add_geometry(cell, (node.x + left, node.y + top, width, height))


def _add_badge(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the dark number badge on the top left corner of a card."""
    box = badge_box(node, theme)
    if box is None:
        return
    rules = theme.explainer
    pairs = {
        "rounded": 1,
        "arcSize": PILL_ARC_PERCENT,
        "html": 1,
        "fillColor": theme.badge.background,
        "strokeColor": "none",
        "fontColor": theme.badge.foreground,
        "fontSize": fmt(rules.badge_font),
        "fontStyle": FONT_BOLD,
        "fontFamily": theme.fonts.mono,
    }
    cell = add_vertex(root, f"badge-{node.id}", esc(node.number or ""), style_string(pairs))
    add_geometry(cell, box)
