"""The layers shape of an explainer: a journey through bands (design 07 section 2.1).

Each band is one row of cards on a tinted strip. The cards are numbered in reading order and
joined by the lines of the story. A small ``branch`` card is a row card, so that two of them
can stack inside one band (``6a`` and ``6b``).
"""

from dataclasses import dataclass, replace

from ..model import Edge, Frame, Node
from ..theme import ExplainerProfile, Theme
from .explainer_block import (
    Area,
    Block,
    Wire,
    card_node,
    make_edge,
    remark_node,
    right_of,
    row_node,
    strip_frame,
)
from .explainer_spec import LINK_ROLES, Band, Card, Layers

HALF = 2
EDGE_PREFIX = "e"
CLOSING_HEIGHT_PX = 20
REMARK_RIGHT_MARGIN_PX = 30  # a remark stops this far from the right end of its band


@dataclass(frozen=True)
class BandPlace:
    """Where a band is: its area, its top edge and the scale it is drawn at."""

    area: Area
    top: float
    profile: ExplainerProfile


def build_layers(spec: Layers, area: Area, profile: ExplainerProfile, theme: Theme) -> Block:
    """Lay out a layered flow inside an area.

    Args:
        spec: The checked layers.
        area: Where the block goes: its left edge, top edge and width.
        profile: The sizes of the scale to draw at.
        theme: The design tokens.

    Returns:
        The block: one strip per band, the cards, the lines and the closing line.
    """
    block = Block()
    numbers = _numbers(spec)
    placed: dict[str, Node] = {}
    bands_of: dict[str, int] = {}
    for index, band in enumerate(spec.bands):
        place = BandPlace(area, area.y + index * profile.band_pitch, profile)
        block.frames.append(_strip(band, index, place))
        nodes = _band_nodes(band, numbers, (place, theme))
        block.nodes += nodes
        placed.update({node.id: node for node in nodes})
        bands_of.update({node.id: index for node in nodes})
        block.nodes += _remark(band, index, nodes, (place, theme))
    block.edges = _edges(spec, placed, theme)
    block.edges = _clear_of_bands(block.edges, bands_of, (area.y, profile))
    bottom = area.y + (len(spec.bands) - 1) * profile.band_pitch + profile.band_height
    block.height = bottom - area.y
    if spec.closing:
        block.nodes.append(_closing(spec.closing, area, bottom, theme))
        block.height += theme.explainer.closing_gap + CLOSING_HEIGHT_PX
    return block


def _strip(band: Band, index: int, place: BandPlace) -> Frame:
    """Build the strip of a band."""
    box = (place.area.x, place.top, place.area.width, place.profile.band_height)
    return strip_frame(f"band-{index}", box, band.label, band.tone)


def _numbers(spec: Layers) -> dict[str, str | None]:
    """Give every card its number: the one written, or the next whole number in reading order."""
    numbers: dict[str, str | None] = {}
    counter = 0
    for band in spec.bands:
        columns = _columns(band)
        for card in sorted(band.cards, key=lambda each: (columns[each.key], each.stack)):
            if card.number is not None:
                numbers[card.key] = card.number
            elif spec.has_numbers:
                counter += 1
                numbers[card.key] = str(counter)
            else:
                numbers[card.key] = None
    return numbers


def _columns(band: Band) -> dict[str, int]:
    """Return the column of every card: the one written, else the card's place in the band."""
    columns: dict[str, int] = {}
    previous = -1
    for card in band.cards:
        previous = card.col if card.col is not None else (previous if card.stack else previous + 1)
        columns[card.key] = previous
    return columns


def _band_nodes(
    band: Band, numbers: dict[str, str | None], context: tuple[BandPlace, Theme]
) -> list[Node]:
    """Build the cards of one band, a column at a time."""
    place, theme = context
    columns = _columns(band)
    stacks: dict[int, list[Card]] = {}
    for card in band.cards:
        stacks.setdefault(columns[card.key], []).append(card)
    nodes = []
    for column, cards in stacks.items():
        ordered = sorted(cards, key=lambda each: each.stack)
        nodes += _stack_nodes(ordered, column, (band, numbers, place, theme))
    return nodes


def _stack_nodes(
    cards: list[Card],
    column: int,
    context: tuple[Band, dict[str, str | None], BandPlace, Theme],
) -> list[Node]:
    """Build the cards of one column of a band, centred on the row of the band."""
    band, numbers, place, theme = context
    profile = place.profile
    sizes = [profile.branch_size if card.is_branch else profile.card_size for card in cards]
    gap = 0 if len(cards) == 1 else theme.explainer.stack_gap
    total = sum(height for _width, height in sizes) + gap * (len(cards) - 1)
    middle = place.top + profile.band_card_top + profile.card_size[1] / HALF
    top = middle - total / HALF
    left = place.area.x + profile.col_offset + column * profile.col_pitch
    nodes = []
    for card, size in zip(cards, sizes, strict=True):
        shown = replace(card, tone=card.tone or band.tone, number=numbers[card.key])
        make = row_node if card.is_branch else card_node
        nodes.append(make(shown, (card.key, left, top), size))
        top += size[1] + gap
    return nodes


def _remark(
    band: Band, index: int, nodes: list[Node], context: tuple[BandPlace, Theme]
) -> list[Node]:
    """Build the bold remark in the free part of a band, or nothing."""
    if not band.remark:
        return []
    place, theme = context
    left = max(right_of(node) for node in nodes) + theme.explainer.remark_gap
    room = place.area.x + place.area.width - REMARK_RIGHT_MARGIN_PX - left
    box = (left, place.top + place.profile.band_card_top, room, place.profile.card_size[1])
    return [remark_node(f"remark-{index}", box, (band.remark,), theme)]


def _edges(spec: Layers, placed: dict[str, Node], theme: Theme) -> list[Edge]:
    """Build the lines of the story between the cards."""
    return [
        make_edge(
            Wire(f"{EDGE_PREFIX}{index + 1}", LINK_ROLES[link.kind], link.label),
            (placed[link.source], placed[link.target]),
            theme,
        )
        for index, link in enumerate(spec.links)
    ]


def _closing(text: str, area: Area, bottom: float, theme: Theme) -> Node:
    """Build the closing line: one bold line under the last band."""
    rules = theme.explainer
    box = (area.x + rules.band_pill_left, bottom + rules.closing_gap, area.width, CLOSING_HEIGHT_PX)
    return remark_node("closing", box, (text,), theme)


def _clear_of_bands(
    edges: list[Edge], bands_of: dict[str, int], place: tuple[float, ExplainerProfile]
) -> list[Edge]:
    """Move the words of a line that runs from one band to another into the gap between them."""
    top, profile = place
    gap = profile.band_pitch - profile.band_height
    moved = []
    for edge in edges:
        first, second = bands_of.get(edge.source or ""), bands_of.get(edge.target or "")
        is_vertical = len({x for x, _y in edge.points}) == 1
        if (
            edge.label is None
            or first is None
            or second is None
            or first == second
            or not is_vertical
        ):
            moved.append(edge)
            continue
        below = max(first, second)
        centre = top + below * profile.band_pitch - gap / HALF
        moved.append(replace(edge, label=replace(edge.label, at=(edge.label.at[0], centre))))
    return moved
