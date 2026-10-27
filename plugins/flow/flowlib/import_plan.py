"""Read the planning nodes back from a draw.io file that Flow wrote.

Flow writes a planning node as one cell whose style carries ``flowShape``, ``flowPlan`` and
``flowTone`` (see ``drawio_plan``). The words of an org card, of the topic of a mind map and of
a leaf are read from the cell or from its child cells; icons are not read back.
"""

import html
import re
from collections.abc import Callable
from dataclasses import replace
from xml.etree import ElementTree as ET

from .drawio_common import FLOW_SHAPE_KEY
from .drawio_plan import PLAN_STYLE_KEY
from .drawio_screen import TONE_STYLE_KEY
from .html_board import BOARD_SHAPES
from .model import MindLevel, Node, PlanView, Shape, Tone
from .plan_scene import decode_plan

NODE_PREFIX = "node-"
PART_NAMES = ("pill", "detail", "mk-text", "disc", "bar", "line")
TAG = re.compile(r"<[^>]+>")
LINE_BREAK = re.compile(r"<br\s*/?>")


def is_plan_cell(style: dict[str, str]) -> bool:
    """Tell a cell that Flow wrote as a planning node."""
    return PLAN_STYLE_KEY in style


def is_plan_part(
    cell: ET.Element, cells: dict[str, ET.Element], parse: Callable[[str], dict[str, str]]
) -> bool:
    """Tell a child cell of a planning node: its fill, check, circle, bar, marks or words."""
    parent = cells.get(cell.get("parent", ""))
    if parent is None:
        return False
    return PLAN_STYLE_KEY in parse(parent.get("style", ""))


def plan_node(
    node: Node, style: dict[str, str], cell: ET.Element, cells: dict[str, ET.Element]
) -> Node:
    """Give a node read from a plain cell its shape, view, tone and words.

    Args:
        node: The node as read from the plain cell.
        style: The style of the cell.
        cell: The cell.
        cells: Every cell of the file by id.

    Returns:
        The planning node.
    """
    view = decode_plan(style[PLAN_STYLE_KEY]) or PlanView()
    shape = Shape(style[FLOW_SHAPE_KEY])
    tone = style.get(TONE_STYLE_KEY)
    stem = cell.get("id", "").removeprefix(NODE_PREFIX)
    node = replace(node, shape=shape, plan=view, tone=Tone(tone) if tone else None)
    parts = {
        name: cells.get(f"{name}-{stem}")
        for name in ("pill", "detail", "mk-text", "disc", "bar", "line")
    }
    if shape in BOARD_SHAPES:
        return _board_words(node, shape, (style, cell), parts)
    if shape is Shape.PERSON_CARD:
        return _card_words(node, parts)
    if shape is Shape.BRANCH and view.level is MindLevel.CENTRE:
        return _centre_words(node, parts)
    if shape is Shape.BRANCH:
        return replace(node, card=parts["disc"] is not None or _is_solid(style))
    if shape is Shape.LEAF:
        return replace(node, card=parts["line"] is None and view.level is not MindLevel.KEY)
    return node


def _board_words(
    node: Node,
    shape: Shape,
    cells: tuple[dict[str, str], ET.Element],
    parts: dict[str, ET.Element | None],
) -> Node:
    """Read the words of a card, a pill, a column header or a row head of a board or roadmap."""
    style, cell = cells
    if shape in (Shape.KANBAN_CARD, Shape.ROADMAP_CARD):
        return replace(
            node,
            text=_words(parts["mk-text"]),
            detail=_words(parts["detail"]),
            dashed=style.get("dashed") == "1",
        )
    if shape is Shape.LANE_HEAD:
        return replace(node, text=_words(parts["pill"]))
    lines = _words(cell)
    return replace(node, text=lines[:1], detail=lines[1:] if shape is Shape.PERIOD_HEAD else ())


def _is_solid(style: dict[str, str]) -> bool:
    """Tell the pill of an illustrated branch, which is filled with the strong colour."""
    return style.get("align") == "left"


def _words(cell: ET.Element | None) -> tuple[str, ...]:
    """Return the lines of text of a cell, without markup."""
    if cell is None:
        return ()
    parts = LINE_BREAK.split(cell.get("value", ""))
    lines = [html.unescape(TAG.sub("", part)).strip() for part in parts]
    return tuple(line for line in lines if line)


def _card_words(node: Node, parts: dict[str, ET.Element | None]) -> Node:
    """Read the name and the role of an org card, plain or illustrated."""
    if parts["pill"] is not None:
        return replace(node, card=True, text=_words(parts["pill"]), detail=_words(parts["detail"]))
    lines = _words(parts["mk-text"])
    return replace(node, card=False, text=lines[:1], detail=lines[1:])


def _centre_words(node: Node, parts: dict[str, ET.Element | None]) -> Node:
    """Read the name and the goal of the topic of a mind map."""
    if parts["pill"] is None:
        return replace(node, card=False)
    return replace(node, card=True, text=_words(parts["pill"]), detail=_words(parts["detail"]))
