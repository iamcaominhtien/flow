"""The draw.io cells of the planning diagrams: bars, people, org cards, mind map branches, leaves.

Each node is one cell whose style carries ``flowShape``, ``flowPlan`` and ``flowTone``, so that
``import_notation`` reads it back as the same node. What sits on a node (the progress fill, the
check, the initials, the icon, the marks) is a child cell made by ``drawio_plan_parts``.
"""

import xml.etree.ElementTree as ET

from .drawio_common import (
    FLOW_FRAME_KEY,
    FLOW_SHAPE_KEY,
    FONT_BOLD,
    add_geometry,
    add_vertex,
    style_string,
)
from .drawio_plan_parts import CHILDREN, PILL_ARC_PERCENT, rounded_pairs
from .drawio_screen import TONE_STYLE_KEY
from .html_plan import (
    BORDER_PX,
    CENTRE_BORDER_PX,
    CENTRE_RADIUS_PX,
    DETAIL_RADIUS_PX,
    DISC_PAD_PX,
    INITIALS_FONT_FRACTION,
    LEAF_ICON_GAP_PX,
    LEAF_PAD_PX,
    LEAF_RADIUS_PX,
    MIN_INITIALS_FONT_PX,
    UNDERLINE_PX,
    UNKNOWN_TONE,
    accent_of,
)
from .markup import esc, fmt
from .model import Frame, FrameVariant, MindLevel, Node, PlanView, Shape, Side, Status
from .plan_scene import encode_plan
from .theme import Theme

PANEL_ARC_PERCENT = 20
PLAN_STYLE_KEY = "flowPlan"  # a style key of ours: what the planning node shows, packed
BAND_FONT_PX = 13
BAND_PAD_PX = 14
DASH_BLOCKED = "4 3"
DASH_OPEN = "6 4"


def add_plan_node(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add a planning node as a cell with the child cells that sit on it.

    Args:
        root: The ``root`` element of the diagram.
        node: A node whose shape is one of the planning shapes.
        theme: The design tokens.
    """
    view = node.plan or PlanView()
    cell = add_vertex(root, f"node-{node.id}", _value(node, view), _style(node, view, theme))
    add_geometry(cell, (node.x, node.y, node.width, node.height))
    CHILDREN[node.shape](root, node, view, theme)


def add_plan_frame(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a panel (a white rounded box) or a band (a grey row with a bold name)."""
    pairs: dict[str, object] = {
        FLOW_FRAME_KEY: frame.variant.value,
        "rounded": 1,
        "arcSize": PANEL_ARC_PERCENT,
        "html": 1,
    }
    if frame.variant is FrameVariant.COLUMN:
        pairs.update(_column_pairs(frame, theme))
    elif frame.variant is FrameVariant.PANEL:
        pairs.update({"fillColor": theme.paper, "strokeColor": theme.rule, "strokeWidth": 1})
    else:
        pairs.update(_band_pairs(frame, theme))
    cell = add_vertex(root, f"frame-{frame.id}", esc(frame.label or ""), style_string(pairs))
    add_geometry(cell, (frame.x, frame.y, frame.width, frame.height))


def _column_pairs(frame: Frame, theme: Theme) -> dict[str, object]:
    """Return the style of a column or a row: a tint with no outline and the column radius."""
    return {
        **rounded_pairs(theme.planning.kanban.column_radius),
        "fillColor": theme.tones[frame.tone].lane,
        "strokeColor": "none",
    }


def _band_pairs(frame: Frame, theme: Theme) -> dict[str, object]:
    """Return the style of a band: a tint, no outline, the name in bold at the left."""
    return {
        "fillColor": theme.tones[frame.tone].box,
        "strokeColor": "none",
        "align": "left",
        "verticalAlign": "middle",
        "spacingLeft": BAND_PAD_PX,
        "fontColor": theme.ink,
        "fontStyle": FONT_BOLD,
        "fontSize": BAND_FONT_PX,
        "fontFamily": theme.fonts.sans,
    }


def _value(node: Node, view: PlanView) -> str:
    """Return the label of the cell of a node: the text that is written on the cell itself."""
    if node.shape is Shape.PERSON:
        return esc(view.initials or " ".join(node.text))
    if node.shape is Shape.BRANCH and view.level is MindLevel.CENTRE and node.card:
        return ""
    if node.shape in (Shape.LABEL, Shape.BRANCH, Shape.LEAF):
        return esc(" ".join(node.text))
    return ""


def _style(node: Node, view: PlanView, theme: Theme) -> str:
    """Return the full style of a node: our keys, the outline and the text."""
    pairs: dict[str, object] = {
        FLOW_SHAPE_KEY: node.shape.value,
        PLAN_STYLE_KEY: encode_plan(view),
        "html": 1,
        "fontFamily": theme.fonts.sans,
        "fontColor": theme.ink,
        "fontSize": fmt(node.font_size),
    }
    if node.tone is not None:
        pairs[TONE_STYLE_KEY] = node.tone.value
    pairs.update(_STYLES[node.shape](node, view, theme))
    return style_string(pairs)


def _person_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of a circle with initials."""
    tone = theme.tones[view.person_tone or UNKNOWN_TONE]
    size = max(MIN_INITIALS_FONT_PX, node.width * INITIALS_FONT_FRACTION)
    return {
        "ellipse": "",
        "fillColor": tone.pill,
        "strokeColor": theme.ink,
        "strokeWidth": BORDER_PX,
        "fontStyle": FONT_BOLD,
        "fontSize": fmt(size),
    }


def _align_of(node: Node, view: PlanView) -> str:
    """Return how a text is aligned: centred, or towards the centre of a mind map."""
    if node.is_centered:
        return "center"
    return "right" if view.side is Side.LEFT else "left"


def _label_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of plain text, aligned the way the HTML page aligns it."""
    align = _align_of(node, view)
    return {
        "text": "",
        "whiteSpace": "nowrap",
        "align": align,
        "verticalAlign": "middle",
        "strokeColor": "none",
        "fillColor": "none",
        "fontStyle": FONT_BOLD if view.is_bold else 0,
    }


def _milestone_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of the diamond of a milestone."""
    colors = theme.planning.milestone
    return {
        "rhombus": "",
        "fillColor": colors.fill,
        "strokeColor": colors.stroke,
        "strokeWidth": BORDER_PX,
    }


def _bar_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of a bar: a rounded box in the colours of its status."""
    colors = theme.planning.status[view.status or Status.PLANNED]
    pairs: dict[str, object] = {
        **rounded_pairs(theme.planning.gantt.bar_radius),
        "fillColor": colors.fill,
        "strokeColor": colors.stroke,
        "strokeWidth": BORDER_PX,
    }
    if view.status is Status.BLOCKED:
        pairs.update({"dashed": 1, "dashPattern": DASH_BLOCKED})
    return pairs


def _card_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of an org card: tinted, or dashed and white for an open role."""
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    pairs: dict[str, object] = {
        **rounded_pairs(theme.style.corner_radius),
        "fillColor": theme.paper if view.is_open else tone.box,
        "strokeColor": theme.slate if view.is_open else theme.ink,
        "strokeWidth": BORDER_PX,
    }
    if view.is_open:
        pairs.update({"dashed": 1, "dashPattern": DASH_OPEN})
    return pairs


def _branch_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of a branch or a group of a mind map: a pill."""
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    base: dict[str, object] = {
        "rounded": 1,
        "arcSize": PILL_ARC_PERCENT,
        "fontStyle": FONT_BOLD,
        "strokeWidth": BORDER_PX,
    }
    if view.level is MindLevel.CENTRE:
        return _centre_style(node, theme)
    if view.level is MindLevel.GROUP:
        return {
            **base,
            "fillColor": tone.box,
            "strokeColor": accent_of(node, theme),
        }
    if node.card:
        room = 2 * DISC_PAD_PX + node.height - 2 * DISC_PAD_PX if node.icon else 0
        return {
            **base,
            "fillColor": accent_of(node, theme),
            "strokeColor": theme.ink,
            "fontColor": theme.on_accent,
            "align": "left",
            "spacingLeft": room + DISC_PAD_PX,
        }
    return {**base, "fillColor": tone.pill, "strokeColor": theme.ink}


def _centre_style(node: Node, theme: Theme) -> dict[str, object]:
    """Return the style of the topic: a tinted card, or a dark pill in the plain style."""
    if not node.card:
        return {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "fillColor": theme.ink,
            "strokeColor": theme.ink,
            "fontColor": theme.paper,
            "fontStyle": FONT_BOLD,
        }
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    return {
        **rounded_pairs(CENTRE_RADIUS_PX),
        "fillColor": tone.box,
        "strokeColor": theme.ink,
        "strokeWidth": CENTRE_BORDER_PX,
    }


def _leaf_style(node: Node, view: PlanView, theme: Theme) -> dict[str, object]:
    """Return the style of a leaf: a card, an underlined phrase, or a tinted detail."""
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    if view.level is MindLevel.KEY:
        return {"fillColor": "none", "strokeColor": "none"}
    if view.level is MindLevel.DETAIL:
        return {
            **rounded_pairs(DETAIL_RADIUS_PX),
            "fillColor": tone.box,
            "strokeColor": "none",
            "align": "left",
            "spacingLeft": LEAF_PAD_PX,
        }
    if not node.card and view.level is MindLevel.LEAF:
        return {
            "fillColor": "none",
            "strokeColor": "none",
            "fontStyle": FONT_BOLD,
            "align": "right" if view.side is Side.LEFT else "left",
            "verticalAlign": "bottom",
            "spacingBottom": UNDERLINE_PX * 2,
        }
    left = theme.planning.mind.bar_width + (LEAF_PAD_PX if node.icon is None else 0)
    icon_room = theme.planning.mind.illustrated.leaf_icon + LEAF_ICON_GAP_PX if node.icon else 0
    return {
        **rounded_pairs(LEAF_RADIUS_PX),
        "fillColor": theme.paper,
        "strokeColor": accent_of(node, theme),
        "strokeWidth": BORDER_PX,
        "align": "left",
        "spacingLeft": left + (LEAF_PAD_PX + icon_room if node.icon else 0),
        "fontStyle": 0,
    }


_STYLES = {
    Shape.PERSON: _person_style,
    Shape.LABEL: _label_style,
    Shape.MILESTONE: _milestone_style,
    Shape.PLAN_BAR: _bar_style,
    Shape.PERSON_CARD: _card_style,
    Shape.BRANCH: _branch_style,
    Shape.LEAF: _leaf_style,
}
