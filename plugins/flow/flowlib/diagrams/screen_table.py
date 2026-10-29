"""The table of coded conditions of a screen flow: one row for each arrow written as a code.

Design 02 keeps the words on an arrow while they stay under about 20 characters; longer ones, or
ones that several arrows share, become a code on the arrow (``C1``) and a row in this table. The
automatic screen flow and the author kit build the same table.
"""

from dataclasses import dataclass

from ..model import Node, Point, Row, Shape, Tone
from ..sizing import estimate_text_width, key_room
from ..theme import LayoutRules

CONDITIONS_TITLE = "Conditions"
CONDITIONS_ID = "conditions"
ARROW_JOIN = " → "
TEXT_JOIN = " · "
MONO_CHAR_EM = 0.62
TABLE_TEXT_MARGIN = 1.12  # the width of a row is estimated, so it gets some room to spare


@dataclass(frozen=True)
class CodedArrow:
    """An arrow written as a code: the code, the two screens it joins and its words."""

    code: str
    source: str  # how the row names the screen the arrow leaves: its id code, else its name
    target: str
    trigger: str = ""
    guard: str | None = None
    effect: str | None = None


def condition_row(arrow: CodedArrow) -> Row:
    """Build a row of the conditions table: the code, the arrow and its trigger, guard and effect.

    Args:
        arrow: The coded arrow.

    Returns:
        The row: ``source → target · trigger`` on the left, ``[guard] / effect`` on the right and
        the code as its key.
    """
    route = arrow.source + ARROW_JOIN + arrow.target
    left = TEXT_JOIN.join(part for part in (route, arrow.trigger) if part)
    guard = f"[{arrow.guard}]" if arrow.guard else ""
    effect = f"/ {arrow.effect}" if arrow.effect else ""
    return Row(
        left=left, right=" ".join(part for part in (guard, effect) if part), flags=(arrow.code,)
    )


def conditions_table(
    rows: tuple[Row, ...], corner: Point, min_width: float, rules: LayoutRules
) -> Node:
    """Build the conditions table as a gray table node.

    Args:
        rows: The rows, from ``condition_row``.
        corner: The top-left corner of the table.
        min_width: The narrowest the table may be, for example the width of the diagram above it.
        rules: The layout rules, which size the table.

    Returns:
        The table node, with the id ``conditions``.
    """
    width = max(_table_width(rows, rules), min_width)
    height = rules.table_header_height + len(rows) * rules.table_row_height + rules.table_bottom_pad
    return Node(
        id=CONDITIONS_ID,
        shape=Shape.TABLE,
        x=corner[0],
        y=corner[1],
        width=width,
        height=height,
        text=(CONDITIONS_TITLE,),
        icon=None,
        tone=Tone.GRAY,
        number=None,
        font_size=rules.table_name_font_size,
        sections=(rows,),
    )


def _table_width(rows: tuple[Row, ...], rules: LayoutRules) -> float:
    """Estimate the width the longest row of the conditions table needs."""
    mono = MONO_CHAR_EM * rules.detail_font_size
    widest = max(
        estimate_text_width(row.left, rules, rules.table_name_font_size) + len(row.right) * mono
        for row in rows
    )
    room = 2 * rules.table_padding_x + key_room((rows,), rules) + rules.table_row_gap
    return max(rules.table_min_width, widest * TABLE_TEXT_MARGIN + room)
