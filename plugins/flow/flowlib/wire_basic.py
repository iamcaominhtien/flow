"""The plain wireframe blocks: text, button, form field, image, chips, stepper, rows, checklist."""

from .model import ElementStyle, Tone, WireBlock
from .screen_part import Align, Bounds
from .wire_kit import (
    HALF,
    MINUS_PATH,
    PLUS_PATH,
    Drawn,
    Ink,
    Line,
    WireContext,
    add_tap,
    bar,
    button_parts,
    card_box,
    check_path,
    chip_parts,
    chip_width,
    cross_box,
    has_flag,
    icon,
    label,
    line_height,
    middle,
    pill,
    rect,
    stroke_path,
    text_width,
)

HEADING_FLAG = "heading"
LABEL_FLAG = "label"
BOLD_FLAG = "bold"
FOCUS_FLAG = "focus"
BAR_FRACTIONS = (1.0, 0.82, 0.6)  # of the width: the lengths of the grey lines of body text
ROW_SEPARATOR = "|"  # between the name and the value of a row
INPUT_BAR_FRACTION = 0.3  # of the field: the grey bar that stands for a placeholder
STEPPER_GLYPH_PX = 12


def stepper_parts(box: Bounds, value: str, ctx: WireContext) -> list:
    """Draw a quantity stepper: a pill with a minus, the quantity and a plus."""
    colors, rules = ctx.colors, ctx.rules
    x, y, width, height = box
    glyph = (height - STEPPER_GLYPH_PX) / HALF
    line = Line(colors.muted, rules.stepper_stroke)
    ink = Ink(rules.font_body, colors.ink, is_bold=True, align=Align.CENTER)
    return [
        pill(box, colors.paper, Line(colors.cross)),
        stroke_path(
            (x + rules.stepper_pad, y + glyph, STEPPER_GLYPH_PX, STEPPER_GLYPH_PX), MINUS_PATH, line
        ),
        label(box, value, ink),
        stroke_path(
            (
                x + width - rules.stepper_pad - STEPPER_GLYPH_PX,
                y + glyph,
                STEPPER_GLYPH_PX,
                STEPPER_GLYPH_PX,
            ),
            PLUS_PATH,
            line,
        ),
    ]


def text_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a text block: its line and the grey bars under it."""
    rules = ctx.rules
    height = line_height(_text_size(block, ctx), ctx) if block.text else 0
    return height + block.bars * (rules.bar_height + rules.bar_gap)


def draw_text(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a line of text, a chip beside it and grey bars under it."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, _ = box
    drawn = Drawn()
    top = y
    if block.text:
        size = _text_size(block, ctx)
        is_strong = has_flag(block, HEADING_FLAG) or has_flag(block, BOLD_FLAG)
        is_strong = is_strong or has_flag(block, LABEL_FLAG)
        height = line_height(size, ctx)
        ink = Ink(size, colors.ink if is_strong else colors.text, is_bold=is_strong)
        drawn.parts.append(label((x, y, width, height), block.text, ink))
        drawn.anchors["text"] = (x, y, text_width(block.text, size, ctx), height)
        top += height
        if block.chip:
            _add_beside_chip(drawn, block, (x + text_width(block.text, size, ctx), y, height), ctx)
    for index in range(block.bars):
        fraction = BAR_FRACTIONS[index % len(BAR_FRACTIONS)]
        top += rules.bar_gap
        drawn.parts.append(bar((x, top, width * fraction, rules.bar_height), colors.bar))
        top += rules.bar_height
    return drawn


def _text_size(block: WireBlock, ctx: WireContext) -> float:
    """Return the font size of a text block: a heading is large, a section label small."""
    rules = ctx.rules
    if has_flag(block, HEADING_FLAG):
        return rules.font_heading
    if has_flag(block, LABEL_FLAG):
        return rules.font_label
    return rules.font_body


def _add_beside_chip(
    drawn: Drawn, block: WireBlock, place: tuple[float, float, float], ctx: WireContext
) -> None:
    """Add the chip that stands beside a heading, on its middle line."""
    rules = ctx.rules
    left, top, line = place
    width = chip_width(block.chip, ctx)
    box = (left + rules.chip_gap, top + (line - rules.chip_height) / HALF, width, rules.chip_height)
    drawn.parts.extend(chip_parts(box, block.chip, block.tone or Tone.GRAY, ctx))
    drawn.anchors["chip"] = box


def button_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a button: large on a phone, where a thumb taps it."""
    if block.height:
        return block.height
    return ctx.rules.button_height_phone if ctx.is_phone else ctx.rules.button_height


def draw_button(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a button: filled blue for the primary action, outlined for the others."""
    colors, rules = ctx.colors, ctx.rules
    style = block.style or ElementStyle.PRIMARY
    drawn = Drawn(button_parts(box, block.text, style, ctx), {"button": box})
    if block.icon:
        reach = (
            text_width(block.text, rules.button_font, ctx) / HALF
            + rules.button_icon
            + rules.icon_gap
        )
        size = rules.button_icon
        place = (box[0] + box[2] / HALF - reach, middle(box, size), size, size)
        drawn.parts.append(icon(place, block.icon, colors.blue))
    add_tap(drawn, block, box, ctx)
    return drawn


def field_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a form field: its label, its input and its hint."""
    rules = ctx.rules
    height = rules.input_height
    if block.text:
        height += line_height(rules.font_label, ctx) + rules.label_gap
    if block.hint:
        height += rules.hint_gap + line_height(rules.font_hint, ctx)
    return height


def draw_field(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a form field: a label, a box with a placeholder or a value, and a hint."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, _ = box
    drawn = Drawn()
    top = y
    if block.text:
        height = line_height(rules.font_label, ctx)
        ink = Ink(rules.font_label, colors.muted, is_bold=True)
        drawn.parts.append(label((x, top, width, height), block.text, ink))
        top += height + rules.label_gap
    action_width = rules.field_action_width if block.action else 0
    gap = rules.field_action_gap if block.action else 0
    field = (x, top, width - action_width - gap, rules.input_height)
    drawn.parts.extend(_input_parts(block, field, ctx))
    drawn.anchors["input"] = field
    if block.action:
        action = (x + width - action_width, top, action_width, rules.input_height)
        drawn.parts.extend(button_parts(action, block.action, ElementStyle.SECONDARY, ctx))
        drawn.anchors["action"] = action
    if block.hint:
        is_error = block.tone is Tone.RED
        ink = Ink(rules.font_hint, colors.rose if is_error else colors.muted)
        hint = (
            x,
            top + rules.input_height + rules.hint_gap,
            width,
            line_height(rules.font_hint, ctx),
        )
        drawn.parts.append(label(hint, block.hint, ink))
    return drawn


def _input_parts(block: WireBlock, field: Bounds, ctx: WireContext) -> list:
    """Draw the box of an input: blue ring when focused, rose when wrong, and what is in it."""
    colors, rules = ctx.colors, ctx.rules
    border = Line(colors.line)
    if has_flag(block, FOCUS_FLAG):
        border = Line(colors.blue, rules.selected_border)
    if block.tone is Tone.RED:
        border = Line(colors.rose, rules.selected_border)
    parts = [rect(field, colors.paper, border, rules.input_radius)]
    x, y, width, height = field
    inner = (x + rules.input_pad, y, width - 2 * rules.input_pad, height)
    if block.value or block.detail:
        shown = block.value or block.detail
        ink = Ink(rules.font_body, colors.ink if block.value else colors.muted)
        parts.append(label(inner, shown, ink))
        return parts
    bar_box = (
        inner[0],
        y + (height - rules.bar_height) / HALF,
        width * INPUT_BAR_FRACTION,
        rules.bar_height,
    )
    parts.append(bar(bar_box, colors.bar))
    return parts


def image_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of an image: its own, or the default of the device."""
    return block.height or ctx.rules.image_height


def draw_image(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw an image as a crossed box; a text is the words laid on it, such as a hero line."""
    rules, colors = ctx.rules, ctx.colors
    drawn = Drawn(cross_box(box, ctx, rules.card_radius), {"image": box})
    if block.text:
        size = rules.font_hero if box[2] >= rules.hero_narrow else rules.font_hero_small
        height = line_height(size, ctx)
        place = (box[0] + rules.hero_pad, middle(box, height), box[2] - 2 * rules.hero_pad, height)
        drawn.parts.append(label(place, block.text, Ink(size, colors.ink, is_bold=True)))
    return drawn


def chip_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a chip block: a status chip is small, a choice is a pill."""
    return ctx.rules.choice_height if block.items else ctx.rules.chip_height


def draw_chip(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a status chip, or a row of choice chips of which the selected one is blue."""
    if not block.items:
        width = chip_width(block.text, ctx)
        place = (box[0], box[1], width, ctx.rules.chip_height)
        return Drawn(chip_parts(place, block.text, block.tone, ctx), {"chip": place})
    return _choice_chips(block, box, ctx)


def _choice_chips(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw the choices one beside the other; one is selected, and that one is blue."""
    rules, colors = ctx.rules, ctx.colors
    drawn = Drawn()
    left = box[0]
    for index, item in enumerate(block.items):
        width = text_width(item, rules.choice_font, ctx) + 2 * rules.choice_pad
        place = (left, box[1], width, rules.choice_height)
        is_selected = index in block.selected
        fill = colors.blue_tint if is_selected else colors.paper
        line = Line(colors.blue, rules.selected_border) if is_selected else Line(colors.cross)
        ink = Ink(
            rules.choice_font,
            colors.blue if is_selected else colors.ink,
            is_bold=True,
            align=Align.CENTER,
        )
        drawn.parts.extend([pill(place, fill, line), label(place, item, ink)])
        drawn.anchors[f"item-{index}"] = place
        left += width + rules.choice_gap
    return drawn


def stepper_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a quantity stepper."""
    return ctx.rules.stepper_height


def draw_stepper(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a quantity stepper at the left of its box."""
    place = (box[0], box[1], ctx.rules.stepper_width, ctx.rules.stepper_height)
    return Drawn(stepper_parts(place, block.text or block.value, ctx), {"stepper": place})


def rows_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a list of name and value rows."""
    return len(block.items) * ctx.rules.row_height


def draw_rows(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw rows of a name at the left and a value at the right; a total is in bold."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, _ = box
    drawn = Drawn()
    for index, item in enumerate(block.items):
        name, _, value = item.partition(ROW_SEPARATOR)
        is_total = has_flag(block, BOLD_FLAG) and index == len(block.items) - 1
        ink = Ink(rules.font_body, colors.ink, is_bold=is_total)
        top = y + index * rules.row_height
        height = rules.row_height
        drawn.parts.append(label((x + rules.row_pad, top, width, height), name, ink))
        value_box = (
            x + width * rules.row_value_start,
            top,
            width * (1 - rules.row_value_start),
            height,
        )
        drawn.parts.append(label(value_box, value, ink))
        drawn.anchors[f"row-{index}"] = (x, top, width, height)
    return drawn


def checklist_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a checklist panel: its title and one row per choice."""
    rules = ctx.rules
    title = rules.checklist_title if block.text else 0
    return 2 * rules.card_pad + title + len(block.items) * rules.checklist_row


def draw_checklist(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a panel of check boxes, as the filters of a menu page."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, _ = box
    drawn = Drawn([card_box(box, ctx)], {})
    left, top = x + rules.card_pad, y + rules.card_pad
    if block.text:
        ink = Ink(rules.font_label, colors.ink, is_bold=True)
        drawn.parts.append(
            label((left, top, width - 2 * rules.card_pad, rules.checklist_title), block.text, ink)
        )
        top += rules.checklist_title
    for index, item in enumerate(block.items):
        row = (left, top, width - 2 * rules.card_pad, rules.checklist_row)
        drawn.parts.extend(_check_row(item, row, index in block.selected, ctx))
        drawn.anchors[f"item-{index}"] = row
        top += rules.checklist_row
    return drawn


def _check_row(text: str, row: Bounds, is_checked: bool, ctx: WireContext) -> list:
    """Draw one row of a checklist: the check box and its words."""
    rules, colors = ctx.rules, ctx.colors
    size = rules.check_size
    square = (row[0], middle(row, size), size, size)
    if is_checked:
        parts = [rect(square, colors.blue, None, rules.check_radius)]
        parts.append(
            stroke_path(square, check_path(size, size), Line(colors.on_blue, rules.stepper_stroke))
        )
    else:
        parts = [rect(square, colors.paper, Line(colors.muted), rules.check_radius)]
    words = (row[0] + size + rules.check_gap, row[1], row[2] - size - rules.check_gap, row[3])
    parts.append(label(words, text, Ink(rules.font_body, colors.text)))
    return parts
