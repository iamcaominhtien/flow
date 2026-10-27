"""Where the parts of an explainer node sit: the icon, the name, the text, the chips, the badge.

The HTML page (``html_explain``) and the draw.io file (``drawio_explain``) both draw what this
module lists, so the two outputs agree. Every position is in pixels from the top left of the node.
"""

from dataclasses import dataclass
from enum import StrEnum

from .model import Node, Shape, Tone
from .sizing import estimate_text_width
from .theme import ExplainerRules, Theme

EXPLAIN_SHAPES = (
    Shape.EXPLAIN_CARD,
    Shape.ROW_CARD,
    Shape.CELL,
    Shape.PILL_LABEL,
    Shape.REMARK,
    Shape.SECTION_HEAD,
)
COMPOSITE_SHAPES = (Shape.EXPLAIN_CARD, Shape.ROW_CARD, Shape.SECTION_HEAD)  # drawn from parts
OUTLINED_SHAPES = (Shape.EXPLAIN_CARD, Shape.ROW_CARD, Shape.CELL, Shape.PILL_LABEL)
PILL_RADIUS_PX = 999
EXPLAINER = "explainer"  # the ``Scene.diagram`` of an explainer
NAME_LINE_FACTOR = 1.3
DETAIL_LINES = 2  # a card holds two lines of text
ROW_ICON_GAP_PX = 20  # between the icon of a row and its text
ROW_RIGHT_PAD_PX = 18
CHIPS_LABEL = "inside:"
BADGE_PAD_PX = 14
HALF = 2
HEX_RED, HEX_GREEN, HEX_BLUE = 1, 3, 5  # where each channel starts in ``#RRGGBB``
PILL_BORDER_PADDING_PX = 4  # a pill is its text plus the border on both sides


class PartKind(StrEnum):
    """What a part of an explainer node is."""

    ICON = "icon"
    PILL = "pill"
    TEXT = "text"
    CIRCLE = "circle"


@dataclass(frozen=True)
class Part:
    """One thing drawn on a node, with its box relative to the node's top left."""

    kind: PartKind
    name: str  # the cell id prefix in draw.io: ``icon``, ``pill``, ``detail``...
    box: tuple[float, float, float, float]
    text: str = ""
    icon: str | None = None
    fill: str = ""
    color: str = ""
    font_size: float = 0
    is_bold: bool = False
    is_mono: bool = False
    is_centered: bool = False
    is_outlined: bool = False  # a pill or a circle with an ink border


@dataclass(frozen=True)
class Outline:
    """The box of a node: its tint, its border and the roundness of its corners."""

    fill: str
    radius: float
    has_shadow: bool = False  # the pill shadow: a solid ink line under the box


def is_explain_node(node: Node) -> bool:
    """Tell whether a node is drawn by ``html_explain`` and ``drawio_explain``."""
    return node.shape in EXPLAIN_SHAPES


def explain_rules(theme: Theme) -> ExplainerRules:
    """Return the rules of the explainer."""
    return theme.explainer


def outline_of(node: Node, theme: Theme) -> Outline | None:
    """Return the box of a node, or None for a node that has no box (text)."""
    rules = theme.explainer
    if node.shape not in OUTLINED_SHAPES:
        return None
    if node.shape is Shape.PILL_LABEL:
        fill = theme.tones[node.tone].box if node.tone else theme.ink
        return Outline(fill, PILL_RADIUS_PX, has_shadow=True)
    fill = theme.tones[node.tone or Tone.GRAY].box
    radius = {
        Shape.EXPLAIN_CARD: rules.card_radius,
        Shape.ROW_CARD: rules.row_radius,
        Shape.CELL: rules.cell_radius,
    }[node.shape]
    return Outline(fill, radius)


def pill_width(text: str, font_size: float, theme: Theme) -> float:
    """Return the width of a pill that holds a line of text."""
    rules = theme.explainer
    return estimate_text_width(text, theme.layout, font_size) + 2 * rules.pill_pad


def badge_width(text: str, theme: Theme) -> float:
    """Return the width of a number badge: a circle, or a pill when the number has a letter."""
    rules = theme.explainer
    wide = estimate_text_width(text, theme.layout, rules.badge_font) + BADGE_PAD_PX
    return max(rules.badge_size, wide)


def explain_parts(node: Node, theme: Theme) -> list[Part]:
    """List the parts drawn on a node of the explainer, in drawing order.

    Args:
        node: A node whose shape is in ``COMPOSITE_SHAPES``.
        theme: The design tokens.

    Returns:
        The parts; empty for a shape drawn as one cell.
    """
    if node.shape is Shape.EXPLAIN_CARD:
        return _card_parts(node, theme)
    if node.shape is Shape.ROW_CARD:
        return _row_parts(node, theme)
    if node.shape is Shape.SECTION_HEAD:
        return _head_parts(node, theme)
    return []


def _icon_stroke(node: Node, theme: Theme) -> str:
    """Return the line colour of a flat icon on a node of the explainer."""
    return theme.tones[node.tone or Tone.GRAY].stroke


def _card_parts(node: Node, theme: Theme) -> list[Part]:
    """List the icon, the name pill and the text of a vertical card."""
    rules = theme.explainer
    name = " ".join(node.text)
    wide = pill_width(name, rules.card_pill_font, theme)
    parts = []
    if node.icon:
        size = rules.card_icon_size
        parts.append(
            Part(
                PartKind.ICON,
                "icon",
                ((node.width - size) / HALF, rules.card_icon_top, size, size),
                icon=node.icon,
                color=_icon_stroke(node, theme),
            )
        )
    parts.append(
        Part(
            PartKind.PILL,
            "pill",
            ((node.width - wide) / HALF, rules.card_pill_top, wide, rules.card_pill_height),
            text=name,
            fill=theme.tones[node.tone or Tone.GRAY].pill,
            color=theme.ink,
            font_size=rules.card_pill_font,
            is_bold=True,
            is_centered=True,
            is_outlined=True,
        )
    )
    if node.detail:
        room = node.width - 2 * rules.card_pad
        parts.append(
            Part(
                PartKind.TEXT,
                "detail",
                (
                    rules.card_pad,
                    rules.card_detail_top,
                    room,
                    rules.card_detail_line * DETAIL_LINES,
                ),
                text=" ".join(node.detail),
                color=theme.slate,
                font_size=rules.card_detail_font,
                is_centered=True,
            )
        )
    return parts


def _row_icon_size(node: Node, theme: Theme) -> float:
    """Return the size of the icon of a row: large for a file or folder, smaller for a card."""
    rules = theme.explainer.standard
    return rules.row_icon if node.is_mono else rules.branch_icon


def row_text_left(node: Node, theme: Theme) -> float:
    """Return how far from the left edge the text of a row starts."""
    rules = theme.explainer
    if not node.icon:
        return rules.row_icon_inset
    return rules.row_icon_inset + _row_icon_size(node, theme) + ROW_ICON_GAP_PX


def _row_parts(node: Node, theme: Theme) -> list[Part]:
    """List the icon, the name, the text and the chips of a row card."""
    rules = theme.explainer
    parts = []
    if node.icon:
        size = _row_icon_size(node, theme)
        top = (node.height - size) / HALF
        parts.append(
            Part(
                PartKind.ICON,
                "icon",
                (rules.row_icon_inset, top, size, size),
                icon=node.icon,
                color=_icon_stroke(node, theme),
            )
        )
    chips = _chip_parts(node, theme)
    left = row_text_left(node, theme)
    room = (min([part.box[0] for part in chips], default=node.width) - ROW_RIGHT_PAD_PX) - left
    name_font = rules.row_name_font if node.is_mono else rules.card_pill_font
    name_height = name_font * NAME_LINE_FACTOR
    block = (
        name_height + rules.row_detail_gap + rules.card_detail_line * _lines_of(node, room, theme)
    )
    top = (node.height - block) / HALF
    parts.append(
        Part(
            PartKind.TEXT,
            "name",
            (left, top, room, name_height),
            text=" ".join(node.text),
            color=theme.ink,
            font_size=name_font,
            is_bold=True,
            is_mono=node.is_mono,
        )
    )
    parts.append(
        Part(
            PartKind.TEXT,
            "detail",
            (
                left,
                top + name_height + rules.row_detail_gap,
                room,
                rules.card_detail_line * _lines_of(node, room, theme),
            ),
            text=" ".join(node.detail),
            color=theme.slate,
            font_size=rules.row_detail_font,
        )
    )
    return parts + chips


def _lines_of(node: Node, room: float, theme: Theme) -> int:
    """Return how many lines the text of a row takes at an estimated width."""
    rules = theme.explainer
    text = " ".join(node.detail)
    if not text:
        return 1
    width = estimate_text_width(text, theme.layout, rules.row_detail_font)
    return max(1, min(DETAIL_LINES, -(-int(width) // max(int(room), 1))))


def _chip_parts(node: Node, theme: Theme) -> list[Part]:
    """List the ``inside:`` label and the mono chips at the right end of a row."""
    if not node.chips:
        return []
    rules = theme.explainer
    right = node.width - ROW_RIGHT_PAD_PX
    top = (node.height - rules.chip_height) / HALF
    parts = []
    for index, chip in reversed(list(enumerate(node.chips))):
        width = estimate_text_width(chip, theme.layout, rules.chip_font) + 2 * rules.chip_pad
        right -= width
        parts.append(
            Part(
                PartKind.PILL,
                f"chip{index}",
                (right, top, width, rules.chip_height),
                text=chip,
                fill=theme.paper,
                color=theme.ink,
                font_size=rules.chip_font,
                is_bold=True,
                is_mono=True,
                is_centered=True,
                is_outlined=True,
            )
        )
        right -= rules.chip_gap
    label_width = estimate_text_width(CHIPS_LABEL, theme.layout, rules.chips_label_font)
    label = Part(
        PartKind.TEXT,
        "chips",
        (right - label_width, top, label_width, rules.chip_height),
        text=CHIPS_LABEL,
        color=theme.slate,
        font_size=rules.chips_label_font,
        is_bold=True,
    )
    return [label, *reversed(parts)]


def _head_parts(node: Node, theme: Theme) -> list[Part]:
    """List the letter circle and the heading of a section."""
    rules = theme.explainer
    size = rules.section_head_size
    gap = size / HALF - PILL_BORDER_PADDING_PX
    return [
        Part(
            PartKind.CIRCLE,
            "badge",
            (0, 0, size, size),
            text=node.number or "",
            fill=theme.badge.background,
            color=theme.badge.foreground,
            font_size=rules.section_head_letter_font,
            is_bold=True,
            is_mono=True,
            is_centered=True,
        ),
        Part(
            PartKind.TEXT,
            "name",
            (size + gap, 0, node.width - size - gap, size),
            text=" ".join(node.text),
            color=theme.ink,
            font_size=rules.section_head_font,
            is_bold=True,
        ),
    ]


def badge_box(node: Node, theme: Theme) -> tuple[float, float, float, float] | None:
    """Return the box of the number badge of a card on its top left corner, or None."""
    if not node.number or node.shape not in (Shape.EXPLAIN_CARD, Shape.ROW_CARD):
        return None
    rules = theme.explainer
    return (
        node.x - rules.badge_overhang,
        node.y - rules.badge_overhang,
        badge_width(node.number, theme),
        rules.badge_size,
    )


def band_fill(tone: Tone, theme: Theme) -> str:
    """Return the colour of a band: the tint of its tone laid over the page at a fixed strength.

    Args:
        tone: The tone of the band.
        theme: The design tokens.

    Returns:
        A ``#RRGGBB`` colour; opaque so that draw.io can use it too.
    """
    strength = theme.explainer.band_alpha
    tint, page = theme.tones[tone].box, theme.canvas
    channels = []
    for start in (HEX_RED, HEX_GREEN, HEX_BLUE):
        top, below = int(tint[start : start + 2], 16), int(page[start : start + 2], 16)
        channels.append(round(top * strength + below * (1 - strength)))
    return "#" + "".join(f"{channel:02X}" for channel in channels)
