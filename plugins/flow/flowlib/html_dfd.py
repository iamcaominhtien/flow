"""Draw the insides of the Gane-Sarson shapes of a data flow diagram as HTML.

The outline of each shape comes from ``shapes``. This module adds what sits on it: the header
strip with the number of a process, the id cell of a store, the id above the name of an entity,
and the illustrated card version of each.
"""

from .markup import esc, px, tag
from .model import Node, Shape, Tone
from .shapes import table_radius
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

ABSOLUTE = {"position": "absolute"}
STRIP_BORDER_PX = 2
STRIP_TEXT_LEFT_PX = 10
NAME_WEIGHT = 700
DETAIL_GAP_PX = 3
CARD_PADDING_PX = 16
CARD_PILL_HEIGHT_PX = 26
CARD_PILL_PADDING_PX = 12
CARD_ICON_PX = 64
STORE_CARD_ICON_PX = 52
PILL_RADIUS_PX = 999
CARD_DETAIL_FRACTION = 0.55  # the detail text of a card leaves the right part to the icon
CARD_ID_GAP_PX = 10
ENTITY_ID_GAP_PX = 1
PLAIN_ICON_RIGHT_PX = 16


def is_dfd_node(node: Node) -> bool:
    """Tell whether a node is drawn with the data flow shapes: a process, a store or an entity."""
    if node.shape in (Shape.DFD_PROCESS, Shape.DFD_STORE):
        return True
    return node.shape is Shape.ENTITY and node.number is not None


def dfd_html(node: Node, theme: Theme) -> str:
    """Draw what sits on the outline of a data flow node.

    Args:
        node: A process, a store or an entity with an id.
        theme: The design tokens.

    Returns:
        The markup that goes into the node's box after its outline.
    """
    if node.shape is Shape.DFD_PROCESS:
        return _process_html(node, theme)
    if node.shape is Shape.DFD_STORE:
        return _store_html(node, theme)
    return _entity_html(node, theme)


def _tone(node: Node, theme: Theme) -> Tone:
    """Return the tone of a node, gray when it has none."""
    return node.tone or Tone.GRAY


def _id_style(theme: Theme, size: float) -> dict[str, str]:
    """Return the style of the mono text that shows a number or an id."""
    return {
        "font-family": f"'{theme.fonts.mono}',monospace",
        "font-size": px(size),
        "font-weight": "700",
        "color": theme.ink,
    }


def _strip_html(node: Node, theme: Theme) -> str:
    """Draw the header strip of a process with its number in it."""
    rules = theme.dfd
    radius = table_radius(theme.shapes[node.shape]) - 1
    strip = {
        **ABSOLUTE,
        "left": "1px",
        "top": "1px",
        "width": px(node.width - 2),
        "height": px(rules.strip_height),
        "box-sizing": "border-box",
        "background": theme.tones[_tone(node, theme)].pill,
        "border-bottom": f"{px(STRIP_BORDER_PX)} solid {theme.shapes[node.shape].stroke}",
        "border-radius": f"{px(radius)} {px(radius)} 0 0",
    }
    number = {
        **ABSOLUTE,
        "left": px(STRIP_TEXT_LEFT_PX),
        "top": "1px",
        "line-height": px(rules.strip_height),
        **_id_style(theme, rules.id_font_size),
    }
    return tag("div", strip) + tag("div", number, esc(node.number or ""))


def _name_html(node: Node, theme: Theme) -> str:
    """Return the name of a node and its detail as two stacked blocks."""
    name = {"font-size": px(node.font_size), "font-weight": str(NAME_WEIGHT), "color": theme.ink}
    html = tag("div", name, "<br>".join(esc(line) for line in node.text))
    if not node.detail:
        return html
    detail = {
        "font-size": px(theme.layout.detail_font_size),
        "line-height": px(theme.layout.detail_line_height),
        "color": theme.slate,
        "margin-top": px(DETAIL_GAP_PX),
    }
    return html + tag("div", detail, "<br>".join(esc(line) for line in node.detail))


def _icon_svg(node: Node, theme: Theme, size: float, place: str) -> str:
    """Draw the icon of a node, detailed when the library has a detailed drawing."""
    if node.icon is None:
        return ""
    stroke = theme.tones[_tone(node, theme)].stroke
    if (node.card or node.shape is Shape.ENTITY) and has_detailed_icon(node.icon):
        return detailed_icon_svg(node.icon, size, stroke, place)
    return icon_svg(node.icon, size, theme.shapes[node.shape].stroke, place)


def _placed(left: float, top: float) -> str:
    """Return the ``style`` attribute that puts an inline SVG at a position in its box."""
    return f'style="position:absolute;left:{px(left)};top:{px(top)}"'


def _process_html(node: Node, theme: Theme) -> str:
    """Draw a process: its strip, then a name and a detail, or a card."""
    html = _strip_html(node, theme)
    top = theme.dfd.strip_height + STRIP_BORDER_PX
    if node.card:
        return html + _card_html(node, theme, top)
    body = {
        **ABSOLUTE,
        "left": "0",
        "top": px(top),
        "width": px(node.width),
        "height": px(node.height - top),
        "display": "flex",
        "flex-direction": "column",
        "align-items": "center",
        "justify-content": "center",
        "text-align": "center",
    }
    return html + tag("div", body, _name_html(node, theme))


def _pill_html(node: Node, theme: Theme, top: float) -> str:
    """Draw the name of a card as a pill at the left of its box."""
    stroke = theme.shapes[node.shape].stroke
    pill = {
        **ABSOLUTE,
        "left": px(CARD_PADDING_PX),
        "top": px(top),
        "height": px(CARD_PILL_HEIGHT_PX),
        "padding": f"0 {px(CARD_PILL_PADDING_PX)}",
        "box-sizing": "border-box",
        "border": f"2px solid {stroke}",
        "border-radius": px(PILL_RADIUS_PX),
        "background": theme.tones[_tone(node, theme)].pill,
        "font-size": px(node.font_size),
        "font-weight": str(theme.type_scale.pill.weight),
        "line-height": px(CARD_PILL_HEIGHT_PX - 4),
        "color": theme.ink,
        "white-space": "nowrap",
    }
    if theme.style.shadow:
        pill["box-shadow"] = f"0 3px 0 {stroke}"
    return tag("div", pill, esc(" ".join(node.text)))


def _card_text_html(node: Node, theme: Theme, top: float, lines: tuple[str, ...]) -> str:
    """Draw the lines of text under the pill of a card: the id of an entity, or a detail."""
    if not lines:
        return ""
    style = {
        **ABSOLUTE,
        "left": px(CARD_PADDING_PX),
        "top": px(top),
        "width": px(node.width * CARD_DETAIL_FRACTION),
        "font-size": px(theme.layout.detail_font_size),
        "line-height": px(theme.layout.detail_line_height),
        "color": theme.slate,
    }
    return tag("div", style, "<br>".join(esc(line) for line in lines))


def _card_html(node: Node, theme: Theme, top: float) -> str:
    """Draw a card below ``top``: a pill and a text at the left, a large icon at the right.

    An entity shows its id under the pill; a process shows its detail, as it has its number in
    the strip.
    """
    lines = node.detail if node.shape is Shape.DFD_PROCESS else (node.number or "",)
    area = node.height - top
    icon_top = top + (area - CARD_ICON_PX) / 2
    pill_top = top + CARD_PADDING_PX - 2
    text_top = pill_top + CARD_PILL_HEIGHT_PX + CARD_ID_GAP_PX
    icon_left = node.width - CARD_PADDING_PX - CARD_ICON_PX
    icon = _icon_svg(node, theme, CARD_ICON_PX, _placed(icon_left, icon_top))
    return _pill_html(node, theme, pill_top) + _card_text_html(node, theme, text_top, lines) + icon


def _id_cell_html(node: Node, theme: Theme) -> str:
    """Draw the id cell of a store: a tinted block on its left with the id in it."""
    rules = theme.dfd
    cell = {
        **ABSOLUTE,
        "left": "1px",
        "top": "1px",
        "width": px(rules.id_cell_width),
        "height": px(node.height - 2),
        "box-sizing": "border-box",
        "background": theme.tones[_tone(node, theme)].pill,
        "border-right": f"{px(STRIP_BORDER_PX)} solid {theme.shapes[node.shape].stroke}",
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        **_id_style(theme, rules.id_font_size),
    }
    return tag("div", cell, esc(node.number or ""))


def _store_html(node: Node, theme: Theme) -> str:
    """Draw a store: the id cell, the name, and an icon at the right when it has one."""
    rules = theme.dfd
    left = rules.id_cell_width + CARD_PADDING_PX
    name = {
        **ABSOLUTE,
        "left": px(left),
        "top": "0",
        "height": px(node.height),
        "display": "flex",
        "align-items": "center",
        "font-size": px(node.font_size),
        "font-weight": str(NAME_WEIGHT),
        "color": theme.ink,
    }
    html = _id_cell_html(node, theme) + tag("div", name, esc(" ".join(node.text)))
    if node.icon is None:
        return html
    size = STORE_CARD_ICON_PX if node.card else theme.dfd.entity_icon
    icon_left = node.width - PLAIN_ICON_RIGHT_PX - size
    return html + _icon_svg(node, theme, size, _placed(icon_left, (node.height - size) / 2))


def _entity_html(node: Node, theme: Theme) -> str:
    """Draw an entity: its id above its name, with an icon at the left, or as a card."""
    if node.card:
        return _card_html(node, theme, 0)
    rules = theme.dfd
    has_icon = node.icon is not None
    left = rules.entity_text_left if has_icon else CARD_PADDING_PX
    body = {
        **ABSOLUTE,
        "left": px(left),
        "top": "0",
        "height": px(node.height),
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "center",
    }
    small = {
        "font-size": px(rules.entity_id_font_size),
        "color": theme.slate,
        "margin-bottom": px(ENTITY_ID_GAP_PX),
    }
    name = {"font-size": px(node.font_size), "font-weight": str(NAME_WEIGHT), "color": theme.ink}
    inside = tag("div", small, esc(node.number or "")) + tag(
        "div", name, "<br>".join(esc(line) for line in node.text)
    )
    icon_place = _placed(CARD_PADDING_PX, (node.height - rules.entity_icon) / 2)
    return tag("div", body, inside) + _icon_svg(node, theme, rules.entity_icon, icon_place)
