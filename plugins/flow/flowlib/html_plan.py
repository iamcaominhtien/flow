"""Draw the nodes and frames of the planning diagrams as HTML: Gantt, org chart and mind map.

A planning node is drawn from its ``plan`` view (see ``model.PlanView``): a bar coloured by its
status, a person as a circle with initials, a card of an org chart, a branch or a leaf of a mind
map, a milestone, or plain text. The same sizes are used by ``drawio_plan``.
"""

from .markup import esc, fmt, px, tag
from .model import Frame, FrameVariant, MindLevel, Node, PlanView, Shape, Side, Status, Tone
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

ABSOLUTE = {"position": "absolute"}
PLAN_SHAPES = (
    Shape.PERSON,
    Shape.PERSON_CARD,
    Shape.PLAN_BAR,
    Shape.MILESTONE,
    Shape.LABEL,
    Shape.BRANCH,
    Shape.LEAF,
)
PLAN_FRAME_VARIANTS = (FrameVariant.PANEL, FrameVariant.BAND)
PILL_RADIUS_PX = 999
BORDER_PX = 2
THIN_BORDER_PX = 1
SHADOW_DROP_PX = 3
LABEL_WEIGHT = 500
BOLD_WEIGHT = 700
INITIALS_FONT_FRACTION = 0.38  # the initials fill this much of the height of their circle
MIN_INITIALS_FONT_PX = 8
CHECK_FONT_PX = 10
LEAF_RADIUS_PX = 8
DETAIL_RADIUS_PX = 6
LEAF_TEXT_WEIGHT = 600
LEAF_PAD_PX = 12
LEAF_ICON_GAP_PX = 8
UNDERLINE_PX = 3
MARK_HEIGHT_PX = 16
MARK_GAP_PX = 4
MARK_RIGHT_PX = 8
MARK_FONT_PX = 9
MARK_PADDING_PX = 6
BAND_FONT_PX = 13
BAND_PAD_PX = 14
PROGRESS_FULL = 1.0
CARD_ICON_RIGHT_PX = 18
DISC_PAD_PX = 8
UNKNOWN_TONE = Tone.GRAY
CENTRE_ICON_FRACTION = 0.43  # the icon of the topic, as a fraction of the height of its card
CENTRE_PAD_PX = 22
CENTRE_GAP_PX = 14
CENTRE_RADIUS_PX = 18
CENTRE_BORDER_PX = 2.5
CENTRE_PILL_HEIGHT_PX = 34
CENTRE_PILL_PAD_PX = 18
CHECK_GRID_PX = 24
CHECK_STROKE = 3
CHECK_PATH = "M5 12.5L10 17.5L19 7"
MIN_CHECK_BAR_PX = 20  # a bar lower than this has no room for a check
SOLID_LINE = "solid"
BLOCKED_LINE = "dashed"  # the second cue of a blocked bar, besides its reason


def accent_of(node: Node, theme: Theme) -> str:
    """Return the strong colour of the tone of a node: the pill, bar and curve of a branch."""
    return theme.planning.accents[node.tone or UNKNOWN_TONE]


def is_plan_node(node: Node) -> bool:
    """Tell whether a node is drawn by this module."""
    return node.shape in PLAN_SHAPES


def plan_node_html(node: Node, theme: Theme) -> str:
    """Draw one planning node in a box of its size, with whatever hangs outside the box.

    Args:
        node: A node whose shape is one of ``PLAN_SHAPES``.
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
    if node.shape is Shape.PLAN_BAR:
        return tag("div", box, _bar_html(node, view, theme), data_id=node.id) + _reason_html(
            node, view, theme
        )
    return tag("div", box, _inside_html(node, view, theme), data_id=node.id)


def plan_frame_html(frame: Frame, theme: Theme) -> str:
    """Draw a panel (a white rounded box) or a band (a grey row with a bold name).

    Args:
        frame: A frame whose variant is one of ``PLAN_FRAME_VARIANTS``.
        theme: The design tokens.

    Returns:
        The markup of the frame.
    """
    area = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "width": px(frame.width),
        "height": px(frame.height),
        "box-sizing": "border-box",
        "border-radius": px(theme.planning.gantt.header_radius),
    }
    if frame.variant is FrameVariant.PANEL:
        area["background"] = theme.paper
        area["border"] = f"{px(THIN_BORDER_PX)} solid {theme.rule}"
        return tag("div", area, data_id=frame.id)
    area.update(_band_style(frame, theme))
    return tag("div", area, esc(frame.label or ""), data_id=frame.id)


def _band_style(frame: Frame, theme: Theme) -> dict[str, str]:
    """Return the look of a band: a tint, and its name in bold at the left."""
    return {
        "background": theme.tones[frame.tone].box,
        "display": "flex",
        "align-items": "center",
        "padding-left": px(BAND_PAD_PX),
        "font-size": px(BAND_FONT_PX),
        "font-weight": str(BOLD_WEIGHT),
        "color": theme.ink,
    }


def circle_html(initials: str, tone: Tone | None, size: float, theme: Theme) -> str:
    """Draw a person: a circle in the tint of the person, with the initials in it.

    Args:
        initials: One to three letters, or ``?`` for an open role.
        tone: The tint of the person; grey when the tone is not known.
        size: The diameter in pixels.
        theme: The design tokens.

    Returns:
        The markup, positioned at the top left of its parent.
    """
    style = {
        **ABSOLUTE,
        "left": "0",
        "top": "0",
        "width": px(size),
        "height": px(size),
        "box-sizing": "border-box",
        "border-radius": "50%",
        "background": theme.tones[tone or UNKNOWN_TONE].pill,
        "border": f"{px(BORDER_PX)} solid {theme.ink}",
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        "font-size": px(max(MIN_INITIALS_FONT_PX, size * INITIALS_FONT_FRACTION)),
        "font-weight": str(BOLD_WEIGHT),
        "color": theme.ink,
    }
    return tag("div", style, esc(initials))


def _inside_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw what is inside the box of a node that is not a bar."""
    if node.shape is Shape.PERSON:
        return circle_html(
            view.initials or " ".join(node.text), view.person_tone, node.width, theme
        )
    if node.shape is Shape.MILESTONE:
        return _milestone_html(node, theme)
    if node.shape is Shape.LABEL:
        return _label_html(node, view, theme)
    if node.shape is Shape.PERSON_CARD:
        return _person_card_html(node, view, theme)
    if node.shape is Shape.BRANCH:
        return _branch_html(node, view, theme)
    return _leaf_html(node, view, theme)


def _label_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw plain text, left aligned, centred, or right aligned on the side of a mind map."""
    if node.is_centered:
        justify = "center"
    else:
        justify = "flex-end" if view.side is Side.LEFT else "flex-start"
    style = {
        **ABSOLUTE,
        "left": "0",
        "top": "0",
        "width": px(node.width),
        "height": px(node.height),
        "display": "flex",
        "align-items": "center",
        "justify-content": justify,
        "font-size": px(node.font_size),
        "font-weight": str(BOLD_WEIGHT if view.is_bold else LABEL_WEIGHT),
        "color": theme.ink,
        "white-space": "nowrap",
    }
    return tag("div", style, esc(" ".join(node.text)))


def _milestone_html(node: Node, theme: Theme) -> str:
    """Draw the diamond of a milestone."""
    colors = theme.planning.milestone
    width, height = node.width, node.height
    points = f"{fmt(width / 2)},{BORDER_PX} {fmt(width - BORDER_PX)},{fmt(height / 2)} "
    points += f"{fmt(width / 2)},{fmt(height - BORDER_PX)} {BORDER_PX},{fmt(height / 2)}"
    return (
        f'<svg width="{fmt(width)}" height="{fmt(height)}" style="position:absolute;left:0;top:0;'
        f'overflow:visible" aria-hidden="true"><polygon points="{points}" fill="{colors.fill}" '
        f'stroke="{colors.stroke}" stroke-width="{BORDER_PX}" stroke-linejoin="round"/></svg>'
    )


def check_svg(size: float, color: str, attrs: str = "") -> str:
    """Draw a plain check mark of a given size and colour.

    Args:
        size: The width and height in pixels.
        color: The stroke colour.
        attrs: Extra attributes for the ``svg`` element, such as a ``style``.

    Returns:
        An ``svg`` element.
    """
    return (
        f'<svg width="{fmt(size)}" height="{fmt(size)}" viewBox="0 0 {CHECK_GRID_PX} '
        f'{CHECK_GRID_PX}" fill="none" stroke="{color}" stroke-width="{CHECK_STROKE}" '
        f'stroke-linecap="round" stroke-linejoin="round" {attrs}>'
        f'<path d="{CHECK_PATH}"/></svg>'
    )


def _bar_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw a bar by its status: solid with a check, filled to its progress, empty, or dashed."""
    status = view.status or Status.PLANNED
    colors = theme.planning.status[status]
    line = BLOCKED_LINE if status is Status.BLOCKED else SOLID_LINE
    style = {
        **ABSOLUTE,
        "left": "0",
        "top": "0",
        "width": px(node.width),
        "height": px(node.height),
        "box-sizing": "border-box",
        "overflow": "hidden",
        "border-radius": px(theme.planning.gantt.bar_radius),
        "background": colors.fill,
        "border": f"{px(BORDER_PX)} {line} {colors.stroke}",
    }
    inside = ""
    if status is Status.IN_PROGRESS:
        share = min(max(view.progress, 0.0), PROGRESS_FULL)
        fill = {**ABSOLUTE, "left": "0", "top": "0", "bottom": "0"}
        fill.update({"width": f"{fmt(share * 100)}%", "background": colors.mark})
        inside = tag("div", fill)
    if status is Status.DONE and node.height >= MIN_CHECK_BAR_PX:
        size = theme.planning.gantt.check_size
        place = {**ABSOLUTE, "left": px(theme.planning.gantt.bar_inset), "top": "0"}
        place.update({"width": px(size), "height": px(node.height - 2 * BORDER_PX)})
        place.update({"display": "flex", "align-items": "center"})
        inside = tag("div", place, check_svg(size, colors.mark))
    return tag("div", style, inside)


def _reason_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw the short reason of a blocked task after the end of its bar."""
    if view.status is not Status.BLOCKED or not view.reason:
        return ""
    style = {
        **ABSOLUTE,
        "left": px(node.x + node.width + theme.planning.gantt.reason_gap),
        "top": px(node.y),
        "height": px(node.height),
        "display": "flex",
        "align-items": "center",
        "font-size": px(theme.planning.gantt.week_font_size),
        "font-weight": str(BOLD_WEIGHT),
        "color": theme.planning.status[Status.BLOCKED].mark,
        "white-space": "nowrap",
    }
    return tag("div", style, esc(view.reason))


def _card_font(node: Node, theme: Theme) -> tuple[float, float]:
    """Return the font sizes of the name and of the role on an org card."""
    return theme.planning.org.name_font_size, theme.planning.org.role_font_size


def _person_card_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw an org card: plain with initials, or illustrated with a pill and a person icon."""
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    fill = theme.paper if view.is_open else tone.box
    style = {
        **ABSOLUTE,
        "left": "0",
        "top": "0",
        "width": px(node.width),
        "height": px(node.height),
        "box-sizing": "border-box",
        "background": fill,
        "border": f"{px(BORDER_PX)} {'dashed' if view.is_open else 'solid'} "
        f"{theme.slate if view.is_open else theme.ink}",
        "border-radius": px(theme.style.corner_radius),
    }
    if not node.text:
        return tag("div", style)
    body = (
        _illustrated_card_body(node, view, theme)
        if node.card
        else _plain_card_body(node, view, theme)
    )
    if view.is_open and node.card:
        faded = {**ABSOLUTE, "left": "0", "top": "0", "width": "100%", "height": "100%"}
        faded["opacity"] = fmt(theme.planning.org.open_opacity)
        body = tag("div", faded, body)
    return tag("div", style, body)


def _plain_card_body(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw the initials circle, the name and the role of a plain org card."""
    rules = theme.planning.org
    name_size, role_size = _card_font(node, theme)
    holder = {**ABSOLUTE, "left": px(rules.pad - BORDER_PX), "top": "50%"}
    holder.update({"width": px(rules.person_size), "height": px(rules.person_size)})
    holder["transform"] = "translateY(-50%)"
    circle = tag(
        "div", holder, circle_html(view.initials, view.person_tone, rules.person_size, theme)
    )
    left = rules.pad + rules.person_size + rules.pad / 2
    text = {**ABSOLUTE, "left": px(left - BORDER_PX), "right": px(rules.pad), "top": "0"}
    text.update({"bottom": "0", "display": "flex", "flex-direction": "column"})
    text.update({"justify-content": "center", "gap": "4px"})
    name = tag(
        "div",
        {"font-size": px(name_size), "font-weight": str(BOLD_WEIGHT), "color": theme.ink},
        esc(" ".join(node.text)),
    )
    role = tag(
        "div", {"font-size": px(role_size), "color": theme.slate}, esc(" ".join(node.detail))
    )
    return circle + tag("div", text, name + role)


def _illustrated_card_body(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw the name pill, the role line and the person icon of an illustrated org card."""
    rules = theme.planning.org
    tone = theme.tones[view.person_tone or node.tone or UNKNOWN_TONE]
    pill = {
        **ABSOLUTE,
        "left": px(rules.pad),
        "top": px(rules.pad),
        "height": px(rules.pill_height),
    }
    pill.update(
        {
            "box-sizing": "border-box",
            "padding": f"0 {px(rules.pad - BORDER_PX)}",
            "border-radius": px(PILL_RADIUS_PX),
            "background": tone.pill,
            "border": f"{px(BORDER_PX)} solid {theme.ink}",
            "font-size": px(rules.name_font_size),
            "font-weight": str(BOLD_WEIGHT),
            "line-height": px(rules.pill_height - 2 * BORDER_PX),
            "color": theme.ink,
            "white-space": "nowrap",
        }
    )
    if theme.style.shadow:
        pill["box-shadow"] = f"0 {px(SHADOW_DROP_PX)} 0 {theme.ink}"
    role = {**ABSOLUTE, "left": px(rules.pad), "top": px(rules.pad + rules.pill_height + 12)}
    role.update({"font-size": px(rules.role_font_size), "color": theme.slate})
    icon_place = (
        f'style="position:absolute;left:{px(node.width - CARD_ICON_RIGHT_PX - rules.icon_size)};'
        f'top:{px((node.height - rules.icon_size) / 2)}"'
    )
    return (
        tag("div", pill, esc(" ".join(node.text)))
        + tag("div", role, esc(" ".join(node.detail)))
        + _person_icon(node, rules.icon_size, icon_place, theme)
    )


def _person_icon(node: Node, size: float, place: str, theme: Theme) -> str:
    """Draw the person icon of an illustrated card; the icon of the node, else ``user``."""
    name = node.icon or "user"
    stroke = theme.tones[node.tone or UNKNOWN_TONE].stroke
    if has_detailed_icon(name):
        return detailed_icon_svg(name, size, stroke, place)
    return icon_svg(name, size, stroke, place)


def _branch_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw a branch or a group of a mind map as a pill."""
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    if view.level is MindLevel.CENTRE:
        return _centre_html(node, theme)
    if view.level is MindLevel.GROUP:
        return _group_pill_html(node, tone.box, accent_of(node, theme), theme)
    if node.card:
        return _solid_branch_html(node, theme)
    return _tinted_branch_html(node, theme)


def _centre_html(node: Node, theme: Theme) -> str:
    """Draw the topic of a mind map: a dark pill, or a card with a large icon and the goal."""
    if not node.card:
        style = _pill_style(node, theme.ink, theme.ink, BORDER_PX)
        style.update({"justify-content": "center", "color": theme.paper, "white-space": "nowrap"})
        style["font-size"] = px(node.font_size)
        return tag("div", style, esc(" ".join(node.text)))
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    card = _pill_style(node, tone.box, theme.ink, CENTRE_BORDER_PX)
    card.update({"border-radius": px(CENTRE_RADIUS_PX), "display": "block"})
    size = node.height * CENTRE_ICON_FRACTION
    place = f'style="position:absolute;left:{px((node.width - size) / 2)};top:{px(CENTRE_PAD_PX)}"'
    icon = _icon_markup(node.icon or "idea", size, accent_of(node, theme), place)
    pill_top = CENTRE_PAD_PX + size + CENTRE_GAP_PX
    pill_row = {**ABSOLUTE, "left": "0", "right": "0", "top": px(pill_top), "display": "flex"}
    pill_row["justify-content"] = "center"
    pill = _pill_style(node, tone.pill, theme.ink, BORDER_PX)
    pill.update({**{"position": "static", "width": "auto", "height": px(CENTRE_PILL_HEIGHT_PX)}})
    pill.update(
        {"padding": f"0 {px(CENTRE_PILL_PAD_PX)}", "color": theme.ink, "white-space": "nowrap"}
    )
    if theme.style.shadow:
        pill["box-shadow"] = f"0 {px(SHADOW_DROP_PX)} 0 {theme.ink}"
    goal = {**ABSOLUTE, "left": "0", "right": "0", "text-align": "center", "color": theme.slate}
    goal.update(
        {
            "top": px(pill_top + CENTRE_PILL_HEIGHT_PX + CENTRE_GAP_PX),
            "font-size": px(theme.layout.detail_font_size + 1),
        }
    )
    words = tag("div", goal, esc(" ".join(node.detail)))
    return tag(
        "div", card, icon + tag("div", pill_row, tag("div", pill, esc(" ".join(node.text)))) + words
    )


def _pill_style(node: Node, fill: str, border: str, width: float) -> dict[str, str]:
    """Return the style of the rounded box of a pill that fills its node."""
    return {
        **ABSOLUTE,
        "left": "0",
        "top": "0",
        "width": px(node.width),
        "height": px(node.height),
        "box-sizing": "border-box",
        "border-radius": px(PILL_RADIUS_PX),
        "background": fill,
        "border": f"{px(width)} solid {border}",
        "display": "flex",
        "align-items": "center",
        "font-size": px(node.font_size),
        "font-weight": str(BOLD_WEIGHT),
    }


def _group_pill_html(node: Node, fill: str, border: str, theme: Theme) -> str:
    """Draw a group of a mind map: a tinted pill with a thin outline in the branch colour."""
    style = _pill_style(node, fill, border, BORDER_PX)
    style.update({"justify-content": "center", "color": theme.ink, "white-space": "nowrap"})
    return tag("div", style, esc(" ".join(node.text)))


def _solid_branch_html(node: Node, theme: Theme) -> str:
    """Draw an illustrated branch: a solid colour pill with a round icon and white text."""
    theme.tones[node.tone or UNKNOWN_TONE]
    scale = theme.planning.mind.illustrated
    style = _pill_style(node, accent_of(node, theme), theme.ink, BORDER_PX + 1)
    style.update({"color": theme.on_accent, "white-space": "nowrap"})
    if theme.style.shadow:
        style["box-shadow"] = f"0 {px(SHADOW_DROP_PX + 1)} 0 {theme.ink}"
    disc = min(scale.disc, node.height - 2 * DISC_PAD_PX)
    text = (
        {"margin-left": px(DISC_PAD_PX * 2 + disc)}
        if node.icon
        else {"margin-left": px(scale.disc / 2)}
    )
    return tag(
        "div", style, _disc_html(node, disc, theme) + tag("span", text, esc(" ".join(node.text)))
    )


def _disc_html(node: Node, size: float, theme: Theme) -> str:
    """Draw the round white icon at the left of an illustrated branch."""
    if not node.icon:
        return ""
    style = {
        **ABSOLUTE,
        "left": px(DISC_PAD_PX),
        "top": "50%",
        "transform": "translateY(-50%)",
        "width": px(size),
        "height": px(size),
        "box-sizing": "border-box",
        "border-radius": "50%",
        "background": theme.paper,
        "border": f"{px(BORDER_PX)} solid {theme.ink}",
    }
    inner = size - 2 * BORDER_PX
    place = 'style="position:absolute;left:0;top:0"'
    stroke = accent_of(node, theme)
    return tag("div", style, _icon_markup(node.icon, inner, stroke, place))


def _icon_markup(name: str, size: float, stroke: str, place: str) -> str:
    """Draw an icon in its detailed form when there is one, else in its flat form."""
    if has_detailed_icon(name):
        return detailed_icon_svg(name, size, stroke, place)
    return icon_svg(name, size, stroke, place)


def _tinted_branch_html(node: Node, theme: Theme) -> str:
    """Draw a plain branch: a tinted pill with a small icon and the name in ink."""
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    style = _pill_style(node, tone.pill, theme.ink, BORDER_PX)
    style.update({"justify-content": "center", "color": theme.ink, "white-space": "nowrap"})
    style["gap"] = px(LEAF_ICON_GAP_PX)
    if theme.style.shadow:
        style["box-shadow"] = f"0 {px(SHADOW_DROP_PX)} 0 {theme.ink}"
    icon = ""
    if node.icon:
        size = theme.planning.mind.plain.leaf_icon
        icon = icon_svg(node.icon, size, theme.ink, 'style="flex:none"')
    return tag("div", style, icon + tag("span", {}, esc(" ".join(node.text))))


def _leaf_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw a leaf of a mind map: a card, an underlined phrase, or a tinted detail."""
    tone = theme.tones[node.tone or UNKNOWN_TONE]
    if view.level is MindLevel.KEY:
        return _marks_html(view, node, theme)
    if view.level is MindLevel.DETAIL:
        return _detail_leaf_html(node, view, tone.box, theme)
    if not node.card and view.level is MindLevel.LEAF:
        return _underlined_leaf_html(node, view, accent_of(node, theme), theme)
    return _card_leaf_html(node, view, theme)


def _detail_leaf_html(node: Node, view: PlanView, fill: str, theme: Theme) -> str:
    """Draw a detail: a tinted box with a phrase and no outline."""
    style = _leaf_box(node, fill, DETAIL_RADIUS_PX)
    style["font-weight"] = "500"
    return tag(
        "div", style, tag("span", {}, esc(" ".join(node.text))) + _marks_html(view, node, theme)
    )


def _leaf_box(node: Node, fill: str, radius: float) -> dict[str, str]:
    """Return the style of the box of a leaf: a row with the text on its inner side."""
    return {
        **ABSOLUTE,
        "left": "0",
        "top": "0",
        "width": px(node.width),
        "height": px(node.height),
        "box-sizing": "border-box",
        "border-radius": px(radius),
        "background": fill,
        "display": "flex",
        "align-items": "center",
        "padding": f"0 {px(LEAF_PAD_PX)}",
        "font-size": px(node.font_size),
        "font-weight": str(LEAF_TEXT_WEIGHT),
        "color": "inherit",
        "white-space": "nowrap",
    }


def _underlined_leaf_html(node: Node, view: PlanView, color: str, theme: Theme) -> str:
    """Draw a plain leaf: a phrase on an underline in the colour of its branch."""
    is_left = view.side is Side.LEFT
    style = {
        **ABSOLUTE,
        "left": "0",
        "top": "0",
        "width": px(node.width),
        "height": px(node.height),
        "box-sizing": "border-box",
        "border-bottom": f"{px(UNDERLINE_PX)} solid {color}",
        "display": "flex",
        "align-items": "center",
        "justify-content": "flex-end" if is_left else "flex-start",
        "padding": f"0 {px(UNDERLINE_PX * 3)} {px(UNDERLINE_PX)}",
        "font-size": px(node.font_size),
        "font-weight": str(BOLD_WEIGHT),
        "color": theme.ink,
        "white-space": "nowrap",
    }
    return tag("div", style, esc(" ".join(node.text)))


def _card_leaf_html(node: Node, view: PlanView, theme: Theme) -> str:
    """Draw a leaf or an idea: a white card with a colour bar, an icon, a phrase and marks."""
    theme.tones[node.tone or UNKNOWN_TONE]
    style = _leaf_box(node, theme.paper, LEAF_RADIUS_PX)
    style.update(
        {
            "border": f"{px(BORDER_PX)} solid {accent_of(node, theme)}",
            "color": theme.ink,
        }
    )
    bar = {**ABSOLUTE, "left": "0", "top": "0", "bottom": "0"}
    bar.update(
        {
            "width": px(theme.planning.mind.bar_width),
            "background": accent_of(node, theme),
        }
    )
    icon = ""
    if node.icon:
        size = theme.planning.mind.illustrated.leaf_icon
        icon = icon_svg(
            node.icon,
            size,
            accent_of(node, theme),
            'style="flex:none;margin-right:8px"',
        )
    left = {"margin-left": px(theme.planning.mind.bar_width)}
    text = tag("span", left, icon + esc(" ".join(node.text)))
    return tag("div", style, tag("div", bar) + text + _marks_html(view, node, theme))


def _marks_html(view: PlanView, node: Node, theme: Theme) -> str:
    """Draw the marks on the right of an idea: done, priority, owner and hidden ideas."""
    marks = []
    if view.status is Status.DONE:
        marks.append(_done_mark(theme))
    if view.priority:
        marks.append(_priority_mark(view.priority, theme))
    if view.hidden:
        marks.append(_hidden_mark(view.hidden, theme))
    if view.initials:
        size = theme.planning.mind.owner_size
        owner = tag(
            "div",
            {"position": "relative", "width": px(size), "height": px(size)},
            circle_html(view.initials, view.person_tone, size, theme),
        )
        marks.append(owner)
    if not marks:
        return ""
    edge = {"left": "0"} if view.level is MindLevel.KEY else {"right": px(MARK_RIGHT_PX)}
    row = {**ABSOLUTE, **edge, "top": "0", "bottom": "0", "display": "flex"}
    row.update({"align-items": "center", "gap": px(MARK_GAP_PX)})
    return tag("div", row, "".join(marks))


def _small_pill(text: str, fill: str, color: str) -> str:
    """Draw one small rounded mark with a short text."""
    style = {
        "height": px(MARK_HEIGHT_PX),
        "line-height": px(MARK_HEIGHT_PX),
        "padding": f"0 {px(MARK_PADDING_PX)}",
        "border-radius": px(PILL_RADIUS_PX),
        "background": fill,
        "color": color,
        "font-size": px(MARK_FONT_PX),
        "font-weight": str(BOLD_WEIGHT),
    }
    return tag("div", style, esc(text))


def _priority_mark(priority: int, theme: Theme) -> str:
    """Draw P1 or P2."""
    colors = theme.planning.marks[f"priority_{priority}"]
    return _small_pill(f"P{priority}", colors.fill, colors.text)


def _hidden_mark(hidden: int, theme: Theme) -> str:
    """Draw ``+N``: how many ideas below are left out."""
    colors = theme.planning.marks["more"]
    return _small_pill(f"+{hidden}", colors.fill, colors.text)


def _done_mark(theme: Theme) -> str:
    """Draw a green circle with a white check."""
    colors = theme.planning.marks["done"]
    style = {
        "position": "relative",
        "width": px(MARK_HEIGHT_PX),
        "height": px(MARK_HEIGHT_PX),
        "border-radius": "50%",
        "background": colors.fill,
    }
    inset = (MARK_HEIGHT_PX - CHECK_FONT_PX) / 2
    place = f'style="position:absolute;left:{px(inset)};top:{px(inset)}"'
    return tag("div", style, check_svg(CHECK_FONT_PX, colors.text, place))


def plan_text_room(node: Node, theme: Theme) -> float | None:
    """Return how wide the text of a planning node may be, or None when it has no text to fit.

    Args:
        node: A node whose shape is one of ``PLAN_SHAPES``.
        theme: The design tokens.

    Returns:
        The width the text has between its padding, icon and marks, in pixels.
    """
    org, mind = theme.planning.org, theme.planning.mind
    if node.shape is Shape.LABEL:
        return node.width
    if node.shape is Shape.PERSON_CARD and not node.card:
        return node.width - 2 * org.pad - org.person_size - org.pad / 2
    if node.shape is Shape.PERSON_CARD:
        return node.width - 2 * org.pad - org.icon_size
    if node.shape is Shape.BRANCH:
        reserved = 2 * LEAF_PAD_PX + (mind.illustrated.disc if node.icon else 0)
        return node.width - reserved
    if node.shape is Shape.LEAF:
        icon = mind.illustrated.leaf_icon + LEAF_ICON_GAP_PX if node.icon else 0
        return node.width - mind.bar_width - 2 * LEAF_PAD_PX - icon
    return None
