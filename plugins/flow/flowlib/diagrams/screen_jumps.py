"""Draw a jump: a long arrow cut into two short ones that meet at a pair of lettered circles.

An arrow that would cross the whole page (a logout back to the home page, a deep return) can be
written ``"route": "jump"``. It then leaves its source into a circle with a letter, and a circle
with the same letter beside the target leads into it: the off-page connector of the flowchart
design, used on one page. The first part carries the arrow's words.
"""

from dataclasses import dataclass
from itertools import pairwise
from string import ascii_uppercase

from ..model import DEFAULT_FONT_SIZE_PX, Node, Point, Shape, Tone
from ..theme import Theme
from .screen_items import Cell
from .screen_lanes import PortSide
from .screen_plan import Plan, RouteType, sides_of
from .screen_spec import Transition

STUB_PX = 34  # from the frame to the circle
STUB_WORDS_PX = 70  # from the frame to the circle, when the arrow carries words
TRIES = 6  # places to try for a circle, each a step further out
TRY_STEP_PX = 14
CLEAR_PX = 6  # room kept between a circle and another arrow
STEPS = {
    PortSide.NORTH: (0, -1),
    PortSide.SOUTH: (0, 1),
    PortSide.EAST: (1, 0),
    PortSide.WEST: (-1, 0),
}

Routed = tuple[Plan, tuple[Point, ...]]
Box = tuple[float, float, float, float]  # left, top, right, bottom


@dataclass(frozen=True)
class Jump:
    """The second part of a jump arrow, and the two circles it joins."""

    plan: Plan
    points: tuple[Point, ...]  # from the circle by the target into the target
    marks: tuple[Node, Node]  # the circle by the source, then the one by the target


def split_jumps(
    routes: list[Routed], nodes: dict[str, Node], context: tuple[dict[str, Cell], Theme]
) -> tuple[list[Routed], list[Jump]]:
    """Cut every jump arrow into its first part and a jump, and leave the others as they are.

    Each circle goes straight out of its frame side, as near as it can without touching a frame
    or another arrow. The first part is longer when it carries words, so they have room.

    Args:
        routes: Every arrow with its route; a jump's route runs from its source port to its
            target port.
        nodes: The placed nodes, which the circles keep clear of.
        context: The cells of the items, which give the sides of each arrow, and the design
            tokens, which size the circles.

    Returns:
        The routes with each jump cut to its first part, and the jumps.
    """
    cells, theme = context
    size = theme.layout.min_sizes[Shape.CONNECTOR][0]
    lines = [points for plan, points in routes if plan.route is not RouteType.JUMP]
    blocks = [_rect_of(node) for node in nodes.values()]
    kept: list[Routed] = []
    jumps: list[Jump] = []
    for plan, points in routes:
        if plan.route is not RouteType.JUMP:
            kept.append((plan, points))
            continue
        letter = ascii_uppercase[len(jumps) % len(ascii_uppercase)]
        transition = plan.transition
        sides = sides_of(plan, (cells[transition.source], cells[transition.target]))
        first = STUB_WORDS_PX if _has_words(transition) else STUB_PX
        around = (lines, blocks)
        start, out_side, out = _best_end(
            (points[0], sides[0]), nodes[transition.source], (first, size), around
        )
        end, in_side, into = _best_end(
            (points[-1], sides[1]), nodes[transition.target], (STUB_PX, size), around
        )
        marks = (
            _mark(f"jump-{letter}-out", letter, _beyond(start, out_side, out + size / 2), size),
            _mark(f"jump-{letter}-in", letter, _beyond(end, in_side, into + size / 2), size),
        )
        blocks.extend(_rect_of(mark) for mark in marks)
        kept.append((plan, (start, _beyond(start, out_side, out))))
        jumps.append(Jump(plan, (_beyond(end, in_side, into), end), marks))
    return kept, jumps


def _best_end(
    planned: tuple[Point, PortSide],
    node: Node,
    sizes: tuple[float, float],
    around: tuple[list[tuple[Point, ...]], list[Box]],
) -> tuple[Point, PortSide, float]:
    """Choose the side of a frame a jump's circle sits by: the planned one, else the clearest.

    Returns:
        The point on the side, the side, and how far out the circle goes.
    """
    options = [planned] + [(_middle(node, side), side) for side in STEPS if side is not planned[1]]
    best: tuple[int, Point, PortSide, float] | None = None
    for port, side in options:
        hits, distance = _clear_distance(port, side, sizes, around)
        if best is None or hits < best[0]:
            best = (hits, port, side, distance)
        if hits == 0:
            break
    assert best is not None
    return best[1], best[2], best[3]


def _middle(node: Node, side: PortSide) -> Point:
    """Return the middle of a side of a node: for a decision, its tip."""
    centre_x, centre_y = node.x + node.width / 2, node.y + node.height / 2
    step_x, step_y = STEPS[side]
    return centre_x + step_x * node.width / 2, centre_y + step_y * node.height / 2


def _has_words(transition: Transition) -> bool:
    """Tell whether an arrow says anything, so its first part needs room for the words."""
    return bool(transition.trigger or transition.guard or transition.effect or transition.code)


def _clear_distance(
    port: Point,
    side: PortSide,
    sizes: tuple[float, float],
    around: tuple[list[tuple[Point, ...]], list[Box]],
) -> tuple[int, float]:
    """Return how far out of a side the circle goes, the nearest that touches least, and hits."""
    shortest, size = sizes
    lines, blocks = around
    best: tuple[int, float] | None = None
    for step in range(TRIES):
        distance = shortest + step * TRY_STEP_PX
        centre = _beyond(port, side, distance + size / 2)
        box = (
            centre[0] - size / 2,
            centre[1] - size / 2,
            centre[0] + size / 2,
            centre[1] + size / 2,
        )
        stub = (port, _beyond(port, side, distance))
        hits = sum(_box_meets(box, points) for points in lines)
        hits += sum(_overlaps(box, block) for block in blocks)
        hits += sum(
            _overlaps(_segment_box(stub), block) for block in blocks if not _holds(block, port)
        )
        if hits == 0:
            return 0, distance
        if best is None or hits < best[0]:
            best = (hits, distance)
    assert best is not None
    return best


def _beyond(port: Point, side: PortSide, distance: float) -> Point:
    """Return the point a distance straight out of a side."""
    step_x, step_y = STEPS[side]
    return port[0] + step_x * distance, port[1] + step_y * distance


def _mark(name: str, letter: str, centre: Point, size: float) -> Node:
    """Build a lettered circle centred on a point."""
    return Node(
        id=name,
        shape=Shape.CONNECTOR,
        x=centre[0] - size / 2,
        y=centre[1] - size / 2,
        width=size,
        height=size,
        text=(letter,),
        icon=None,
        tone=Tone.GRAY,
        number=None,
        font_size=DEFAULT_FONT_SIZE_PX,
    )


def _rect_of(node: Node) -> Box:
    """Return the box a node covers."""
    return (node.x, node.y, node.x + node.width, node.y + node.height)


def _segment_box(segment: tuple[Point, Point]) -> Box:
    """Return the box of a horizontal or vertical segment."""
    (start_x, start_y), (end_x, end_y) = segment
    return (min(start_x, end_x), min(start_y, end_y), max(start_x, end_x), max(start_y, end_y))


def _overlaps(first: Box, second: Box) -> bool:
    """Tell whether two boxes share area."""
    return (
        first[0] < second[2]
        and first[2] > second[0]
        and first[1] < second[3]
        and first[3] > second[1]
    )


def _holds(block: Box, point: Point) -> bool:
    """Tell whether a point lies on or in a box: the frame a stub leaves."""
    return block[0] - 1 <= point[0] <= block[2] + 1 and block[1] - 1 <= point[1] <= block[3] + 1


def _box_meets(box: Box, points: tuple[Point, ...]) -> bool:
    """Tell whether a route passes through a box widened by the clearance."""
    wide = (box[0] - CLEAR_PX, box[1] - CLEAR_PX, box[2] + CLEAR_PX, box[3] + CLEAR_PX)
    return any(_overlaps(wide, _segment_box(pair)) for pair in pairwise(points))
