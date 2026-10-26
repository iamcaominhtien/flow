"""Draw what is inside a device frame: the skeleton of L1, the key elements of L2, an overlay.

L3 is drawn as L2 for now: the wireframe blocks of design 10 are not placed inside a screen yet.
"""

from dataclasses import dataclass

from .model import (
    Content,
    ElementStyle,
    Fidelity,
    Layer,
    Overlay,
    Placement,
    ScreenElement,
    ScreenView,
    Tone,
)
from .screen_part import Align, Bounds, Part, PartKind
from .theme import ScreenRules, Theme

CONTENT_TBD_TEXT = "content TBD"
MIN_DOT_WIDTH_PX = 56  # a narrower element has no room for the red dot beside its name
ELEMENT_BORDER_PX = 1.5
ELEMENT_TEXT_INSET_PX = 6
HOTSPOT_RING_PX = 1.5
SKELETON_BAR_WIDTHS = (1.0, 0.7)  # of the body width, for the two lines under the title
TITLE_GAP_PX = 9
GLYPH_SIZE_PX = 22
GLYPH_TEXT_SIZE_PX = 24
ILLUSTRATION_GAP_PX = 8
NAME_HEIGHT_PX = 14
NAME_SIZE_PX = 11
SPLASH_RADIUS_PX = 10
BAR_SHORT_PX = 40
BAR_WIDTHS_PX = (60, 40)
SPLASH_BAR_HEIGHT_PX = 4
SPINNER_PX = 28
SPINNER_STROKE_PX = 3
SPINNER_BAR_HEIGHT_PX = 18
SPINNER_BAR_COUNT = 3
EMPTY_BOX_PX = 36
EMPTY_CAPTION_GAP_PX = 6
MIN_BLOCK_HEIGHT_PX = 20
MODAL_WIDTH_FRACTION = 0.84
MODAL_BUTTON_GAP_PX = 6
MODAL_TITLE_HEIGHT_PX = 14
SHEET_HANDLE_WIDTH_PX = 24
SHEET_HANDLE_HEIGHT_PX = 3
SHEET_ROW_HEIGHT_PX = 24
SHEET_RADIUS_PX = 10
TOAST_HEIGHT_PX = 24
TOAST_GAP_PX = 6
TOAST_WIDTH_FRACTION = 0.8
TAB_RADIUS_PX = 10
TAB_BORDER_PX = 1.5
CHECK_ICON = "check"
ERROR_GLYPH = "!"


@dataclass(frozen=True)
class BodyFrame:
    """The screen being drawn: its view, the design tokens, its size and where its body starts."""

    view: ScreenView
    theme: Theme
    width: float
    height: float
    origin: tuple[float, float]

    @property
    def rules(self) -> ScreenRules:
        """Return the screen flow rules of the theme."""
        return self.theme.screen

    @property
    def left(self) -> float:
        """Return the left edge of the body."""
        return self.origin[0]

    @property
    def right(self) -> float:
        """Return the right edge of the body."""
        return self.width - self.rules.inner_pad

    @property
    def bottom(self) -> float:
        """Return the bottom edge of the body."""
        return self.height - self.rules.inner_pad

    @property
    def span(self) -> float:
        """Return the width of the body."""
        return self.right - self.left

    @property
    def middle(self) -> float:
        """Return the x of the centre line of the body."""
        return (self.left + self.right) / 2


def body_parts(frame: BodyFrame) -> list[Part]:
    """Return the parts of the body of a screen and of its overlay, back to front.

    Args:
        frame: The screen being drawn.

    Returns:
        The parts, in drawing order.
    """
    view = frame.view
    parts = _skeleton_parts(frame) if view.fidelity is Fidelity.L1 else _key_parts(frame)
    if view.overlay is not None:
        parts.extend(_overlay_parts(frame))
    return parts


def _plain_text(frame: BodyFrame, bounds: Bounds, text: str) -> Part:
    """Make a centred text part in the small grey type of a placeholder."""
    return Part(
        PartKind.TEXT, bounds, text=text, font_size=frame.rules.text_size, color=frame.theme.slate
    )


def _bold_text(frame: BodyFrame, bounds: Bounds, text: str, size: float) -> Part:
    """Make a centred bold ink text part."""
    return Part(
        PartKind.TEXT, bounds, text=text, font_size=size, is_bold=True, color=frame.theme.ink
    )


def _title_parts(frame: BodyFrame, top: float) -> tuple[list[Part], float]:
    """Draw the name of the screen at the top left of its body.

    Returns:
        The part, and the y below it.
    """
    rules = frame.rules
    bounds = (frame.left, top, frame.span, rules.title_size + 3)
    title = Part(
        PartKind.TEXT,
        bounds,
        text=frame.view.title,
        font_size=rules.title_size,
        is_bold=True,
        color=frame.theme.ink,
        align=Align.LEFT,
    )
    return [title], top + rules.title_size + TITLE_GAP_PX


def _bar(frame: BodyFrame, bounds: Bounds, fill: str) -> Part:
    """Draw a rounded grey bar, the stand-in for a line of text."""
    return Part(PartKind.RECT, bounds, fill=fill, radius=bounds[3] / 2)


def _skeleton_parts(frame: BodyFrame) -> list[Part]:
    """Draw L1: the same generic content on every screen, and "content TBD"."""
    rules, theme = frame.rules, frame.theme
    parts, top = _title_parts(frame, frame.origin[1])
    for fraction in SKELETON_BAR_WIDTHS:
        bounds = (frame.left, top, frame.span * fraction, rules.bar_height)
        parts.append(_bar(frame, bounds, theme.rule))
        top += rules.bar_height + rules.bar_gap
    foot = frame.bottom - rules.element_height
    block = (frame.left, top + rules.bar_gap, frame.span, max(foot - top - 2 * rules.bar_gap, 0))
    gray = theme.tones[Tone.GRAY]
    parts.append(
        Part(
            PartKind.RECT,
            block,
            fill=gray.box,
            stroke=gray.stroke,
            radius=rules.element_radius - 1,
            is_dashed=True,
        )
    )
    parts.append(_plain_text(frame, block, CONTENT_TBD_TEXT))
    base = (frame.left, foot, frame.span, rules.element_height)
    parts.append(Part(PartKind.RECT, base, fill=theme.row_rule, radius=rules.element_radius))
    return parts


def _key_parts(frame: BodyFrame) -> list[Part]:
    """Draw L2: the named elements, the rest of the screen hatched or illustrated."""
    view, rules = frame.view, frame.rules
    elements = [element for element in view.elements if element.layer is Layer.BASE]
    parts: list[Part] = []
    top = frame.origin[1]
    if view.content not in (Content.SPLASH, Content.SUCCESS, Content.ERROR):
        parts, top = _title_parts(frame, top)
    tops = [e for e in elements if e.placement is Placement.TOP]
    bottoms = [e for e in elements if e.placement is Placement.BOTTOM]
    for element in tops:
        parts.extend(_element_parts(frame, (frame.left, top), element))
        top += rules.element_height + rules.element_gap
    floor = frame.bottom
    if view.tab_active is not None:
        parts.extend(_tab_bar_parts(frame))
        floor -= rules.tab_height + rules.element_gap
    for element in reversed(bottoms):
        floor -= rules.element_height
        parts.extend(_element_parts(frame, (frame.left, floor), element))
        floor -= rules.element_gap
    parts.extend(_content_parts(frame, (top, floor)))
    return parts


def _content_parts(frame: BodyFrame, area: tuple[float, float]) -> list[Part]:
    """Draw the body between the top elements and the bottom ones."""
    top, floor = area
    height = max(floor - top, MIN_BLOCK_HEIGHT_PX)
    content = frame.view.content
    if content is Content.HATCH:
        return _hatch_parts(frame, (top, height))
    if content is Content.LOADING:
        return _loading_parts(frame, (top, height))
    if content is Content.EMPTY:
        return _empty_parts(frame, (top, height))
    return _illustration_parts(frame, (top, height))


def _hatch_parts(frame: BodyFrame, area: tuple[float, float]) -> list[Part]:
    """Draw the hatched block that stands for everything that is not named."""
    top, height = area
    bounds = (frame.left, top, frame.span, height)
    hatch = Part(
        PartKind.HATCH,
        bounds,
        fill=frame.theme.row_rule,
        stroke=frame.theme.tones[Tone.GRAY].stroke,
        radius=frame.rules.element_radius - 1,
        is_dashed=True,
    )
    return [hatch, _plain_text(frame, bounds, frame.view.hatch_label)]


def _illustration_parts(frame: BodyFrame, area: tuple[float, float]) -> list[Part]:
    """Draw a splash, a success or an error: a symbol, the name under it and grey bars."""
    top, height = area
    rules, theme = frame.rules, frame.theme
    symbol = rules.illustration
    bars = len(BAR_WIDTHS_PX) if frame.view.content is not Content.SPLASH else 0
    stack = (
        symbol + ILLUSTRATION_GAP_PX + NAME_HEIGHT_PX + bars * (rules.bar_height + rules.bar_gap)
    )
    start = top + max((height - stack) / 2, 0)
    box = (frame.middle - symbol / 2, start, symbol, symbol)
    parts = _symbol_parts(frame, box)
    name_top = start + symbol + ILLUSTRATION_GAP_PX
    parts.append(
        _bold_text(
            frame,
            (frame.left, name_top, frame.span, NAME_HEIGHT_PX),
            frame.view.title,
            NAME_SIZE_PX,
        )
    )
    bar_top = name_top + NAME_HEIGHT_PX + rules.bar_gap
    for width in BAR_WIDTHS_PX[:bars]:
        bar = (frame.middle - width / 2, bar_top, width, rules.bar_height)
        parts.append(_bar(frame, bar, theme.rule))
        bar_top += rules.bar_height + rules.bar_gap
    if frame.view.content is Content.SPLASH:
        base = (
            frame.middle - BAR_SHORT_PX / 2,
            frame.bottom - SPLASH_BAR_HEIGHT_PX,
            BAR_SHORT_PX,
            SPLASH_BAR_HEIGHT_PX,
        )
        parts.append(_bar(frame, base, theme.rule))
    return parts


def _symbol_parts(frame: BodyFrame, box: Bounds) -> list[Part]:
    """Draw the symbol of an illustrated screen: a logo, a check or an alert."""
    theme = frame.theme
    content = frame.view.content
    if content is Content.SPLASH:
        accent = theme.tones[Tone.BLUE].accent
        return [Part(PartKind.RECT, box, fill=accent, radius=SPLASH_RADIUS_PX)]
    tone = theme.tones[Tone.GREEN if content is Content.SUCCESS else Tone.RED]
    ring = Part(PartKind.CIRCLE, box, fill=tone.box, stroke=tone.accent, stroke_width=2)
    if content is Content.SUCCESS:
        size = GLYPH_SIZE_PX
        place = (box[0] + (box[2] - size) / 2, box[1] + (box[3] - size) / 2, size, size)
        return [ring, Part(PartKind.ICON, place, stroke=tone.accent, icon=CHECK_ICON)]
    glyph = Part(
        PartKind.TEXT,
        box,
        text=ERROR_GLYPH,
        font_size=GLYPH_TEXT_SIZE_PX,
        is_bold=True,
        color=tone.accent,
    )
    return [ring, glyph]


def _loading_parts(frame: BodyFrame, area: tuple[float, float]) -> list[Part]:
    """Draw a spinner and three grey bars: data that has not arrived yet."""
    top, height = area
    rules, theme = frame.rules, frame.theme
    ring = (frame.middle - SPINNER_PX / 2, top + rules.bar_gap, SPINNER_PX, SPINNER_PX)
    accent = theme.tones[Tone.BLUE].accent
    parts = [
        Part(PartKind.CIRCLE, ring, stroke=theme.row_rule, stroke_width=SPINNER_STROKE_PX),
        Part(PartKind.ARC, ring, stroke=accent, stroke_width=SPINNER_STROKE_PX),
    ]
    bar_top = ring[1] + SPINNER_PX + rules.element_gap
    for _ in range(SPINNER_BAR_COUNT):
        if bar_top + SPINNER_BAR_HEIGHT_PX > top + height:
            break
        bounds = (frame.left, bar_top, frame.span, SPINNER_BAR_HEIGHT_PX)
        parts.append(
            Part(PartKind.RECT, bounds, fill=theme.row_rule, radius=rules.element_radius - 1)
        )
        bar_top += SPINNER_BAR_HEIGHT_PX + rules.element_gap
    return parts


def _empty_parts(frame: BodyFrame, area: tuple[float, float]) -> list[Part]:
    """Draw an empty state: a dashed box and a line of text under it."""
    top, height = area
    rules, theme = frame.rules, frame.theme
    stack = EMPTY_BOX_PX + EMPTY_CAPTION_GAP_PX + NAME_HEIGHT_PX
    start = top + max((height - stack) / 2, 0)
    gray = theme.tones[Tone.GRAY]
    box = (frame.middle - EMPTY_BOX_PX / 2, start, EMPTY_BOX_PX, EMPTY_BOX_PX)
    parts = [
        Part(
            PartKind.RECT,
            box,
            fill=gray.box,
            stroke=gray.stroke,
            radius=rules.element_radius,
            is_dashed=True,
        )
    ]
    caption = (frame.left, start + EMPTY_BOX_PX + EMPTY_CAPTION_GAP_PX, frame.span, NAME_HEIGHT_PX)
    parts.append(_bold_text(frame, caption, frame.view.hatch_label, rules.text_size))
    return parts


def _tab_bar_parts(frame: BodyFrame) -> list[Part]:
    """Draw the tab bar at the foot of a screen: one dot per tab, the active one blue."""
    rules, theme = frame.rules, frame.theme
    count = frame.view.tab_count
    bar = (frame.left, frame.bottom - rules.tab_height, frame.span, rules.tab_height)
    parts = [
        Part(
            PartKind.RECT,
            bar,
            fill=theme.paper,
            stroke=theme.rule,
            stroke_width=TAB_BORDER_PX,
            radius=TAB_RADIUS_PX,
        )
    ]
    for index in range(count):
        centre = frame.left + frame.span * (index + 0.5) / count
        is_active = index == frame.view.tab_active
        fill = theme.tones[Tone.BLUE].accent if is_active else theme.rule
        dot = (centre - rules.tab_dot / 2, bar[1] + (rules.tab_height - rules.tab_dot) / 2)
        parts.append(Part(PartKind.RECT, (*dot, rules.tab_dot, rules.tab_dot), fill=fill, radius=3))
    return parts


def _element_colors(frame: BodyFrame, style: ElementStyle) -> tuple[str | None, str | None, str]:
    """Return the fill, the border and the text colour of an element style."""
    theme = frame.theme
    blue = theme.tones[Tone.BLUE]
    danger = theme.tones[Tone.RED]
    table = {
        ElementStyle.PRIMARY: (blue.accent, None, theme.on_accent),
        ElementStyle.SECONDARY: (blue.box, blue.accent, theme.ink),
        ElementStyle.OUTLINE: (theme.paper, blue.accent, blue.accent),
        ElementStyle.DANGER: (theme.paper, danger.accent, danger.accent),
        ElementStyle.FIELD: (theme.paper, theme.tones[Tone.GRAY].stroke, theme.slate),
    }
    return table[style]


def _element_parts(
    frame: BodyFrame, origin: tuple[float, float], element: ScreenElement
) -> list[Part]:
    """Draw one named element: its box, its name and, when it was tapped, the red dot."""
    rules = frame.rules
    box = (origin[0], origin[1], frame.span, rules.element_height)
    return _box_parts(frame, box, element)


def _box_parts(frame: BodyFrame, box: Bounds, element: ScreenElement) -> list[Part]:
    """Draw an element in a given box."""
    rules = frame.rules
    fill, border, color = _element_colors(frame, element.style)
    is_field = element.style is ElementStyle.FIELD
    parts = [
        Part(
            PartKind.RECT,
            box,
            fill=fill,
            stroke=border,
            stroke_width=ELEMENT_BORDER_PX,
            radius=rules.element_radius,
        )
    ]
    has_dot = element.is_hotspot and box[2] > MIN_DOT_WIDTH_PX
    room = 2 * rules.halo_radius if has_dot else 0
    text_box = (
        box[0] + ELEMENT_TEXT_INSET_PX,
        box[1],
        box[2] - 2 * ELEMENT_TEXT_INSET_PX - room,
        box[3],
    )
    parts.append(
        Part(
            PartKind.TEXT,
            text_box,
            text=element.text,
            font_size=rules.text_size,
            is_bold=not is_field,
            color=color,
            align=Align.LEFT if is_field else Align.CENTER,
        )
    )
    if has_dot:
        parts.extend(_hotspot_parts(frame, box))
    return parts


def _hotspot_parts(frame: BodyFrame, box: Bounds) -> list[Part]:
    """Draw the red dot with a halo on the right end of the element that was tapped."""
    rules = frame.rules
    centre_x = box[0] + box[2] - rules.halo_radius - 2
    centre_y = box[1] + box[3] / 2
    halo = (
        centre_x - rules.halo_radius,
        centre_y - rules.halo_radius,
        2 * rules.halo_radius,
        2 * rules.halo_radius,
    )
    dot = (
        centre_x - rules.hotspot_radius,
        centre_y - rules.hotspot_radius,
        2 * rules.hotspot_radius,
        2 * rules.hotspot_radius,
    )
    return [
        Part(PartKind.CIRCLE, halo, fill=rules.halo_color),
        Part(
            PartKind.CIRCLE,
            dot,
            fill=rules.hotspot_color,
            stroke=frame.theme.paper,
            stroke_width=HOTSPOT_RING_PX,
        ),
    ]


def _overlay_parts(frame: BodyFrame) -> list[Part]:
    """Draw the modal, the sheet or the toast that covers the screen."""
    overlay = frame.view.overlay
    elements = [e for e in frame.view.elements if e.layer is Layer.OVERLAY]
    if overlay is Overlay.TOAST:
        return _toast_parts(frame)
    parts = [_scrim_part(frame)]
    if overlay is Overlay.MODAL:
        return parts + _modal_parts(frame, elements)
    return parts + _sheet_parts(frame, elements)


def _scrim_part(frame: BodyFrame) -> Part:
    """Dim the whole screen under a modal or a sheet, so that the user's context stays visible."""
    inset = frame.rules.border / 2
    bounds = (inset, inset, frame.width - 2 * inset, frame.height - 2 * inset)
    radius = frame.rules.radius[frame.view.device.value] - inset
    return Part(
        PartKind.RECT,
        bounds,
        fill=frame.theme.ink,
        radius=radius,
        opacity=frame.rules.scrim_opacity,
    )


def _modal_parts(frame: BodyFrame, buttons: list[ScreenElement]) -> list[Part]:
    """Draw a modal: a white card with a title, two grey lines and a row of buttons."""
    rules, theme = frame.rules, frame.theme
    pad = rules.inner_pad
    width = frame.width * MODAL_WIDTH_FRACTION
    height = (
        2 * pad
        + MODAL_TITLE_HEIGHT_PX
        + 2 * (rules.bar_height + rules.bar_gap)
        + rules.element_height
    )
    left, top = (frame.width - width) / 2, (frame.height - height) / 2
    parts = [
        Part(
            PartKind.RECT, (left, top, width, height), fill=theme.paper, radius=rules.element_radius
        )
    ]
    title = (left + pad, top + pad, width - 2 * pad, MODAL_TITLE_HEIGHT_PX)
    parts.append(
        Part(
            PartKind.TEXT,
            title,
            text=frame.view.overlay_title,
            font_size=rules.text_size,
            is_bold=True,
            color=theme.ink,
            align=Align.LEFT,
        )
    )
    line_top = title[1] + MODAL_TITLE_HEIGHT_PX
    for _ in range(2):
        parts.append(
            _bar(frame, (left + pad, line_top, width - 2 * pad, rules.bar_height), theme.rule)
        )
        line_top += rules.bar_height + rules.bar_gap
    count = max(len(buttons), 1)
    each = (width - 2 * pad - (count - 1) * MODAL_BUTTON_GAP_PX) / count
    for index, element in enumerate(buttons):
        x = left + pad + index * (each + MODAL_BUTTON_GAP_PX)
        parts.extend(
            _box_parts(frame, (x, line_top + rules.bar_gap, each, rules.element_height), element)
        )
    return parts


def _sheet_parts(frame: BodyFrame, rows: list[ScreenElement]) -> list[Part]:
    """Draw a bottom sheet: a white panel with a handle and one row per element."""
    rules, theme = frame.rules, frame.theme
    pad = rules.inner_pad
    inset = rules.border / 2
    height = (
        pad + SHEET_HANDLE_HEIGHT_PX + pad + len(rows) * (SHEET_ROW_HEIGHT_PX + rules.element_gap)
    )
    top = frame.height - inset - height
    sheet = (inset, top, frame.width - 2 * inset, height)
    parts = [Part(PartKind.RECT, sheet, fill=theme.paper, radius=SHEET_RADIUS_PX)]
    handle = (
        frame.middle - SHEET_HANDLE_WIDTH_PX / 2,
        top + pad / 2,
        SHEET_HANDLE_WIDTH_PX,
        SHEET_HANDLE_HEIGHT_PX,
    )
    parts.append(_bar(frame, handle, theme.rule))
    row_top = top + pad + SHEET_HANDLE_HEIGHT_PX
    for element in rows:
        box = (frame.left, row_top, frame.span, SHEET_ROW_HEIGHT_PX)
        parts.extend(_box_parts(frame, box, element))
        row_top += SHEET_ROW_HEIGHT_PX + rules.element_gap
    return parts


def _toast_parts(frame: BodyFrame) -> list[Part]:
    """Draw a toast: a dark pill that dims nothing and leaves by itself."""
    rules, theme = frame.rules, frame.theme
    width = frame.width * TOAST_WIDTH_FRACTION
    bottoms = sum(
        1 for e in frame.view.elements if e.placement is Placement.BOTTOM and e.layer is Layer.BASE
    )
    lift = bottoms * (rules.element_height + rules.element_gap) + TOAST_GAP_PX
    box = ((frame.width - width) / 2, frame.bottom - lift - TOAST_HEIGHT_PX, width, TOAST_HEIGHT_PX)
    pill = Part(PartKind.RECT, box, fill=theme.ink, radius=TOAST_HEIGHT_PX / 2)
    text = Part(
        PartKind.TEXT,
        box,
        text=frame.view.overlay_title,
        font_size=rules.text_size,
        is_bold=True,
        color=theme.paper,
    )
    return [pill, text]
