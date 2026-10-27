"""Draw the cards, rows, cells, pills and bands of an explainer as HTML (design 07)."""

from .explain_parts import (
    COMPOSITE_SHAPES,
    PILL_RADIUS_PX,
    Outline,
    Part,
    PartKind,
    badge_box,
    band_fill,
    explain_parts,
    outline_of,
)
from .markup import esc, px, tag
from .model import Frame, Node, Shape
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

ABSOLUTE = {"position": "absolute"}
LINE_HEIGHT = 1.3
TEXT_LINE_HEIGHT = 1.4
BOLD = "700"
REGULAR = "400"
LABEL_WEIGHT = "700"
CIRCLE_RADIUS = "50%"
CHIP_PREFIX = "chip"  # the parts of a row that are small pills with no shadow


def explain_node_html(node: Node, theme: Theme) -> str:
    """Draw one node of an explainer: its box, what is on it and its number badge.

    Args:
        node: A node whose shape is one of ``explain_parts.EXPLAIN_SHAPES``.
        theme: The design tokens.

    Returns:
        The markup of the node.
    """
    box = {
        **ABSOLUTE,
        "left": px(node.x),
        "top": px(node.y),
        "width": px(node.width),
        "height": px(node.height),
        **_outline_style(outline_of(node, theme), node, theme),
    }
    inside = "".join(_part_html(part, node, theme) for part in explain_parts(node, theme))
    if node.shape not in COMPOSITE_SHAPES:
        inside += _own_text_html(node, theme)
    return tag("div", box, inside, data_id=node.id) + _badge_html(node, theme)


def strip_frame_html(frame: Frame, theme: Theme) -> str:
    """Draw a band: a tinted strip with a pill label at its top left.

    Args:
        frame: A frame whose variant is ``STRIP``.
        theme: The design tokens.

    Returns:
        The markup of the band and of its label.
    """
    rules = theme.explainer
    area = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "width": px(frame.width),
        "height": px(frame.height),
        "background": band_fill(frame.tone, theme),
        "border-radius": px(rules.band_radius),
    }
    html = tag("div", area, data_id=frame.id)
    if not frame.label:
        return html
    pill = {
        **ABSOLUTE,
        "left": px(frame.x + rules.band_pill_left),
        "top": px(frame.y + rules.band_pill_top),
        **_pill_style(theme.tones[frame.tone].pill, theme),
        "height": px(rules.band_pill_height),
        "padding": f"0 {px(rules.band_pill_pad)}",
        "line-height": px(rules.band_pill_height - 2 * rules.border_width),
        "font-size": px(rules.band_pill_font),
        "font-weight": LABEL_WEIGHT,
        "white-space": "nowrap",
    }
    return html + tag("div", pill, esc(frame.label))


def _pill_style(fill: str, theme: Theme) -> dict[str, str]:
    """Return the look of a pill: a tint, an ink border and the solid shadow under it."""
    rules = theme.explainer
    return {
        "box-sizing": "border-box",
        "background": fill,
        "color": theme.ink,
        "border": f"{px(rules.border_width)} solid {theme.ink}",
        "border-radius": px(PILL_RADIUS_PX),
        "box-shadow": f"0 {px(rules.pill_shadow)} 0 {theme.ink}",
    }


def _outline_style(outline: Outline | None, node: Node, theme: Theme) -> dict[str, str]:
    """Return the CSS of the box of a node, or nothing for a node with no box."""
    if outline is None:
        return {}
    rules = theme.explainer
    style = {
        "box-sizing": "border-box",
        "background": outline.fill,
        "border": f"{px(rules.border_width)} solid {theme.ink}",
        "border-radius": px(outline.radius),
    }
    if outline.has_shadow:
        style["box-shadow"] = f"0 {px(rules.pill_shadow)} 0 {theme.ink}"
    return style


def _badge_html(node: Node, theme: Theme) -> str:
    """Draw the dark number badge on the top left corner of a card."""
    box = badge_box(node, theme)
    if box is None:
        return ""
    left, top, width, height = box
    style = {
        **ABSOLUTE,
        "left": px(left),
        "top": px(top),
        "width": px(width),
        "height": px(height),
        "border-radius": px(PILL_RADIUS_PX),
        "background": theme.badge.background,
        "color": theme.badge.foreground,
        "font": _badge_font(height, theme),
        "text-align": "center",
    }
    return tag("div", style, esc(node.number or ""))


def _badge_font(height: float, theme: Theme) -> str:
    """Return the CSS ``font`` of a number badge: bold mono on one line as high as the badge."""
    size = px(theme.explainer.badge_font)
    return f"{BOLD} {size}/{px(height)} '{theme.fonts.mono}',monospace"


def _part_html(part: Part, node: Node, theme: Theme) -> str:
    """Draw one part of a node."""
    if part.kind is PartKind.ICON:
        return _icon_html(part)
    place = {
        **ABSOLUTE,
        "left": px(part.box[0]),
        "top": px(part.box[1]),
        "width": px(part.box[2]),
        "height": px(part.box[3]),
    }
    if part.kind is PartKind.PILL:
        return tag("div", {**place, **_part_pill_style(part, theme)}, esc(part.text))
    if part.kind is PartKind.CIRCLE:
        return tag("div", {**place, **_circle_style(part, theme)}, esc(part.text))
    return tag("div", {**place, **_text_style(part, theme)}, esc(part.text))


def _icon_html(part: Part) -> str:
    """Draw the icon of a card, in its detailed form when it has one."""
    left, top, size, _ = part.box
    place = f'style="position:absolute;left:{px(left)};top:{px(top)}"'
    name = part.icon or ""
    if has_detailed_icon(name):
        return detailed_icon_svg(name, size, part.color, place)
    return icon_svg(name, size, part.color, place)


def _font_family(part: Part, theme: Theme) -> str:
    """Return the font family of a part: the mono font for code, else the sans font."""
    if part.is_mono:
        return f"'{theme.fonts.mono}',monospace"
    return f"'{theme.fonts.sans}',sans-serif"


def _text_style(part: Part, theme: Theme) -> dict[str, str]:
    """Return the CSS of a text part."""
    return {
        "font-family": _font_family(part, theme),
        "font-size": px(part.font_size),
        "font-weight": BOLD if part.is_bold else REGULAR,
        "line-height": str(TEXT_LINE_HEIGHT if part.name == "detail" else LINE_HEIGHT),
        "color": part.color,
        "text-align": "center" if part.is_centered else "left",
    }


def _part_pill_style(part: Part, theme: Theme) -> dict[str, str]:
    """Return the CSS of a pill part: the name of a card or a chip of a row."""
    rules = theme.explainer
    height = part.box[3]
    style = {
        **_pill_style(part.fill, theme),
        "font-family": _font_family(part, theme),
        "font-size": px(part.font_size),
        "font-weight": BOLD,
        "line-height": px(height - 2 * rules.border_width),
        "text-align": "center",
        "white-space": "nowrap",
    }
    if part.name.startswith(CHIP_PREFIX):
        del style["box-shadow"]
    return style


def _circle_style(part: Part, theme: Theme) -> dict[str, str]:
    """Return the CSS of the dark circle that holds a section letter."""
    return {
        "border-radius": CIRCLE_RADIUS,
        "background": part.fill,
        "color": part.color,
        "font-family": _font_family(part, theme),
        "font-size": px(part.font_size),
        "font-weight": BOLD,
        "line-height": px(part.box[3]),
        "text-align": "center",
    }


def _own_text_html(node: Node, theme: Theme) -> str:
    """Draw the text of a node that is one box: a cell, a pill label or a remark."""
    rules = theme.explainer
    is_pill = node.shape is Shape.PILL_LABEL
    is_remark = node.shape is Shape.REMARK
    is_middle = is_pill or node.is_centered
    style = {
        "width": "100%",
        "height": "100%",
        "box-sizing": "border-box",
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "center",
        "align-items": "center" if is_middle else "flex-start",
        "text-align": "center" if is_middle else "left",
        "padding": "0" if is_pill or is_remark else f"0 {px(rules.cell_pad)}",
        "font-size": px(node.font_size),
        "line-height": str(TEXT_LINE_HEIGHT),
    }
    if is_remark:
        return tag("div", style, _remark_lines(node, theme))
    color = theme.on_accent if is_pill and node.tone is None else theme.ink
    weight = BOLD if is_pill else REGULAR
    inner = {"color": color, "font-weight": weight}
    return tag("div", style, tag("div", inner, "<br>".join(esc(line) for line in node.text)))


def _remark_lines(node: Node, theme: Theme) -> str:
    """Write the lines of a remark: bold ink for the text, regular slate for the detail."""
    bold = {"font-weight": BOLD, "color": theme.ink}
    plain = {"font-weight": REGULAR, "color": theme.slate}
    html = "".join(tag("div", bold, esc(line)) for line in node.text)
    return html + "".join(tag("div", plain, esc(line)) for line in node.detail)
