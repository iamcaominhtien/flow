"""Work out the size of a node and how its text wraps, without a font to measure with.

Text width is estimated from the number of characters: the average width of a character
is ``char_width_em`` times the font size. The estimate has a safety margin built into
``char_width_em``; the checks flag text that may still not fit.
"""

import math
from dataclasses import dataclass

from .model import DEFAULT_FONT_SIZE_PX, Shape
from .text_area import text_area_width
from .theme import LayoutRules

WIDTH_STEP_PX = 10  # a node is widened in steps of this size until its text fits
LINE_HEIGHT_FACTOR = 1.25


@dataclass(frozen=True)
class FittedNode:
    """The size of a node and its text, wrapped into lines."""

    width: float
    height: float
    lines: tuple[str, ...]


def estimate_text_width(text: str, rules: LayoutRules, font_size: float) -> float:
    """Estimate how wide a line of text is when drawn.

    Args:
        text: One line of text.
        rules: The layout rules, which hold the average character width.
        font_size: The font size in pixels.

    Returns:
        The estimated width in pixels.
    """
    return len(text) * rules.char_width_em * font_size


def wrap_text(text: str, rules: LayoutRules, max_width: float, font_size: float) -> list[str]:
    """Break text into lines that each fit ``max_width``, at spaces only.

    Args:
        text: The text to wrap.
        rules: The layout rules.
        max_width: The widest a line may be, in pixels.
        font_size: The font size in pixels.

    Returns:
        The lines. A single word wider than ``max_width`` stays on a line of its own.
    """
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and estimate_text_width(candidate, rules, font_size) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def fit_node(shape: Shape, text: str, has_icon: bool, rules: LayoutRules) -> FittedNode:
    """Choose the smallest size that holds the text in at most ``max_text_lines`` lines.

    The node starts at the minimum size for its shape and is widened, never made taller,
    until the text fits. Only when the widest allowed node still needs more lines does the
    node grow taller.

    Args:
        shape: The node shape.
        text: The node text, not yet wrapped.
        has_icon: Whether the node shows an icon.
        rules: The layout rules.

    Returns:
        The width, height and wrapped lines.
    """
    min_width, min_height = rules.min_sizes[shape]
    font_size = DEFAULT_FONT_SIZE_PX
    width = min_width
    while True:
        lines = wrap_text(text, rules, text_area_width(shape, width, has_icon), font_size)
        if len(lines) <= rules.max_text_lines or width >= rules.max_node_width:
            break
        width += WIDTH_STEP_PX
    needed = math.ceil(len(lines) * font_size * LINE_HEIGHT_FACTOR) + 2 * rules.line_padding
    return FittedNode(width=width, height=max(min_height, needed), lines=tuple(lines))
