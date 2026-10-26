"""Draw the illustrated architecture card as HTML: a pill, a detail and a large icon."""

from .markup import esc, px, tag
from .model import Node, Shape, Tone
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

ABSOLUTE = {"position": "absolute"}
PADDING_PX = 16
PILL_HEIGHT_PX = 26
PILL_PADDING_PX = 12
PILL_BORDER_PX = 2
PILL_RADIUS_PX = 999
PILL_SHADOW_PX = 3
DETAIL_GAP_PX = 10
ICON_RIGHT_PX = 14
DETAIL_WIDTH_FRACTION = 0.6  # the detail text leaves the right part of the card to the icon


def is_wide_card(node: Node) -> bool:
    """Tell whether a node is an illustrated architecture card."""
    return node.shape is Shape.WIDE_CARD


def wide_card_html(node: Node, theme: Theme) -> str:
    """Draw the inside of an illustrated architecture card.

    Args:
        node: A card with ``text`` (the name), ``detail`` and an icon.
        theme: The design tokens.

    Returns:
        The markup that goes into the box after its outline.
    """
    return _pill_html(node, theme) + _detail_html(node, theme) + _icon_html(node, theme)


def _pill_html(node: Node, theme: Theme) -> str:
    """Draw the name of the card as a pill at its top left."""
    stroke = theme.shapes[node.shape].stroke
    style = {
        **ABSOLUTE,
        "left": px(PADDING_PX),
        "top": px(PADDING_PX),
        "height": px(PILL_HEIGHT_PX),
        "padding": f"0 {px(PILL_PADDING_PX)}",
        "box-sizing": "border-box",
        "border": f"{px(PILL_BORDER_PX)} solid {stroke}",
        "border-radius": px(PILL_RADIUS_PX),
        "background": theme.tones[node.tone or Tone.GRAY].pill,
        "font-size": px(node.font_size),
        "font-weight": str(theme.type_scale.pill.weight),
        "line-height": px(PILL_HEIGHT_PX - 2 * PILL_BORDER_PX),
        "color": theme.ink,
        "white-space": "nowrap",
    }
    if theme.style.shadow:
        style["box-shadow"] = f"0 {px(PILL_SHADOW_PX)} 0 {stroke}"
    return tag("div", style, esc(" ".join(node.text)))


def _detail_html(node: Node, theme: Theme) -> str:
    """Draw the detail line under the pill."""
    if not node.detail:
        return ""
    style = {
        **ABSOLUTE,
        "left": px(PADDING_PX),
        "top": px(PADDING_PX + PILL_HEIGHT_PX + DETAIL_GAP_PX),
        "width": px(node.width * DETAIL_WIDTH_FRACTION),
        "font-size": px(theme.layout.detail_font_size),
        "line-height": px(theme.layout.detail_line_height),
        "color": theme.slate,
    }
    return tag("div", style, "<br>".join(esc(line) for line in node.detail))


def _icon_html(node: Node, theme: Theme) -> str:
    """Draw the large icon at the right, vertically centred."""
    if node.icon is None:
        return ""
    size = theme.architecture.card_icon_size
    place = (
        f'style="position:absolute;left:{px(node.width - ICON_RIGHT_PX - size)};'
        f'top:{px((node.height - size) / 2)}"'
    )
    if has_detailed_icon(node.icon):
        stroke = theme.tones[node.tone or Tone.GRAY].stroke
        return detailed_icon_svg(node.icon, size, stroke, place)
    return icon_svg(node.icon, size, theme.shapes[node.shape].stroke, place)
