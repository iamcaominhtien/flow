"""Move the label chips of a finished scene off boxes and captions, keeping them on their lines."""

from dataclasses import replace
from itertools import pairwise

from .check import Rect, caption_rect, label_rect, node_rect
from .model import Edge, EdgeLabel, Node, Point, Scene
from .theme import LayoutRules, load_theme

ALONG_FRACTIONS = (0.5, 0.3, 0.7, 0.15, 0.85)  # where on a segment a chip is tried
SAME_LINE_TOLERANCE_PX = 1.0  # a segment shorter across than this counts as straight


def place_labels(scene: Scene) -> Scene:
    """Move every label chip that covers a node, a caption or another chip to a clear spot.

    A chip that is already clear stays where it is. A chip that is not is tried at several
    places along its line, beside the line when the line is vertical.

    Args:
        scene: A scene with routed lines.

    Returns:
        A new scene; the lines are not changed.
    """
    rules = load_theme().layout
    fixed = _fixed_rects(scene.nodes, rules)
    taken: list[Rect] = []
    edges = []
    for edge in scene.edges:
        label = edge.label
        if label is not None:
            label = _clear_label(edge, label, fixed + taken, rules)
            taken.append(_chip_rect(edge, label, rules))
        edges.append(replace(edge, label=label))
    return replace(scene, edges=tuple(edges))


def _fixed_rects(nodes: tuple[Node, ...], rules: LayoutRules) -> list[Rect]:
    """Return the rectangle of every node and every caption."""
    rects = [node_rect(node) for node in nodes]
    rects.extend(rect for node in nodes if (rect := caption_rect(node, rules)) is not None)
    return rects


def _chip_rect(edge: Edge, label: EdgeLabel, rules: LayoutRules) -> Rect:
    """Return the rectangle a label chip covers when it is on this edge."""
    rect = label_rect(replace(edge, label=label), rules)
    assert rect is not None
    return rect


def _candidates(edge: Edge, rules: LayoutRules) -> list[Point]:
    """Return places for a chip along a line: longest segments first, beside vertical ones."""
    found: list[Point] = []
    for start, end in sorted(pairwise(edge.points), key=_length, reverse=True):
        is_vertical = abs(start[0] - end[0]) < SAME_LINE_TOLERANCE_PX
        for fraction in ALONG_FRACTIONS:
            at_x = start[0] + (end[0] - start[0]) * fraction
            at_y = start[1] + (end[1] - start[1]) * fraction
            if is_vertical:
                found.extend([(at_x + rules.label_offset, at_y), (at_x - rules.label_offset, at_y)])
            else:
                found.append((at_x, at_y))
    return found


def _length(segment: tuple[Point, Point]) -> float:
    """Return the length of a horizontal or vertical segment."""
    (start_x, start_y), (end_x, end_y) = segment
    return abs(end_x - start_x) + abs(end_y - start_y)


def _clear_label(edge: Edge, label: EdgeLabel, avoid: list[Rect], rules: LayoutRules) -> EdgeLabel:
    """Return the label at its own place when that is clear, else at the first clear place."""
    if not any(_chip_rect(edge, label, rules).overlaps(rect) for rect in avoid):
        return label
    for at in _candidates(edge, rules):
        moved = replace(label, at=at)
        if not any(_chip_rect(edge, moved, rules).overlaps(rect) for rect in avoid):
            return moved
    return label
