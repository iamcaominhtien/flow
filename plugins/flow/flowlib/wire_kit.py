"""The small pieces every wireframe block is drawn from: bars, boxes, chips, text and anchors.

A block drawer returns its parts and the boxes of the parts that an annotation may point at. All
boxes are ``(x, y, width, height)`` in the pixels of the device, before the wireframe is shrunk.
"""

from dataclasses import dataclass, field

from .model import Device, ElementStyle, Tone, WireBlock
from .screen_part import Align, Bounds, Part, PartKind
from .sizing import estimate_text_width, wrap_text
from .theme import Theme, WireColors, WireRules

HALF = 2
WIDTH_SAFETY = 1.1  # the estimate of a text width is this much wider, so that bold text fits
WIDTH_PAD_PX = 4  # and this many pixels, which a short word needs most
TAP_FLAG = "tap"
PILL_FRACTION = 0.5  # of the height: the radius of a pill
CHECK_POINTS = ((0.2, 0.52), (0.42, 0.74), (0.8, 0.28))  # of the box: the corners of a check
CHEVRON_LEFT_PATH = "M9 1L2 8l7 7"
PLUS_PATH = "M1 6h10M6 1v10"
MINUS_PATH = "M1 6h10"


@dataclass(frozen=True)
class WireContext:
    """Everything a drawer needs besides the block: the theme, the device and the width."""

    theme: Theme
    device: Device
    is_plain: bool = (
        False  # the frame has no status bar, so a phone navbar is as tall as a desktop one
    )

    @property
    def rules(self) -> WireRules:
        """Return the wireframe rules of the theme."""
        return self.theme.wire

    @property
    def colors(self) -> WireColors:
        """Return the wireframe palette."""
        return self.theme.wire.colors

    @property
    def is_phone(self) -> bool:
        """Tell whether the screen is a phone, which has larger touch targets."""
        return self.device is Device.PHONE

    @property
    def gap(self) -> float:
        """Return the gap between two cards on this device."""
        return self.rules.gap[self.device.value]


@dataclass
class Drawn:
    """What a block drawer made: the parts, and the boxes of the named parts."""

    parts: list[Part] = field(default_factory=list)
    anchors: dict[str, Bounds] = field(default_factory=dict)


def text_width(text: str, size: float, ctx: WireContext) -> float:
    """Estimate the width of a line of text in the wireframe font, with room to spare for bold."""
    return estimate_text_width(text, ctx.theme.layout, size) * WIDTH_SAFETY + WIDTH_PAD_PX


def wrapped(text: str, width: float, size: float, ctx: WireContext) -> list[str]:
    """Break a text into lines that fit a width."""
    return wrap_text(text, ctx.theme.layout, width, size)


@dataclass(frozen=True)
class Line:
    """The colour and width of a border or a stroke."""

    color: str
    width: float = 1


@dataclass(frozen=True)
class Ink:
    """How a text is set: its size, its colour, its weight and where it sits in its box."""

    size: float
    color: str
    is_bold: bool = False
    align: Align = Align.LEFT
    is_mono: bool = False


def rect(box: Bounds, fill: str | None, line: Line | None = None, radius: float = 0) -> Part:
    """Make a rectangle part with an optional border."""
    return Part(
        PartKind.RECT,
        box,
        fill=fill,
        stroke=line.color if line else None,
        stroke_width=line.width if line else 1,
        radius=radius,
    )


def pill(box: Bounds, fill: str | None, line: Line | None = None) -> Part:
    """Make a rectangle whose ends are half circles."""
    return rect(box, fill, line, box[3] * PILL_FRACTION)


def circle(box: Bounds, fill: str | None, line: Line | None = None) -> Part:
    """Make a circle part, with a border when it has a line."""
    return Part(
        PartKind.CIRCLE,
        box,
        fill=fill,
        stroke=line.color if line else None,
        stroke_width=line.width if line else 1,
    )


def dashed_circle(box: Bounds, fill: str, line: Line) -> Part:
    """Make a circle with a dashed border, as the empty-state icon is."""
    return Part(
        PartKind.CIRCLE,
        box,
        fill=fill,
        stroke=line.color,
        stroke_width=line.width,
        is_dashed=True,
    )


def label(box: Bounds, text: str, ink: Ink) -> Part:
    """Make a text part; a text is one line, so a long text is wrapped before."""
    return Part(
        PartKind.TEXT,
        box,
        text=text,
        font_size=ink.size,
        is_bold=ink.is_bold,
        is_mono=ink.is_mono,
        color=ink.color,
        align=ink.align,
    )


def stroke_path(box: Bounds, path: str, line: Line) -> Part:
    """Make a stroked path part."""
    return Part(PartKind.PATH, box, stroke=line.color, stroke_width=line.width, path=path)


def icon(box: Bounds, name: str, color: str) -> Part:
    """Make an icon part; a name that is not an icon is drawn as a grey square by the caller."""
    return Part(PartKind.ICON, box, stroke=color, icon=name)


def bar(box: Bounds, color: str) -> Part:
    """Make a grey bar, the stand-in for a line of text."""
    return pill(box, color)


def cross_box(box: Bounds, ctx: WireContext, radius: float) -> list[Part]:
    """Make an image placeholder: a tinted box with its two diagonals."""
    colors = ctx.colors
    _, _, width, height = box
    diagonals = f"M0 0L{width:g} {height:g}M{width:g} 0L0 {height:g}"
    return [
        rect(box, colors.image, Line(colors.line), radius),
        stroke_path(box, diagonals, Line(colors.cross)),
    ]


def chip_colors(tone: Tone | None, ctx: WireContext) -> tuple[str, str]:
    """Return the fill and the text colour of a status chip; only these tones carry colour."""
    colors = ctx.colors
    table = {
        Tone.GREEN: (colors.green_tint, colors.green),
        Tone.AMBER: (colors.amber_tint, colors.amber),
        Tone.RED: (colors.rose_tint, colors.rose),
        Tone.BLUE: (colors.blue_tint, colors.blue),
    }
    return table.get(tone, (colors.gray_tint, colors.chip_text)) if tone else table[Tone.BLUE]


def chip_width(text: str, ctx: WireContext) -> float:
    """Return the width of a status chip that holds a text."""
    rules = ctx.rules
    return text_width(text, rules.chip_font, ctx) + 2 * rules.chip_pad


def chip_parts(box: Bounds, text: str, tone: Tone | None, ctx: WireContext) -> list[Part]:
    """Make a status chip: a tinted pill with a bold word in the colour of its tone."""
    fill, color = chip_colors(tone, ctx)
    ink = Ink(ctx.rules.chip_font, color, is_bold=True, align=Align.CENTER)
    return [pill(box, fill), label(box, text, ink)]


def button_colors(style: ElementStyle, ctx: WireContext) -> tuple[str, str | None, str]:
    """Return the fill, the border and the text colour of a button of a style."""
    colors = ctx.colors
    table = {
        ElementStyle.PRIMARY: (colors.blue, None, colors.on_blue),
        ElementStyle.SECONDARY: (colors.paper, colors.blue, colors.blue),
        ElementStyle.OUTLINE: (colors.paper, colors.blue, colors.blue),
        ElementStyle.DANGER: (colors.paper, colors.rose, colors.rose),
        ElementStyle.DISABLED: (colors.fill, colors.line, colors.muted),
        ElementStyle.FIELD: (colors.paper, colors.line, colors.muted),
    }
    return table[style]


def button_parts(box: Bounds, text: str, style: ElementStyle, ctx: WireContext) -> list[Part]:
    """Make a button: filled blue for the primary action, outlined for every other one."""
    fill, border, color = button_colors(style, ctx)
    rules = ctx.rules
    radius = min(rules.button_radius, box[3] / HALF)
    line = Line(border, rules.button_border) if border else None
    ink = Ink(rules.button_font, color, is_bold=True, align=Align.CENTER)
    return [rect(box, fill, line, radius), label(box, text, ink)]


def inset(box: Bounds, pad: float) -> Bounds:
    """Shrink a box by a padding on every side."""
    x, y, width, height = box
    return (x + pad, y + pad, max(width - 2 * pad, 0), max(height - 2 * pad, 0))


def card_box(box: Bounds, ctx: WireContext, *, is_selected: bool = False) -> Part:
    """Make the white card with a light border that most blocks sit on."""
    colors, rules = ctx.colors, ctx.rules
    if is_selected:
        return rect(box, colors.paper, Line(colors.blue, rules.selected_border), rules.card_radius)
    return rect(box, colors.paper, Line(colors.line), rules.card_radius)


def middle(box: Bounds, height: float) -> float:
    """Return the top of a part of a given height centred vertically in a box."""
    return box[1] + (box[3] - height) / HALF


def has_flag(block: WireBlock, flag: str) -> bool:
    """Tell whether a block carries a flag such as ``back`` or ``tap``."""
    return flag in block.flags


def line_height(size: float, ctx: WireContext) -> float:
    """Return the height of one line of text of a font size."""
    return size * ctx.rules.line_factor


def tap_parts(box: Bounds, ctx: WireContext) -> list[Part]:
    """Make the red dot with a halo near the right end of the target that is tapped.

    It sits on the target and off the label (design 10 section 3), the same dot as a screen flow.
    """
    rules, screen = ctx.rules, ctx.theme.screen
    is_narrow = box[2] < rules.tap_narrow
    centre_x = (
        box[0] + box[2] - (rules.tap_edge if is_narrow else rules.halo_radius + rules.tap_inset)
    )
    centre_y = box[1] + box[3] / HALF
    halo = (
        centre_x - rules.halo_radius,
        centre_y - rules.halo_radius,
        2 * rules.halo_radius,
        2 * rules.halo_radius,
    )
    dot = (
        centre_x - rules.dot_radius,
        centre_y - rules.dot_radius,
        2 * rules.dot_radius,
        2 * rules.dot_radius,
    )
    return [
        circle(halo, screen.halo_color),
        circle(dot, screen.hotspot_color, Line(ctx.colors.paper, rules.dot_ring)),
    ]


def add_tap(drawn: Drawn, block: WireBlock, target: Bounds, ctx: WireContext) -> None:
    """Add the tap dot to a drawing when the block says that its target is tapped."""
    if has_flag(block, TAP_FLAG):
        drawn.parts.extend(tap_parts(target, ctx))


def check_path(width: float, height: float) -> str:
    """Return the path of a check mark that fills a box of a size."""
    corners = [f"{width * across:g} {height * down:g}" for across, down in CHECK_POINTS]
    return "M" + "L".join(corners)
