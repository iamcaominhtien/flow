"""The drawing of a screen of a screen flow, as a list of simple parts shared by both renderers.

A part is a rectangle, a text, a circle, an icon, a hatched block or an arc, placed relative to
the top-left corner of the screen node. The HTML renderer turns each part into an element and the
draw.io renderer into a child cell, so both show the same screen (design 02 sections 1 and 2.3).
"""

from .model import ChipPlace, Device, Fidelity, Node, Orientation, ScreenView, Tone
from .screen_body import BodyFrame, body_parts
from .screen_capture import capture_parts
from .screen_part import Align, Bounds, Part, PartKind
from .theme import ScreenRules, Theme
from .wire_layout import natural_size, plan_screen, scale_parts

CHIP_FONT_SIZE_PX = 10
CHIP_CHAR_WIDTH_EM = 0.62  # of a mono font, with a margin
CARD_NAME_SIZE_PX = 13
CARD_NAME_CHAR_WIDTH_EM = 0.58
CARD_ICON_PX = 14
TAG_FONT_SIZE_PX = 8
TAG_HEIGHT_PX = 14
TAG_PADDING_PX = 6
TAG_GAP_PX = 8
TBD_TEXT = "TBD"
CARD_STROKE_PX = 2
DESKTOP_DOT_RADIUS_PX = 3
DESKTOP_DOT_FIRST_PX = 12
DESKTOP_DOT_STEP_PX = 8
DESKTOP_ADDRESS_LEFT_PX = 40
DESKTOP_ADDRESS_HEIGHT_PX = 8
DESKTOP_ADDRESS_RIGHT_PX = 12
BROWSER_TOP_GAP_PX = 8
WATCH_TOP_PX = 12
DEVICE_ICONS: dict[Device, str] = {
    Device.PHONE: "phone",
    Device.TABLET: "phone",
    Device.DESKTOP: "laptop",
    Device.WATCH: "clock",
}


def screen_size(view: ScreenView, theme: Theme) -> tuple[float, float]:
    """Return the width and height a screen is drawn at.

    Every fidelity level has the width of the device frame, so raising a screen from L0 to L2
    never moves an arrow; only a card (L0 or undecided) is lower than the frame.

    Args:
        view: What the screen shows.
        theme: The design tokens.

    Returns:
        The size in pixels.
    """
    rules = theme.screen
    if view.blocks and not is_card(view):
        width, height = natural_size(view, theme)
        return width * view.scale, height * view.scale
    width, height = rules.sizes[_size_key(view)]
    if is_card(view):
        return width, rules.card_height
    return width, height


def chip_width(text: str, theme: Theme) -> float:
    """Estimate the width of an id chip."""
    return len(text) * CHIP_CHAR_WIDTH_EM * CHIP_FONT_SIZE_PX + 2 * theme.screen.chip_padding


def screen_parts(node: Node, theme: Theme) -> list[Part]:
    """Return the parts that draw a screen node, back to front, including its id chip.

    Args:
        node: A node with a ``screen`` view.
        theme: The design tokens.

    Returns:
        The parts. L3 with ``blocks`` is a wireframe (design 10); without blocks it is L2. L4 shows
        its screenshot (``screen_capture``).
    """
    view = node.screen
    assert view is not None
    if is_card(view):
        return _card_parts(node, view, theme)
    if view.blocks:
        return _wire_parts(node, view, theme)
    frame = BodyFrame(view, theme, node.width, node.height, _body_origin(view, theme))
    parts = [_frame_part(node, theme), *_chrome_parts(node, view, theme)]
    body = capture_parts(frame) if view.fidelity is Fidelity.L4 else body_parts(frame)
    return [
        *parts,
        *body,
        _chip_part(node, view, theme),
        _chip_text(node, view, theme),
    ]


def _wire_parts(node: Node, view: ScreenView, theme: Theme) -> list[Part]:
    """Draw a screen that has wireframe blocks: its device, its blocks and its badges.

    The blocks are laid out at the real size of the device and shrunk to the node, so that a
    screen of a flow at L3 and a screen of a wireframe are the same drawing at two sizes.
    """
    plan = plan_screen(view, theme, (node.width / view.scale, node.height / view.scale))
    parts = scale_parts(plan.parts, view.scale)
    if view.is_captioned or view.is_bare:
        return parts
    return [*parts, _chip_part(node, view, theme), _chip_text(node, view, theme)]


def is_card(view: ScreenView) -> bool:
    """Tell whether a screen is drawn as a rounded card: nothing on it is decided."""
    return view.fidelity is Fidelity.L0 or view.is_undecided


def _size_key(view: ScreenView) -> str:
    """Return the name of the device size in the theme: phone, phone_landscape, tablet, ..."""
    is_wide = view.orientation is Orientation.LANDSCAPE
    if view.device is Device.PHONE and view.is_mini and not is_wide:
        return "phone_mini"
    if is_wide and view.device in (Device.PHONE, Device.TABLET):
        return f"{view.device.value}_landscape"
    return view.device.value


def _body_origin(view: ScreenView, theme: Theme) -> tuple[float, float]:
    """Return where the body of a screen starts: below the notch or the browser bar."""
    rules = theme.screen
    notch_room = rules.notch_top + rules.notch_height + rules.inner_pad
    if view.device is Device.DESKTOP:
        return rules.inner_pad, rules.browser_bar + BROWSER_TOP_GAP_PX
    if view.device is Device.WATCH:
        return rules.inner_pad, WATCH_TOP_PX
    if view.orientation is Orientation.LANDSCAPE:
        return notch_room, rules.inner_pad
    return rules.inner_pad, notch_room


def _frame_part(node: Node, theme: Theme) -> Part:
    """Draw the device frame: a 3 px ink border."""
    rules = theme.screen
    view = node.screen
    assert view is not None
    return Part(
        PartKind.RECT,
        (0, 0, node.width, node.height),
        fill=theme.paper,
        stroke=theme.ink,
        stroke_width=rules.border,
        radius=rules.radius[view.device.value],
    )


def _chrome_parts(node: Node, view: ScreenView, theme: Theme) -> list[Part]:
    """Draw what a device has besides the screen: a notch, or the bar of a browser."""
    rules = theme.screen
    if view.device is Device.WATCH:
        return []
    if view.device is Device.DESKTOP:
        return _browser_parts(node, rules, theme)
    if view.orientation is Orientation.LANDSCAPE:
        bounds = (
            rules.notch_top,
            (node.height - rules.notch_width) / 2,
            rules.notch_height,
            rules.notch_width,
        )
    else:
        bounds = (
            (node.width - rules.notch_width) / 2,
            rules.notch_top,
            rules.notch_width,
            rules.notch_height,
        )
    return [Part(PartKind.RECT, bounds, fill=theme.ink, radius=rules.notch_height / 2)]


def _browser_parts(node: Node, rules: ScreenRules, theme: Theme) -> list[Part]:
    """Draw the bar of a desktop browser: three dots and an address field."""
    inset = rules.border / 2
    corner = rules.radius[Device.DESKTOP.value] - inset
    middle = inset + rules.browser_bar / 2
    parts = [
        Part(
            PartKind.RECT,
            (inset, inset, node.width - 2 * inset, rules.browser_bar),
            fill=theme.tones[Tone.GRAY].box,
            radius=corner,
        )
    ]
    colors = (rules.dot_red, rules.dot_amber, rules.dot_green)
    for index, color in enumerate(colors):
        centre = DESKTOP_DOT_FIRST_PX + index * DESKTOP_DOT_STEP_PX
        left = centre - DESKTOP_DOT_RADIUS_PX
        diameter = 2 * DESKTOP_DOT_RADIUS_PX
        bounds = (left, middle - DESKTOP_DOT_RADIUS_PX, diameter, diameter)
        parts.append(Part(PartKind.CIRCLE, bounds, fill=color))
    address = (
        DESKTOP_ADDRESS_LEFT_PX,
        middle - DESKTOP_ADDRESS_HEIGHT_PX / 2,
        node.width - DESKTOP_ADDRESS_LEFT_PX - DESKTOP_ADDRESS_RIGHT_PX,
        DESKTOP_ADDRESS_HEIGHT_PX,
    )
    parts.append(
        Part(PartKind.RECT, address, fill=theme.paper, radius=DESKTOP_ADDRESS_HEIGHT_PX / 2)
    )
    return parts


def _chip_colors(node: Node, theme: Theme) -> tuple[str, str]:
    """Return the fill and text colour of the id chip: ink and teal, or the zone colour."""
    is_zone_tone = node.tone is not None and node.tone is not Tone.GRAY
    if is_zone_tone:
        return theme.tones[node.tone].accent, theme.on_accent
    return theme.badge.background, theme.badge.foreground


def chip_box(node: Node, view: ScreenView, theme: Theme) -> Bounds:
    """Return where the id chip sits: above a frame at a corner, or inside the corner of a card.

    Args:
        node: The screen node.
        view: Its screen.
        theme: The design tokens.

    Returns:
        The chip as ``(left, top, width, height)``, relative to the node.
    """
    rules = theme.screen
    width = chip_width(view.code, theme)
    if is_card(view):
        return (rules.inner_pad, rules.inner_pad, width, rules.chip_height)
    left = node.width - width if view.chip_place is ChipPlace.ABOVE_RIGHT else 0
    top = (
        node.height + rules.chip_gap
        if view.chip_place is ChipPlace.BELOW
        else -(rules.chip_height + rules.chip_gap)
    )
    return (left, top, width, rules.chip_height)


def _chip_part(node: Node, view: ScreenView, theme: Theme) -> Part:
    """Draw the id chip: a pill that names the screen."""
    fill = _chip_colors(node, theme)[0]
    if view.is_undecided:
        fill = theme.tones[Tone.GRAY].accent
    bounds = chip_box(node, view, theme)
    return Part(PartKind.RECT, bounds, fill=fill, radius=bounds[3] / 2)


def _chip_text(node: Node, view: ScreenView, theme: Theme) -> Part:
    """Draw the text of the id chip."""
    color = theme.on_accent if view.is_undecided else _chip_colors(node, theme)[1]
    return Part(
        PartKind.TEXT,
        chip_box(node, view, theme),
        text=view.code,
        font_size=CHIP_FONT_SIZE_PX,
        is_bold=True,
        is_mono=True,
        color=color,
    )


def _card_parts(node: Node, view: ScreenView, theme: Theme) -> list[Part]:
    """Draw an L0 card: id chip, device icon and name; dashed with a TBD tag when undecided."""
    rules = theme.screen
    card = Part(
        PartKind.RECT,
        (0, 0, node.width, node.height),
        fill=theme.paper,
        stroke=theme.slate if view.is_undecided else theme.ink,
        stroke_width=CARD_STROKE_PX,
        radius=rules.radius[Device.PHONE.value] - 2,
        is_dashed=view.is_undecided,
    )
    pad = rules.inner_pad
    icon = Part(
        PartKind.ICON,
        (node.width - pad - CARD_ICON_PX, pad, CARD_ICON_PX, CARD_ICON_PX),
        stroke=theme.ink,
        icon=DEVICE_ICONS[view.device],
    )
    name_top = node.height - pad - CARD_NAME_SIZE_PX - 4
    name_width = len(node.text[0]) * CARD_NAME_CHAR_WIDTH_EM * CARD_NAME_SIZE_PX if node.text else 0
    name = Part(
        PartKind.TEXT,
        (pad, name_top, node.width - 2 * pad, CARD_NAME_SIZE_PX + 4),
        text=" ".join(node.text),
        font_size=CARD_NAME_SIZE_PX,
        is_bold=True,
        color=theme.ink,
        align=Align.LEFT,
    )
    parts = [card, _chip_part(node, view, theme), _chip_text(node, view, theme), icon, name]
    if view.is_undecided:
        parts.extend(_tbd_parts(pad + name_width + TAG_GAP_PX, name_top + 2, theme))
    return parts


def _tbd_parts(left: float, top: float, theme: Theme) -> list[Part]:
    """Draw the amber TBD tag of an undecided screen."""
    amber = theme.tones[Tone.AMBER]
    width = len(TBD_TEXT) * CHIP_CHAR_WIDTH_EM * TAG_FONT_SIZE_PX + 2 * TAG_PADDING_PX
    bounds = (left, top, width, TAG_HEIGHT_PX)
    return [
        Part(PartKind.RECT, bounds, fill=amber.pill, radius=TAG_HEIGHT_PX / 2),
        Part(
            PartKind.TEXT,
            bounds,
            text=TBD_TEXT,
            font_size=TAG_FONT_SIZE_PX,
            is_bold=True,
            color=amber.label,
        ),
    ]
