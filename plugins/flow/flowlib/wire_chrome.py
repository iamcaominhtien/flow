"""The wireframe blocks that frame a screen: navbar, sidebar, tab bar, bottom nav, search bar."""

from .model import ElementStyle, WireBlock
from .screen_part import Align, Bounds
from .wire_kit import (
    CHEVRON_LEFT_PATH,
    HALF,
    Drawn,
    Ink,
    Line,
    WireContext,
    button_parts,
    circle,
    has_flag,
    icon,
    label,
    middle,
    pill,
    rect,
    stroke_path,
    text_width,
)

BACK_FLAG = "back"
MENU_FLAG = "menu"
AVATAR_FLAG = "avatar"
BELL_FLAG = "bell"
LOGO_FLAG = "logo"
CHEVRON_SIZE = (10, 16)  # the width and height of the back chevron
HAMBURGER_ROWS = (0.1, 0.5, 0.9)  # of the height: where the three bars of a menu button sit
SEARCH_ICON = "search"
BELL_ICON = "bell"
USER_ICON = "user"
DEFAULT_ICON = "doc"


def navbar_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a navbar: low on a phone, taller on a desktop."""
    is_low = ctx.is_phone and not ctx.is_plain
    return ctx.rules.navbar_height_phone if is_low else ctx.rules.navbar_height


def draw_navbar(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a navbar: back arrow or logo, the title, search, links, an action and the menu."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, height = box
    drawn = Drawn([rect((x, y + height - 1, width, 1), colors.hairline)], {})
    left = x + (rules.navbar_pad_phone if ctx.is_phone else rules.navbar_pad)
    right = x + width - (rules.navbar_pad_phone if ctx.is_phone else rules.navbar_pad)
    left = _leading_parts(drawn, block, (left, y, height), ctx)
    right = _trailing_parts(drawn, block, (right, y, height), ctx)
    title = (left, y, max(right - left, 0), height)
    size = rules.font_navbar if ctx.is_phone and not ctx.is_plain else rules.font_brand
    drawn.parts.append(label(title, block.text, Ink(size, colors.ink, is_bold=True)))
    drawn.anchors["title"] = (left, y, text_width(block.text, size, ctx), height)
    if block.detail and not ctx.is_phone:
        _search_in_bar(drawn, block, box, ctx)
    return drawn


def _leading_parts(
    drawn: Drawn, block: WireBlock, place: tuple[float, float, float], ctx: WireContext
) -> float:
    """Draw what starts a navbar (a back chevron or a logo) and return where the title starts."""
    rules, colors = ctx.rules, ctx.colors
    left, top, height = place
    if has_flag(block, BACK_FLAG):
        size = CHEVRON_SIZE
        chevron = (left + rules.chevron_inset, top + (height - size[1]) / HALF, size[0], size[1])
        drawn.parts.append(
            stroke_path(chevron, CHEVRON_LEFT_PATH, Line(colors.ink, rules.chevron_stroke))
        )
        drawn.anchors["back"] = chevron
        return left + rules.title_inset
    if has_flag(block, LOGO_FLAG):
        square = (left, top + (height - rules.logo_size) / HALF, rules.logo_size, rules.logo_size)
        drawn.parts.append(rect(square, colors.blue, None, rules.logo_radius))
        drawn.anchors["logo"] = square
        return left + rules.logo_size + rules.logo_gap
    return left


def _trailing_parts(
    drawn: Drawn, block: WireBlock, place: tuple[float, float, float], ctx: WireContext
) -> float:
    """Draw what ends a navbar, from the right: menu, avatar, bell, action and links."""
    rules, colors = ctx.rules, ctx.colors
    right, top, height = place
    if has_flag(block, MENU_FLAG):
        size = rules.hamburger_size
        box = (right - size, top + (height - size) / HALF, size, size)
        drawn.parts.append(
            stroke_path(box, _hamburger(size), Line(colors.ink, rules.hamburger_stroke))
        )
        drawn.anchors["menu"] = box
        right -= size + rules.nav_gap
    if has_flag(block, AVATAR_FLAG):
        size = rules.avatar_size
        box = (right - size, top + (height - size) / HALF, size, size)
        drawn.parts.append(circle(box, colors.image, Line(colors.line)))
        drawn.parts.append(icon(_centred(box, rules.avatar_icon), USER_ICON, colors.cross))
        drawn.anchors["avatar"] = box
        right -= size + rules.nav_gap
    if has_flag(block, BELL_FLAG):
        size = rules.bell_size
        box = (right - size, top + (height - size) / HALF, size, size)
        drawn.parts.append(icon(box, BELL_ICON, colors.ink))
        drawn.anchors["bell"] = box
        right -= size + rules.nav_gap
    return _links_parts(drawn, block, (right, top, height), ctx)


def _hamburger(size: float) -> str:
    """Return the path of the three bars of a menu button of a size."""
    return "".join(f"M0 {size * row:g}h{size:g}" for row in HAMBURGER_ROWS)


def _centred(box: Bounds, size: float) -> Bounds:
    """Return a square of a size in the middle of a box."""
    return (box[0] + (box[2] - size) / HALF, box[1] + (box[3] - size) / HALF, size, size)


def _links_parts(
    drawn: Drawn, block: WireBlock, place: tuple[float, float, float], ctx: WireContext
) -> float:
    """Draw the links of a wide navbar and its one action; return where they start."""
    rules, colors = ctx.rules, ctx.colors
    right, top, height = place
    if block.action:
        box = (
            right - rules.nav_action_width,
            top + (height - rules.nav_action_height) / HALF,
            rules.nav_action_width,
            rules.nav_action_height,
        )
        drawn.parts.extend(button_parts(box, block.action, ElementStyle.PRIMARY, ctx))
        drawn.anchors["action"] = box
        right -= rules.nav_action_width + rules.link_gap
    for index in reversed(range(len(block.items))):
        text = block.items[index]
        width = text_width(text, rules.font_link, ctx)
        is_selected = index in block.selected
        ink = Ink(rules.font_link, colors.blue if is_selected else colors.ink, is_bold=is_selected)
        box = (right - width, top, width, height)
        drawn.parts.append(label(box, text, ink))
        drawn.anchors[f"item-{index}"] = box
        right -= width + rules.link_gap
    return right


def _search_in_bar(drawn: Drawn, block: WireBlock, box: Bounds, ctx: WireContext) -> None:
    """Draw the search box in the middle of a wide navbar."""
    rules = ctx.rules
    width = rules.nav_search_width
    place = (
        box[0] + (box[2] - width) / HALF,
        middle(box, rules.search_height),
        width,
        rules.search_height,
    )
    drawn.parts.extend(_search_parts(place, block.detail, ctx))
    drawn.anchors["search"] = place


def _search_parts(box: Bounds, text: str, ctx: WireContext) -> list:
    """Draw a search pill: a magnifier and a grey placeholder."""
    rules, colors = ctx.rules, ctx.colors
    parts = [pill(box, colors.fill, Line(colors.line))]
    size = rules.search_icon
    parts.append(
        icon((box[0] + rules.search_pad, middle(box, size), size, size), SEARCH_ICON, colors.muted)
    )
    words = (
        box[0] + rules.search_pad + size + rules.icon_gap,
        box[1],
        box[2] - 2 * rules.search_pad - size,
        box[3],
    )
    parts.append(label(words, text, Ink(rules.font_small + 0.5, colors.muted)))
    return parts


def search_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a search bar."""
    return ctx.rules.search_height


def draw_search(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a search bar: a pill with a magnifier."""
    return Drawn(_search_parts(box, block.text or block.detail, ctx), {"search": box})


def sidebar_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height a sidebar needs for its items."""
    rules = ctx.rules
    return 2 * rules.sidebar_pad + len(block.items) * rules.sidebar_pitch


def draw_sidebar(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a sidebar menu: icon and name for each item, the selected one tinted blue."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, height = box
    drawn = Drawn(
        [rect(box, colors.paper), rect((x + width - 1, y, 1, height), colors.hairline)], {}
    )
    for index, text in enumerate(block.items):
        row = (
            x + rules.sidebar_pad,
            y + rules.sidebar_pad + index * rules.sidebar_pitch,
            width - 2 * rules.sidebar_pad - 1,
            rules.sidebar_row,
        )
        is_selected = index in block.selected
        if is_selected:
            drawn.parts.append(rect(row, colors.blue_soft, None, rules.item_radius))
        tint = colors.blue if is_selected else colors.cross
        names = block.icons[index] if index < len(block.icons) else DEFAULT_ICON
        size = rules.sidebar_icon
        drawn.parts.append(
            icon((row[0] + rules.sidebar_icon_pad, middle(row, size), size, size), names, tint)
        )
        words = (
            row[0] + rules.sidebar_icon_pad + size + rules.sidebar_text_gap,
            row[1],
            row[2],
            row[3],
        )
        ink = Ink(rules.font_link, colors.blue if is_selected else colors.text, is_bold=True)
        drawn.parts.append(label(words, text, ink))
        drawn.anchors[f"item-{index}"] = row
    return drawn


def tabs_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a tab bar."""
    return ctx.rules.tab_height


def draw_tabs(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a tab bar: the active tab is blue with a line under it."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, height = box
    drawn = Drawn([rect((x, y + height - 1, width, 1), colors.line)], {})
    count = max(len(block.items), 1)
    each = width / count
    for index, text in enumerate(block.items):
        tab = (x + index * each, y, each, height)
        is_active = index in block.selected
        ink = Ink(
            rules.font_link,
            colors.blue if is_active else colors.muted,
            is_bold=True,
            align=Align.CENTER,
        )
        drawn.parts.append(label(tab, text, ink))
        drawn.anchors[f"item-{index}"] = tab
        if is_active:
            drawn.parts.append(
                rect(
                    (tab[0], y + height - rules.tab_underline, each, rules.tab_underline),
                    colors.blue,
                )
            )
    return drawn


def bottom_nav_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a bottom navigation bar."""
    return ctx.rules.bottom_nav_height


def draw_bottom_nav(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a bottom navigation bar: an icon and a name for each place, the current one blue."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, height = box
    drawn = Drawn([rect((x, y, width, 1), colors.hairline)], {})
    count = max(len(block.items), 1)
    each = width / count
    for index, text in enumerate(block.items):
        tab = (x + index * each, y, each, height)
        tint = colors.blue if index in block.selected else colors.muted
        name = block.icons[index] if index < len(block.icons) else DEFAULT_ICON
        size = rules.bottom_icon
        drawn.parts.append(
            icon((tab[0] + (each - size) / HALF, y + rules.bottom_icon_top, size, size), name, tint)
        )
        words = (
            tab[0],
            y + rules.bottom_icon_top + size + rules.bottom_label_gap,
            each,
            rules.font_nav,
        )
        drawn.parts.append(
            label(words, text, Ink(rules.font_nav, tint, is_bold=True, align=Align.CENTER))
        )
        drawn.anchors[f"item-{index}"] = tab
    return drawn
