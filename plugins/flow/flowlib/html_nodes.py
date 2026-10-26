"""Draw the nodes of a scene as HTML: outline, icon, text, table rows, badge and caption."""

from dataclasses import replace

from .cards import card_parts
from .html_screen import screen_html
from .markup import esc, px, tag
from .model import KEY_FLAG_TONES, Node, Row, Shape, Tone
from .shapes import outline_svg, table_radius
from .sizing import key_room
from .text_area import text_area_width
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

# Text inside a node
LINE_HEIGHT_FACTOR = 1.25
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
TABLE_HEADER_INSET_PX = (
    1  # the header sits inside the outline, so its corners are this much tighter
)
TABLE_PILL_HEIGHT_PX = 28  # the name pill in the header of an illustrated table
TABLE_CARD_ICON_PX = 52
TABLE_CHIP_HEIGHT_PX = 16
TABLE_CHIP_FONT_SIZE_PX = 10
TABLE_CHIP_RADIUS_PX = 4

# Caption under a node
CAPTION_WIDTH_PX = 150
CAPTION_GAP_PX = 4
CAPTION_FONT_SIZE_PX = 12

# Note beside an off-page connector: where the flow continues
CONNECTOR_NOTE_GAP_PX = 10
CONNECTOR_NOTE_WIDTH_PX = 140
CONNECTOR_NOTE_FONT_SIZE_PX = 11

DASH_PATTERN = "6 4"  # the outline of a reference to a table drawn on another page
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
        "font-weight": str(NOTE_TEXT_WEIGHT if is_note else theme.type_scale.node.weight),
        "color": theme.slate if is_note else theme.ink,
    }
    title = "<br>".join(esc(line) for line in node.text)
    if not node.detail or node.shape is Shape.CONNECTOR:
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


def _header_height(node: Node, theme: Theme) -> float:
    """Return the height of the header band of a table: tall when it is illustrated."""
    if node.card:
        return theme.layout.table_card_header_height
    return theme.layout.table_header_height


def _header_box(node: Node, theme: Theme) -> dict[str, str]:
    """Return the style of the coloured band at the top of a table."""
    tone = theme.tones[node.tone or Tone.GRAY]
    stroke = theme.shapes[node.shape].stroke
    corner = px(table_radius(theme.shapes[node.shape]) - TABLE_HEADER_INSET_PX)
    radius = f"{corner} {corner} 0 0"
    return {
        **ABSOLUTE,
        "left": "1px",
        "top": "1px",
        "width": px(node.width - 2),
        "height": px(_header_height(node, theme)),
        "box-sizing": "border-box",
        "background": tone.pill if node.card else tone.box,
        "border-bottom": f"2px solid {stroke}",
        "border-radius": radius,
    }


def _table_title_html(node: Node, theme: Theme) -> str:
    """Draw the name of a table: plain text in a band, or a pill beside a large icon."""
    name = esc(" ".join(node.text))
    if not node.card:
        shift = ICON_TEXT_SHIFT_PX * 2 if node.icon else 0
        title = {
            **_header_box(node, theme),
            "padding": f"0 {px(TABLE_TEXT_PADDING_PX)} 0 {px(TABLE_TEXT_PADDING_PX + shift)}",
            "display": "flex",
            "align-items": "center",
            "font-size": px(node.font_size),
            "font-weight": str(theme.type_scale.node.weight),
            "color": theme.ink,
        }
        return tag("div", title, name)
    stroke = theme.shapes[node.shape].stroke
    pill = {
        **ABSOLUTE,
        "left": px(TABLE_TEXT_PADDING_PX),
        "top": px((theme.layout.table_card_header_height - TABLE_PILL_HEIGHT_PX) / 2),
        "height": px(TABLE_PILL_HEIGHT_PX),
        "padding": f"0 {px(theme.layout.card_pill_padding)}",
        "border": f"2px solid {stroke}",
        "border-radius": px(PILL_RADIUS_PX),
        "background": theme.tones[node.tone or Tone.GRAY].box,
        "box-sizing": "border-box",
        "font-size": px(node.font_size),
        "font-weight": str(theme.type_scale.pill.weight),
        "line-height": px(TABLE_PILL_HEIGHT_PX - 4),
        "color": theme.ink,
        "white-space": "nowrap",
    }
    if theme.style.shadow:
        pill["box-shadow"] = f"0 3px 0 {stroke}"
    return (
        tag("div", _header_box(node, theme))
        + tag("div", pill, name)
        + _table_icon_html(node, theme)
    )


def _table_icon_html(node: Node, theme: Theme) -> str:
    """Draw the large icon at the right of an illustrated table header."""
    if node.icon is None:
        return ""
    size = TABLE_CARD_ICON_PX
    left = node.width - TABLE_TEXT_PADDING_PX - size
    top = (theme.layout.table_card_header_height - size) / 2
    place = f'style="position:absolute;left:{px(left)};top:{px(top)}"'
    stroke = theme.tones[node.tone or Tone.GRAY].stroke
    if has_detailed_icon(node.icon):
        return detailed_icon_svg(node.icon, size, stroke, place)
    return icon_svg(node.icon, size, stroke, place)


def _table_html(node: Node, theme: Theme) -> str:
    """Draw the header band and the rows of a table node."""
    rules = theme.layout
    html = _table_title_html(node, theme)
    key_width = key_room(node.sections, rules)
    y = _header_height(node, theme) + 2
    for index, section in enumerate(node.sections):
        if index:
            rule = {
                **ABSOLUTE,
                "left": "1px",
                "top": px(y + rules.table_section_gap / 2 - 1),
                "width": px(node.width - 2),
                "border-top": f"1px solid {theme.rule}",
            }
            html += tag("div", rule)
            y += rules.table_section_gap
        for position, row in enumerate(section):
            html += _row_html(row, (node.width, y, key_width, position > 0), theme)
            y += rules.table_row_height
    return html


def _chip_html(flag: str, theme: Theme) -> str:
    """Draw one key chip (``PK``, ``FK``, ``UQ``) in the tone of its kind."""
    tone = theme.tones[KEY_FLAG_TONES.get(flag, Tone.GRAY)]
    chip = {
        "display": "inline-block",
        "width": px(theme.layout.table_chip_width),
        "box-sizing": "border-box",
        "text-align": "center",
        "margin-right": "2px",
        "border-radius": px(TABLE_CHIP_RADIUS_PX),
        "background": tone.pill,
        "color": tone.label,
        "font": (
            f"700 {px(TABLE_CHIP_FONT_SIZE_PX)}/{px(TABLE_CHIP_HEIGHT_PX)} "
            f"'{theme.fonts.sans}',sans-serif"
        ),
    }
    return tag("span", chip, esc(flag))


def _row_html(row: Row, place: tuple[float, float, float, bool], theme: Theme) -> str:
    """Draw one row of a table: key chips and a name on the left, a type on the right.

    The name is in the sans font, bold for a primary key; the type is in the mono font and
    grey. A thin rule separates a row from the one above it.
    """
    width, top, key_width, has_rule = place
    rules = theme.layout
    mono = theme.type_scale.mono
    style = {
        **ABSOLUTE,
        "left": "1px",
        "top": px(top),
        "width": px(width - 2),
        "height": px(rules.table_row_height),
        "box-sizing": "border-box",
        "padding": f"0 {px(TABLE_TEXT_PADDING_PX)}",
        "display": "flex",
        "align-items": "center",
        "border-top": f"1px solid {theme.row_rule}" if has_rule else "0",
        "font-size": px(rules.table_name_font_size),
        "color": theme.ink,
    }
    chips = "".join(_chip_html(flag, theme) for flag in row.flags)
    key_cell = tag("span", {"display": "inline-block", "width": px(key_width)}, chips)
    weight = "700" if "PK" in row.flags else "500"
    name = tag("span", {"font-weight": weight, "flex": "1"}, esc(row.left))
    kind_font = f"{mono.weight} {px(mono.size)}/1 '{theme.fonts.mono}',monospace"
    kind = tag("span", {"color": theme.slate, "font": kind_font}, esc(row.right))
    return tag("div", style, (key_cell if key_width else "") + name + kind)


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
        "font-weight": str(theme.type_scale.node.weight),
        "color": theme.ink,
        "line-height": px(int(CAPTION_FONT_SIZE_PX * LINE_HEIGHT_FACTOR)),
    }
    return tag("div", style, esc(node.caption))


def _connector_note_html(node: Node, theme: Theme) -> str:
    """Draw the note that says where an off-page connector continues, beside its circle."""
    if node.shape is not Shape.CONNECTOR or not node.detail:
        return ""
    style = {
        **ABSOLUTE,
        "left": px(node.x + node.width + CONNECTOR_NOTE_GAP_PX),
        "top": px(node.y),
        "width": px(CONNECTOR_NOTE_WIDTH_PX),
        "height": px(node.height),
        "display": "flex",
        "align-items": "center",
        "font-size": px(CONNECTOR_NOTE_FONT_SIZE_PX),
        "line-height": px(theme.layout.detail_line_height),
        "color": theme.slate,
    }
    return tag("div", style, esc(" ".join(node.detail)))


def _card_html(node: Node, theme: Theme) -> str:
    """Draw the inside of an illustrated card: icon disc, name pill and detail text."""
    rules = theme.layout
    parts = card_parts(node, theme)
    tone = theme.tones[node.tone or Tone.BLUE]
    disc = rules.card_disc
    icon_size = disc * rules.card_icon_fraction
    inset = (disc - icon_size) / 2
    disc_style = {
        **ABSOLUTE,
        "left": px((node.width - disc) / 2),
        "top": px(parts.icon_top),
        "width": px(disc),
        "height": px(disc),
        "border-radius": "50%",
        "background": tone.pill,
    }
    html = ""
    if has_detailed_icon(node.icon or ""):
        left = px((node.width - disc) / 2)
        place = f'style="position:absolute;left:{left};top:{px(parts.icon_top)}"'
        html = detailed_icon_svg(node.icon or "", disc, tone.stroke, place)
    else:
        place = f'style="position:absolute;left:{px(inset)};top:{px(inset)}"'
        icon = icon_svg(node.icon or "", icon_size, tone.stroke, place)
        html = tag("div", disc_style, icon)
    pill_top = parts.pill_top
    pill_row = {
        **ABSOLUTE,
        "left": px(rules.card_padding),
        "top": px(pill_top),
        "width": px(node.width - 2 * rules.card_padding),
        "height": px(parts.pill_height),
        "display": "flex",
        "justify-content": "center",
    }
    pill = {
        "padding": f"0 {px(rules.card_pill_padding)}",
        "border-radius": px(PILL_RADIUS_PX),
        "background": tone.pill,
        "font-size": px(node.font_size),
        "font-weight": str(theme.type_scale.pill.weight),
        "line-height": px(parts.pill_height),
        "color": theme.ink,
        "white-space": "nowrap",
    }
    html += tag("div", pill_row, tag("span", pill, esc(" ".join(node.text))))
    if node.detail:
        detail = {
            **ABSOLUTE,
            "left": px(rules.card_padding),
            "top": px(pill_top + parts.pill_height + rules.card_gap),
            "width": px(node.width - 2 * rules.card_padding),
            "text-align": "center",
            "font-size": px(rules.detail_font_size),
            "line-height": px(rules.detail_line_height),
            "color": theme.slate,
        }
        html += tag("div", detail, "<br>".join(esc(line) for line in node.detail))
    return html


def _screen_node_html(node: Node, theme: Theme) -> str:
    """Draw a screen of a screen flow: its parts sit in a box of the size of the node."""
    box = {
        **ABSOLUTE,
        "left": px(node.x),
        "top": px(node.y),
        "width": px(node.width),
        "height": px(node.height),
    }
    return tag("div", box, screen_html(node, theme), data_id=node.id)


def node_html(node: Node, theme: Theme) -> str:
    """Draw one node: its outline, icon and text, its badge and its caption.

    Args:
        node: The node to draw.
        theme: The design tokens.

    Returns:
        The markup of the node and of what hangs on it.
    """
    if node.screen is not None:
        return _screen_node_html(node, theme)
    colors = theme.shapes[node.shape]
    if node.tone is not None and node.shape is not Shape.TABLE:
        colors = replace(colors, fill=theme.tones[node.tone].box)
    if node.dashed:
        colors = replace(colors, dash=DASH_PATTERN)
    inside = outline_svg(node.shape, node.width, node.height, colors)
    if node.card and node.shape is not Shape.TABLE:
        inside += _card_html(node, theme)
    elif node.shape is Shape.TABLE:
        inside += _table_html(node, theme)
        if not node.card:
            inside += _icon_html(node, colors.stroke, _header_height(node, theme))
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
        + _connector_note_html(node, theme)
    )
