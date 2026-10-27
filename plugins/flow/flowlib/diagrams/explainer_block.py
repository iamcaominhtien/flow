"""The pieces every explainer shape is made of: cards, lines, labels and a block of geometry.

A shape builds a ``Block`` at a place on the page (an ``Area``); a page of sections moves
blocks into their columns.
"""

from dataclasses import dataclass, field, replace
from itertools import pairwise

from ..model import (
    Edge,
    EdgeLabel,
    Frame,
    FrameVariant,
    Head,
    LabelKind,
    Node,
    Point,
    Role,
    Shape,
    Tone,
)
from ..sizing import estimate_text_width
from ..theme import Theme
from .explainer_spec import Card

HALF = 2
CHIP_FONT_PX = 10  # the size of the words on a line
CHIP_PADDING_PX = 16  # room around the words inside their chip
MIN_OVERLAP_PX = 24  # two cards share a row or a column when they overlap by this much


@dataclass(frozen=True)
class Area:
    """The room a block has: its left edge, its top edge and its width."""

    x: float
    y: float
    width: float


@dataclass(frozen=True)
class Wire:
    """What a line is called, how it looks and what it says."""

    name: str
    role: Role
    label: str


@dataclass
class Block:
    """The frames, nodes and lines of one shape, and how tall it is."""

    frames: list[Frame] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    height: float = 0

    def extend(self, other: "Block") -> None:
        """Add everything of another block."""
        self.frames += other.frames
        self.nodes += other.nodes
        self.edges += other.edges


def moved(block: Block, shift_x: float, shift_y: float) -> Block:
    """Return a copy of a block moved by a distance."""

    def point(at: Point) -> Point:
        """Move one point."""
        return (at[0] + shift_x, at[1] + shift_y)

    def edge(each: Edge) -> Edge:
        """Move a line and its words."""
        label = replace(each.label, at=point(each.label.at)) if each.label else None
        return replace(each, points=tuple(point(at) for at in each.points), label=label)

    return Block(
        [replace(f, x=f.x + shift_x, y=f.y + shift_y) for f in block.frames],
        [replace(n, x=n.x + shift_x, y=n.y + shift_y) for n in block.nodes],
        [edge(each) for each in block.edges],
        block.height,
    )


def card_node(card: Card, place: tuple[str, float, float], size: tuple[float, float]) -> Node:
    """Build the vertical card of a card as written.

    Args:
        card: The card; its tone must be set.
        place: The id of the node and the left and top edge.
        size: Width and height.

    Returns:
        The node.
    """
    name, left, top = place
    return Node(
        id=name,
        shape=Shape.EXPLAIN_CARD,
        x=left,
        y=top,
        width=size[0],
        height=size[1],
        text=(card.name,),
        icon=card.icon,
        tone=card.tone,
        number=card.number,
        font_size=0,
        detail=(card.text,) if card.text else (),
    )


def row_node(card: Card, place: tuple[str, float, float], size: tuple[float, float]) -> Node:
    """Build a row card: icon at the left, a name and a line of text."""
    return replace(card_node(card, place, size), shape=Shape.ROW_CARD)


def plain_node(shape: Shape, name: str, box: tuple[float, float, float, float]) -> Node:
    """Build a node with no content yet, at ``(x, y, width, height)``; the caller sets the text."""
    left, top, width, height = box
    return Node(name, shape, left, top, width, height, (), None, None, None, 0)


def remark_node(
    name: str, box: tuple[float, float, float, float], lines: tuple[str, ...], theme: Theme
) -> Node:
    """Build a bold remark: text with no outline."""
    return replace(
        plain_node(Shape.REMARK, name, box), text=lines, font_size=theme.explainer.remark_font
    )


def note_node(
    name: str, box: tuple[float, float, float, float], lines: tuple[str, ...], theme: Theme
) -> Node:
    """Build a small grey note: text with no outline."""
    return replace(
        plain_node(Shape.REMARK, name, box), detail=lines, font_size=theme.explainer.note_font
    )


def strip_frame(name: str, box: tuple[float, float, float, float], label: str, tone: Tone) -> Frame:
    """Build a band: a tinted strip with its name in a pill at the top left."""
    left, top, width, height = box
    return Frame(name, left, top, width, height, label or None, tone, FrameVariant.STRIP)


def right_of(node: Node) -> float:
    """Return the right edge of a node."""
    return node.x + node.width


def centre_x(node: Node) -> float:
    """Return the horizontal middle of a node."""
    return node.x + node.width / HALF


def centre_y(node: Node) -> float:
    """Return the vertical middle of a node."""
    return node.y + node.height / HALF


def _overlap(first: tuple[float, float], second: tuple[float, float]) -> tuple[float, float] | None:
    """Return the span two spans share when it is long enough to run a line through, or None."""
    start, end = max(first[0], second[0]), min(first[1], second[1])
    return (start, end) if end - start >= MIN_OVERLAP_PX else None


def _across(source: Node, target: Node) -> list[Point] | None:
    """Route a line sideways between two cards that share a row, or return None."""
    rows = _overlap((source.y, source.y + source.height), (target.y, target.y + target.height))
    if rows is None:
        return None
    low, high = rows
    inside_target = low <= centre_y(target) <= high
    inside_source = low <= centre_y(source) <= high
    level = (
        centre_y(target)
        if inside_target
        else centre_y(source)
        if inside_source
        else (low + high) / 2
    )
    is_forward = centre_x(target) >= centre_x(source)
    start = right_of(source) if is_forward else source.x
    end = target.x if is_forward else right_of(target)
    return [(start, level), (end, level)]


def _down(source: Node, target: Node) -> list[Point] | None:
    """Route a straight vertical line between two cards that share a column, or return None."""
    columns = _overlap((source.x, right_of(source)), (target.x, right_of(target)))
    if columns is None:
        return None
    middle = (columns[0] + columns[1]) / HALF
    is_below = centre_y(target) >= centre_y(source)
    start = source.y + source.height if is_below else source.y
    end = target.y if is_below else target.y + target.height
    return [(middle, start), (middle, end)]


def _bent(source: Node, target: Node) -> list[Point]:
    """Route a line with two bends: out of one card, across the gap, into the other."""
    is_below = centre_y(target) >= centre_y(source)
    start = source.y + source.height if is_below else source.y
    end = target.y if is_below else target.y + target.height
    middle = (start + end) / HALF
    return [
        (centre_x(source), start),
        (centre_x(source), middle),
        (centre_x(target), middle),
        (centre_x(target), end),
    ]


def route_cards(source: Node, target: Node) -> list[Point]:
    """Route a line from one card to another with at most two bends.

    Args:
        source: The card the line leaves.
        target: The card the line enters.

    Returns:
        The points: sideways when the cards share a row, straight down or up when they share a
        column, else out of the near edge, across the gap and in.
    """
    return _across(source, target) or _down(source, target) or _bent(source, target)


def line_label(text: str, points: list[Point], theme: Theme) -> EdgeLabel | None:
    """Place the words of a line: on a sideways line, beside a vertical one.

    Args:
        text: The words in everyday language, or an empty string for none.
        points: The route of the line.
        theme: The design tokens.

    Returns:
        The label, or None when there are no words.
    """
    if not text:
        return None
    start, end = max(
        pairwise(points),
        key=lambda pair: abs(pair[1][0] - pair[0][0]) + abs(pair[1][1] - pair[0][1]),
    )
    centre = ((start[0] + end[0]) / HALF, (start[1] + end[1]) / HALF)
    if start[0] != end[0]:
        return EdgeLabel(text, centre, LabelKind.PLAIN)
    half = (estimate_text_width(text, theme.layout, CHIP_FONT_PX) + CHIP_PADDING_PX) / HALF
    return EdgeLabel(
        text, (centre[0] + theme.explainer.label_gap + half, centre[1]), LabelKind.PLAIN
    )


def make_edge(wire: Wire, ends: tuple[Node, Node], theme: Theme) -> Edge:
    """Build a line between two cards, with the words on it.

    Args:
        wire: The id, the role and the words of the line.
        ends: The card the line leaves and the card it enters.
        theme: The design tokens.

    Returns:
        The edge, routed with at most two bends.
    """
    source, target = ends
    points = route_cards(source, target)
    label = line_label(wire.label, points, theme)
    return Edge(wire.name, wire.role, tuple(points), label, source.id, target.id, Head.FILLED)


def prefixed(block: Block, prefix: str) -> Block:
    """Return a copy of a block whose ids all start with a prefix, so that blocks never clash."""

    def edge(each: Edge) -> Edge:
        """Rename a line and the cards it joins."""
        return replace(
            each,
            id=prefix + each.id,
            source=prefix + each.source if each.source else None,
            target=prefix + each.target if each.target else None,
        )

    return Block(
        [replace(frame, id=prefix + frame.id) for frame in block.frames],
        [replace(node, id=prefix + node.id) for node in block.nodes],
        [edge(each) for each in block.edges],
        block.height,
    )
