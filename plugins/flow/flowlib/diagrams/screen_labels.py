"""The words on an arrow of a screen flow: ``trigger [guard] / effect`` (design 02 section 2.1).

The trigger is a chip on the line (dark for the user, slate with an icon for the system), the
guard is mono in square brackets under the line (green on the success path, rose on failure) and
the effect follows a slash in grey. A long condition is replaced on the arrow by a code (C1) and
written in a table.
"""

from dataclasses import dataclass

from ..model import EdgeLabel, LabelKind, Point
from .screen_spec import Conditions, Transition, TransitionKind, Trigger

TRIGGER_CHAR_EM = 0.66  # of the 10 px bold chip type, with a margin
TRIGGER_FONT_PX = 10
MONO_CHAR_EM = 0.62
MONO_FONT_PX = 11
EFFECT_CHAR_EM = 0.58
CHIP_PADDING_PX = 16  # the horizontal padding the renderers give a chip
ICON_ROOM_PX = 16  # an icon and its gap at the start of a chip
CHIP_ABOVE_PX = 18  # the chip sits this far above a horizontal line
TEXT_BELOW_PX = 19  # the guard and the effect sit this far below it
SIDE_GAP_PX = 10  # between a vertical line and the chip beside it
STACK_PX = 12  # half the distance between the chip and the text of a vertical line
VERTICAL_LABEL_FRACTION = 0.35  # how far down a vertical line its words sit, clear of zone pills
CODE_PREFIX = "C"


@dataclass(frozen=True)
class Caption:
    """What one arrow says, already split into the parts that are drawn."""

    trigger: Trigger | None
    code: str | None
    guard: str | None
    effect: str | None
    is_failure: bool

    @property
    def has_text(self) -> bool:
        """Tell whether there is anything to write on the arrow."""
        return bool(self.chip_text or self.guard or self.effect)

    @property
    def chip_text(self) -> str:
        """Return the text of the chip: the code when there is one, else the trigger."""
        if self.code:
            return self.code
        return self.trigger.text if self.trigger else ""


def is_coded(transition: Transition, mode: Conditions) -> bool:
    """Tell whether a transition is written as a code and a table row.

    Args:
        transition: The transition.
        mode: The ``conditions`` setting of the spec.

    Returns:
        True for an explicit ``code``, or for any transition with words in coded mode.
    """
    if transition.code:
        return True
    has_words = bool(transition.trigger or transition.guard or transition.effect)
    return mode is Conditions.CODED and has_words


def assign_codes(transitions: tuple[Transition, ...], mode: Conditions) -> dict[int, str]:
    """Give each coded transition its code: its own, or C1, C2 in the order of the spec.

    Args:
        transitions: The transitions of the spec.
        mode: The ``conditions`` setting of the spec.

    Returns:
        Transition index to code, for the coded transitions only.
    """
    codes: dict[int, str] = {}
    taken = {transition.code for transition in transitions if transition.code}
    counter = 0
    for index, transition in enumerate(transitions):
        if not is_coded(transition, mode):
            continue
        if transition.code:
            codes[index] = transition.code
            continue
        counter += 1
        while f"{CODE_PREFIX}{counter}" in taken:
            counter += 1
        codes[index] = f"{CODE_PREFIX}{counter}"
    return codes


def caption_of(transition: Transition, code: str | None) -> Caption:
    """Build the caption of a transition; a coded one keeps only its code on the arrow."""
    failure = transition.kind is TransitionKind.FAILURE
    if code:
        return Caption(transition.trigger, code, None, None, failure)
    return Caption(transition.trigger, None, transition.guard, transition.effect, failure)


def _text_width(text: str, char_em: float, font_px: float) -> float:
    """Estimate the width of a text, padding of the chip included."""
    return len(text) * char_em * font_px + CHIP_PADDING_PX


def chip_width(caption: Caption) -> float:
    """Estimate the width of the trigger chip, or of the code box."""
    if not caption.chip_text:
        return 0.0
    if caption.code:
        return _text_width(caption.code, MONO_CHAR_EM, MONO_FONT_PX)
    icon = ICON_ROOM_PX if caption.trigger and caption.trigger.system_icon else 0
    return _text_width(caption.chip_text, TRIGGER_CHAR_EM, TRIGGER_FONT_PX) + icon


def _guard_text(caption: Caption) -> str:
    """Return the guard as written: in square brackets."""
    return f"[{caption.guard}]" if caption.guard else ""


def _effect_text(caption: Caption) -> str:
    """Return the effect as written: after a slash."""
    return f"/ {caption.effect}" if caption.effect else ""


def _guard_width(caption: Caption) -> float:
    """Estimate the width of the guard."""
    return _text_width(_guard_text(caption), MONO_CHAR_EM, MONO_FONT_PX) if caption.guard else 0.0


def _effect_width(caption: Caption) -> float:
    """Estimate the width of the effect."""
    text = _effect_text(caption)
    return _text_width(text, EFFECT_CHAR_EM, MONO_FONT_PX) if caption.effect else 0.0


def line_width(caption: Caption) -> float:
    """Estimate the width of the line of text under the arrow: the guard, then the effect."""
    return _guard_width(caption) + _effect_width(caption)


def caption_width(caption: Caption) -> float:
    """Estimate how wide the whole caption is: the wider of the chip and the text line."""
    return max(chip_width(caption), line_width(caption))


def trigger_label(caption: Caption, at: Point) -> EdgeLabel | None:
    """Make the chip of a caption: dark for the user, slate with an icon for the system."""
    if not caption.chip_text:
        return None
    if caption.code:
        return EdgeLabel(caption.code, at, LabelKind.CODE)
    system = caption.trigger.system_icon if caption.trigger else None
    kind = LabelKind.SYSTEM if system else LabelKind.USER
    return EdgeLabel(caption.chip_text, at, kind, icon=system)


def text_labels(caption: Caption, centre: Point) -> tuple[EdgeLabel, ...]:
    """Make the guard and the effect, side by side and centred on a point."""
    if not line_width(caption):
        return ()
    kind = LabelKind.GUARD_FAIL if caption.is_failure else LabelKind.GUARD_OK
    start = centre[0] - line_width(caption) / 2
    labels = []
    if caption.guard:
        at = (start + _guard_width(caption) / 2, centre[1])
        labels.append(EdgeLabel(_guard_text(caption), at, kind))
        start += _guard_width(caption)
    if caption.effect:
        at = (start + _effect_width(caption) / 2, centre[1])
        labels.append(EdgeLabel(_effect_text(caption), at, LabelKind.EFFECT))
    return tuple(labels)


def place_caption(
    segment: tuple[Point, Point], caption: Caption
) -> tuple[EdgeLabel | None, tuple[EdgeLabel, ...]]:
    """Place a caption on the longest segment of an arrow.

    On a horizontal line the chip sits above the line and the guard and effect below it. On a
    vertical line both sit to the right, the chip above the text.

    Args:
        segment: The two ends of the segment.
        caption: What the arrow says.

    Returns:
        The chip, or None, and the guard and effect labels.
    """
    (x0, y0), (x1, y1) = segment
    if y0 == y1:
        middle = (x0 + x1) / 2
        chip_at = (middle, y0 - CHIP_ABOVE_PX)
        return trigger_label(caption, chip_at), text_labels(caption, (middle, y0 + TEXT_BELOW_PX))
    middle_y = y0 + (y1 - y0) * VERTICAL_LABEL_FRACTION
    has_chip = bool(caption.chip_text)
    has_text = bool(line_width(caption))
    chip_y = middle_y - (STACK_PX if has_text else 0)
    text_y = middle_y + (STACK_PX if has_chip else 0)
    chip_at = (x0 + SIDE_GAP_PX + chip_width(caption) / 2, chip_y)
    text_centre = (x0 + SIDE_GAP_PX + line_width(caption) / 2, text_y)
    return trigger_label(caption, chip_at), text_labels(caption, text_centre)
