"""Draw the cards, pills and heads of a Kanban board and of a roadmap as HTML.

A card shows a title, a small tag and, when it has an owner, a circle with initials (the same
circle as in a Gantt chart or an org chart). The same positions are used by ``drawio_board``,
which asks ``card_layout`` for them.
"""

from dataclasses import dataclass

from .html_plan import (
    BOLD_WEIGHT,
    BORDER_PX,
    PILL_RADIUS_PX,
    SHADOW_DROP_PX,
    UNKNOWN_TONE,
    circle_html,
    icon_markup,
)
from .markup import esc, fmt, px, tag
from .model import Node, PillKind, PlanView, Shape, Status, Tone
from .sizing import estimate_text_width
from .theme import Theme

ABSOLUTE = {"position": "absolute"}
BOARD_SHAPES = (
    Shape.KANBAN_CARD,
    Shape.ROADMAP_CARD,
    Shape.BOARD_PILL,
    Shape.LANE_HEAD,
    Shape.PERIOD_HEAD,
)
LINE_HEIGHT = 1.3
TAG_WEIGHT = 600
DETAIL_GAP_PX = 2
DASH_STYLE = "dashed"
CARD_SHAPES = (Shape.KANBAN_CARD, Shape.ROADMAP_CARD)


@dataclass(frozen=True)
class CardLook:
    """The sizes of the parts of a card, taken from the rules of its diagram."""

    pad: float
    radius: float
    title_font: float
    detail_font: float
    title_top: float
    tag_height: float
    tag_font: float
    tag_pad: float
    tag_radius: float
    tag_gap: float
    tag_bottom: float | None  # distance of the tag from the bottom; None: it follows the title
    owner_size: float
    owner_right: float
    owner_bottom: float
    done_opacity: float


@dataclass(frozen=True)
class CardLayout:
    """Where the parts of a card are, as ``(x, y, width, height)`` relative to the card."""

    title: tuple[float, float, float, float]
    detail: tuple[float, float, float, float]
    tag: tuple[float, float, float, float]
    owner: tuple[float, float, float, float]


def is_board_node(node: Node) -> bool:
    """Tell whether a node is drawn by this module."""
    return node.shape in BOARD_SHAPES


def card_look(node: Node, theme: Theme) -> CardLook:
    """Return the sizes of a card: those of a Kanban card, or of a roadmap card.

    Args:
        node: A node whose shape is ``KANBAN_CARD`` or ``ROADMAP_CARD``.
        theme: The design tokens.

    Returns:
        The look of the card.
    """
    board, road = theme.planning.kanban, theme.planning.roadmap
    is_board = node.shape is Shape.KANBAN_CARD
    return CardLook(
        pad=board.card_pad if is_board else road.card_pad,
        radius=board.card_radius if is_board else road.card_radius,
        title_font=board.title_font_size if is_board else road.title_font_size,
        detail_font=board.detail_font_size if is_board else road.detail_font_size,
        title_top=board.title_top if is_board else road.title_top,
        tag_height=board.tag_height,
        tag_font=board.tag_font_size,
        tag_pad=board.tag_pad,
        tag_radius=board.tag_radius,
        tag_gap=road.tag_gap,
        tag_bottom=board.tag_bottom if is_board else None,
        owner_size=board.owner_size if is_board else road.owner_size,
        owner_right=board.owner_right if is_board else road.owner_right,
        owner_bottom=board.owner_bottom if is_board else road.owner_bottom,
        done_opacity=board.done_opacity,
    )


def card_layout(node: Node, theme: Theme) -> CardLayout:
    """Place the title, the detail, the tag and the owner circle of a card.

    Args:
        node: A card.
        theme: The design tokens.

    Returns:
        The boxes of the parts. A part the card does not have still gets a box, which is not drawn.
    """
    look = card_look(node, theme)
    view = node.plan or PlanView()
    width = node.width - 2 * look.pad
    title_height = len(node.text) * look.title_font * LINE_HEIGHT
    title = (look.pad, look.title_top, width, title_height)
    detail_top = look.title_top + title_height + DETAIL_GAP_PX
    detail_height = len(node.detail) * look.detail_font * LINE_HEIGHT
    tag_width = tag_width_of(view.tag, look, theme)
    if look.tag_bottom is None:
        tag_top = look.title_top + title_height + look.tag_gap
        detail_top = tag_top + look.tag_height + look.tag_gap
    else:
        tag_top = node.height - look.tag_bottom - look.tag_height
    tag_box = (look.pad, tag_top, tag_width, look.tag_height)
    owner = (
        node.width - look.owner_right - look.owner_size,
        node.height - look.owner_bottom - look.owner_size,
        look.owner_size,
        look.owner_size,
    )
    return CardLayout(title, (look.pad, detail_top, width, detail_height), tag_box, owner)


def tag_width_of(text: str, look: CardLook, theme: Theme) -> float:
    """Return the width of a tag: its text, estimated, and the padding at both ends."""
    return estimate_text_width(text, theme.layout, look.tag_font) + 2 * look.tag_pad


def tag_colors(view: PlanView, theme: Theme) -> tuple[str, str]:
    """Return the fill and the text colour of the tag of a card.

    Args:
        view: The planning view of the card.
        theme: The design tokens.

    Returns:
        A tint and the colour that reads on it, from the tone of the tag.
    """
    colors = theme.tones[view.tag_tone or UNKNOWN_TONE]
    return colors.box, colors.label


def card_border(node: Node, theme: Theme) -> str:
    """Return the colour of the outline of a card: ink, slate for a finished card."""
    view = node.plan or PlanView()
    return theme.slate if view.status is Status.DONE else theme.ink


def pill_colors(node: Node, view: PlanView, theme: Theme) -> tuple[str, str, str]:
    """Return the fill, the outline and the text colour of a pill of a column header.

    Args:
        node: The pill.
        view: Its planning view, which says what it states.
        theme: The design tokens.

    Returns:
        The three colours; the outline equals the fill for a pill that has none.
    """
    if view.pill is PillKind.COUNT:
        return theme.ink, theme.ink, theme.paper
    if view.pill is PillKind.FULL:
        red = theme.tones[Tone.RED].accent
        return red, red, theme.on_accent
    if view.pill is PillKind.LIMIT:
        return theme.paper, theme.ink, theme.ink
    return theme.tones[node.tone or UNKNOWN_TONE].pill, theme.ink, theme.ink


def board_node_html(node: Node, theme: Theme) -> str:
    """Draw one node of a Kanban board or a roadmap.

    Args:
        node: A node whose shape is one of ``BOARD_SHAPES``.
        theme: The design tokens.

    Returns:
        The markup of the node.
    """
    view = node.plan or PlanView()
    box = {
        **ABSOLUTE,
        "left": px(node.x),
        "top": px(node.y),
        "width": px(node.width),
        "height": px(node.height),
    }
    return tag("div", box, _DRAWERS[node.shape](node, view, theme), data_id=node.id)


def board_text_room(node: Node, theme: Theme) -> float | None:
    """Return how wide the text of a board node may be, or None when it is not checked.

    Args:
        node: A node whose shape is one of ``BOARD_SHAPES``.
        theme: The design tokens.

    Returns:
        The width of the text between its padding, in pixels.
    """
    if node.shape in CARD_SHAPES:
        return node.width - 2 * card_look(node, theme).pad
    if node.shape is Shape.PERIOD_HEAD:
        return node.width - 2 * theme.planning.roadmap.card_pad
    if node.shape is Shape.LANE_HEAD:
        return node.width - 2 * theme.planning.roadmap.lane_pill_pad
    return None


def _fill_box(extra: dict[str, str]) -> dict[str, str]:
    """Return the style of a box that fills its node, with ``extra`` properties on top."""
    return {
        **ABSOLUTE,
        "left": "0",
        "top": "0",
        "width": "100%",
        "height": "100%",
        "box-sizing": "border-box",
        **extra,
    }


def _part_box(box: tuple[float, float, float, float]) -> dict[str, str]:
    """Return the position and size of a part of a card as CSS."""
    x, y, width, height = box
    return {**ABSOLUTE, "left": px(x), "top": px(y), "width": px(width), "height": px(height)}


def _card_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw a card: a white box, its title, its detail, its tag and its owner."""
    look = card_look(node, theme)
    is_done = view.status is Status.DONE
    outline = DASH_STYLE if node.dashed else "solid"
    border = theme.slate if node.dashed else card_border(node, theme)
    style = _fill_box(
        {
            "background": theme.paper,
            "border": f"{px(BORDER_PX)} {outline} {border}",
            "border-radius": px(look.radius),
        }
    )
    layout = card_layout(node, theme)
    inside = _title_html(node, view, layout, (look, theme))
    inside += _detail_html(node, layout, look, theme)
    inside += _tag_html(view, layout, (look, theme))
    inside += _owner_html(view, layout, theme)
    if is_done:
        inside = tag("div", _fill_box({"opacity": fmt(look.done_opacity)}), inside)
    return tag("div", style, inside)


def _title_html(
    node: Node, view: PlanView, layout: CardLayout, context: tuple[CardLook, Theme]
) -> str:
    """Draw the title of a card, struck through when the card is done."""
    look, theme = context
    style = _part_box(layout.title)
    style.update(
        {
            "font-size": px(look.title_font),
            "font-weight": str(BOLD_WEIGHT),
            "line-height": fmt(LINE_HEIGHT),
            "color": theme.slate if view.status is Status.DONE else theme.ink,
        }
    )
    if view.status is Status.DONE:
        style["text-decoration"] = "line-through"
    return tag("div", style, "<br>".join(esc(line) for line in node.text))


def _detail_html(node: Node, layout: CardLayout, look: CardLook, theme: Theme) -> str:
    """Draw the small grey line under the title, when the card has one."""
    if not node.detail:
        return ""
    style = _part_box(layout.detail)
    style.update(
        {
            "font-size": px(look.detail_font),
            "line-height": fmt(LINE_HEIGHT),
            "color": theme.slate,
        }
    )
    return tag("div", style, "<br>".join(esc(line) for line in node.detail))


def _tag_html(view: PlanView, layout: CardLayout, context: tuple[CardLook, Theme]) -> str:
    """Draw the tag of a card: a small tinted pill with its kind or its state."""
    look, theme = context
    if not view.tag:
        return ""
    fill, color = tag_colors(view, theme)
    style = _part_box(layout.tag)
    style.update(
        {
            "background": fill,
            "color": color,
            "border-radius": px(look.tag_radius),
            "font-size": px(look.tag_font),
            "font-weight": str(TAG_WEIGHT),
            "display": "flex",
            "align-items": "center",
            "justify-content": "center",
            "white-space": "nowrap",
        }
    )
    return tag("div", style, esc(view.tag))


def _owner_html(view: PlanView, layout: CardLayout, theme: Theme) -> str:
    """Draw the circle with the initials of the owner, when the card has an owner."""
    if not view.initials:
        return ""
    box = _part_box(layout.owner)
    return tag("div", box, circle_html(view.initials, view.person_tone, layout.owner[2], theme))


def _pill_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw a pill of a column header: the name, the count or the limit."""
    fill, outline, color = pill_colors(node, view, theme)
    is_name = view.pill is PillKind.NAME or view.pill is None
    style = _fill_box(
        {
            "border-radius": px(PILL_RADIUS_PX),
            "background": fill,
            "border": f"{px(BORDER_PX)} solid {outline}",
            "color": color,
            "display": "flex",
            "align-items": "center",
            "justify-content": "center",
            "font-size": px(node.font_size),
            "font-weight": str(BOLD_WEIGHT),
            "white-space": "nowrap",
        }
    )
    if is_name and theme.style.shadow:
        style["box-shadow"] = f"0 {px(SHADOW_DROP_PX)} 0 {theme.ink}"
    return tag("div", style, esc(" ".join(node.text)))


def _period_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw the header of a roadmap column: its name in bold and its dates in words."""
    rules = theme.planning.roadmap
    style = _fill_box(
        {
            "background": theme.tones[node.tone or UNKNOWN_TONE].pill,
            "border": f"{px(BORDER_PX)} solid {theme.ink}",
            "border-radius": px(rules.period_radius),
            "padding-left": px(rules.card_pad - BORDER_PX),
            "display": "flex",
            "flex-direction": "column",
            "justify-content": "center",
            "color": theme.ink,
        }
    )
    name = tag(
        "div",
        {
            "font-size": px(rules.period_font_size),
            "font-weight": str(BOLD_WEIGHT),
            "line-height": fmt(LINE_HEIGHT),
        },
        esc(" ".join(node.text)),
    )
    words = tag(
        "div",
        {"font-size": px(rules.period_detail_font_size), "color": theme.slate},
        esc(" ".join(node.detail)),
    )
    return tag("div", style, name + (words if node.detail else ""))


def _lane_head_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw the card at the left of a roadmap row: a large icon and the name of the theme."""
    rules = theme.planning.roadmap
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    style = _fill_box(
        {
            "background": tone.box,
            "border": f"{px(BORDER_PX)} solid {theme.ink}",
            "border-radius": px(theme.planning.kanban.card_radius),
        }
    )
    pill = {
        **ABSOLUTE,
        "left": "50%",
        "bottom": px(rules.lane_pill_bottom),
        "transform": "translateX(-50%)",
        "height": px(rules.lane_pill_height),
        "box-sizing": "border-box",
        "padding": f"0 {px(rules.lane_pill_pad)}",
        "border-radius": px(PILL_RADIUS_PX),
        "background": tone.pill,
        "border": f"{px(BORDER_PX)} solid {theme.ink}",
        "display": "flex",
        "align-items": "center",
        "font-size": px(rules.lane_pill_font_size),
        "font-weight": str(BOLD_WEIGHT),
        "color": theme.ink,
        "white-space": "nowrap",
    }
    if theme.style.shadow:
        pill["box-shadow"] = f"0 {px(SHADOW_DROP_PX)} 0 {theme.ink}"
    return tag("div", style, _lane_icon_html(node, theme) + tag("div", pill, esc(node.text[0])))


def _lane_icon_html(node: Node, theme: Theme) -> str:
    """Draw the large icon of a roadmap row, centred above its name."""
    if not node.icon:
        return ""
    rules = theme.planning.roadmap
    box = {
        **ABSOLUTE,
        "left": px((node.width - rules.lane_icon_size) / 2 - BORDER_PX),
        "top": px(rules.lane_icon_top - BORDER_PX),
        "width": px(rules.lane_icon_size),
        "height": px(rules.lane_icon_size),
    }
    place = 'style="position:absolute;left:0;top:0"'
    stroke = theme.tones[node.tone or UNKNOWN_TONE].stroke
    return tag("div", box, icon_markup(node.icon, rules.lane_icon_size, stroke, place))


_DRAWERS = {
    Shape.KANBAN_CARD: _card_html,
    Shape.ROADMAP_CARD: _card_html,
    Shape.BOARD_PILL: _pill_html,
    Shape.LANE_HEAD: _lane_head_html,
    Shape.PERIOD_HEAD: _period_html,
}
