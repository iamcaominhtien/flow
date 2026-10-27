"""Draw a screen of a screen flow as HTML: each part of the drawing becomes an element."""

import math

from .markup import esc, fmt, px, tag
from .model import Node, Tone
from .screen_part import Align, Part, PartKind
from .screen_parts import screen_parts
from .theme import Theme, icon_svg

ABSOLUTE = {"position": "absolute"}
BOLD_WEIGHT = 700
REGULAR_WEIGHT = 500
HATCH_ANGLE_DEG = 135
TEXT_LINE_HEIGHT = 1.2
ARC_SPAN_FRACTION = 0.25  # of a full turn
ARC_START_DEG = -90  # at the top of the circle
JUSTIFY = {Align.LEFT: "flex-start", Align.CENTER: "center", Align.RIGHT: "flex-end"}


def screen_html(node: Node, theme: Theme) -> str:
    """Draw the inside of a screen node: frame, chrome, body, overlay and id chip.

    Args:
        node: A node with a ``screen`` view.
        theme: The design tokens.

    Returns:
        The markup of the parts, positioned relative to the node's box.
    """
    return "".join(_part_html(part, theme) for part in screen_parts(node, theme))


def _box_style(part: Part) -> dict[str, str]:
    """Return the position and size of a part."""
    x, y, width, height = part.bounds
    return {
        **ABSOLUTE,
        "left": px(x),
        "top": px(y),
        "width": px(width),
        "height": px(height),
        "box-sizing": "border-box",
    }


def _paint_style(part: Part) -> dict[str, str]:
    """Return the fill, border, corner radius and opacity of a rectangle or a circle."""
    style: dict[str, str] = {}
    if part.fill:
        style["background"] = part.fill
    if part.stroke:
        line = "dashed" if part.is_dashed else "solid"
        style["border"] = f"{px(part.stroke_width)} {line} {part.stroke}"
    if part.kind is PartKind.CIRCLE:
        style["border-radius"] = "50%"
    elif part.radius:
        style["border-radius"] = px(part.radius)
    if part.opacity < 1:
        style["opacity"] = fmt(part.opacity)
    return style


def _text_html(part: Part, theme: Theme) -> str:
    """Draw a text centred in its box, or at its left edge."""
    family = theme.fonts.mono if part.is_mono else theme.fonts.sans
    style = {
        **_box_style(part),
        "display": "flex",
        "align-items": "center",
        "justify-content": JUSTIFY[part.align],
        "font-family": f"'{family}',{'monospace' if part.is_mono else 'sans-serif'}",
        "font-size": px(part.font_size),
        "font-weight": str(BOLD_WEIGHT if part.is_bold else REGULAR_WEIGHT),
        "line-height": fmt(TEXT_LINE_HEIGHT),
        "color": part.color,
        "white-space": "nowrap",
        "overflow": "hidden",
    }
    return tag("div", style, esc(part.text))


def _hatch_html(part: Part, theme: Theme) -> str:
    """Draw the hatched block: grey diagonal stripes in a dashed outline."""
    stripe = theme.screen.hatch_stripe
    light = theme.tones[Tone.GRAY].box
    stripes = (
        f"repeating-linear-gradient({HATCH_ANGLE_DEG}deg,{part.fill} 0 {px(stripe)},"
        f"{light} {px(stripe)} {px(2 * stripe)})"
    )
    style = {**_box_style(part), **_paint_style(part), "background": stripes}
    return tag("div", style)


def _arc_html(part: Part) -> str:
    """Draw a quarter of a ring, the moving part of a spinner."""
    size = part.bounds[2]
    radius = (size - part.stroke_width) / 2
    start = math.radians(ARC_START_DEG)
    end = start + 2 * math.pi * ARC_SPAN_FRACTION
    centre = size / 2
    begin = (centre + radius * math.cos(start), centre + radius * math.sin(start))
    finish = (centre + radius * math.cos(end), centre + radius * math.sin(end))
    sweep = f"A{fmt(radius)} {fmt(radius)} 0 0 1 {fmt(finish[0])} {fmt(finish[1])}"
    path = f"M{fmt(begin[0])} {fmt(begin[1])}{sweep}"
    svg = (
        f'<svg width="{fmt(size)}" height="{fmt(size)}" viewBox="0 0 {fmt(size)} {fmt(size)}" '
        'style="display:block">'
        f'<path d="{path}" fill="none" stroke="{part.stroke}" '
        f'stroke-width="{fmt(part.stroke_width)}" stroke-linecap="round"/></svg>'
    )
    return tag("div", {**_box_style(part)}, svg)


def _path_html(part: Part) -> str:
    """Draw an SVG path in its box: a chevron, a cross, a check or a hamburger."""
    _, _, width, height = part.bounds
    paint = (
        f'fill="{part.fill or "none"}" stroke="{part.stroke or "none"}" '
        f'stroke-width="{fmt(part.stroke_width)}" stroke-linecap="round" stroke-linejoin="round"'
    )
    size = f'width="{fmt(width)}" height="{fmt(height)}" viewBox="0 0 {fmt(width)} {fmt(height)}"'
    svg = f'<svg {size} style="display:block"><path d="{part.path}" {paint}/></svg>'
    return tag("div", {**_box_style(part)}, svg)


def _part_html(part: Part, theme: Theme) -> str:
    """Draw one part of a screen."""
    if part.kind is PartKind.TEXT:
        return _text_html(part, theme)
    if part.kind is PartKind.HATCH:
        return _hatch_html(part, theme)
    if part.kind is PartKind.ARC:
        return _arc_html(part)
    if part.kind is PartKind.PATH:
        return _path_html(part)
    if part.kind is PartKind.ICON:
        place = f'style="position:absolute;left:{px(part.bounds[0])};top:{px(part.bounds[1])}"'
        return icon_svg(part.icon, part.bounds[2], part.stroke or theme.ink, place)
    return tag("div", {**_box_style(part), **_paint_style(part)})
