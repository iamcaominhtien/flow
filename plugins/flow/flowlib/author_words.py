"""The words on a screen flow arrow, for a hand-laid diagram: ``trigger [guard] / effect``.

The same chips as the automatic screen flow draws (design 02 section 2.1): a dark chip for what
the person does, a slate chip with an icon for what the system does, a guard in square brackets
(green, or rose for a failure) and an effect after a slash. The author names the parts; this
module builds the chips and puts them beside the line.
"""

from dataclasses import dataclass
from itertools import pairwise

from .diagrams.screen_labels import (
    CHIP_ABOVE_PX,
    SIDE_GAP_PX,
    STACK_PX,
    TEXT_BELOW_PX,
    Caption,
    chip_width,
    line_width,
    text_labels,
    trigger_label,
)
from .diagrams.screen_spec import Trigger
from .model import EdgeLabel, Point

MIDDLE = 0.5
FLAT_TOLERANCE_PX = 1.0  # a segment this close to level counts as horizontal


@dataclass(frozen=True)
class EdgeWords:
    """What an arrow says, and where on the line the words go."""

    trigger: str | None = None
    system_icon: str | None = None  # an icon name makes the trigger a system event (slate chip)
    guard: str | None = None  # written without the brackets
    effect: str | None = None  # written without the slash
    is_failure: bool = False  # the guard is rose, and the line is a "no" line unless a role is set
    # A code such as ``C1``: the arrow shows only the code, and its words go in the conditions
    # table (``Canvas.conditions``). Use it when the words are longer than about 20 characters.
    code: str | None = None
    segment: int | None = None  # which stretch of the line carries the words; default the longest
    along: float = MIDDLE  # how far along that stretch, from 0 to 1
    shift: Point = (0.0, 0.0)  # a last nudge of the words, in pixels
    # On a vertical stretch, put the words left of the line (True) or right (False). None lets
    # the canvas choose: the side away from the middle of the screen the line runs along, so the
    # two lines of a back-and-forth pair carry their words outside the pair.
    is_left: bool | None = None


def build_words(
    words: EdgeWords, points: list[Point]
) -> tuple[EdgeLabel | None, tuple[EdgeLabel, ...]]:
    """Build the chips of an arrow and place them beside a stretch of its line.

    Args:
        words: What the arrow says.
        points: The corners of the line.

    Returns:
        The main chip (the trigger, else the guard, else the effect) and the extra chips.
        ``(None, ())`` when the arrow says nothing.
    """
    caption = _caption(words)
    if not caption.has_text:
        return None, ()
    start, end = stretch_of(words, points)
    x = start[0] + (end[0] - start[0]) * words.along + words.shift[0]
    y = start[1] + (end[1] - start[1]) * words.along + words.shift[1]
    if abs(start[1] - end[1]) < FLAT_TOLERANCE_PX:
        chip_at, text_at = (x, y - CHIP_ABOVE_PX), (x, y + TEXT_BELOW_PX)
    else:
        chip_at, text_at = _beside(caption, (x, y), -1 if words.is_left else 1)
    chip = trigger_label(caption, chip_at)
    texts = text_labels(caption, text_at)
    if chip is None:
        return texts[0], texts[1:]
    return chip, texts


def _caption(words: EdgeWords) -> Caption:
    """Build the caption the screen flow modules draw from the words of an arrow.

    A coded arrow keeps only its code on the line; its words go in the conditions table.
    """
    trigger = Trigger(words.trigger, words.system_icon) if words.trigger else None
    if words.code:
        return Caption(trigger, words.code, None, None, words.is_failure)
    return Caption(trigger, None, words.guard, words.effect, words.is_failure)


def stretch_of(words: EdgeWords, points: list[Point]) -> tuple[Point, Point]:
    """Return the stretch of the line that carries the words: the chosen one, else the longest.

    Args:
        words: What the arrow says; its ``segment`` picks a stretch.
        points: The corners of the line.

    Returns:
        The start and the end of the stretch.
    """
    stretches = list(pairwise(points))
    if words.segment is not None:
        return stretches[words.segment]
    return max(
        stretches, key=lambda pair: abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1])
    )


def _beside(caption: Caption, middle: Point, side: int) -> tuple[Point, Point]:
    """Return the centres of the chip and of the text beside a vertical line, chip over text."""
    chip_y = middle[1] - (STACK_PX if line_width(caption) else 0)
    text_y = middle[1] + (STACK_PX if caption.chip_text else 0)
    chip_x = middle[0] + side * (SIDE_GAP_PX + chip_width(caption) / 2)
    text_x = middle[0] + side * (SIDE_GAP_PX + line_width(caption) / 2)
    return (chip_x, chip_y), (text_x, text_y)
