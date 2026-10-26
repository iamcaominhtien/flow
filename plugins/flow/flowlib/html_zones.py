"""Draw the frames of cloud and architecture diagrams as HTML.

A cloud frame is tinted with its own colour, solid or dashed by kind, with a pill in that colour
on its top edge. An architecture layer is the same shape with a dark pill. Tints are see-through
so that a frame inside another one shows as a darker area of the same family.
"""

from .markup import esc, px, tag
from .model import Frame, FrameVariant
from .sizing import estimate_text_width
from .theme import Theme

ABSOLUTE = {"position": "absolute"}
PILL_RADIUS_PX = 999
PILL_PADDING_PX = 12
HEX_DIGITS = 2
RGB_START = 1
RGB_PARTS = 3
BYTE_MAX = 255
ZONE_VARIANTS = (FrameVariant.NETWORK, FrameVariant.LAYER)


def zone_html(frame: Frame, theme: Theme) -> str:
    """Draw a cloud frame or an architecture layer with its pill.

    Args:
        frame: A frame whose variant is ``NETWORK`` or ``LAYER``.
        theme: The design tokens.

    Returns:
        The markup of the frame and of its label.
    """
    tone = theme.tones[frame.tone]
    rules = theme.cloud
    style = "solid" if frame.is_solid else "dashed"
    area = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "width": px(frame.width),
        "height": px(frame.height),
        "box-sizing": "border-box",
        "background": tint(tone.stroke, rules.tint_alpha),
        "border": f"{px(rules.border_width)} {style} {tone.stroke}",
        "border-radius": px(theme.style.frame_radius),
    }
    html = tag("div", area, data_id=frame.id)
    if not frame.label:
        return html
    fill = theme.ink if frame.variant is FrameVariant.LAYER else tone.accent
    return html + _pill_html(frame, fill, theme)


def pill_width(label: str, theme: Theme) -> float:
    """Return the width of the pill that carries a frame's name."""
    return (
        estimate_text_width(label, theme.layout, theme.type_scale.pill.size) + 2 * PILL_PADDING_PX
    )


def tint(color: str, alpha: float) -> str:
    """Return a ``#RRGGBB`` colour as a see-through ``rgba`` colour."""
    channels = [
        int(color[RGB_START + HEX_DIGITS * i : RGB_START + HEX_DIGITS * (i + 1)], 16)
        for i in range(RGB_PARTS)
    ]
    return f"rgba({channels[0]},{channels[1]},{channels[2]},{alpha})"


def _pill_html(frame: Frame, fill: str, theme: Theme) -> str:
    """Draw the pill on the top edge of a frame, at its left."""
    rules = theme.cloud
    pill = {
        **ABSOLUTE,
        "left": px(frame.x + rules.pill_inset),
        "top": px(frame.y - rules.pill_height / 2),
        "height": px(rules.pill_height),
        "padding": f"0 {px(PILL_PADDING_PX)}",
        "box-sizing": "border-box",
        "border-radius": px(PILL_RADIUS_PX),
        "background": fill,
        "color": theme.on_accent,
        "font-size": px(theme.type_scale.pill.size),
        "font-weight": str(theme.type_scale.pill.weight),
        "line-height": px(rules.pill_height),
        "white-space": "nowrap",
    }
    return tag("div", pill, esc(frame.label or ""))
