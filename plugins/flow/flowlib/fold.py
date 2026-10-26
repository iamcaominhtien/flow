"""Fold a layout that is too long along the flow into bands that sit side by side.

A long chain of steps would make a page many thousand pixels long. The layout is cut between
rows into bands of at most ``fold_extent`` pixels; the bands are put side by side in layout
space, so that a flow that runs left to right ends up as rows stacked on the page, like the
lines of a text. A line inside a band is only moved; a line that crosses a cut is routed again.
"""

from dataclasses import dataclass, replace
from itertools import pairwise

from .model import Edge, EdgeLabel, Frame, Node, Point
from .routing import Port, route_across
from .theme import LayoutRules

MIN_BAND_SHARE = 0.6  # a cut is looked for between this share of the extent and the whole


@dataclass(frozen=True)
class Folded:
    """Nodes, frames and lines: what a fold takes and what it leaves."""

    nodes: tuple[Node, ...]
    frames: tuple[Frame, ...]
    edges: tuple[Edge, ...]


@dataclass(frozen=True)
class _Band:
    """One band: the rows it takes, and where it goes.

    Lanes that hold no node in the band are dropped, and the lanes that remain are moved
    together, so ``removed`` lists the empty spans along x that have to be closed.
    """

    top: float
    bottom: float
    shift_y: float
    left: float
    offset_x: float
    removed: tuple[tuple[float, float], ...]

    def column(self, x: float) -> float:
        """Return where an x of the original layout lands in this band."""
        closed = sum(min(width, max(0.0, x - start)) for start, width in self.removed)
        return x - closed - self.left + self.offset_x

    def place(self, point: Point) -> Point:
        """Return where a point of the original layout lands in this band."""
        return self.column(point[0]), point[1] + self.shift_y


def fold(layout: Folded, rules: LayoutRules, caption_port: Port) -> Folded:
    """Fold a layout into bands when it is longer than the rules allow.

    Args:
        layout: The placed nodes, the lane and zone frames and the routed lines, in layout space
            (the flow runs down).
        rules: The layout rules.
        caption_port: The side captions hang from, which tells whether the layout is mirrored.

    Returns:
        The same things, folded; unchanged when nothing is too long.
    """
    nodes, frames, edges = layout.nodes, layout.frames, layout.edges
    cuts = _choose_cuts(nodes, edges, rules.fold_extent)
    if not cuts:
        return layout
    bands = _bands(nodes, frames, cuts, rules)
    moved_nodes = tuple(_move_node(node, _band_of(node.y, bands)) for node in nodes)
    by_id = {node.id: node for node in moved_nodes}
    original = {node.id: node for node in nodes}
    kept: list[Edge] = []
    crossing: list[Edge] = []
    for edge in edges:
        first, second = original[edge.source or ""], original[edge.target or ""]
        same = _band_of(first.y, bands) is _band_of(second.y, bands)
        (kept if same else crossing).append(edge)
    drawn = [_move_edge(edge, _band_of(original[edge.source or ""].y, bands)) for edge in kept]
    lines = [segment for edge in drawn for segment in pairwise(edge.points)]
    rerouted = []
    for edge in crossing:
        ends = (edge.source or "", edge.target or "")
        points = route_across(by_id, ends, lines, caption_port)
        lines.extend(pairwise(points))
        rerouted.append(_with_points(edge, points))
    ordered = {edge.id: edge for edge in [*drawn, *rerouted]}
    folded_frames = _fold_frames(frames, nodes, bands)
    return Folded(moved_nodes, folded_frames, tuple(ordered[edge.id] for edge in edges))


def _row_tops(nodes: tuple[Node, ...]) -> list[float]:
    """Return the distinct y of the top of every row of nodes, in order."""
    return sorted({node.y for node in nodes})


def _choose_cuts(nodes: tuple[Node, ...], edges: tuple[Edge, ...], extent: float) -> list[float]:
    """Choose the y at which to cut, between rows, or an empty list when no fold is needed."""
    rows = _row_tops(nodes)
    bottom = max(node.y + node.height for node in nodes)
    if bottom - rows[0] <= extent * (1 + MIN_BAND_SHARE / 2):
        return []
    cuts: list[float] = []
    start = rows[0]
    while bottom - start > extent * (1 + MIN_BAND_SHARE / 2):
        window = [row for row in rows if extent * MIN_BAND_SHARE <= row - start <= extent]
        if not window:
            break
        cut = min(window, key=lambda row: _crossings(row, nodes, edges))
        cuts.append(cut)
        start = cut
    return cuts


def _crossings(cut: float, nodes: tuple[Node, ...], edges: tuple[Edge, ...]) -> int:
    """Count the lines whose two ends lie on different sides of a cut just above ``cut``."""
    top = {node.id: node.y for node in nodes}
    return sum(
        1
        for edge in edges
        if edge.source in top
        and edge.target in top
        and (top[edge.source] < cut) != (top[edge.target] < cut)
    )


def _bands(
    nodes: tuple[Node, ...], frames: tuple[Frame, ...], cuts: list[float], rules: LayoutRules
) -> list[_Band]:
    """Build the bands: the rows from one cut to the next, each with a place beside the last."""
    lefts = [node.x for node in nodes] + [frame.x for frame in frames]
    rights = [node.x + node.width for node in nodes] + [frame.x + frame.width for frame in frames]
    tops = [node.y for node in nodes] + [frame.y for frame in frames]
    bottoms = [node.y + node.height for node in nodes] + [
        frame.y + frame.height for frame in frames
    ]
    top, bottom, left, right = min(tops), max(bottoms), min(lefts), max(rights)
    starts = [top]
    for cut in cuts:
        above = max(node.y + node.height for node in nodes if node.y < cut)
        starts.append((above + cut) / 2)
    ends = [*starts[1:], bottom]
    bands: list[_Band] = []
    offset = left
    for start, end in zip(starts, ends, strict=True):
        members = [node for node in nodes if start <= node.y < end]
        removed = _empty_spans(frames, members, (start, end))
        bands.append(_Band(start, end, top - start, left, offset, removed))
        offset += right - left - sum(width for _, width in removed) + rules.band_gap
    return bands


def _empty_spans(
    frames: tuple[Frame, ...], members: list[Node], window: tuple[float, float]
) -> tuple[tuple[float, float], ...]:
    """Return the x spans of the frames that hold none of the given nodes inside a y window."""
    spans = set()
    for frame in frames:
        if frame.y >= window[1] or frame.y + frame.height <= window[0]:
            continue
        if not any(_inside(node, frame) for node in members):
            spans.add((frame.x, frame.width))
    return tuple(sorted(spans))


def _inside(node: Node, frame: Frame) -> bool:
    """Tell whether the centre of a node lies in the x range of a frame."""
    center = node.x + node.width / 2
    return frame.x <= center <= frame.x + frame.width


def _band_of(y: float, bands: list[_Band]) -> _Band:
    """Return the band that holds a node whose top is at ``y``."""
    for band in bands:
        if band.top <= y < band.bottom:
            return band
    return bands[-1]


def _shifted(value: Point, shift: Point) -> Point:
    """Move a point by a shift."""
    return value[0] + shift[0], value[1] + shift[1]


def _move_node(node: Node, band: _Band) -> Node:
    """Move a node into its band."""
    x, y = band.place((node.x, node.y))
    return replace(node, x=x, y=y)


def _move_label(label: EdgeLabel | None, band: _Band) -> EdgeLabel | None:
    """Move a label chip into a band."""
    return None if label is None else replace(label, at=band.place(label.at))


def _move_edge(edge: Edge, band: _Band) -> Edge:
    """Move a line, its label and its end labels into a band."""
    return replace(
        edge,
        points=tuple(band.place(point) for point in edge.points),
        label=_move_label(edge.label, band),
        extras=tuple(label for each in edge.extras if (label := _move_label(each, band))),
    )


def _with_points(edge: Edge, points: list[Point]) -> Edge:
    """Give a line new points; its label goes to the middle of the longest segment.

    End labels (such as multiplicities) keep their offset from the end of the line they were at.
    """
    start, end = max(pairwise(points), key=_length)
    middle = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    label = None if edge.label is None else replace(edge.label, at=middle)
    old_first, old_last = edge.points[0], edge.points[-1]
    extras = []
    for each in edge.extras:
        near_first = _length((each.at, old_first)) <= _length((each.at, old_last))
        old, new = (old_first, points[0]) if near_first else (old_last, points[-1])
        offset = (each.at[0] - old[0], each.at[1] - old[1])
        extras.append(replace(each, at=_shifted(new, offset)))
    return replace(edge, points=tuple(points), label=label, extras=tuple(extras))


def _length(segment: tuple[Point, Point]) -> float:
    """Return the length of a horizontal or vertical segment."""
    (start_x, start_y), (end_x, end_y) = segment
    return abs(end_x - start_x) + abs(end_y - start_y)


def _fold_frames(
    frames: tuple[Frame, ...], nodes: tuple[Node, ...], bands: list[_Band]
) -> tuple[Frame, ...]:
    """Cut every frame at the bands: one piece per band in which the frame holds a node."""
    pieces = []
    for frame in frames:
        for index, band in enumerate(bands):
            low, high = max(frame.y, band.top), min(frame.y + frame.height, band.bottom)
            members = [node for node in nodes if band.top <= node.y < band.bottom]
            if high <= low or not any(_inside(node, frame) for node in members):
                continue
            x, y = band.place((frame.x, low))
            width = band.column(frame.x + frame.width) - x
            name = frame.id if index == 0 else f"{frame.id}-{index + 1}"
            pieces.append(replace(frame, id=name, x=x, y=y, width=width, height=high - low))
    return tuple(pieces)
