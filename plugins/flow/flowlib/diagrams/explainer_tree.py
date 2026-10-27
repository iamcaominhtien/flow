"""The tree shape of an explainer: a root card and a row for each of its parts (design 07 2.2).

The rows have no numbers, because their order does not matter. One bus line leaves the root and
one arrow enters each row.
"""

from dataclasses import replace

from ..model import Edge, Head, Node, Role, Tone
from ..theme import ExplainerProfile, Theme
from .explainer_block import (
    Area,
    Block,
    card_node,
    centre_y,
    note_node,
    right_of,
    row_node,
)
from .explainer_spec import Card, Row, Tree

HALF = 2
EDGE_PREFIX = "e"
ROOT_KEY = "root"
NOTE_HEIGHT_PX = 20
ROW_TONES = (Tone.BLUE, Tone.VIOLET, Tone.GREEN, Tone.TEAL, Tone.AMBER, Tone.GRAY, Tone.RED)


def build_tree(spec: Tree, area: Area, profile: ExplainerProfile, theme: Theme) -> Block:
    """Lay out a root card and its rows inside an area.

    Args:
        spec: The checked tree.
        area: Where the block goes; the root is at its left edge and the rows end at its right.
        profile: The sizes of the scale to draw at.
        theme: The design tokens.

    Returns:
        The block: the root, the rows, the bus lines and the note under them.
    """
    row_width, row_height = profile.row_size
    rows_height = len(spec.rows) * profile.row_pitch - (profile.row_pitch - row_height)
    root_height = profile.root_size[1]
    height = max(rows_height, root_height)
    root = card_node(
        replace(spec.root, tone=spec.root.tone or Tone.AMBER),
        (ROOT_KEY, area.x, area.y + (height - root_height) / HALF),
        profile.root_size,
    )
    rows_left = area.x + area.width - row_width
    rows_top = area.y + (height - rows_height) / HALF
    rows = [
        _row(row, index, (rows_left, rows_top + index * profile.row_pitch), (spec, profile))
        for index, row in enumerate(spec.rows)
    ]
    block = Block(nodes=[root, *rows], height=height)
    bus = min(theme.explainer.tree_bus_gap, (rows_left - right_of(root)) / HALF)
    block.edges = [_edge(root, row, index, right_of(root) + bus) for index, row in enumerate(rows)]
    if spec.note:
        top = area.y + height + theme.explainer.note_gap - profile.row_pitch / HALF
        block.nodes.append(
            note_node("note", (area.x, top, area.width, NOTE_HEIGHT_PX), (spec.note,), theme)
        )
        block.height = top + NOTE_HEIGHT_PX - area.y
    return block


def _row(
    row: Row, index: int, corner: tuple[float, float], context: tuple[Tree, ExplainerProfile]
) -> Node:
    """Build the row card of one part."""
    spec, profile = context
    card = Card(
        f"row-{index}", row.name, row.text, row.icon, row.tone or ROW_TONES[index % len(ROW_TONES)]
    )
    node = row_node(card, (f"row-{index}", *corner), profile.row_size)
    return replace(node, is_mono=spec.is_code, chips=row.inside)


def _edge(root: Node, row: Node, index: int, bus_x: float) -> Edge:
    """Build the arrow from the root, along the bus, into a row."""
    start = (right_of(root), centre_y(root))
    end = (row.x, centre_y(row))
    if start[1] == end[1]:
        points = (start, end)
    else:
        points = (start, (bus_x, start[1]), (bus_x, end[1]), end)
    return Edge(f"{EDGE_PREFIX}{index + 1}", Role.NEXT, points, None, root.id, row.id, Head.FILLED)
