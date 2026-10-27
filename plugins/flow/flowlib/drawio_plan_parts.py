"""The child cells of the planning nodes in draw.io: fill, check, circle, icon, bar and marks.

A child cell moves with its node. ``drawio_plan`` adds the node itself and calls ``CHILDREN``
for the shape.
"""

import base64
import xml.etree.ElementTree as ET

from .drawio_common import FONT_BOLD, add_geometry, add_vertex, style_string
from .html_plan import (
    BORDER_PX,
    CARD_ICON_RIGHT_PX,
    CENTRE_GAP_PX,
    CENTRE_ICON_FRACTION,
    CENTRE_PAD_PX,
    CENTRE_PILL_HEIGHT_PX,
    CENTRE_PILL_PAD_PX,
    DISC_PAD_PX,
    INITIALS_FONT_FRACTION,
    LEAF_ICON_GAP_PX,
    LEAF_PAD_PX,
    MARK_FONT_PX,
    MARK_GAP_PX,
    MARK_HEIGHT_PX,
    MARK_PADDING_PX,
    MARK_RIGHT_PX,
    MIN_CHECK_BAR_PX,
    UNDERLINE_PX,
    UNKNOWN_TONE,
    accent_of,
    check_svg,
)
from .markup import esc, fmt
from .model import MindLevel, Node, PlanView, Shape, Status
from .sizing import estimate_text_width
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
PILL_ARC_PERCENT = 50
TEXT_SLACK_PX = 8
OPEN_ROLE_FADE = 55  # percent opacity of the content of an open role card
CHECK_CHARACTER = "\u2713"  # the check of the mark of a done idea


def rounded_pairs(radius: float) -> dict[str, object]:
    """Return the style pairs of a rectangle with rounded corners of a radius in pixels."""
    return {"rounded": 1, "absoluteArcSize": 1, "arcSize": 2 * radius}


def _child(root: ET.Element, node: Node, name: str, style: dict[str, object]) -> ET.Element:
    """Add a child cell of a node, with an id made of a prefix and the id of the node."""
    cell = add_vertex(root, f"{name}-{node.id}", "", style_string(style))
    cell.set("parent", f"node-{node.id}")
    return cell


def image_style(svg: str) -> dict[str, object]:
    """Return the style of a cell that shows an SVG image."""
    return {
        "shape": "image",
        "image": "data:image/svg+xml," + base64.b64encode(svg.encode()).decode(),
    }


def detailed_icon_markup(name: str, size: float, stroke: str) -> str:
    """Return an icon as standalone SVG, detailed when there is a detailed form."""
    attrs = f'xmlns="{SVG_NAMESPACE}"'
    if has_detailed_icon(name):
        return detailed_icon_svg(name, size, stroke, attrs)
    return icon_svg(name, size, stroke, attrs)


def _flat_icon_svg(name: str, size: float, stroke: str) -> str:
    """Return an icon as standalone SVG in its flat form, which is what small icons use."""
    return icon_svg(name, size, stroke, f'xmlns="{SVG_NAMESPACE}"')


def _no_children(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add nothing: the node is one cell."""


def _bar_children(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add the progress fill, the check or the reason of a bar."""
    colors = theme.planning.status[view.status or Status.PLANNED]
    rules = theme.planning.gantt
    if view.status is Status.IN_PROGRESS and view.progress > 0:
        style = {
            **rounded_pairs(rules.bar_radius),
            "fillColor": colors.mark,
            "strokeColor": colors.stroke,
        }
        style["strokeWidth"] = BORDER_PX
        add_geometry(
            _child(root, node, "fill", style),
            (0, 0, node.width * min(view.progress, 1.0), node.height),
        )
    if view.status is Status.DONE and node.height >= MIN_CHECK_BAR_PX:
        image = _child(
            root,
            node,
            "check",
            image_style(check_svg(rules.check_size, colors.mark, f'xmlns="{SVG_NAMESPACE}"')),
        )
        add_geometry(
            image,
            (
                rules.bar_inset,
                (node.height - rules.check_size) / 2,
                rules.check_size,
                rules.check_size,
            ),
        )
    if view.status is Status.BLOCKED and view.reason:
        _reason_cell(root, node, view, theme)


def _reason_cell(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add the short reason of a blocked task after the end of its bar."""
    rules = theme.planning.gantt
    style = {
        "text": "",
        "html": 1,
        "whiteSpace": "nowrap",
        "align": "left",
        "verticalAlign": "middle",
        "strokeColor": "none",
        "fillColor": "none",
        "fontStyle": FONT_BOLD,
        "fontSize": rules.week_font_size,
        "fontColor": theme.planning.status[Status.BLOCKED].mark,
        "fontFamily": theme.fonts.sans,
    }
    cell = add_vertex(root, f"reason-{node.id}", esc(view.reason), style_string(style))
    cell.set("parent", f"node-{node.id}")
    width = estimate_text_width(view.reason, theme.layout, rules.week_font_size) + TEXT_SLACK_PX
    add_geometry(cell, (node.width + rules.reason_gap, 0, width, node.height))


def _card_children(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add the parts of an org card: initials, name and role, or pill, role and icon."""
    if not node.text:
        return
    if node.card:
        _illustrated_card(root, node, view, theme)
    else:
        _plain_card(root, node, view, theme)


def _faded(view: PlanView) -> dict[str, object]:
    """Return the pairs that fade the content of an open role card."""
    return {"opacity": OPEN_ROLE_FADE, "textOpacity": OPEN_ROLE_FADE} if view.is_open else {}


def _plain_card(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add the initials circle, and the name and the role, of a plain card."""
    rules = theme.planning.org
    tone = theme.tones[view.person_tone or UNKNOWN_TONE]
    ring = {
        "ellipse": "", "html": 1, "fillColor": tone.pill, "strokeColor": theme.ink,
        "strokeWidth": BORDER_PX, "fontStyle": FONT_BOLD, "fontColor": theme.ink,
        "fontSize": fmt(rules.person_size * INITIALS_FONT_FRACTION), "fontFamily": theme.fonts.sans,
    }  # fmt: skip
    circle = _child(root, node, "ring", ring)
    circle.set("value", esc(view.initials))
    top = (node.height - rules.person_size) / 2
    add_geometry(
        circle, (rules.pad - BORDER_PX, top - BORDER_PX, rules.person_size, rules.person_size)
    )
    left = rules.pad + rules.person_size + rules.pad / 2 - BORDER_PX
    name = f"<b>{esc(' '.join(node.text))}</b>"
    role_style = f"font-size:{fmt(rules.role_font_size)}px;color:{theme.slate}"
    role = f'<span style="{role_style}">{esc(" ".join(node.detail))}</span>'
    style = {
        "text": "", "html": 1, "whiteSpace": "wrap", "align": "left", "verticalAlign": "middle",
        "strokeColor": "none", "fillColor": "none", "fontSize": fmt(rules.name_font_size),
        "fontColor": theme.ink, "fontFamily": theme.fonts.sans,
    }  # fmt: skip
    cell = add_vertex(root, f"mk-text-{node.id}", f"{name}<br>{role}", style_string(style))
    cell.set("parent", f"node-{node.id}")
    add_geometry(cell, (left, 0, node.width - left - rules.pad, node.height))


def _illustrated_card(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add the name pill, the role and the person icon of an illustrated card."""
    rules = theme.planning.org
    tone = theme.tones[view.person_tone or node.tone or UNKNOWN_TONE]
    name = " ".join(node.text)
    pill_style = {
        "rounded": 1, "arcSize": PILL_ARC_PERCENT, "html": 1, "fillColor": tone.pill,
        "strokeColor": theme.ink, "strokeWidth": BORDER_PX, "fontStyle": FONT_BOLD,
        "fontSize": fmt(rules.name_font_size), "fontColor": theme.ink,
        "fontFamily": theme.fonts.sans, **_faded(view),
    }  # fmt: skip
    pill = add_vertex(root, f"pill-{node.id}", esc(name), style_string(pill_style))
    pill.set("parent", f"node-{node.id}")
    width = estimate_text_width(name, theme.layout, rules.name_font_size) + 2 * rules.pad
    add_geometry(pill, (rules.pad, rules.pad, width, rules.pill_height))
    detail_style = {
        "text": "", "html": 1, "align": "left", "verticalAlign": "top", "strokeColor": "none",
        "fillColor": "none", "fontSize": fmt(rules.role_font_size), "fontColor": theme.slate,
        "fontFamily": theme.fonts.sans, **_faded(view),
    }  # fmt: skip
    detail = add_vertex(
        root, f"detail-{node.id}", esc(" ".join(node.detail)), style_string(detail_style)
    )
    detail.set("parent", f"node-{node.id}")
    add_geometry(detail, (rules.pad, rules.pad + rules.pill_height + 12, node.width / 2, rules.pad))
    icon = _child(
        root,
        node,
        "mk-icon",
        {
            **image_style(detailed_icon_markup(node.icon or "user", rules.icon_size, tone.stroke)),
            **_faded(view),
        },
    )
    left = node.width - CARD_ICON_RIGHT_PX - rules.icon_size
    add_geometry(
        icon, (left, (node.height - rules.icon_size) / 2, rules.icon_size, rules.icon_size)
    )


def _branch_children(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add what sits on a branch: the topic's parts, the small icon, or the round icon."""
    if view.level is MindLevel.CENTRE:
        _centre_children(root, node, theme)
    elif not node.icon or view.level is MindLevel.GROUP:
        return
    elif node.card:
        _round_icon(root, node, theme)
    else:
        _small_icon(root, node, theme)


def _small_icon(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the small icon at the left of the name of a plain branch."""
    size = theme.planning.mind.plain.leaf_icon
    name_width = estimate_text_width(" ".join(node.text), theme.layout, node.font_size)
    left = node.width / 2 - size - 2 * LEAF_ICON_GAP_PX - name_width / 2
    icon = _child(
        root, node, "mk-icon", image_style(_flat_icon_svg(node.icon or "", size, theme.ink))
    )
    add_geometry(icon, (left, (node.height - size) / 2, size, size))


def _round_icon(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the white disc of an illustrated branch, and the icon on it."""
    size = min(theme.planning.mind.illustrated.disc, node.height - 2 * DISC_PAD_PX)
    look = {"ellipse": "", "fillColor": theme.paper, "strokeColor": theme.ink}
    look["strokeWidth"] = BORDER_PX
    disc = _child(root, node, "disc", look)
    add_geometry(disc, (DISC_PAD_PX, (node.height - size) / 2, size, size))
    inner = size - 2 * BORDER_PX
    image = image_style(detailed_icon_markup(node.icon or "", inner, accent_of(node, theme)))
    icon = _child(root, node, "mk-icon", image)
    add_geometry(icon, (DISC_PAD_PX + BORDER_PX, (node.height - inner) / 2, inner, inner))


def _centre_children(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the large icon, the name pill and the goal line of the topic of a mind map."""
    if not node.card:
        return
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    size = node.height * CENTRE_ICON_FRACTION
    icon = _child(
        root,
        node,
        "mk-icon",
        image_style(detailed_icon_markup(node.icon or "idea", size, tone.stroke)),
    )
    add_geometry(icon, ((node.width - size) / 2, CENTRE_PAD_PX, size, size))
    name = " ".join(node.text)
    pill_style = {
        "rounded": 1, "arcSize": PILL_ARC_PERCENT, "html": 1, "fillColor": tone.pill,
        "strokeColor": theme.ink, "strokeWidth": BORDER_PX, "fontStyle": FONT_BOLD,
        "fontSize": fmt(node.font_size), "fontColor": theme.ink, "fontFamily": theme.fonts.sans,
    }  # fmt: skip
    pill = add_vertex(root, f"pill-{node.id}", esc(name), style_string(pill_style))
    pill.set("parent", f"node-{node.id}")
    width = estimate_text_width(name, theme.layout, node.font_size) + 2 * CENTRE_PILL_PAD_PX
    top = CENTRE_PAD_PX + size + CENTRE_GAP_PX
    add_geometry(pill, ((node.width - width) / 2, top, width, CENTRE_PILL_HEIGHT_PX))
    goal_style = {
        "text": "", "html": 1, "align": "center", "verticalAlign": "top", "strokeColor": "none",
        "fillColor": "none", "fontSize": fmt(theme.layout.detail_font_size + 1),
        "fontColor": theme.slate, "fontFamily": theme.fonts.sans,
    }  # fmt: skip
    goal = add_vertex(
        root, f"detail-{node.id}", esc(" ".join(node.detail)), style_string(goal_style)
    )
    goal.set("parent", f"node-{node.id}")
    goal_top = top + CENTRE_PILL_HEIGHT_PX + CENTRE_GAP_PX
    add_geometry(goal, (0, goal_top, node.width, theme.layout.detail_line_height))


def _leaf_children(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add the colour bar, the icon, the underline and the marks of a leaf."""
    if not node.card and view.level is MindLevel.LEAF:
        line = _child(
            root,
            node,
            "line",
            {"fillColor": accent_of(node, theme), "strokeColor": "none"},
        )
        add_geometry(line, (0, node.height - UNDERLINE_PX, node.width, UNDERLINE_PX))
        return
    if view.level not in (MindLevel.DETAIL, MindLevel.KEY):
        _bar_and_icon(root, node, theme)
    _marks(root, node, view, theme)


def _bar_and_icon(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the colour bar at the left of a card, and its small icon."""
    rules = theme.planning.mind
    bar = _child(
        root,
        node,
        "bar",
        {
            "fillColor": accent_of(node, theme),
            "strokeColor": "none",
            "rounded": 0,
        },
    )
    add_geometry(bar, (0, 0, rules.bar_width, node.height))
    if not node.icon:
        return
    size = rules.illustrated.leaf_icon
    icon = _child(
        root,
        node,
        "mk-icon",
        image_style(_flat_icon_svg(node.icon, size, accent_of(node, theme))),
    )
    add_geometry(icon, (rules.bar_width + LEAF_PAD_PX, (node.height - size) / 2, size, size))


def _marks(root: ET.Element, node: Node, view: PlanView, theme: Theme) -> None:
    """Add the marks on the right of an idea: done, priority, hidden ideas and owner."""
    widths = _mark_widths(view, theme)
    gaps = MARK_GAP_PX * max(len(widths) - 1, 0)
    x = node.width - MARK_RIGHT_PX - sum(widths.values()) - gaps
    if view.level is MindLevel.KEY:
        x = 0.0
    for name, width in widths.items():
        cell = _mark_cell(root, node, name, (view, theme))
        add_geometry(cell, (x, (node.height - MARK_HEIGHT_PX) / 2, width, MARK_HEIGHT_PX))
        x += width + MARK_GAP_PX


def _mark_widths(view: PlanView, theme: Theme) -> dict[str, float]:
    """Return the width of each mark an idea has, in the order they are drawn."""
    widths: dict[str, float] = {}
    if view.status is Status.DONE:
        widths["done"] = MARK_HEIGHT_PX
    if view.priority:
        widths["priority"] = _pill_width(f"P{view.priority}", theme)
    if view.hidden:
        widths["more"] = _pill_width(f"+{view.hidden}", theme)
    if view.initials:
        widths["owner"] = theme.planning.mind.owner_size
    return widths


def _pill_width(text: str, theme: Theme) -> float:
    """Return the estimated width of a small pill with a short text."""
    return estimate_text_width(text, theme.layout, MARK_FONT_PX) + 2 * MARK_PADDING_PX


def _mark_cell(
    root: ET.Element, node: Node, name: str, context: tuple[PlanView, Theme]
) -> ET.Element:
    """Add the cell of one mark and return it, so that its geometry can be set."""
    view, theme = context
    base = {"html": 1, "fontStyle": FONT_BOLD, "fontSize": MARK_FONT_PX}
    base["fontFamily"] = theme.fonts.sans
    if name == "owner":
        tone = theme.tones[view.person_tone or UNKNOWN_TONE]
        look = {"ellipse": "", "fillColor": tone.pill, "strokeColor": theme.ink}
        look.update({"strokeWidth": BORDER_PX, "fontColor": theme.ink})
        text = view.initials
    elif name == "done":
        colors = theme.planning.marks[name]
        look = {"ellipse": "", "fillColor": colors.fill, "strokeColor": "none"}
        look["fontColor"] = colors.text
        text = CHECK_CHARACTER
    else:
        key = f"priority_{view.priority}" if name == "priority" else name
        colors = theme.planning.marks[key]
        look = {"rounded": 1, "arcSize": PILL_ARC_PERCENT, "fillColor": colors.fill}
        look.update({"strokeColor": "none", "fontColor": colors.text})
        text = f"P{view.priority}" if name == "priority" else f"+{view.hidden}"
    cell = _child(root, node, f"mk-{name}", {**base, **look})
    cell.set("value", esc(text))
    return cell


CHILDREN = {
    Shape.PERSON: _no_children,
    Shape.LABEL: _no_children,
    Shape.MILESTONE: _no_children,
    Shape.PLAN_BAR: _bar_children,
    Shape.PERSON_CARD: _card_children,
    Shape.BRANCH: _branch_children,
    Shape.LEAF: _leaf_children,
}
