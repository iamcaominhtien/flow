"""Draw the frames of BPMN pools and of an opened DFD process as HTML."""

from .html_zones import ZONE_VARIANTS, zone_html
from .markup import esc, px, tag
from .model import Frame, FrameVariant
from .theme import Theme

ABSOLUTE = {"position": "absolute"}
POOL_BORDER_PX = 1.5
POOL_RADIUS_PX = 6
BAND_FONT_SIZE_PX = 13
OPENED_BORDER_PX = 1.5
OPENED_DASH = "dashed"
OPENED_PILL_HEIGHT_PX = 22
OPENED_PILL_PADDING_PX = 12
OPENED_PILL_FONT_SIZE_PX = 11
PILL_RADIUS_PX = 999
BAND_VARIANTS = (
    FrameVariant.POOL,
    FrameVariant.BLACK_BOX,
    FrameVariant.OPENED,
    FrameVariant.SYSTEM,
    *ZONE_VARIANTS,
)
SYSTEM_RADIUS_PX = 16
SYSTEM_LABEL_LEFT_PX = 20
SYSTEM_LABEL_TOP_PX = 14
SYSTEM_LABEL_FONT_SIZE_PX = 15


def frame_with_band_html(frame: Frame, theme: Theme) -> str:
    """Draw a pool, a black-box pool or an opened-process frame.

    Args:
        frame: A frame whose variant is one of ``BAND_VARIANTS``.
        theme: The design tokens.

    Returns:
        The markup of the frame and its label.
    """
    if frame.variant in ZONE_VARIANTS:
        return zone_html(frame, theme)
    if frame.variant is FrameVariant.POOL:
        return _pool_html(frame, theme)
    if frame.variant is FrameVariant.BLACK_BOX:
        return _black_box_html(frame, theme)
    if frame.variant is FrameVariant.SYSTEM:
        return _system_html(frame, theme)
    return _opened_html(frame, theme)


def _box(frame: Frame) -> dict[str, str]:
    """Return the position and size of a frame as CSS."""
    return {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "width": px(frame.width),
        "height": px(frame.height),
        "box-sizing": "border-box",
    }


def _pool_html(frame: Frame, theme: Theme) -> str:
    """Draw a pool: a white box with a coloured band on the left that carries the name."""
    tone = theme.tones[frame.tone]
    ink = theme.ink
    area = {
        **_box(frame),
        "background": theme.paper,
        "border": f"{px(POOL_BORDER_PX)} solid {ink}",
    }
    band = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "width": px(theme.bpmn.band_width),
        "height": px(frame.height),
        "box-sizing": "border-box",
        "background": tone.pill,
        "border": f"{px(POOL_BORDER_PX)} solid {ink}",
        "color": ink,
        "font-size": px(BAND_FONT_SIZE_PX),
        "font-weight": "700",
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        "writing-mode": "vertical-rl",
        "transform": "rotate(180deg)",
        "overflow": "hidden",
    }
    return tag("div", area, data_id=frame.id) + tag("div", band, esc(frame.label or ""))


def _black_box_html(frame: Frame, theme: Theme) -> str:
    """Draw a black-box pool: a filled bar with its name in the middle."""
    area = {
        **_box(frame),
        "background": theme.tones[frame.tone].pill,
        "border": f"{px(POOL_BORDER_PX)} solid {theme.ink}",
        "border-radius": px(POOL_RADIUS_PX),
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        "color": theme.ink,
        "font-size": px(BAND_FONT_SIZE_PX),
        "font-weight": "700",
    }
    return tag("div", area, esc(frame.label or ""), data_id=frame.id)


def _opened_html(frame: Frame, theme: Theme) -> str:
    """Draw the dashed frame around an opened process, with its name in a pill at the bottom."""
    tone = theme.tones[frame.tone]
    rules = theme.dfd
    area = {
        **_box(frame),
        "background": tone.lane,
        "border": f"{px(OPENED_BORDER_PX)} {OPENED_DASH} {tone.stroke}",
        "border-radius": px(theme.style.frame_radius),
    }
    pill = {
        **ABSOLUTE,
        "left": px(frame.x + rules.frame_pill_inset),
        "top": px(frame.y + frame.height - rules.frame_pill_height / 2),
        "height": px(rules.frame_pill_height),
        "padding": f"0 {px(OPENED_PILL_PADDING_PX)}",
        "box-sizing": "border-box",
        "border-radius": px(PILL_RADIUS_PX),
        "background": tone.accent,
        "color": theme.on_accent,
        "font-size": px(OPENED_PILL_FONT_SIZE_PX),
        "font-weight": "700",
        "line-height": px(rules.frame_pill_height),
        "white-space": "nowrap",
    }
    return tag("div", area, data_id=frame.id) + tag("div", pill, esc(frame.label or ""))


def _system_html(frame: Frame, theme: Theme) -> str:
    """Draw the system of a use case diagram: a white box with its name at the top left."""
    area = {
        **_box(frame),
        "background": theme.paper,
        "border": f"{px(POOL_BORDER_PX)} solid {theme.ink}",
        "border-radius": px(SYSTEM_RADIUS_PX),
    }
    name = {
        **ABSOLUTE,
        "left": px(frame.x + SYSTEM_LABEL_LEFT_PX),
        "top": px(frame.y + SYSTEM_LABEL_TOP_PX),
        "color": theme.ink,
        "font-size": px(SYSTEM_LABEL_FONT_SIZE_PX),
        "font-weight": "700",
        "white-space": "nowrap",
    }
    return tag("div", area, data_id=frame.id) + tag("div", name, esc(frame.label or ""))
