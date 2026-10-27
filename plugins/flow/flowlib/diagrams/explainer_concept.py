"""The concept shape of an explainer: a hub, four facts around it and an analogy (design 07 2.4)."""

from dataclasses import replace

from ..model import Edge, Head, Node, Role, Tone
from ..theme import ExplainerProfile, Theme
from .explainer_block import (
    Area,
    Block,
    Wire,
    card_node,
    centre_x,
    make_edge,
    remark_node,
    strip_frame,
)
from .explainer_spec import Analogy, Concept

HALF = 2
HUB_KEY = "hub"
EDGE_PREFIX = "e"
ANALOGY_TONES = (Tone.BLUE, Tone.GREEN)
FACT_TONES = (Tone.AMBER, Tone.VIOLET, Tone.BLUE, Tone.GREEN)
HUB_TONE = Tone.TEAL
CLOSING_HEIGHT_PX = 20
CLOSING_UP_PX = 38  # the closing line sits this far above the bottom of the band
COLUMNS = 2


def build_concept(spec: Concept, area: Area, profile: ExplainerProfile, theme: Theme) -> Block:
    """Lay out the hub, its facts and the analogy under them.

    Args:
        spec: The checked concept.
        area: Where the block goes; the hub is in the middle of its width.
        profile: The sizes of the scale to draw at.
        theme: The design tokens.

    Returns:
        The block.
    """
    rules = theme.explainer
    middle = area.x + area.width / HALF
    fact_width, fact_height = profile.fact_size
    hub_width, hub_height = profile.hub_size
    hub_centre = area.y + rules.concept_row_pitch / HALF + fact_height / HALF
    hub = card_node(
        replace(spec.hub, tone=spec.hub.tone or HUB_TONE, number=None),
        (HUB_KEY, middle - hub_width / HALF, hub_centre - hub_height / HALF),
        profile.hub_size,
    )
    block = Block(nodes=[hub])
    for index, fact in enumerate(spec.facts):
        is_right, is_low = index % COLUMNS, index // COLUMNS
        left = (
            middle
            + (rules.concept_spread if is_right else -rules.concept_spread)
            - fact_width / HALF
        )
        top = area.y + is_low * rules.concept_row_pitch
        shown = replace(
            fact, tone=fact.tone or FACT_TONES[index], number=fact.number or str(index + 1)
        )
        node = card_node(shown, (f"fact-{index}", left, top), profile.fact_size)
        block.nodes.append(node)
        block.edges.append(_spoke(hub, node, (index, rules.hub_line_offset)))
    block.height = rules.concept_row_pitch + fact_height
    if spec.analogy:
        top = area.y + block.height + rules.rule_gap
        analogy = build_analogy(spec.analogy, Area(area.x, top, area.width), profile, theme)
        block.extend(analogy)
        block.height += rules.rule_gap + analogy.height
    return block


def _spoke(hub: Node, fact: Node, side: tuple[int, float]) -> Edge:
    """Build the arrow from the side of the hub to a fact: sideways, then up or down."""
    index, offset = side
    is_right, is_low = index % COLUMNS, index // COLUMNS
    start_x = hub.x + hub.width if is_right else hub.x
    start_y = hub.y + hub.height / HALF + (offset if is_low else -offset)
    end_y = fact.y if is_low else fact.y + fact.height
    points = ((start_x, start_y), (centre_x(fact), start_y), (centre_x(fact), end_y))
    return Edge(f"{EDGE_PREFIX}{index + 1}", Role.NEXT, points, None, hub.id, fact.id, Head.FILLED)


def build_analogy(spec: Analogy, area: Area, profile: ExplainerProfile, theme: Theme) -> Block:
    """Lay out an analogy: a band with two cards joined by a spoken label.

    Args:
        spec: The checked analogy.
        area: Where the band goes.
        profile: The sizes of the scale to draw at.
        theme: The design tokens.

    Returns:
        The block, with its closing line when the analogy has one.
    """
    rules = theme.explainer
    width, height = profile.fact_size
    middle = area.x + area.width / HALF
    top = area.y + rules.analogy_card_top
    left = replace(spec.left, tone=spec.left.tone or ANALOGY_TONES[0])
    right = replace(spec.right, tone=spec.right.tone or ANALOGY_TONES[1])
    first = card_node(
        left, ("left", middle - area.width / 4 - width / HALF, top), profile.fact_size
    )
    second = card_node(
        right, ("right", middle + area.width / 4 - width / HALF, top), profile.fact_size
    )
    band_height = rules.analogy_card_top + height + rules.analogy_bottom
    frame = strip_frame("analogy", (area.x, area.y, area.width, band_height), spec.label, spec.tone)
    block = Block([frame], [first, second], [], band_height)
    block.edges.append(
        make_edge(Wire(f"{EDGE_PREFIX}-link", Role.NEXT, spec.link), (first, second), theme)
    )
    if spec.closing:
        box = (area.x, area.y + band_height - CLOSING_UP_PX, area.width, CLOSING_HEIGHT_PX)
        block.nodes.append(
            replace(remark_node("closing", box, (spec.closing,), theme), is_centered=True)
        )
    return block
