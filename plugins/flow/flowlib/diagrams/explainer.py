"""The explainer: one question answered with cards, bands and one blue path (design 07).

See ``explainer_spec`` for the spec format. A page has one shape (layers, tree, comparison or
concept) or several sections laid out in two columns, as in the card payment example. Every
card is drawn as an illustrated card; there is no plain mode.
"""

from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace

from ..model import Node, Scene, Shape
from ..reader import SpecError
from ..theme import ExplainerProfile, Theme, load_theme
from .explainer_block import Area, Block, plain_node, prefixed
from .explainer_compare import build_comparison
from .explainer_concept import build_analogy, build_concept
from .explainer_layers import build_layers
from .explainer_spec import (
    Analogy,
    Body,
    Column,
    Comparison,
    Concept,
    ExplainerSpec,
    Layers,
    Section,
    Tree,
    read_spec,
)
from .explainer_tree import build_tree

HALF = 2
SECTION_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
EXTRA_COLUMN_WIDTH_PX = 400  # a layered flow with more columns than fit gets this much wider each

Builder = Callable[[Body, Area, ExplainerProfile, Theme], Block]


@dataclass(frozen=True)
class Page:
    """A built page: its blocks in place and the size of its canvas."""

    block: Block
    width: float
    height: float


def layout_raw(raw: object) -> Scene:
    """Lay out an explainer from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on an ``explainer`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: With every problem found.
    """
    spec = read_spec(raw)
    if not spec.sections and spec.body is None:
        raise SpecError(["spec: nothing to draw"])
    return layout(spec)


def layout(spec: ExplainerSpec) -> Scene:
    """Place the cards of a checked spec.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with the canvas sized to the page.
    """
    theme = load_theme()
    page = _sections_page(spec, theme) if spec.sections else _single_page(spec, theme)
    block = page.block
    return Scene(
        width=page.width,
        height=page.height,
        title=spec.title,
        description=spec.description,
        frames=tuple(block.frames),
        nodes=tuple(block.nodes),
        edges=tuple(block.edges),
    )


def _build(body: Body, area: Area, profile: ExplainerProfile, theme: Theme) -> Block:
    """Build the block of one body at an area."""
    if isinstance(body, Layers):
        return build_layers(body, area, profile, theme)
    if isinstance(body, Tree):
        return build_tree(body, area, profile, theme)
    if isinstance(body, Comparison):
        return build_comparison(body, area, profile, theme)
    if isinstance(body, Concept):
        return build_concept(body, area, profile, theme)
    return build_analogy(body, area, profile, theme)


def _top_of(body: Body, theme: Theme) -> float:
    """Return where the first block of a page of one shape starts, from the top."""
    rules = theme.explainer
    tops = {
        Layers: rules.layers_top,
        Tree: rules.tree_top,
        Comparison: rules.compare_top,
        Concept: rules.concept_top,
        Analogy: rules.concept_top,
    }
    return tops[type(body)]


def _single_page(spec: ExplainerSpec, theme: Theme) -> Page:
    """Build a page with one shape in it."""
    rules = theme.explainer
    body = spec.body
    assert body is not None
    width = _page_width(body, theme)
    margin = rules.page_margin
    area = Area(margin, _top_of(body, theme), width - 2 * margin)
    if isinstance(body, Tree):
        area = Area(margin + rules.tree_root_inset, area.y, area.width - rules.tree_root_inset)
    block = _build(body, area, theme.explainer.standard, theme)
    return Page(block, width, area.y + block.height + rules.bottom_margin)


def _page_width(body: Body, theme: Theme) -> float:
    """Return the canvas width of a page of one shape."""
    rules = theme.explainer
    if isinstance(body, Layers):
        columns = max(_column_count(body), 1)
        wanted = (
            2 * rules.page_margin
            + rules.standard.col_offset
            + (columns - 1) * rules.standard.col_pitch
            + rules.standard.card_size[0]
            + rules.page_margin
        )
        return max(rules.canvas_width, wanted)
    return rules.narrow_width


def _column_count(body: Layers) -> int:
    """Return how many columns the widest band of a layered flow uses."""
    widest = 0
    for band in body.bands:
        used = [card.col for card in band.cards if card.col is not None]
        widest = max(widest, (max(used) + 1) if used else len(band.cards))
    return widest


def _sections_page(spec: ExplainerSpec, theme: Theme) -> Page:
    """Build a page of sections in two columns, and a full-width section under them."""
    rules = theme.explainer
    margin = rules.page_margin
    left_x = margin
    right_x = margin + rules.left_column_width + rules.column_gap
    full_width = rules.left_column_width + rules.column_gap + rules.right_column_width
    cursors = {Column.LEFT: rules.first_section_top, Column.RIGHT: rules.first_section_top}
    columns = {
        Column.LEFT: Area(left_x, 0, rules.left_column_width),
        Column.RIGHT: Area(right_x, 0, rules.right_column_width),
    }
    whole = Block()
    letters = iter(SECTION_LETTERS)
    for index, section in enumerate(spec.sections):
        prefix = f"s{index + 1}."
        if section.column is Column.FULL:
            top = max(cursors.values()) - rules.section_gap + rules.column_gap
            area = Area(left_x, top, full_width)
            part = _section_block(section, (area, letters), (prefix, theme))
            cursors = dict.fromkeys(cursors, top + part.height + rules.section_gap)
        else:
            area = replace(columns[section.column], y=cursors[section.column])
            part = _section_block(section, (area, letters), (prefix, theme))
            cursors[section.column] += part.height + rules.section_gap
        whole.extend(part)
    bottom = max(cursors.values()) - rules.section_gap
    return Page(whole, 2 * margin + full_width, bottom + rules.bottom_margin)


def _section_block(
    section: Section, context: tuple[Area, Iterator[str]], naming: tuple[str, Theme]
) -> Block:
    """Build one section: its letter heading, if it has a title, and its shape under it."""
    area, letters = context
    prefix, theme = naming
    rules = theme.explainer
    profile = rules.compact
    block = Block()
    top = area.y
    if section.title:
        block.nodes.append(_heading(section.title, next(letters), area, rules.section_head_size))
        top += rules.section_head_gap
    body = _build(section.body, replace(area, y=top), profile, theme)
    block.extend(body)
    block.height = top - area.y + body.height
    return prefixed(block, prefix)


def _heading(title: str, letter: str, area: Area, size: float) -> Node:
    """Build the heading of a section: a dark circle with its letter, then the title."""
    node = plain_node(Shape.SECTION_HEAD, f"head-{letter}", (area.x, area.y, area.width, size))
    return replace(node, text=(title,), number=letter)
