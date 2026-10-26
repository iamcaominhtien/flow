"""The parts a screen drawing is made of: rectangles, texts, circles, icons, hatches and arcs."""

from dataclasses import dataclass
from enum import StrEnum


class PartKind(StrEnum):
    """What a part of a screen drawing is."""

    RECT = "rect"
    TEXT = "text"
    CIRCLE = "circle"
    ICON = "icon"
    HATCH = "hatch"
    ARC = "arc"


class Align(StrEnum):
    """How the text of a part sits in its box."""

    LEFT = "left"
    CENTER = "center"


Bounds = tuple[float, float, float, float]  # x, y, width, height, relative to the node


@dataclass(frozen=True)
class Part:
    """One shape or text of a screen drawing."""

    kind: PartKind
    bounds: Bounds
    fill: str | None = None
    stroke: str | None = None
    stroke_width: float = 1
    radius: float = 0
    is_dashed: bool = False
    opacity: float = 1.0
    text: str = ""
    font_size: float = 9
    is_bold: bool = False
    is_mono: bool = False
    color: str = ""
    align: Align = Align.CENTER
    icon: str = ""
