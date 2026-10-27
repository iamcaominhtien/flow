"""Work out the size of a node and how its text wraps, without a font to measure with.

Text width is estimated from the number of characters: the average width of a character
is ``char_width_em`` times the font size. The estimate has a safety margin built into
``char_width_em``; the checks flag text that may still not fit.
"""

import math
from dataclasses import dataclass

from .model import DEFAULT_FONT_SIZE_PX, Node, Row, Shape
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


def fit_card(content: NodeContent, rules: LayoutRules) -> FittedNode:
    """Size an illustrated card: an icon disc on top, a name pill under it, then a detail text.

    The name stays on one line, inside the pill; the card widens to hold it, up to the maximum
    node width. A longer name is flagged by the text-fit check.

    Args:
        content: The name, the optional detail text and whether there is an icon.
        rules: The layout rules.

    Returns:
        The width, the height, the name as one line and the wrapped detail lines.
    """
    pill = estimate_text_width(content.title, rules, DEFAULT_FONT_SIZE_PX)
    pill += 2 * rules.card_pill_padding
    width = min(max(rules.card_min_width, pill + 2 * rules.card_padding), rules.max_node_width)
    room = width - 2 * rules.card_padding
    detail = (
        wrap_text(content.detail, rules, room, rules.detail_font_size) if content.detail else []
    )
    height = 2 * rules.card_padding + rules.card_disc + rules.card_gap + rules.card_pill_height
    if detail:
        height += rules.card_gap + len(detail) * rules.detail_line_height
    return FittedNode(width, height, (content.title,), tuple(detail))


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
    extra = ICON_TEXT_RESERVE_PX if has_icon else 0
    return _fit_table(title, sections, (extra, rules.table_header_height), rules)


def fit_table_card(
    title: str, sections: tuple[tuple[Row, ...], ...], rules: LayoutRules
) -> FittedNode:
    """Size an illustrated table: a tall header with the name in a pill and a large icon.

    Args:
        title: The table name, shown in a pill.
        sections: The groups of rows, with a divider between groups.
        rules: The layout rules.

    Returns:
        The size; ``lines`` holds the title.
    """
    extra = 2 * rules.card_pill_padding + rules.card_disc
    return _fit_table(title, sections, (extra, rules.table_card_header_height), rules)


def table_header_height(node: Node, rules: LayoutRules) -> float:
    """Return the height of the header band of a table node.

    Args:
        node: The table.
        rules: The layout rules.

    Returns:
        The tall band of an illustrated table, or the plain one, plus a line for a stereotype.
    """
    base = rules.table_card_header_height if node.card else rules.table_header_height
    return base + (rules.table_stereotype_height if node.stereotype else 0)


def key_room(sections: tuple[tuple[Row, ...], ...], rules: LayoutRules) -> float:
    """Return the width reserved before the column names for the key chips of a table.

    Args:
        sections: The groups of rows.
        rules: The layout rules.

    Returns:
        Zero when no row has a chip; otherwise room for the most chips on one row.
    """
    has_chips = any(row.flags for section in sections for row in section)
    if not has_chips:
        return 0
    columns = rules.table_key_columns
    return columns * rules.table_chip_width + (columns - 1) * 2 + rules.table_chip_gap


def _row_name_width(row: Row, rules: LayoutRules) -> float:
    """Return the width of the name of a row: mono text is wider than the sans text."""
    if row.is_mono:
        return len(row.left) * rules.char_width_em * rules.detail_font_size
    return estimate_text_width(row.left, rules, rules.table_name_font_size)


def _fit_table(
    title: str,
    sections: tuple[tuple[Row, ...], ...],
    header: tuple[float, float],
    rules: LayoutRules,
) -> FittedNode:
    """Size a table from its title, its rows and its header: (extra width, height)."""
    mono_width = rules.char_width_em * rules.detail_font_size
    widest_row = max(
        (
            _row_name_width(row, rules) + len(row.right) * mono_width + rules.table_row_gap
            for section in sections
            for row in section
        ),
        default=0,
    )
    widest_row += key_room(sections, rules)
    header_extra, header_height = header
    title_width = estimate_text_width(title, rules, DEFAULT_FONT_SIZE_PX) + header_extra
    width = max(
        rules.table_min_width,
        widest_row + 2 * rules.table_padding_x,
        title_width + 2 * rules.table_padding_x,
    )
    rows = sum(len(section) for section in sections)
    gaps = max(len(sections) - 1, 0) * rules.table_section_gap
    bottom = rules.table_bottom_pad if rows else 0
    height = header_height + rows * rules.table_row_height + gaps + bottom
    return FittedNode(
        width=min(width, rules.max_node_width + rules.table_extra_width),
        height=height,
        lines=(title,),
    )
