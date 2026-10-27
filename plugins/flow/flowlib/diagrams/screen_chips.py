"""Put the words of each arrow of a screen flow where nothing is under them (design 02, Layout).

The words go on the longest stretch of the line, in the middle, as before. When that place is
taken by a frame, an id chip, a zone label, other words or another line, the next best place on
the same line is tried: another point of the stretch, the other side of a vertical one, or another
stretch.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from itertools import pairwise

from ..check import Rect, chip_rect
from ..html_zones import pill_width
from ..model import EdgeLabel, Frame, Node, Point
from ..screen_parts import chip_box, is_card
from ..theme import Theme
from .screen_labels import (
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

HORIZONTAL_FRACTION = 0.5  # how far along a horizontal stretch the words sit first
VERTICAL_FRACTION = 0.35  # the same for a vertical stretch, clear of the pills of zones
FRACTIONS = (0.5, 0.35, 0.65, 0.2, 0.8, 0.1, 0.9)  # the other points of a stretch, in order
MIN_STRETCH_PX = 30.0  # a shorter stretch is a turn, not a place for words
TEXT_HEIGHT_PX = 16.0  # the height of the line of text under an arrow
ZONE_LABEL_DEPTH_PX = 36.0  # how far down from the top of a zone its label reaches
ZONE_LABEL_PAD_PX = 24.0  # the room a zone label takes beside its text
BORDER_HALF_PX = 1.0  # half the thickness given to the border of a zone
LINE_CLEAR_PX = 8.0  # words keep this far from the lines of other arrows, or they seem to be theirs
LINE_COST = 1  # for each line of another arrow that runs under the words
BLOCK_COST = 100  # for each frame, chip or word that is under the words


@dataclass(frozen=True)
class Spot:
    """A place for the words of one arrow: its chip, its text and the rectangles they cover."""

    chip: EdgeLabel | None
    texts: tuple[EdgeLabel, ...]
    rects: tuple[Rect, ...]


@dataclass
class Crowd:
    """What the words of an arrow must keep clear of."""

    blocks: list[Rect] = field(default_factory=list)
    lines: list[tuple[int, Rect]] = field(default_factory=list)  # the owner, then the line


def blocks_of(nodes: dict[str, Node], frames: list[Frame], theme: Theme) -> list[Rect]:
    """List the rectangles that words must not cover: frames, id chips, system chips, zone pills.

    Args:
        nodes: The placed nodes.
        frames: The zone frames.
        theme: The design tokens.

    Returns:
        The rectangles.
    """
    blocks: list[Rect] = []
    for node in nodes.values():
        blocks.append(Rect(node.x, node.y, node.x + node.width, node.y + node.height))
        if node.screen is not None and not is_card(node.screen):
            left, top, width, height = chip_box(node, node.screen, theme)
            x, y = node.x + left, node.y + top
            blocks.append(Rect(x, y, x + width, y + height))
        if node.chip is not None:
            at = (node.x + node.chip.at[0], node.y + node.chip.at[1])
            blocks.append(chip_rect(EdgeLabel(node.chip.text, at, node.chip.kind), theme.layout))
    for frame in frames:
        width = pill_width(frame.label or "", theme) + ZONE_LABEL_PAD_PX
        blocks.append(Rect(frame.x, frame.y, frame.x + width, frame.y + ZONE_LABEL_DEPTH_PX))
        blocks.extend(_border_of(frame))
    return blocks


def _border_of(frame: Frame) -> list[Rect]:
    """Return the four sides of a zone frame as thin rectangles: words must not straddle them."""
    left, top = frame.x, frame.y
    right, bottom = left + frame.width, top + frame.height
    half = BORDER_HALF_PX
    return [
        Rect(left - half, top, left + half, bottom),
        Rect(right - half, top, right + half, bottom),
        Rect(left, top - half, right, top + half),
        Rect(left, bottom - half, right, bottom + half),
    ]


def lines_of(routes: list[tuple[Point, ...]]) -> list[tuple[int, Rect]]:
    """Turn the routes of all arrows into thin rectangles, one per stretch, with their owner."""
    return [
        (owner, Rect(min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])))
        for owner, points in enumerate(routes)
        for a, b in pairwise(points)
    ]


def choose_spot(
    owner: int, points: tuple[Point, ...], caption: Caption, around: tuple[Crowd, Theme]
) -> Spot:
    """Pick the place for the words of an arrow: the first that covers nothing, else the best.

    Args:
        owner: The number of the arrow in the list of routes that made the crowd.
        points: The route of the arrow.
        caption: What the arrow says.
        around: What to keep clear of, and the design tokens.

    Returns:
        The spot. Its rectangles are not yet in the crowd.
    """
    crowd, theme = around
    best: tuple[int, Spot] | None = None
    for spot in _spots(points, caption, theme):
        cost = _cost(spot, crowd, owner)
        if cost == 0:
            return spot
        if best is None or cost < best[0]:
            best = (cost, spot)
    assert best is not None
    return best[1]


def _cost(spot: Spot, crowd: Crowd, owner: int) -> int:
    """Count what the words of a spot cover: frames and words cost far more than a line."""
    cost = 0
    for rect in spot.rects:
        cost += BLOCK_COST * sum(rect.overlaps(block) for block in crowd.blocks)
        cost += LINE_COST * sum(
            rect.overlaps(line, LINE_CLEAR_PX) for who, line in crowd.lines if who != owner
        )
    return cost


def _length(stretch: tuple[Point, Point]) -> float:
    """Return the length of a stretch."""
    return abs(stretch[1][0] - stretch[0][0]) + abs(stretch[1][1] - stretch[0][1])


def _spots(points: tuple[Point, ...], caption: Caption, theme: Theme) -> Iterator[Spot]:
    """Yield the places to try, best first: the longest stretch, in the middle, comes first."""
    stretches = sorted(pairwise(points), key=lambda stretch: -_length(stretch))
    for number, stretch in enumerate(stretches):
        if number and _length(stretch) < MIN_STRETCH_PX:
            continue
        is_flat = stretch[0][1] == stretch[1][1]
        first = HORIZONTAL_FRACTION if is_flat else VERTICAL_FRACTION
        for fraction in dict.fromkeys((first, *FRACTIONS)):
            for side in (1,) if is_flat else (1, -1):
                yield _spot(stretch, caption, (fraction, side), theme)


def _spot(
    stretch: tuple[Point, Point], caption: Caption, anchor: tuple[float, int], theme: Theme
) -> Spot:
    """Make the words of an arrow at a point of one of its stretches.

    On a horizontal line the chip is above it and the text below; on a vertical one both are
    beside it, the chip over the text.
    """
    (x0, y0), (x1, y1) = stretch
    fraction, side = anchor
    if y0 == y1:
        middle = x0 + (x1 - x0) * fraction
        return _made(caption, (middle, y0 - CHIP_ABOVE_PX), (middle, y0 + TEXT_BELOW_PX), theme)
    middle_y = y0 + (y1 - y0) * fraction
    chip_y = middle_y - (STACK_PX if line_width(caption) else 0)
    text_y = middle_y + (STACK_PX if caption.chip_text else 0)
    chip_x = x0 + side * (SIDE_GAP_PX + chip_width(caption) / 2)
    text_x = x0 + side * (SIDE_GAP_PX + line_width(caption) / 2)
    return _made(caption, (chip_x, chip_y), (text_x, text_y), theme)


def _made(caption: Caption, chip_at: Point, text_at: Point, theme: Theme) -> Spot:
    """Build a spot from the centre of the chip and the centre of the text."""
    chip = trigger_label(caption, chip_at)
    rects = [chip_rect(chip, theme.layout)] if chip is not None else []
    if line_width(caption):
        half = line_width(caption) / 2
        rects.append(
            Rect(
                text_at[0] - half,
                text_at[1] - TEXT_HEIGHT_PX / 2,
                text_at[0] + half,
                text_at[1] + TEXT_HEIGHT_PX / 2,
            )
        )
    return Spot(chip, text_labels(caption, text_at), tuple(rects))
