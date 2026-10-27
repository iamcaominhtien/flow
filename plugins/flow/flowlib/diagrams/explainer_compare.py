"""The comparison shape of an explainer: two panels and rows read across (design 07 2.3)."""

from dataclasses import replace

from ..model import Edge, Frame, FrameVariant, Head, Node, Role, Shape, Tone
from ..theme import ExplainerProfile, Theme
from .explainer_block import Area, Block, card_node, note_node, plain_node, remark_node
from .explainer_spec import Comparison

HALF = 2
EDGE_PREFIX = "e"
VS_TEXT = "vs"
RULE_KEY = "rule"
DIVIDER_KEY = "divider"


def build_comparison(
    spec: Comparison, area: Area, profile: ExplainerProfile, theme: Theme
) -> Block:
    """Lay out two cards, the rows between them and the rule of thumb.

    Args:
        spec: The checked comparison.
        area: Where the block goes; the two sides sit on either side of its middle.
        profile: The sizes of the scale to draw at.
        theme: The design tokens.

    Returns:
        The block.
    """
    middle = area.x + area.width / HALF
    spread = profile.compare_spread
    left = replace(spec.left, tone=spec.left.tone or Tone.BLUE)
    right = replace(spec.right, tone=spec.right.tone or Tone.GREEN)
    head_width, head_height = profile.head_size
    block = Block()
    block.nodes += [
        card_node(left, ("left", middle - spread - head_width / HALF, area.y), profile.head_size),
        card_node(right, ("right", middle + spread - head_width / HALF, area.y), profile.head_size),
        _versus((middle, area.y + head_height / HALF), profile, theme),
    ]
    first = area.y + head_height + profile.compare_gap
    for index in range(len(spec.rows)):
        block.nodes += _row_nodes(
            spec, index, (middle, first + index * profile.compare_pitch), (profile, theme)
        )
    last = first + (len(spec.rows) - 1) * profile.compare_pitch + profile.cell_size[1]
    reach = theme.explainer.rule_line_extend
    block.edges.append(_divider(middle, first - reach, last + reach))
    block.height = last - area.y
    if spec.rule_text:
        block.extend(_rule(spec, Area(area.x, last + theme.explainer.rule_gap, area.width), theme))
        block.height += theme.explainer.rule_gap + theme.explainer.rule_height
    return block


def _versus(centre: tuple[float, float], profile: ExplainerProfile, theme: Theme) -> Node:
    """Build the dark ``vs`` pill between the two cards."""
    width, height = profile.vs_size
    node = plain_node(
        Shape.PILL_LABEL,
        VS_TEXT,
        (centre[0] - width / HALF, centre[1] - height / HALF, width, height),
    )
    return replace(node, text=(VS_TEXT,), font_size=theme.explainer.vs_font)


def _row_nodes(
    spec: Comparison, index: int, place: tuple[float, float], scale: tuple[ExplainerProfile, Theme]
) -> list[Node]:
    """Build the two cells of a row and the pill that names it."""
    profile, theme = scale
    middle, top = place
    row = spec.rows[index]
    cell_width, cell_height = profile.cell_size
    pill_width, pill_height = profile.label_size
    spread = profile.compare_spread
    left = plain_node(
        Shape.CELL,
        f"left-{index}",
        (middle - spread - cell_width / HALF, top, cell_width, cell_height),
    )
    right = plain_node(
        Shape.CELL,
        f"right-{index}",
        (middle + spread - cell_width / HALF, top, cell_width, cell_height),
    )
    pill_top = top + (cell_height - pill_height) / HALF
    pill = plain_node(
        Shape.PILL_LABEL,
        f"label-{index}",
        (middle - pill_width / HALF, pill_top, pill_width, pill_height),
    )
    font = theme.explainer.cell_font
    return [
        replace(left, text=(row.left,), tone=spec.left.tone or Tone.BLUE, font_size=font),
        replace(right, text=(row.right,), tone=spec.right.tone or Tone.GREEN, font_size=font),
        replace(pill, text=(row.label,), tone=Tone.AMBER, font_size=theme.explainer.label_font),
    ]


def _divider(middle: float, top: float, bottom: float) -> Edge:
    """Build the thin dashed line down the middle that the labels sit on."""
    return Edge(
        DIVIDER_KEY, Role.LIFELINE, ((middle, top), (middle, bottom)), None, None, None, Head.NONE
    )


def _rule(spec: Comparison, area: Area, theme: Theme) -> Block:
    """Build the white box with the rule of thumb."""
    rules = theme.explainer
    panel = Frame(
        RULE_KEY, area.x, area.y, area.width, rules.rule_height, None, Tone.GRAY, FrameVariant.PANEL
    )
    inner = area.width - 2 * rules.rule_pad
    title_box = (
        area.x + rules.rule_pad,
        area.y + rules.rule_title_top,
        inner,
        rules.rule_title_font,
    )
    text_box = (
        area.x + rules.rule_pad,
        area.y + rules.rule_text_top,
        inner,
        rules.rule_height - rules.rule_text_top,
    )
    title = replace(
        remark_node("rule-title", title_box, (spec.rule_title,), theme),
        font_size=rules.rule_title_font,
    )
    text = replace(
        note_node("rule-text", text_box, (spec.rule_text,), theme), font_size=rules.rule_text_font
    )
    return Block([panel], [title, text], [])
