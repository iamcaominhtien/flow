"""Read back what a screen flow writes into a draw.io file: screens, chips, line roles, words.

A screen is a frame cell whose style carries a ``flowScreen`` word (see ``drawio_screen``); the
parts inside it are child cells and are not nodes. The guard and the effect of a transition are free
text cells named after their line (``edge-<id>-end1``). The colours of a line and of a label say
which role and which kind they have.
"""

import re
from collections.abc import Callable
from dataclasses import replace
from xml.etree import ElementTree as ET

from .drawio_screen import SCREEN_STYLE_KEY, TONE_STYLE_KEY
from .model import Edge, EdgeLabel, LabelKind, Node, Role, Shape, Tone
from .screen_scene import decode_screen
from .theme import load_theme

CHIP_PREFIX = "chip-"
WORDS_ID = re.compile(r"^(edge-.+)-end\d+$")
LAYER_IDS = {"0", "1"}
BORDER_TOLERANCE_PX = 1.0
Style = dict[str, str]


def is_screen_part(
    cell: ET.Element, cells: dict[str, ET.Element], parse: Callable[[str], Style]
) -> bool:
    """Tell a cell that belongs to a screen or to a node chip, which the node already holds."""
    parent = cells.get(cell.get("parent", ""))
    if parent is None or parent.get("id") in LAYER_IDS:
        return False
    is_chip = cell.get("id", "").startswith(CHIP_PREFIX)
    return is_chip or SCREEN_STYLE_KEY in parse(parent.get("style", ""))


def is_edge_words(cell: ET.Element) -> bool:
    """Tell a free text cell that holds the guard or the effect of a line."""
    return WORDS_ID.match(cell.get("id", "")) is not None


def screen_node(node: Node, style: Style) -> Node:
    """Turn a node read from a frame cell into a screen, when its style has a packed view."""
    view = decode_screen(style.get(SCREEN_STYLE_KEY, ""))
    if view is None:
        return node
    tone = style.get(TONE_STYLE_KEY)
    known = {member.value: member for member in Tone}
    return replace(
        node, shape=Shape.SCREEN, text=(view.title,), screen=view, tone=known.get(tone or "")
    )


def label_kind(style: Style) -> LabelKind:
    """Guess the kind of a line label from its background and text colours."""
    chips = load_theme().chips
    background = (style.get("labelBackgroundColor") or style.get("fillColor", "")).lower()
    for kind, colors in chips.items():
        if background and colors.background.lower() == background and kind is not LabelKind.PLAIN:
            return kind
    return LabelKind.TEXT if not background else LabelKind.PLAIN


def line_role(style: Style) -> Role:
    """Guess the role of a line from its colour and dash."""
    color = style.get("strokeColor", "").lower()
    roles = load_theme().roles
    for role in (Role.MAIN, Role.YES, Role.NO, Role.BACK):
        if roles[role].color.lower() == color:
            return role
    return Role.NEXT


def attach_words(edges: list[Edge], words: list[tuple[str, EdgeLabel]]) -> list[Edge]:
    """Give each line the guard and effect text cells that were named after it."""
    found: dict[str, list[EdgeLabel]] = {}
    for edge_id, label in words:
        found.setdefault(edge_id, []).append(label)
    return [replace(edge, extras=tuple(found.get(edge.id, ()))) for edge in edges]


def words_kind(style: Style) -> LabelKind:
    """Guess whether a free text is a guard (mono, green or rose) or an effect (grey)."""
    colors = load_theme().chips
    foreground = style.get("fontColor", "").lower()
    if colors[LabelKind.GUARD_FAIL].foreground.lower() == foreground:
        return LabelKind.GUARD_FAIL
    if colors[LabelKind.GUARD_OK].foreground.lower() == foreground:
        return LabelKind.GUARD_OK
    return LabelKind.EFFECT
