"""Measure a line of text with the widths of the characters of Inter, the sans font of every theme.

The estimate of ``sizing`` counts characters; it is safe for laying out a node but is off by up
to 10% either way for one line of bold words. A device frame hides what does not fit, so the
check of a screen measures its words with these widths instead. They were measured in Chromium
with the canvas ``measureText`` at 100 px, weights 500 and 700 (the regular and the bold weight
of a screen). Kerning is left out; it changes a word by about 1%.
"""

import json
from enum import StrEnum
from functools import cache
from pathlib import Path
from statistics import fmean

WIDTHS_FILE = Path(__file__).with_name("inter_widths.json")
MEASURED_SIZE_PX = 100  # the font size the widths in the file were measured at


class FontWeight(StrEnum):
    """A weight of Inter that the widths file holds."""

    REGULAR = "500"
    BOLD = "700"


def inter_width(text: str, font_size: float, weight: FontWeight) -> float:
    """Return how wide a line of text is drawn in Inter.

    Args:
        text: One line of text.
        font_size: The font size in pixels.
        weight: The weight it is drawn in.

    Returns:
        The width in pixels. A character the file does not hold (outside ASCII) counts as an
        average letter.
    """
    widths = _widths()[weight]
    average = _average_letter(weight)
    return sum(widths.get(char, average) for char in text) * font_size / MEASURED_SIZE_PX


@cache
def _widths() -> dict[str, dict[str, float]]:
    """Read the widths file: for each weight, the width of each character at 100 px."""
    return json.loads(WIDTHS_FILE.read_text(encoding="utf-8"))


@cache
def _average_letter(weight: FontWeight) -> float:
    """Return the mean width of the letters of one weight, at 100 px."""
    return fmean(width for char, width in _widths()[weight].items() if char.isalpha())
