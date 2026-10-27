"""The note below a wireframe: a numbered badge, a bold title and one line (design 10 section 3)."""

from .model import WireBlock
from .screen_part import Align, Bounds
from .wire_kit import Drawn, Ink, WireContext, circle, label, wrapped


def note_lines(block: WireBlock, width: float, ctx: WireContext) -> list[str]:
    """Break the line of a note into the lines that fit beside its badge."""
    notes = ctx.rules.notes
    return wrapped(block.detail, width - notes.text_left, notes.text_font, ctx)


def note_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a note: its title and the lines of its text."""
    notes = ctx.rules.notes
    return notes.title_height + len(note_lines(block, width, ctx)) * notes.line_height


def draw_note(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a note: the badge, the title beside it and the text under the title."""
    rules, colors, notes = ctx.rules, ctx.colors, ctx.rules.notes
    x, y, width, _ = box
    badge = ctx.theme.badge
    disc = (x, y + (notes.title_height - rules.badge_size) / 2, rules.badge_size, rules.badge_size)
    number = Ink(rules.font_badge, badge.foreground, is_bold=True, align=Align.CENTER, is_mono=True)
    drawn = Drawn(
        [circle(disc, badge.background), label(disc, block.value, number)], {"badge": disc}
    )
    left = x + notes.text_left
    title = (left, y, width - notes.text_left, notes.title_height)
    drawn.parts.append(label(title, block.text, Ink(notes.title_font, colors.ink, is_bold=True)))
    for index, line in enumerate(note_lines(block, width, ctx)):
        place = (
            left,
            y + notes.title_height + index * notes.line_height,
            width - notes.text_left,
            notes.line_height,
        )
        drawn.parts.append(label(place, line, Ink(notes.text_font, colors.muted)))
    return drawn
