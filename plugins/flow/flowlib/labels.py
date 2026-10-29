"""Move the label chips of a finished scene off boxes and captions, keeping them on their lines.

A line may carry a main chip and extra chips (the guard and the effect of a screen flow arrow).
They move together: the group keeps its shape and slides along the line. A chip also keeps off
the other lines when it can: on another line a reader cannot tell which line it names.
"""

from collections.abc import Iterator
from dataclasses import replace
from itertools import pairwise

from .check import Rect, caption_rect, chip_rect, frame_rect, line_rects, node_rect
from .model import Edge, EdgeLabel, Frame, Node, Point, Scene
from .screen_parts import chip_box, is_card
from .theme import LayoutRules, load_theme

ALONG_FRACTIONS = (0.5, 0.3, 0.7, 0.15, 0.85)  # where on a segment a chip is tried
SAME_LINE_TOLERANCE_PX = 1.0  # a segment shorter across than this counts as straight
BORDER_STRIP_PX = 3.0  # a chip this close to a frame border or divider counts as on it
NUDGE_STEP_PX = 10.0  # how far a chip slides along its own segment at each try


def place_labels(scene: Scene) -> Scene:
    """Move every label group that covers a node, a caption or another chip to a clear spot.

    A group (the main chip and its extra chips) that is already clear stays where it is. One
    that is not is first slid along its own stretch of the line in small steps, then tried at
    several places along the line, beside the line when the line is vertical.

    Args:
        scene: A scene with routed lines.

    Returns:
        A new scene; the lines are not changed.
    """
    rules = load_theme().layout
    fixed = _fixed_rects(scene.nodes, rules) + _border_rects(scene.frames)
    lines = {edge.id: line_rects(edge) for edge in scene.edges}
    taken: list[Rect] = []
    edges = []
    for edge in scene.edges:
        others = [rect for line_id, rects in lines.items() if line_id != edge.id for rect in rects]
        placed = clear_edge(edge, fixed + taken + others, rules)
        if not _is_clear(_group(placed), fixed + taken, rules):
            placed = clear_edge(edge, fixed + taken, rules)
        taken.extend(_group_rects(placed, rules))
        edges.append(placed)
    return replace(scene, edges=tuple(edges))


def clear_edge(edge: Edge, avoid: list[Rect], rules: LayoutRules) -> Edge:
    """Return the edge with its chips at their own place when clear, else moved along the line.

    Args:
        edge: A routed line with an optional main chip and extra chips.
        avoid: The rectangles the chips must not cover.
        rules: The layout rules, which size the chips.

    Returns:
        The same edge when its chips are clear or no clear place exists, else a copy whose
        chips all moved by the same distance.
    """
    group = _group(edge)
    if not group or _is_clear(group, avoid, rules):
        return edge
    for shift in _shifts(edge, group[0], rules):
        moved = [
            replace(label, at=(label.at[0] + shift[0], label.at[1] + shift[1])) for label in group
        ]
        if _is_clear(moved, avoid, rules):
            return replace(edge, label=moved[0], extras=tuple(moved[1:]))
    return edge


def _fixed_rects(nodes: tuple[Node, ...], rules: LayoutRules) -> list[Rect]:
    """Return the rectangle of every node, every caption and every id chip of a screen."""
    rects = [node_rect(node) for node in nodes]
    rects.extend(rect for node in nodes if (rect := caption_rect(node, rules)) is not None)
    rects.extend(_id_chip_rects(nodes))
    return rects


def _id_chip_rects(nodes: tuple[Node, ...]) -> list[Rect]:
    """Return the rectangle of the id chip of every screen drawn as a device frame."""
    theme = load_theme()
    rects = []
    for node in nodes:
        if node.screen is None or is_card(node.screen):
            continue
        left, top, width, height = chip_box(node, node.screen, theme)
        rects.append(
            Rect(node.x + left, node.y + top, node.x + left + width, node.y + top + height)
        )
    return rects


def _border_rects(frames: tuple[Frame, ...]) -> list[Rect]:
    """Return a thin strip along each border and divider of every frame, which a chip avoids."""
    strips = []
    half = BORDER_STRIP_PX
    for frame in frames:
        box = frame_rect(frame)
        strips.extend(
            [
                Rect(box.left - half, box.top - half, box.right + half, box.top + half),
                Rect(box.left - half, box.bottom - half, box.right + half, box.bottom + half),
                Rect(box.left - half, box.top, box.left + half, box.bottom),
                Rect(box.right - half, box.top, box.right + half, box.bottom),
            ]
        )
        strips.extend(
            Rect(box.left, divider.y - half, box.right, divider.y + half)
            for divider in frame.dividers
        )
    return strips


def _group(edge: Edge) -> list[EdgeLabel]:
    """Return the chips of a line: the main one first, then the extras."""
    if edge.label is None:
        return []
    return [edge.label, *edge.extras]


def _group_rects(edge: Edge, rules: LayoutRules) -> list[Rect]:
    """Return the rectangle of every chip of a line."""
    return [chip_rect(label, rules) for label in _group(edge)]


def _is_clear(group: list[EdgeLabel], avoid: list[Rect], rules: LayoutRules) -> bool:
    """Tell whether no chip of the group covers any of the rectangles."""
    return not any(chip_rect(label, rules).overlaps(rect) for label in group for rect in avoid)


def _shifts(edge: Edge, label: EdgeLabel, rules: LayoutRules) -> Iterator[Point]:
    """Yield how far to move the main chip, nearest first: a slide, then other places."""
    anchor, segment = _anchor(edge.points, label.at)
    yield from _slides(segment, anchor)
    is_beside = _distance(label.at, anchor) > SAME_LINE_TOLERANCE_PX
    for place in _candidates(edge, rules, segment if is_beside else None):
        yield place[0] - anchor[0], place[1] - anchor[1]


def _anchor(points: tuple[Point, ...], at: Point) -> tuple[Point, tuple[Point, Point]]:
    """Return the point of the line nearest to a position, and the segment it lies on."""
    best = min(pairwise(points), key=lambda segment: _distance(at, _nearest(segment, at)))
    return _nearest(best, at), best


def _nearest(segment: tuple[Point, Point], at: Point) -> Point:
    """Return the point of a segment nearest to a position."""
    (start_x, start_y), (end_x, end_y) = segment
    run_x, run_y = end_x - start_x, end_y - start_y
    square = run_x * run_x + run_y * run_y
    if square == 0:
        return segment[0]
    ratio = ((at[0] - start_x) * run_x + (at[1] - start_y) * run_y) / square
    ratio = max(0.0, min(1.0, ratio))
    return start_x + run_x * ratio, start_y + run_y * ratio


def _distance(first: Point, second: Point) -> float:
    """Return the distance between two points along the axes (the lines are right-angled)."""
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _slides(segment: tuple[Point, Point], anchor: Point) -> Iterator[Point]:
    """Yield small moves along a segment, the nearest first, both ways, inside the segment."""
    length = _length(segment)
    if length == 0:
        return
    (start_x, start_y), (end_x, end_y) = segment
    unit = (end_x - start_x) / length, (end_y - start_y) / length
    here = _distance(segment[0], anchor)
    steps = int(length // NUDGE_STEP_PX)
    for count in range(1, steps + 1):
        for direction in (1, -1):
            offset = direction * count * NUDGE_STEP_PX
            if 0 <= here + offset <= length:
                yield unit[0] * offset, unit[1] * offset


def _candidates(edge: Edge, rules: LayoutRules, like: tuple[Point, Point] | None) -> list[Point]:
    """Return places on a line for a chip: longest segments first, beside vertical ones.

    Args:
        edge: The line.
        rules: The layout rules.
        like: When given, the segment a chip already sits beside; only segments running the
            same way are used and the places are on the line, because the chip keeps its offset.
    """
    found: list[Point] = []
    for start, end in sorted(pairwise(edge.points), key=_length, reverse=True):
        is_vertical = abs(start[0] - end[0]) < SAME_LINE_TOLERANCE_PX
        if like is not None and is_vertical != (
            abs(like[0][0] - like[1][0]) < SAME_LINE_TOLERANCE_PX
        ):
            continue
        for fraction in ALONG_FRACTIONS:
            at_x = start[0] + (end[0] - start[0]) * fraction
            at_y = start[1] + (end[1] - start[1]) * fraction
            if is_vertical and like is None:
                found.extend([(at_x + rules.label_offset, at_y), (at_x - rules.label_offset, at_y)])
            else:
                found.append((at_x, at_y))
    return found


def _length(segment: tuple[Point, Point]) -> float:
    """Return the length of a horizontal or vertical segment."""
    (start_x, start_y), (end_x, end_y) = segment
    return abs(end_x - start_x) + abs(end_y - start_y)
