"""Work out the size of a node and how its text wraps, without a font to measure with.

Text width is estimated from the number of characters: the average width of a character
is ``char_width_em`` times the font size. The estimate has a safety margin built into
``char_width_em``; the checks flag text that may still not fit.
"""

import math
from dataclasses import dataclass

from .model import DEFAULT_FONT_SIZE_PX, Row, Shape
from .text_area import ICON_TEXT_RESERVE_PX, text_area_width
from .theme import LayoutRules

WIDTH_STEP_PX = 10  # a node is widened in steps of this size until its text fits
LINE_HEIGHT_FACTOR = 1.25


@dataclass(frozen=True)
class FittedNode:
    """The size of a node and its text, wrapped into lines."""

    width: float
    height: float
    lines: tuple[str, ...]
    detail: tuple[str, ...] = ()


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


@dataclass(frozen=True)
class NodeContent:
    """The text of a node as the author wrote it, and whether it shows an icon."""

    title: str
    detail: str = ""
    has_icon: bool = False


def fit_node(shape: Shape, content: NodeContent, rules: LayoutRules) -> FittedNode:
    """Choose the smallest size that holds the text in at most ``max_text_lines`` lines.

    The node starts at the minimum size for its shape and is widened, never made taller,
    until the title fits. Only when the widest allowed node still needs more lines does the
    node grow taller. A detail text goes under the title in a smaller font and may add height.

    Args:
        shape: The node shape.
        content: The title, an optional detail text for under it, and whether there is an icon.
        rules: The layout rules.

    Returns:
        The width, height, wrapped title lines and wrapped detail lines.
    """
    min_width, min_height = rules.min_sizes[shape]
    font_size = DEFAULT_FONT_SIZE_PX
    width = min_width
    while True:
        room = text_area_width(shape, width, content.has_icon)
        lines = wrap_text(content.title, rules, room, font_size)
        if len(lines) <= rules.max_text_lines or width >= rules.max_node_width:
            break
        width += WIDTH_STEP_PX
    detail = content.detail
    detail_lines = wrap_text(detail, rules, room, rules.detail_font_size) if detail else []
    needed = math.ceil(len(lines) * font_size * LINE_HEIGHT_FACTOR)
    needed += len(detail_lines) * rules.detail_line_height + 2 * rules.line_padding
    return FittedNode(width, max(min_height, needed), tuple(lines), tuple(detail_lines))


def fit_table(
    title: str, sections: tuple[tuple[Row, ...], ...], has_icon: bool, rules: LayoutRules
) -> FittedNode:
    """Size a table node from its title and its rows.

    Args:
        title: The table name, shown in the header.
        sections: The groups of rows, with a divider between groups.
        has_icon: Whether the header shows an icon.
        rules: The layout rules.

    Returns:
        The size; ``lines`` holds the title.
    """
    mono_width = rules.char_width_em * rules.detail_font_size
    widest_row = max(
        (
            (len(row.left) + len(row.right)) * mono_width + rules.table_row_gap
            for section in sections
            for row in section
        ),
        default=0,
    )
    header = estimate_text_width(title, rules, DEFAULT_FONT_SIZE_PX) + (
        ICON_TEXT_RESERVE_PX if has_icon else 0
    )
    width = max(
        rules.table_min_width,
        widest_row + 2 * rules.table_padding_x,
        header + 2 * rules.table_padding_x,
    )
    rows = sum(len(section) for section in sections)
    gaps = max(len(sections) - 1, 0) * rules.table_section_gap
    height = (
        rules.table_header_height + rows * rules.table_row_height + gaps + rules.table_bottom_pad
    )
    return FittedNode(
        width=min(width, rules.max_node_width + rules.table_extra_width),
        height=height,
        lines=(title,),
    )
