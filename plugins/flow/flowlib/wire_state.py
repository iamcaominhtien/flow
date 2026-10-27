"""The states and overlays of a wireframe: loading, empty, error, success, modal, sheet, toast."""

from .model import BlockKind, ElementStyle, WireBlock
from .screen_part import Align, Bounds, Part, PartKind
from .wire_kit import (
    HALF,
    Drawn,
    Ink,
    Line,
    WireContext,
    add_tap,
    bar,
    button_parts,
    card_box,
    check_path,
    circle,
    dashed_circle,
    icon,
    label,
    line_height,
    middle,
    pill,
    rect,
    stroke_path,
    text_width,
    wrapped,
)

EMPTY_ICON = "cart"
ERROR_GLYPH = "!"
MESSAGE_LINES = 2
SKELETON_BAR_FRACTIONS = (0.62, 0.42)  # of the text column: the two bars of a skeleton row
DEFAULT_SKELETON_ROWS = 4


def state_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a loading, empty, error or success block."""
    rules = ctx.rules
    if block.kind is BlockKind.LOADING:
        count = block.bars or DEFAULT_SKELETON_ROWS
        return count * (rules.skeleton_height + ctx.gap) + rules.spinner_room
    stack = rules.state_top + _icon_size(block, ctx) + rules.state_gap
    stack += line_height(rules.font_state_title, ctx) + rules.state_gap / HALF
    stack += MESSAGE_LINES * line_height(rules.font_body, ctx)
    if block.action:
        stack += rules.state_gap + rules.state_button
    if block.items:
        stack += rules.state_button_gap + rules.state_button
    return stack


def draw_state(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw one of the four faces of a screen that loads data, or the success of a task."""
    if block.kind is BlockKind.LOADING:
        return _draw_loading(block, box, ctx)
    return _draw_message(block, box, ctx)


def _icon_size(block: WireBlock, ctx: WireContext) -> float:
    """Return the size of the round symbol: success is smaller than the empty and error ones."""
    rules = ctx.rules
    return rules.success_icon if block.kind is BlockKind.SUCCESS else rules.state_icon


def _draw_loading(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw skeleton rows in the shape of the real rows, then a spinner and its words."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, _ = box
    drawn = Drawn()
    top = y
    for index in range(block.bars or DEFAULT_SKELETON_ROWS):
        row = (x, top, width, rules.skeleton_height)
        drawn.parts.append(card_box(row, ctx))
        disc = (
            x + rules.card_pad,
            middle(row, rules.skeleton_disc),
            rules.skeleton_disc,
            rules.skeleton_disc,
        )
        drawn.parts.append(circle(disc, colors.skeleton))
        left = disc[0] + rules.skeleton_disc + rules.item_gap
        room = x + width - rules.card_pad - left
        first = (
            left,
            row[1] + rules.skeleton_bar_offset,
            room * SKELETON_BAR_FRACTIONS[0],
            rules.skeleton_bar,
        )
        second = (
            left,
            first[1] + rules.skeleton_bar + rules.bar_gap * 2,
            room * SKELETON_BAR_FRACTIONS[1],
            rules.bar_height,
        )
        drawn.parts.extend([bar(first, colors.skeleton), bar(second, colors.skeleton)])
        drawn.anchors[f"row-{index}"] = row
        top += rules.skeleton_height + ctx.gap
    drawn.parts.extend(_spinner_parts((x, top, width), block.text, ctx))
    drawn.anchors["spinner"] = (
        x + (width - rules.spinner_size) / HALF,
        top + rules.spinner_top,
        rules.spinner_size,
        rules.spinner_size,
    )
    return drawn


def _spinner_parts(place: tuple[float, float, float], text: str, ctx: WireContext) -> list[Part]:
    """Draw a ring with a blue quarter, and the words under it: ``Loading your orders...``."""
    rules, colors = ctx.rules, ctx.colors
    left, top, width = place
    size = rules.spinner_size
    ring = (left + (width - size) / HALF, top + rules.spinner_top, size, size)
    parts = [
        circle(ring, None, Line(colors.skeleton, rules.spinner_stroke)),
        Part(PartKind.ARC, ring, stroke=colors.blue, stroke_width=rules.spinner_stroke),
    ]
    if text:
        words = (
            left,
            ring[1] + size + rules.spinner_gap,
            width,
            line_height(rules.font_small + 1, ctx),
        )
        parts.append(
            label(words, text, Ink(rules.font_small + 1, colors.muted, align=Align.CENTER))
        )
    return parts


def _draw_message(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a round symbol, a title, a sentence and the actions: one, or retry first."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, _ = box
    size = _icon_size(block, ctx)
    symbol = (x + (width - size) / HALF, y + rules.state_top, size, size)
    drawn = Drawn(_symbol_parts(block, symbol, ctx), {"icon": symbol})
    top = symbol[1] + size + rules.state_gap
    title_height = line_height(rules.font_state_title, ctx)
    title = Ink(rules.font_state_title, colors.ink, is_bold=True, align=Align.CENTER)
    drawn.parts.append(label((x, top, width, title_height), block.text, title))
    top += title_height + rules.state_gap / HALF
    line = line_height(rules.font_body, ctx)
    for words in wrapped(block.detail, width - 2 * rules.state_text_pad, rules.font_body, ctx)[
        :MESSAGE_LINES
    ]:
        drawn.parts.append(
            label(
                (x, top, width, line), words, Ink(rules.font_body, colors.muted, align=Align.CENTER)
            )
        )
        top += line
    top = y + _message_end(block, ctx)
    _action_parts(drawn, block, (x, top, width), ctx)
    return drawn


def _message_end(block: WireBlock, ctx: WireContext) -> float:
    """Return how far below the top of a state block its sentence ends."""
    rules = ctx.rules
    stack = rules.state_top + _icon_size(block, ctx) + rules.state_gap
    stack += line_height(rules.font_state_title, ctx) + rules.state_gap / HALF
    return stack + MESSAGE_LINES * line_height(rules.font_body, ctx)


def _symbol_parts(block: WireBlock, box: Bounds, ctx: WireContext) -> list[Part]:
    """Draw the round symbol: a dashed grey ring, a rose ring with a mark, or a green check."""
    rules, colors = ctx.rules, ctx.colors
    ring = rules.symbol_stroke
    if block.kind is BlockKind.SUCCESS:
        inner = box[2] * rules.check_fraction
        place = (box[0] + (box[2] - inner) / HALF, box[1] + (box[3] - inner) / HALF, inner, inner)
        return [
            circle(box, colors.green_tint, Line(colors.green, ring)),
            stroke_path(place, check_path(inner, inner), Line(colors.green, rules.check_stroke)),
        ]
    if block.kind is BlockKind.ERROR:
        mark = Ink(rules.font_error_mark, colors.rose, is_bold=True, align=Align.CENTER)
        return [
            circle(box, colors.rose_tint, Line(colors.rose, ring)),
            label(box, ERROR_GLYPH, mark),
        ]
    inner = box[2] * rules.empty_icon_fraction
    place = (box[0] + (box[2] - inner) / HALF, box[1] + (box[3] - inner) / HALF, inner, inner)
    return [
        dashed_circle(box, colors.screen, Line(colors.cross, ring)),
        icon(place, block.icon or EMPTY_ICON, colors.cross),
    ]


def _action_parts(
    drawn: Drawn, block: WireBlock, place: tuple[float, float, float], ctx: WireContext
) -> None:
    """Draw the one action of an empty state, or the retry and the support of an error."""
    rules = ctx.rules
    left, top, width = place
    if block.action:
        top += rules.state_gap
        box = (
            left + (width - rules.state_button_width) / HALF,
            top,
            rules.state_button_width,
            rules.state_button,
        )
        drawn.parts.extend(button_parts(box, block.action, ElementStyle.PRIMARY, ctx))
        drawn.anchors["action"] = box
        add_tap(drawn, block, box, ctx)
        top += rules.state_button
    for index, text in enumerate(block.items):
        top += rules.state_button_gap
        box = (
            left + (width - rules.state_button_width) / HALF,
            top,
            rules.state_button_width,
            rules.state_button,
        )
        drawn.parts.extend(button_parts(box, text, ElementStyle.SECONDARY, ctx))
        drawn.anchors[f"item-{index}"] = box
        top += rules.state_button


def scrim_part(screen: Bounds, radius: float, ctx: WireContext) -> Part:
    """Dim the whole screen under a modal or a sheet, so that the context stays visible."""
    inset = ctx.theme.wire.border / HALF
    box = (inset, inset, screen[2] - 2 * inset, screen[3] - 2 * inset)
    return Part(
        PartKind.RECT,
        box,
        fill=ctx.colors.ink,
        radius=radius - inset,
        opacity=ctx.rules.scrim_opacity,
    )


def draw_overlay(block: WireBlock, screen: Bounds, ctx: WireContext) -> Drawn:
    """Draw a modal, a bottom sheet or a toast on the screen that it covers."""
    if block.kind is BlockKind.MODAL:
        return _draw_modal(block, screen, ctx)
    if block.kind is BlockKind.SHEET:
        return _draw_sheet(block, screen, ctx)
    return _draw_toast(block, screen, ctx)


def _draw_modal(block: WireBlock, screen: Bounds, ctx: WireContext) -> Drawn:
    """Draw a modal: a white card with a title, two lines and a row of buttons."""
    rules, colors = ctx.rules, ctx.colors
    pad = rules.modal_pad
    width = screen[2] * rules.modal_fraction
    lines = wrapped(block.detail, width - 2 * pad, rules.font_body, ctx) if block.detail else []
    body = (
        len(lines) * line_height(rules.font_body, ctx)
        if lines
        else 2 * (rules.bar_height + rules.bar_gap)
    )
    height = (
        2 * pad
        + line_height(rules.font_title + 1, ctx)
        + rules.bar_gap * 2
        + body
        + rules.modal_gap
        + rules.modal_button
    )
    card = ((screen[2] - width) / HALF, (screen[3] - height) / HALF, width, height)
    drawn = Drawn([rect(card, colors.paper, None, rules.modal_radius)], {"card": card})
    left, top = card[0] + pad, card[1] + pad
    title_height = line_height(rules.font_title + 1, ctx)
    drawn.parts.append(
        label(
            (left, top, width - 2 * pad, title_height),
            block.text,
            Ink(rules.font_title + 1, colors.ink, is_bold=True),
        )
    )
    top += title_height + rules.bar_gap * 2
    top = _modal_body(drawn, lines, (left, top, width - 2 * pad), ctx)
    _modal_buttons(drawn, block, (left, top + rules.modal_gap, width - 2 * pad), ctx)
    return drawn


def _modal_body(
    drawn: Drawn, lines: list[str], place: tuple[float, float, float], ctx: WireContext
) -> float:
    """Draw the words of a modal, or grey bars when it has none; return where they end."""
    rules, colors = ctx.rules, ctx.colors
    left, top, width = place
    if not lines:
        for fraction in (1.0, 0.7):
            drawn.parts.append(bar((left, top, width * fraction, rules.bar_height), colors.bar))
            top += rules.bar_height + rules.bar_gap
        return top
    for words in lines:
        height = line_height(rules.font_body, ctx)
        drawn.parts.append(
            label((left, top, width, height), words, Ink(rules.font_body, colors.muted))
        )
        top += height
    return top


def _modal_buttons(
    drawn: Drawn, block: WireBlock, place: tuple[float, float, float], ctx: WireContext
) -> None:
    """Draw the buttons of a modal in a row: the last one is the action."""
    rules = ctx.rules
    left, top, width = place
    count = max(len(block.items), 1)
    each = (width - (count - 1) * rules.state_button_gap) / count
    for index, text in enumerate(block.items):
        is_last = index == count - 1
        style = (block.style or ElementStyle.PRIMARY) if is_last else ElementStyle.SECONDARY
        box = (left + index * (each + rules.state_button_gap), top, each, rules.modal_button)
        drawn.parts.extend(button_parts(box, text, style, ctx))
        drawn.anchors[f"item-{index}"] = box


def _draw_sheet(block: WireBlock, screen: Bounds, ctx: WireContext) -> Drawn:
    """Draw a bottom sheet: a white panel with a handle, a title and one row per choice."""
    rules, colors = ctx.rules, ctx.colors
    inset = ctx.theme.wire.border / HALF
    title = rules.sheet_title if block.text else 0
    height = rules.sheet_top + title + len(block.items) * rules.sheet_row + rules.sheet_foot
    panel = (inset, screen[3] - inset - height, screen[2] - 2 * inset, height)
    drawn = Drawn([rect(panel, colors.paper, None, rules.sheet_radius)], {"sheet": panel})
    handle = (
        panel[0] + (panel[2] - rules.handle_width) / HALF,
        panel[1] + rules.handle_top,
        rules.handle_width,
        rules.handle_height,
    )
    drawn.parts.append(pill(handle, colors.line))
    top = panel[1] + rules.sheet_top
    left, width = panel[0] + rules.modal_pad, panel[2] - 2 * rules.modal_pad
    if block.text:
        drawn.parts.append(
            label(
                (left, top, width, rules.sheet_title),
                block.text,
                Ink(rules.font_title + 1, colors.ink, is_bold=True),
            )
        )
        top += rules.sheet_title
    for index, text in enumerate(block.items):
        row = (left, top + index * rules.sheet_row, width, rules.sheet_row)
        drawn.parts.append(label(row, text, Ink(rules.font_body + 1, colors.ink)))
        drawn.parts.append(rect((left, row[1] + row[3] - 1, width, 1), colors.hairline))
        drawn.anchors[f"item-{index}"] = row
    return drawn


def _draw_toast(block: WireBlock, screen: Bounds, ctx: WireContext) -> Drawn:
    """Draw a toast: a dark pill with a short sentence that leaves by itself."""
    rules, colors = ctx.rules, ctx.colors
    width = text_width(block.text, rules.font_body, ctx) + 2 * rules.toast_pad
    box = (
        (screen[2] - width) / HALF,
        screen[3] - rules.toast_lift - rules.toast_height,
        width,
        rules.toast_height,
    )
    ink = Ink(rules.font_body, colors.paper, is_bold=True, align=Align.CENTER)
    return Drawn([pill(box, colors.ink), label(box, block.text, ink)], {"toast": box})
