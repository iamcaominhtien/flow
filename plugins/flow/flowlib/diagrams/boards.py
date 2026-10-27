"""Boards of cards: a Kanban comparison (columns) and layers (bands).

The JSON formats::

    {"type": "kanban",
     "columns": [{"label", "tone", "cards": [{"label", "detail", "icon", "tone"}]}]}
    {"type": "layers", "flow": true,
     "layers": [{"label", "tone", "items": [{"label", "detail", "icon"}]}]}

Both have ``title`` and ``desc``. A Kanban board with kinds, owners or limits is drawn by
``kanban``; this module draws the side-by-side comparison (each option a column, each point a
card, ``"use": "compare"``) and the layers. The wireframe has its own module, ``wireframe``.
"""

from dataclasses import dataclass, field
from typing import Any

from ..canvas import fit_canvas
from ..model import DEFAULT_FONT_SIZE_PX, Edge, Frame, Head, Node, Role, Scene, Shape, Tone
from ..reader import Reader, SpecError
from ..sizing import FittedNode, NodeContent, fit_card, fit_node
from ..theme import LayoutRules, icon_names, load_theme
from . import kanban, kanban_spec

KANBAN = "kanban"
LAYERS = "layers"
CARD_GAP_PX = 12.0
FRAME_TOP_PX = 36.0
FRAME_PAD_PX = 16.0
FRAME_GAP_PX = 24.0
LAYER_GAP_PX = 40.0
CARD_KEYS = {"label", "detail", "icon", "tone"}
COLUMN_KEYS = {"label", "tone", "cards"}
LAYER_KEYS = {"label", "tone", "items"}
SPEC_KEYS = {"type", "title", "desc", "columns", "layers", "flow", "style"}


@dataclass
class _Card:
    """One card as written."""

    label: str
    detail: str
    icon: str | None
    tone: Tone | None
    is_card: bool = False


@dataclass
class _Group:
    """A frame and the cards in it."""

    label: str | None
    tone: Tone
    cards: list[_Card] = field(default_factory=list)


def _card(raw: object, where: str, read: Reader) -> _Card | None:
    """Read one card, reporting what is wrong with it."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, CARD_KEYS, where)
    icon = raw.get("icon")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    return _Card(
        read.text(raw, "label", where) or "",
        read.text(raw, "detail", where) or "",
        icon,
        read.enum(Tone, raw, "tone", where),
    )


def _groups(raw: dict[str, Any], key: str, member_key: str, read: Reader) -> list[_Group]:
    """Read the columns or layers of a board: each has a label, a tone and a list of cards."""
    allowed = COLUMN_KEYS if key == "columns" else LAYER_KEYS
    groups = []
    listed = raw.get(key, [])
    for index, item in enumerate(listed if isinstance(listed, list) else []):
        where = f"{key}[{index}]"
        if not isinstance(item, dict):
            read.report(where, "must be an object")
            continue
        read.check_keys(item, allowed, where)
        group = _Group(
            read.text(item, "label", where), read.enum(Tone, item, "tone", where) or Tone.GRAY
        )
        members = item.get(member_key, [])
        for number, member in enumerate(members if isinstance(members, list) else []):
            card = _card(member, f"{where}.{member_key}[{number}]", read)
            if card is not None:
                group.cards.append(card)
        groups.append(group)
    if not groups:
        read.report("spec", f"'{key}' must list at least one entry")
    return groups


def _fit(card: _Card, rules: LayoutRules) -> FittedNode:
    """Size a card to its text; an illustrated card has its own size."""
    content = NodeContent(card.label, card.detail, card.icon is not None)
    if card.is_card:
        return fit_card(content, rules)
    return fit_node(Shape.PROCESS, content, rules)


def _wrapped(card: _Card, size: FittedNode, name: str, box: tuple[float, float, float]) -> Node:
    """Build the scene node of a card using the wrapped lines of its fitted size."""
    x, y, width = box
    return Node(
        name,
        Shape.PROCESS,
        x,
        y,
        width,
        size.height,
        size.lines,
        card.icon,
        card.tone,
        None,
        DEFAULT_FONT_SIZE_PX,
        detail=size.detail,
        card=card.is_card,
    )


def _kanban(groups: list[_Group], rules: LayoutRules, top: float) -> tuple[list[Frame], list[Node]]:
    """Lay the columns side by side, with the cards stacked in each."""
    frames, nodes = [], []
    left = rules.margin
    for index, group in enumerate(groups):
        sizes = [_fit(card, rules) for card in group.cards]
        width = max([size.width for size in sizes] + [rules.min_sizes[Shape.PROCESS][0]])
        y = top + FRAME_TOP_PX
        for number, (card, size) in enumerate(zip(group.cards, sizes, strict=True)):
            nodes.append(
                _wrapped(card, size, f"c{index}-{number}", (left + FRAME_PAD_PX, y, width))
            )
            y += size.height + CARD_GAP_PX
        height = max(y - CARD_GAP_PX + FRAME_PAD_PX - top, FRAME_TOP_PX + FRAME_PAD_PX)
        frames.append(
            Frame(
                f"column-{index}",
                left,
                top,
                width + 2 * FRAME_PAD_PX,
                height,
                group.label,
                group.tone,
            )
        )
        left += width + 2 * FRAME_PAD_PX + FRAME_GAP_PX
    return frames, nodes


def _layers(
    groups: list[_Group], rules: LayoutRules, top: float, has_flow: bool
) -> tuple[list[Frame], list[Node], list[Edge]]:
    """Stack the layers top to bottom, each with its cards in a row, and join them if asked."""
    sized = [[_fit(card, rules) for card in group.cards] for group in groups]
    inner = max(sum(s.width for s in row) + CARD_GAP_PX * (len(row) - 1) for row in sized)
    width = inner + 2 * FRAME_PAD_PX
    frames, nodes, edges = [], [], []
    y = top
    for index, (group, row) in enumerate(zip(groups, sized, strict=True)):
        tallest = max(size.height for size in row)
        x = (
            rules.margin
            + FRAME_PAD_PX
            + (inner - sum(s.width for s in row) - CARD_GAP_PX * (len(row) - 1)) / 2
        )
        for number, (card, size) in enumerate(zip(group.cards, row, strict=True)):
            nodes.append(
                _wrapped(card, size, f"l{index}-{number}", (x, y + FRAME_TOP_PX, size.width))
            )
            x += size.width + CARD_GAP_PX
        height = FRAME_TOP_PX + tallest + FRAME_PAD_PX
        frames.append(
            Frame(f"layer-{index}", rules.margin, y, width, height, group.label, group.tone)
        )
        if has_flow and index:
            centre = rules.margin + width / 2
            edges.append(
                Edge(
                    f"flow-{index}",
                    Role.MAIN,
                    ((centre, y - LAYER_GAP_PX), (centre, y)),
                    None,
                    None,
                    None,
                    Head.FILLED,
                )
            )
        y += height + LAYER_GAP_PX
    return frames, nodes, edges


def _illustrate(groups: list[_Group], illustrated: bool) -> list[_Group]:
    """Mark the cards that have an icon as illustrated cards, when the spec asks for it."""
    for group in groups:
        for card in group.cards:
            card.is_card = illustrated and card.icon is not None
    return groups


def layout_board(kind: str, raw: object) -> Scene:
    """Check a board spec and lay it out.

    Args:
        kind: ``kanban`` or ``layers``.
        raw: The result of ``json.loads`` on the spec.

    Returns:
        The scene.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    rules = load_theme().layout
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    illustrated = read.illustrated(raw, "spec")
    top = rules.margin + (rules.title_block_height if title else 0)
    edges: list[Edge] = []
    if kind == KANBAN:
        groups = _illustrate(_groups(raw, "columns", "cards", read), illustrated)
        frames, nodes = _kanban(groups, rules, top) if not read.problems else ([], [])
    else:
        groups = _illustrate(_groups(raw, "layers", "items", read), illustrated)
        ready = not read.problems and all(group.cards for group in groups)
        if not ready and not read.problems:
            read.report("spec", "every layer needs at least one item")
        frames, nodes, edges = (
            _layers(groups, rules, top, raw.get("flow") is True) if ready else ([], [], [])
        )
    if read.problems:
        raise SpecError(read.problems)
    return fit_canvas(Scene(0, 0, title, description, tuple(frames), tuple(nodes), tuple(edges)))


def layout_kanban(raw: object) -> Scene:
    """Lay out a Kanban board, or a comparison of options when the spec asks for one.

    Args:
        raw: The result of ``json.loads`` on a Kanban spec.

    Returns:
        The scene.
    """
    if kanban_spec.is_board(raw):
        return kanban.layout_raw(raw)
    if isinstance(raw, dict):
        raw = {key: value for key, value in raw.items() if key != "use"}
    return layout_board(KANBAN, raw)


def layout_layers(raw: object) -> Scene:
    """Lay out layers.

    Args:
        raw: The result of ``json.loads`` on a layers spec.

    Returns:
        The scene.
    """
    return layout_board(LAYERS, raw)
