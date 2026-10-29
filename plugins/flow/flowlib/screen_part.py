"""The parts a screen drawing is made of: rectangles, texts, circles, icons, arcs and images."""

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
    PATH = "path"  # a stroked outline drawn from an SVG path: a chevron, a cross, a check
    IMAGE = "image"  # a screenshot, fitted to the width of its box and cut at its bottom


class Align(StrEnum):
    """How the text of a part sits in its box."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


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
    path: str = ""  # the ``d`` of an SVG path, in the units of the box of a PATH part
    image: str = ""  # the base64 text of the PNG of an IMAGE part
