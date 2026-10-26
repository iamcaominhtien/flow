"""Draw the nodes of a scene as HTML: outline, icon, text, table rows, badge and caption."""

from .markup import esc, px, tag
from .model import Node, Shape, Tone
from .shapes import outline_svg
from .text_area import text_area_width
from .theme import ShapeColors, Theme, detailed_icon_svg, has_detailed_icon, icon_svg

# Text inside a node
LINE_HEIGHT_FACTOR = 1.25
NODE_TEXT_WEIGHT = 600
NOTE_TEXT_WEIGHT = 400
DETAIL_TEXT_WEIGHT = 400
DETAIL_GAP_PX = 2
DOCUMENT_LABEL_TRIM_PX = 6  # the wavy bottom of a document leaves less room for text
DOCUMENT_ICON_LIFT_PX = 3
SHAPES_WITHOUT_TEXT = (Shape.TABLE,)  # drawn by their own function

# Icon inside a node
ICON_SIZE_PX = 18
ICON_STROKE_WIDTH = 2
ICON_TEXT_SHIFT_PX = 12  # text moves right by half of that
ICON_LEFT_PX: dict[Shape, float] = {
    Shape.SUBPROCESS: 22,
    Shape.IO: 26,
    Shape.PREPARATION: 24,
}
DEFAULT_ICON_LEFT_PX = 14
CENTERED_ICON_SHAPES = (Shape.INTERMEDIATE, Shape.DECISION)  # the icon is a marker in the middle

# Number badge on a node corner
BADGE_OVERHANG_LEFT_PX = 6
BADGE_OVERHANG_TOP_PX = 10
BADGE_MIN_WIDTH_PX = 22
BADGE_HEIGHT_PX = 20
BADGE_PADDING_X_PX = 6
BADGE_FONT_SIZE_PX = 11
PILL_RADIUS_PX = 999

# Table node
TABLE_TEXT_PADDING_PX = 14
TABLE_ROW_FONT_SIZE_PX = 11
TABLE_RULE_COLOR = "#CBD5E1"
TABLE_HEADER_RADIUS_PX = 7

# Caption under a node
CAPTION_WIDTH_PX = 150
CAPTION_GAP_PX = 4
CAPTION_FONT_SIZE_PX = 12

ABSOLUTE = {"position": "absolute"}


def _icon_html(node: Node, stroke: str, band: float | None = None) -> str:
    """Draw the icon of a node at its left side, or return nothing if it has none.

    Args:
        node: The node.
        stroke: The icon colour.
        band: The height of the strip the icon is centred in; the whole node by default.

    Returns:
        An ``svg`` element, or an empty string.
    """
    if node.icon is None:
        return ""
    left = ICON_LEFT_PX.get(node.shape, DEFAULT_ICON_LEFT_PX)
    if node.shape in CENTERED_ICON_SHAPES and not node.text:
        left = (node.width - ICON_SIZE_PX) / 2
    top = ((band or node.height) - ICON_SIZE_PX) / 2
    if node.shape is Shape.DOCUMENT:
        top -= DOCUMENT_ICON_LIFT_PX
    place = f'style="position:absolute;left:{px(left)};top:{px(top)}"'
    return icon_svg(node.icon, ICON_SIZE_PX, stroke, place)


def _label_html(node: Node, theme: Theme) -> str:
    """Draw the text of a node, centred in the space the shape leaves for it."""
    if not node.text:
        return ""
    has_icon = node.icon is not None
    width = text_area_width(node.shape, node.width, has_icon)
    shift = ICON_TEXT_SHIFT_PX if has_icon else 0.0
    height = node.height - (DOCUMENT_LABEL_TRIM_PX if node.shape is Shape.DOCUMENT else 0)
    is_note = node.shape in (Shape.NOTE, Shape.TEXT)
    style = {
        **ABSOLUTE,
        "left": px((node.width - width) / 2 + shift),
        "top": "0",
        "width": px(width),
        "height": px(height),
        "display": "flex",
        "align-items": "center",
        "justify-content": "flex-start" if is_note else "center",
        "text-align": "left" if is_note else "center",
        "font-size": px(node.font_size),
        "line-height": px(int(node.font_size * LINE_HEIGHT_FACTOR)),
        "font-weight": str(NOTE_TEXT_WEIGHT if is_note else NODE_TEXT_WEIGHT),
        "color": theme.slate if is_note else theme.ink,
    }
    title = "<br>".join(esc(line) for line in node.text)
    if not node.detail:
        return tag("div", style, title)
    style.update({"flex-direction": "column", "justify-content": "center"})
    detail_style = {
        "font-size": px(theme.layout.detail_font_size),
        "line-height": px(theme.layout.detail_line_height),
        "font-weight": str(DETAIL_TEXT_WEIGHT),
        "color": theme.slate,
        "margin-top": px(DETAIL_GAP_PX),
    }
    detail = tag("div", detail_style, "<br>".join(esc(line) for line in node.detail))
    return tag("div", style, tag("div", {}, title) + detail)


def _badge_html(node: Node, theme: Theme) -> str:
    """Draw the number badge on the top-left corner of a node, or return nothing."""
    if node.number is None:
        return ""
    style = {
        **ABSOLUTE,
        "left": px(node.x - BADGE_OVERHANG_LEFT_PX),
        "top": px(node.y - BADGE_OVERHANG_TOP_PX),
        "min-width": px(BADGE_MIN_WIDTH_PX),
        "height": px(BADGE_HEIGHT_PX),
        "padding": f"0 {px(BADGE_PADDING_X_PX)}",
        "box-sizing": "border-box",
        "border-radius": px(PILL_RADIUS_PX),
        "background": theme.badge.background,
        "color": theme.badge.foreground,
        "font": f"700 {px(BADGE_FONT_SIZE_PX)}/{px(BADGE_HEIGHT_PX)} "
        f"'{theme.fonts.mono}',monospace",
        "text-align": "center",
    }
    return tag("div", style, esc(node.number))


def _header_height(theme: Theme) -> float:
    """Return the height of the header band of a table."""
    return theme.layout.table_header_height


def _table_html(node: Node, theme: Theme) -> str:
    """Draw the header band and the rows of a table node."""
    rules = theme.layout
    tone = theme.tones[node.tone or Tone.GRAY]
    stroke = theme.shapes[node.shape].stroke
    header_height = _header_height(theme)
    shift = ICON_TEXT_SHIFT_PX * 2 if node.icon else 0
    header = {
        **ABSOLUTE,
        "left": "1px",
        "top": "1px",
        "width": px(node.width - 2),
        "height": px(header_height),
        "box-sizing": "border-box",
        "background": tone.box,
        "border-bottom": f"2px solid {stroke}",
        "border-radius": f"{px(TABLE_HEADER_RADIUS_PX)} {px(TABLE_HEADER_RADIUS_PX)} 0 0",
        "padding": f"0 {px(TABLE_TEXT_PADDING_PX)} 0 {px(TABLE_TEXT_PADDING_PX + shift)}",
        "display": "flex",
        "align-items": "center",
        "font-size": px(node.font_size),
        "font-weight": str(NODE_TEXT_WEIGHT),
        "color": theme.ink,
    }
    html = tag("div", header, esc(" ".join(node.text)))
    y = header_height + 2
    for index, section in enumerate(node.sections):
        if index:
            rule = {
                **ABSOLUTE,
                "left": "1px",
                "top": px(y + rules.table_section_gap / 2 - 1),
                "width": px(node.width - 2),
                "border-top": f"1px solid {TABLE_RULE_COLOR}",
            }
            html += tag("div", rule)
            y += rules.table_section_gap
        for row in section:
            html += _row_html(row.left, row.right, (node.width, y), theme)
            y += rules.table_row_height
    return html


def _row_html(left: str, right: str, place: tuple[float, float], theme: Theme) -> str:
    """Draw one row of a table: a name on the left and a note on the right."""
    width, top = place
    row = {
        **ABSOLUTE,
        "left": px(TABLE_TEXT_PADDING_PX),
        "top": px(top),
        "width": px(width - 2 * TABLE_TEXT_PADDING_PX),
        "height": px(theme.layout.table_row_height),
        "display": "flex",
        "align-items": "center",
        "justify-content": "space-between",
        "font": f"500 {px(TABLE_ROW_FONT_SIZE_PX)}/1 '{theme.fonts.mono}',monospace",
        "color": theme.ink,
    }
    muted = tag("span", {"color": theme.slate}, esc(right))
    return tag("div", row, tag("span", {}, esc(left)) + muted)


def _caption_html(node: Node, theme: Theme) -> str:
    """Draw the caption under a node (an event, an actor), or return nothing."""
    if not node.caption:
        return ""
    style = {
        **ABSOLUTE,
        "left": px(node.x + node.width / 2 - CAPTION_WIDTH_PX / 2),
        "top": px(node.y + node.height + CAPTION_GAP_PX),
        "width": px(CAPTION_WIDTH_PX),
        "text-align": "center",
        "font-size": px(CAPTION_FONT_SIZE_PX),
        "font-weight": str(NODE_TEXT_WEIGHT),
        "color": theme.ink,
        "line-height": px(int(CAPTION_FONT_SIZE_PX * LINE_HEIGHT_FACTOR)),
    }
    return tag("div", style, esc(node.caption))


def _card_html(node: Node, theme: Theme) -> str:
    """Draw the inside of an illustrated card: icon disc, name pill and detail text."""
    rules = theme.layout
    tone = theme.tones[node.tone or Tone.BLUE]
    disc = rules.card_disc
    icon_size = disc * rules.card_icon_fraction
    inset = (disc - icon_size) / 2
    disc_style = {
        **ABSOLUTE,
        "left": px((node.width - disc) / 2),
        "top": px(rules.card_padding),
        "width": px(disc),
        "height": px(disc),
        "border-radius": "50%",
        "background": tone.pill,
    }
    html = ""
    if has_detailed_icon(node.icon or ""):
        left = px((node.width - disc) / 2)
        place = f'style="position:absolute;left:{left};top:{px(rules.card_padding)}"'
        html = detailed_icon_svg(node.icon or "", disc, tone.stroke, place)
    else:
        place = f'style="position:absolute;left:{px(inset)};top:{px(inset)}"'
        icon = icon_svg(node.icon or "", icon_size, tone.stroke, place)
        html = tag("div", disc_style, icon)
    pill_top = rules.card_padding + disc + rules.card_gap
    pill_row = {
        **ABSOLUTE,
        "left": px(rules.card_padding),
        "top": px(pill_top),
        "width": px(node.width - 2 * rules.card_padding),
        "height": px(rules.card_pill_height),
        "display": "flex",
        "justify-content": "center",
    }
    pill = {
        "padding": f"0 {px(rules.card_pill_padding)}",
        "border-radius": px(PILL_RADIUS_PX),
        "background": tone.pill,
        "font-size": px(node.font_size),
        "font-weight": str(NODE_TEXT_WEIGHT),
        "line-height": px(rules.card_pill_height),
        "color": theme.ink,
        "white-space": "nowrap",
    }
    html += tag("div", pill_row, tag("span", pill, esc(" ".join(node.text))))
    if node.detail:
        detail = {
            **ABSOLUTE,
            "left": px(rules.card_padding),
            "top": px(pill_top + rules.card_pill_height + rules.card_gap),
            "width": px(node.width - 2 * rules.card_padding),
            "text-align": "center",
            "font-size": px(rules.detail_font_size),
            "line-height": px(rules.detail_line_height),
            "color": theme.slate,
        }
        html += tag("div", detail, "<br>".join(esc(line) for line in node.detail))
    return html


def node_html(node: Node, theme: Theme) -> str:
    """Draw one node: its outline, icon and text, its badge and its caption.

    Args:
        node: The node to draw.
        theme: The design tokens.

    Returns:
        The markup of the node and of what hangs on it.
    """
    colors = theme.shapes[node.shape]
    if node.tone is not None and node.shape is not Shape.TABLE:
        colors = ShapeColors(fill=theme.tones[node.tone].box, stroke=colors.stroke)
    inside = outline_svg(node.shape, node.width, node.height, colors)
    if node.card:
        inside += _card_html(node, theme)
    elif node.shape is Shape.TABLE:
        inside += _table_html(node, theme)
        inside += _icon_html(node, colors.stroke, _header_height(theme))
    else:
        inside += _icon_html(node, colors.stroke) + _label_html(node, theme)
    box = {
        **ABSOLUTE,
        "left": px(node.x),
        "top": px(node.y),
        "width": px(node.width),
        "height": px(node.height),
    }
    return (
        tag("div", box, inside, data_id=node.id)
        + _badge_html(node, theme)
        + _caption_html(node, theme)
    )
