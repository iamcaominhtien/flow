"""The draw.io cells of a Kanban board and a roadmap: cards, column pills, row heads and headers.

Each node is one cell whose style carries ``flowShape``, ``flowPlan`` and ``flowTone``, so that
``import_plan`` reads it back as the same node. What sits on a card (its title, tag and owner
circle) is a child cell. The positions come from ``html_board.card_layout``, so both outputs agree.
"""

import xml.etree.ElementTree as ET

from .drawio_common import FLOW_SHAPE_KEY, FONT_BOLD, add_geometry, add_vertex, style_string
from .drawio_plan import DASH_OPEN, PLAN_STYLE_KEY
from .drawio_plan_parts import PILL_ARC_PERCENT, detailed_icon_markup, image_style, rounded_pairs
from .drawio_screen import TONE_STYLE_KEY
from .html_board import (
    CARD_SHAPES,
    CardLayout,
    card_border,
    card_layout,
    card_look,
    pill_colors,
    tag_colors,
)
from .html_plan import BORDER_PX, INITIALS_FONT_FRACTION, UNKNOWN_TONE
from .markup import esc, fmt
from .model import Node, PlanView, Shape, Status
from .plan_scene import encode_plan
from .sizing import estimate_text_width
from .theme import Theme

DONE_FADE = 60  # percent opacity of the content of a finished card
STRIKE_OPEN = "<s>"
STRIKE_CLOSE = "</s>"
DETAIL_JOIN = " "
TEXT_SLACK_PX = 8


def add_board_node(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add a node of a Kanban board or a roadmap as a cell with the child cells on it.

    Args:
        root: The ``root`` element of the diagram.
        node: A node whose shape is one of ``html_board.BOARD_SHAPES``.
        theme: The design tokens.
    """
    view = node.plan or PlanView()
    style = {
        FLOW_SHAPE_KEY: node.shape.value,
        PLAN_STYLE_KEY: encode_plan(view),
        "html": 1,
        "fontFamily": theme.fonts.sans,
        "fontColor": theme.ink,
        "fontSize": fmt(node.font_size),
        **_STYLES[node.shape](node, view, theme),
    }
    if node.tone is not None:
        style[TONE_STYLE_KEY] = node.tone.value
    cell = add_vertex(root, f"node-{node.id}", _value(node, view, theme), style_string(style))
    add_geometry(cell, (node.x, node.y, node.width, node.height))
    if node.shape in CARD_SHAPES:
        _card_children(root, node, view, theme)
    elif node.shape is Shape.LANE_HEAD:
        _lane_children(root, node, theme)


def _value(node: Node, view: PlanView, theme: Theme) -> str:
    """Return the text written on the cell itself: a pill, or a header with its dates."""
    if node.shape is Shape.BOARD_PILL:
        return esc(" ".join(node.text))
    if node.shape is Shape.PERIOD_HEAD:
        words = esc(DETAIL_JOIN.join(node.detail))
        grey = f'<span style="font-size:{fmt(theme.planning.roadmap.period_detail_font_size)}px;'
        grey += f'color:{theme.slate}">{words}</span>'
        return f"<b>{esc(' '.join(node.text))}</b>" + (f"<br>{grey}" if node.detail else "")
    return ""


def _card_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of a card: white, with an ink outline, dashed when it is an idea."""
    pairs: dict[str, object] = {
        **rounded_pairs(card_look(node, theme).radius),
        "fillColor": theme.paper,
        "strokeColor": theme.slate if node.dashed else card_border(node, theme),
        "strokeWidth": BORDER_PX,
    }
    if node.dashed:
        pairs.update({"dashed": 1, "dashPattern": DASH_OPEN})
    return pairs


def _pill_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of a pill of a column header."""
    fill, outline, color = pill_colors(node, view, theme)
    return {
        "rounded": 1,
        "arcSize": PILL_ARC_PERCENT,
        "fillColor": fill,
        "strokeColor": outline,
        "strokeWidth": BORDER_PX,
        "fontColor": color,
        "fontStyle": FONT_BOLD,
        "whiteSpace": "nowrap",
    }


def _period_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of the header of a roadmap column."""
    rules = theme.planning.roadmap
    return {
        **rounded_pairs(rules.period_radius),
        "fillColor": theme.tones[node.tone or UNKNOWN_TONE].pill,
        "strokeColor": theme.ink,
        "strokeWidth": BORDER_PX,
        "align": "left",
        "verticalAlign": "middle",
        "spacingLeft": rules.card_pad - BORDER_PX,
        "fontSize": fmt(rules.period_font_size),
    }


def _lane_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of the card at the left of a roadmap row."""
    return {
        **rounded_pairs(theme.planning.kanban.card_radius),
        "fillColor": theme.tones[node.tone or UNKNOWN_TONE].box,
        "strokeColor": theme.ink,
        "strokeWidth": BORDER_PX,
    }


def _part(root: ET.Element, node: Node, name: str, style: dict[str, object]) -> ET.Element:
    """Add a child cell of a node, with an id made of a prefix and the id of the node."""
    cell = add_vertex(root, f"{name}-{node.id}", "", style_string({"html": 1, **style}))
    cell.set("parent", f"node-{node.id}")
    return cell


def _text_style(theme: Theme, size: float, color: str) -> dict[str, object]:
    """Return the style of a child cell that holds plain text at the top left."""
    return {
        "text": "",
        "whiteSpace": "wrap",
        "align": "left",
        "verticalAlign": "top",
        "strokeColor": "none",
        "fillColor": "none",
        "fontSize": fmt(size),
        "fontColor": color,
        "fontFamily": theme.fonts.sans,
    }


def _faded(view: PlanView) -> dict[str, object]:
    """Return the pairs that fade the content of a finished card."""
    return {"opacity": DONE_FADE, "textOpacity": DONE_FADE} if view.status is Status.DONE else {}


def _card_children(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add the title, the detail, the tag and the owner circle of a card."""
    look = card_look(node, theme)
    layout = card_layout(node, theme)
    done = view.status is Status.DONE
    title = " ".join(node.text)
    shown = f"{STRIKE_OPEN}{esc(title)}{STRIKE_CLOSE}" if done else esc(title)
    ink = theme.slate if done else theme.ink
    style = {**_text_style(theme, look.title_font, ink), "fontStyle": FONT_BOLD, **_faded(view)}
    _text_cell(root, node, ("mk-text", shown), (style, layout.title))
    if node.detail:
        style = {**_text_style(theme, look.detail_font, theme.slate), **_faded(view)}
        _text_cell(
            root, node, ("detail", esc(DETAIL_JOIN.join(node.detail))), (style, layout.detail)
        )
    if view.tag:
        _tag_cell(root, node, view, (layout, theme))
    if view.initials:
        _owner_cell(root, node, view, (layout, theme))


def _text_cell(
    root: ET.Element,
    node: Node,
    named: tuple[str, str],
    placed: tuple[dict[str, object], tuple[float, float, float, float]],
) -> None:
    """Add a child cell with some text, given its name and value and its style and box."""
    name, value = named
    style, box = placed
    cell = _part(root, node, name, style)
    cell.set("value", value)
    add_geometry(cell, box)


def _tag_cell(
    root: ET.Element, node: Node, view: PlanView, context: tuple[CardLayout, Theme]
) -> None:
    """Add the tag of a card: a small tinted pill."""
    layout, theme = context
    look = card_look(node, theme)
    fill, color = tag_colors(view, theme)
    style = {
        **rounded_pairs(look.tag_radius),
        "fillColor": fill,
        "strokeColor": "none",
        "fontColor": color,
        "fontSize": fmt(look.tag_font),
        "fontStyle": FONT_BOLD,
        "fontFamily": theme.fonts.sans,
        "whiteSpace": "nowrap",
        **_faded(view),
    }
    cell = _part(root, node, "tag", style)
    cell.set("value", esc(view.tag))
    add_geometry(cell, layout.tag)


def _owner_cell(
    root: ET.Element, node: Node, view: PlanView, context: tuple[CardLayout, Theme]
) -> None:
    """Add the circle with the initials of the owner of a card."""
    layout, theme = context
    tone = theme.tones[view.person_tone or UNKNOWN_TONE]
    style = {
        "ellipse": "",
        "fillColor": tone.pill,
        "strokeColor": theme.ink,
        "strokeWidth": BORDER_PX,
        "fontStyle": FONT_BOLD,
        "fontColor": theme.ink,
        "fontSize": fmt(layout.owner[2] * INITIALS_FONT_FRACTION),
        "fontFamily": theme.fonts.sans,
        **_faded(view),
    }
    cell = _part(root, node, "ring", style)
    cell.set("value", esc(view.initials))
    add_geometry(cell, layout.owner)


def _lane_children(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the large icon and the name pill of a roadmap row head."""
    rules = theme.planning.roadmap
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    if node.icon:
        size = rules.lane_icon_size
        image = _part(
            root, node, "mk-icon", image_style(detailed_icon_markup(node.icon, size, tone.stroke))
        )
        add_geometry(image, ((node.width - size) / 2, rules.lane_icon_top, size, size))
    name = node.text[0]
    width = estimate_text_width(name, theme.layout, rules.lane_pill_font_size)
    width += 2 * rules.lane_pill_pad + TEXT_SLACK_PX
    style = {
        "rounded": 1,
        "arcSize": PILL_ARC_PERCENT,
        "fillColor": tone.pill,
        "strokeColor": theme.ink,
        "strokeWidth": BORDER_PX,
        "fontStyle": FONT_BOLD,
        "fontColor": theme.ink,
        "fontSize": fmt(rules.lane_pill_font_size),
        "fontFamily": theme.fonts.sans,
    }
    pill = _part(root, node, "pill", style)
    pill.set("value", esc(name))
    top = node.height - rules.lane_pill_bottom - rules.lane_pill_height
    add_geometry(pill, ((node.width - width) / 2, top, width, rules.lane_pill_height))


_STYLES = {
    Shape.KANBAN_CARD: _card_style,
    Shape.ROADMAP_CARD: _card_style,
    Shape.BOARD_PILL: _pill_style,
    Shape.PERIOD_HEAD: _period_style,
    Shape.LANE_HEAD: _lane_style,
}
