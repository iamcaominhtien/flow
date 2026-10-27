"""The wireframe blocks that hold content: list item, card, figure, table and chart."""

from .model import CellKind, ElementStyle, Tone, WireBlock, WireCell
from .screen_part import Align, Bounds, Part
from .wire_basic import stepper_parts
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
    chip_parts,
    chip_width,
    circle,
    cross_box,
    has_flag,
    icon,
    label,
    line_height,
    middle,
    rect,
    text_width,
)

TINT_FLAG = "tinted"
LEADS_WITH_DISC = ("avatar", "pin")
RADIO_DOT_FRACTION = 0.5  # of the radio circle: the dot of the selected choice
BAR_WIDTH_FRACTIONS = (0.6, 0.4)  # of the text column: the title bar and the detail bar
BARS_IN_CARD = 2


def item_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a list item: a disc or a thumbnail needs more room than a radio."""
    rules = ctx.rules
    if block.height:
        return block.height
    if block.lead in LEADS_WITH_DISC:
        return rules.item_height_disc
    return rules.item_height


def draw_item(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a list item: a lead, two lines, and a chip or a link at the end."""
    rules, colors = ctx.rules, ctx.colors
    x, y, _, height = box
    fill = colors.fill if has_flag(block, TINT_FLAG) else colors.paper
    border = Line(colors.blue, rules.selected_border) if block.selected else Line(colors.line)
    drawn = Drawn([rect(box, fill, border, rules.card_radius)], {})
    left = x + rules.item_pad
    left += _lead_parts(drawn, block, (left, y, height), ctx) + rules.item_gap
    right = _trail_parts(drawn, block, box, ctx)
    _item_text(drawn, block, (left, y, right - left, height), ctx)
    add_tap(drawn, block, box, ctx)
    return drawn


def _lead_parts(
    drawn: Drawn, block: WireBlock, place: tuple[float, float, float], ctx: WireContext
) -> float:
    """Draw what starts a list item and return the width it takes."""
    rules, colors = ctx.rules, ctx.colors
    left, top, height = place
    lead = block.lead
    if not lead:
        return 0
    if lead == "radio":
        size = rules.radio_size
        circle_box = (left, top + (height - size) / HALF, size, size)
        drawn.parts.extend(_radio_parts(circle_box, bool(block.selected), ctx))
        drawn.anchors["lead"] = circle_box
        return size
    size = rules.lead_size
    disc = (left, top + (height - size) / HALF, size, size)
    if lead == "thumb":
        drawn.parts.extend(cross_box(disc, ctx, rules.thumb_radius))
    else:
        drawn.parts.append(circle(disc, colors.image, Line(colors.line)))
        if lead == "pin":
            inner = rules.lead_icon
            drawn.parts.append(
                icon(
                    (
                        disc[0] + (size - inner) / HALF,
                        disc[1] + (size - inner) / HALF,
                        inner,
                        inner,
                    ),
                    "pin",
                    colors.cross,
                )
            )
    drawn.anchors["lead"] = disc
    return size


def _radio_parts(box: Bounds, is_selected: bool, ctx: WireContext) -> list[Part]:
    """Draw a radio button: a ring, with a dot in it when it is the choice."""
    rules, colors = ctx.rules, ctx.colors
    if not is_selected:
        return [circle(box, colors.paper, Line(colors.cross, rules.radio_stroke))]
    dot = box[2] * RADIO_DOT_FRACTION
    inner = (box[0] + (box[2] - dot) / HALF, box[1] + (box[3] - dot) / HALF, dot, dot)
    return [
        circle(box, colors.paper, Line(colors.blue, rules.radio_stroke)),
        circle(inner, colors.blue),
    ]


def _trail_parts(drawn: Drawn, block: WireBlock, box: Bounds, ctx: WireContext) -> float:
    """Draw what ends a list item (a chip or a link) and return where the text must stop."""
    rules, colors = ctx.rules, ctx.colors
    right = box[0] + box[2] - rules.item_pad
    if block.chip:
        width = chip_width(block.chip, ctx)
        chip = (right - width, middle(box, rules.chip_height), width, rules.chip_height)
        drawn.parts.extend(chip_parts(chip, block.chip, block.tone or Tone.BLUE, ctx))
        drawn.anchors["chip"] = chip
        return chip[0] - rules.item_gap
    if block.trail:
        width = text_width(block.trail, rules.font_label, ctx)
        place = (right - width, box[1], width, box[3])
        drawn.parts.append(
            label(place, block.trail, Ink(rules.font_label, colors.blue, is_bold=True))
        )
        drawn.anchors["trail"] = place
        return place[0] - rules.item_gap
    return right


def _item_text(drawn: Drawn, block: WireBlock, area: Bounds, ctx: WireContext) -> None:
    """Draw the title and the detail of a list item, as one block in the middle of the item."""
    rules, colors = ctx.rules, ctx.colors
    left, top, width, height = area
    title = line_height(rules.font_title, ctx)
    detail = line_height(rules.font_small, ctx) if block.detail else 0
    start = top + (height - title - detail) / HALF
    drawn.parts.append(
        label(
            (left, start, width, title), block.text, Ink(rules.font_title, colors.ink, is_bold=True)
        )
    )
    drawn.anchors["title"] = (left, start, width, title)
    if block.detail:
        drawn.parts.append(
            label(
                (left, start + title, width, detail),
                block.detail,
                Ink(rules.font_small, colors.muted),
            )
        )


def card_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a card: its own, or what its image, its lines and its footer need."""
    rules = ctx.rules
    if block.height:
        return block.height
    if block.image == "top":
        footer = rules.card_footer if (block.chip or block.action) else 0
        lines = _lines_height(block, ctx)
        return 2 * rules.card_pad + rules.card_image + rules.card_text_gap + lines + footer
    return rules.card_row_height


def _lines_height(block: WireBlock, ctx: WireContext) -> float:
    """Return the height of what a card says: a title and a detail, or the two grey bars."""
    rules = ctx.rules
    if not block.text:
        return rules.card_bar_top + rules.card_bar_title + 2 * rules.bar_gap + rules.bar_height
    detail = line_height(rules.font_small, ctx) if block.detail else 0
    return line_height(rules.font_title, ctx) + detail


def draw_card(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a card: an image at the left or on top, a title, a detail, a price and an action."""
    rules = ctx.rules
    x, y, width, height = box
    drawn = Drawn([card_box(box, ctx, is_selected=bool(block.selected))], {})
    pad = rules.card_pad
    text_left, text_top, text_right = x + pad, y + pad, x + width - pad
    if block.image == "left":
        thumb_width = rules.card_thumb_bars if not block.text else rules.card_thumb
        thumb_height = height - 2 * pad if block.height else rules.card_thumb
        thumb = (x + pad, y + pad, thumb_width, thumb_height)
        drawn.parts.extend(cross_box(thumb, ctx, rules.thumb_radius))
        drawn.anchors["image"] = thumb
        text_left = thumb[0] + thumb_width + rules.item_gap
    if block.image == "top":
        picture = (x + pad, y + pad, width - 2 * pad, rules.card_image)
        drawn.parts.extend(cross_box(picture, ctx, rules.thumb_radius))
        drawn.anchors["image"] = picture
        text_top = picture[1] + picture[3] + rules.card_text_gap
    area = (text_left, text_top, text_right - text_left, y + height - pad - text_top)
    _card_lines(drawn, block, area, ctx)
    _card_end(drawn, block, (x, y, width, height), ctx)
    add_tap(drawn, block, box, ctx)
    return drawn


def _card_lines(drawn: Drawn, block: WireBlock, area: Bounds, ctx: WireContext) -> None:
    """Draw the title and the detail of a card, or two grey bars when it has no words yet."""
    rules, colors = ctx.rules, ctx.colors
    left, top, width, _ = area
    price_room = (
        text_width(block.price, rules.font_title, ctx) + rules.item_gap if block.price else 0
    )
    if not block.text:
        strong = (
            left,
            top + rules.card_bar_top,
            width * BAR_WIDTH_FRACTIONS[0],
            rules.card_bar_title,
        )
        soft = (
            left,
            strong[1] + rules.card_bar_title + rules.bar_gap,
            width * BAR_WIDTH_FRACTIONS[1],
            rules.bar_height,
        )
        drawn.parts.extend([bar(strong, colors.cross), bar(soft, colors.bar)])
        drawn.anchors["title"] = strong
        return
    title = line_height(rules.font_title, ctx)
    drawn.parts.append(
        label(
            (left, top, width - price_room, title),
            block.text,
            Ink(rules.font_title, colors.ink, is_bold=True),
        )
    )
    drawn.anchors["title"] = (left, top, width - price_room, title)
    if block.detail:
        detail = (left, top + title, width - price_room, line_height(rules.font_small, ctx))
        drawn.parts.append(label(detail, block.detail, Ink(rules.font_small, colors.muted)))
    if block.price:
        price = (
            left + width - price_room + rules.item_gap,
            top,
            price_room - rules.item_gap,
            title,
        )
        drawn.parts.append(
            label(
                price,
                block.price,
                Ink(rules.font_title, colors.ink, is_bold=True, align=Align.RIGHT),
            )
        )
        drawn.anchors["price"] = _padded(price, rules.price_pad)


def _card_end(drawn: Drawn, block: WireBlock, box: Bounds, ctx: WireContext) -> None:
    """Draw the foot of a card: a stepper, or a chip at the left and a small action at the right."""
    rules = ctx.rules
    x, y, width, height = box
    right, bottom = x + width - rules.card_pad, y + height - rules.card_pad
    if block.stepper:
        stepper = (
            right - rules.stepper_width,
            bottom - rules.stepper_height,
            rules.stepper_width,
            rules.stepper_height,
        )
        drawn.parts.extend(stepper_parts(stepper, block.stepper, ctx))
        drawn.anchors["stepper"] = stepper
        return
    if block.action:
        place = (
            right - rules.mini_width,
            bottom - rules.mini_height,
            rules.mini_width,
            rules.mini_height,
        )
        drawn.parts.extend(button_parts(place, block.action, ElementStyle.PRIMARY, ctx))
        drawn.anchors["action"] = place
    if block.chip:
        width = chip_width(block.chip, ctx)
        chip = (
            _foot_left(drawn, block, x, ctx),
            bottom - rules.mini_height / HALF - rules.chip_height / HALF,
            width,
            rules.chip_height,
        )
        drawn.parts.extend(chip_parts(chip, block.chip, block.tone or Tone.BLUE, ctx))
        drawn.anchors["chip"] = chip


def _foot_left(drawn: Drawn, block: WireBlock, left: float, ctx: WireContext) -> float:
    """Return where the foot of a card starts: under its words, which are after a side image."""
    rules = ctx.rules
    if block.image != "left":
        return left + rules.card_pad
    image = drawn.anchors["image"]
    return image[0] + image[2] + rules.item_gap


def figure_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a figure card."""
    return block.height or ctx.rules.figure_height


def draw_figure(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a key figure: its name, the value in large type and the change as a chip."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, height = box
    left = x + rules.figure_pad
    drawn = Drawn([card_box(box, ctx)], {})
    top = y + rules.figure_pad
    name = line_height(rules.font_small, ctx)
    drawn.parts.append(
        label((left, top, width, name), block.text, Ink(rules.font_small, colors.muted))
    )
    value = line_height(rules.font_figure, ctx)
    value_box = (left, top + name + rules.figure_gap, width - 2 * rules.figure_pad, value)
    drawn.parts.append(
        label(value_box, block.value, Ink(rules.font_figure, colors.ink, is_bold=True))
    )
    drawn.anchors["value"] = value_box
    if block.chip:
        chip = (
            left,
            y + height - rules.figure_pad - rules.chip_height,
            chip_width(block.chip, ctx),
            rules.chip_height,
        )
        drawn.parts.extend(chip_parts(chip, block.chip, block.tone or Tone.GRAY, ctx))
        drawn.anchors["chip"] = chip
    return drawn


def table_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a table: its title, its header row and its body rows."""
    rules = ctx.rules
    title = rules.table_title if block.text else 0
    return block.height or (
        2 * rules.card_pad + title + rules.table_header + len(block.cells) * rules.table_row
    )


def draw_table(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a table: a title, a header row with a rule, and rows of text, chips and buttons."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, _ = box
    drawn = Drawn([card_box(box, ctx)], {})
    left, top = x + rules.card_pad, y + rules.card_pad
    inner = width - 2 * rules.card_pad
    if block.text:
        drawn.parts.append(
            label(
                (left, top, inner, rules.table_title),
                block.text,
                Ink(rules.font_label, colors.ink, is_bold=True),
            )
        )
        top += rules.table_title
    edges = _column_edges(block, left, inner)
    for index, column in enumerate(block.columns):
        place = (
            edges[index] + rules.table_cell_pad,
            top,
            edges[index + 1] - edges[index],
            rules.table_header,
        )
        drawn.parts.append(
            label(place, column.label, Ink(rules.font_header, colors.muted, is_bold=True))
        )
    top += rules.table_header
    drawn.parts.append(rect((left, top, inner, 1), colors.line))
    for number, cells in enumerate(block.cells):
        row = (left, top + number * rules.table_row, inner, rules.table_row)
        _row_parts(drawn, block, (number, cells, row), ctx)
    return drawn


def _column_edges(block: WireBlock, left: float, inner: float) -> list[float]:
    """Return the x of the left edge of each column and of the right edge of the last."""
    total = sum(column.weight for column in block.columns) or 1
    edges = [left]
    for column in block.columns:
        edges.append(edges[-1] + inner * column.weight / total)
    return edges


def _row_parts(
    drawn: Drawn,
    block: WireBlock,
    row: tuple[int, tuple[WireCell, ...], Bounds],
    ctx: WireContext,
) -> None:
    """Draw the cells of one table row and note the box of its action."""
    number, cells, box = row
    rules = ctx.rules
    edges = _column_edges(block, box[0], box[2])
    drawn.anchors[f"row-{number}"] = box
    for index, (column, cell) in enumerate(zip(block.columns, cells, strict=False)):
        place = (
            edges[index] + rules.table_cell_pad,
            box[1],
            edges[index + 1] - edges[index] - rules.table_cell_pad,
            box[3],
        )
        parts = _cell_parts(column.kind, cell, place, ctx)
        drawn.parts.extend(parts[0])
        if parts[1]:
            drawn.anchors[f"action-{number}"] = parts[1]
            if _is_tapped(block, cell):
                add_tap(drawn, block, parts[1], ctx)


def _is_tapped(block: WireBlock, cell: WireCell) -> bool:
    """Tell whether a table button is the one that is tapped: the primary one."""
    return has_flag(block, "tap") and cell.style == ElementStyle.PRIMARY.value


def _cell_parts(
    kind: CellKind, cell: WireCell, place: Bounds, ctx: WireContext
) -> tuple[list[Part], Bounds | None]:
    """Draw one cell; a button cell also returns its box, so that it can be pointed at."""
    rules, colors = ctx.rules, ctx.colors
    text, style = cell.text, cell.style
    if kind is CellKind.CHIP:
        width = chip_width(text, ctx)
        box = (place[0], middle(place, rules.chip_height), width, rules.chip_height)
        return chip_parts(box, text, Tone(style) if style else Tone.GRAY, ctx), None
    if kind is CellKind.BUTTON:
        box = (
            place[0],
            middle(place, rules.table_button_height),
            rules.table_button_width,
            rules.table_button_height,
        )
        return button_parts(
            box, text, ElementStyle(style) if style else ElementStyle.SECONDARY, ctx
        ), box
    ink = Ink(
        rules.font_small + 1,
        colors.ink if kind is CellKind.BOLD else colors.text,
        is_bold=kind is CellKind.BOLD,
    )
    return [label(place, text, ink)], None


def chart_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a chart card."""
    return block.height or ctx.rules.chart_height


def draw_chart(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a bar chart: grey bars, the key one in blue, on a baseline."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, height = box
    drawn = Drawn([card_box(box, ctx)], {})
    top = y + rules.card_pad
    if block.text:
        drawn.parts.append(
            label(
                (x + rules.card_pad, top, width, rules.table_title),
                block.text,
                Ink(rules.font_label, colors.ink, is_bold=True),
            )
        )
    inner_left, inner_width = x + rules.chart_pad, width - 2 * rules.chart_pad
    base = y + height - rules.chart_pad
    area = base - (y + rules.chart_top)
    drawn.parts.append(rect((inner_left, base, inner_width, 1), colors.line))
    highest = max(block.values, default=1) or 1
    key = (
        block.selected[0] if block.selected else block.values.index(highest) if block.values else -1
    )
    slot = inner_width / max(len(block.values), 1)
    for index, value in enumerate(block.values):
        bar_width = slot * rules.bar_fraction
        bar_height = area * value / highest * rules.bar_headroom
        place = (
            inner_left + index * slot + (slot - bar_width) / HALF,
            base - bar_height,
            bar_width,
            bar_height,
        )
        fill = colors.blue if index == key else colors.bar
        drawn.parts.append(rect(place, fill, None, rules.bar_radius))
        drawn.anchors[f"bar-{index}"] = place
    return drawn


def _padded(box: Bounds, pad: float) -> Bounds:
    """Grow a box by a padding on every side, so that a badge on its corner clears the text."""
    return (box[0] - pad, box[1] - pad, box[2] + 2 * pad, box[3] + 2 * pad)
