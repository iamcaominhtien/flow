"""Choose the box of every item of a mind map: the topic in the middle, branches on both sides.

A branch with what hangs on it is a block of rows. Inside a branch the rows of one level are
stacked, and a parent sits half way between its first and its last child. On a map of two
levels the branches sit on fixed slots (300 px apart in the illustrated style); on a larger
map the blocks are stacked so that no leaf overlaps another.
"""

from dataclasses import dataclass, field

from ..model import MindLevel, Side
from ..theme import MindScale
from .mindmap_spec import Idea, MindSpec

Size = tuple[float, float]
BRANCH_DEPTH = 1
SECOND_DEPTH = 2  # a leaf, or a group on a larger map
IDEA_DEPTH = 3


@dataclass(frozen=True)
class Box:
    """Where an item is, in pixels."""

    x: float
    y: float
    width: float
    height: float

    @property
    def centre_y(self) -> float:
        """Return the y of the middle of the box."""
        return self.y + self.height / 2


@dataclass
class _Context:
    """What the placing of one side needs: the sizes, the children and the extents so far."""

    scale: MindScale
    spec: MindSpec
    children: dict[str, list[Idea]]
    extents: dict[str, float] = field(default_factory=dict)
    centres: dict[str, float] = field(default_factory=dict)


def level_of(idea: Idea, spec: MindSpec) -> MindLevel:
    """Return what an item is drawn as, from its depth and the depth of the map.

    Args:
        idea: Any item.
        spec: The checked spec.

    Returns:
        The topic, a branch, then a leaf (a map of two levels) or a group, an idea and a detail.
    """
    if idea.depth == 0:
        return MindLevel.CENTRE
    if idea.depth == BRANCH_DEPTH:
        return MindLevel.BRANCH
    if idea.depth == SECOND_DEPTH:
        return MindLevel.LEAF if spec.depth == SECOND_DEPTH else MindLevel.GROUP
    return MindLevel.IDEA if idea.depth == IDEA_DEPTH else MindLevel.DETAIL


def size_of(level: MindLevel, scale: MindScale) -> Size:
    """Return the width and the height of an item of a level."""
    sizes = {
        MindLevel.CENTRE: scale.centre,
        MindLevel.BRANCH: scale.branch,
        MindLevel.GROUP: scale.group,
        MindLevel.LEAF: scale.idea,
        MindLevel.IDEA: scale.idea,
        MindLevel.DETAIL: scale.detail,
    }
    return sizes[level]


def place_ideas(spec: MindSpec, scale: MindScale, origin: tuple[float, float]) -> dict[str, Box]:
    """Return the box of every item.

    Args:
        spec: The checked spec.
        scale: The sizes of the style and size of map.
        origin: The left edge and the top edge of the map, in pixels.

    Returns:
        Item id to box. The topic is in the middle and the branches are on its two sides.
    """
    children: dict[str, list[Idea]] = {}
    for idea in spec.ideas:
        if idea.parent is not None:
            children.setdefault(idea.parent, []).append(idea)
    context = _Context(scale, spec, children)
    sides = {
        side: [idea for idea in children.get(spec.ideas[0].id, []) if idea.side is side]
        for side in (Side.RIGHT, Side.LEFT)
    }
    most = max(len(branches) for branches in sides.values())
    relative = {}
    for branches in sides.values():
        relative.update(_place_side(branches, most, context))
    return _with_columns(spec, scale, relative, origin)


def _place_side(branches: list[Idea], most: int, context: _Context) -> dict[str, float]:
    """Return the centre y of every item on one side, relative to the middle of the map.

    A side with fewer branches than the other spreads them over the same height.
    """
    if not branches:
        return {}
    for branch in branches:
        _measure(branch, context)
    scale = context.scale
    if scale.branch_pitch > 0:
        pitch = max(
            scale.branch_pitch, *(context.extents[b.id] + scale.subtree_gap for b in branches)
        )
        span = (most - 1) * pitch
        for index, branch in enumerate(branches):
            middle = index * span / (len(branches) - 1) - span / 2 if len(branches) > 1 else 0.0
            _centre(branch, middle - context.extents[branch.id] / 2, context)
    else:
        total = sum(context.extents[b.id] for b in branches) + scale.subtree_gap * (
            len(branches) - 1
        )
        top = -total / 2
        for branch in branches:
            _centre(branch, top, context)
            top += context.extents[branch.id] + scale.subtree_gap
    return dict(context.centres)


def _own_height(idea: Idea, context: _Context) -> float:
    """Return the height of the box of one item."""
    return size_of(level_of(idea, context.spec), context.scale)[1]


def _gap(first: Idea, second: Idea, context: _Context) -> float:
    """Return the space between two siblings: a row gap for leaves, more for blocks."""
    if context.children.get(first.id) or context.children.get(second.id):
        return context.scale.subtree_gap
    return context.scale.row_gap


def _measure(idea: Idea, context: _Context) -> float:
    """Work out how tall an item and everything hanging on it is, and remember it."""
    below = context.children.get(idea.id, [])
    block = 0.0
    for index, child in enumerate(below):
        block += _measure(child, context)
        if index:
            block += _gap(below[index - 1], child, context)
    context.extents[idea.id] = max(_own_height(idea, context), block)
    return context.extents[idea.id]


def _centre(idea: Idea, top: float, context: _Context) -> float:
    """Place an item in the space that starts at ``top``; return the y of its centre."""
    below = context.children.get(idea.id, [])
    extent = context.extents[idea.id]
    if not below:
        context.centres[idea.id] = top + extent / 2
        return context.centres[idea.id]
    block = sum(context.extents[child.id] for child in below)
    block += sum(_gap(below[i - 1], below[i], context) for i in range(1, len(below)))
    running = top + (extent - block) / 2
    centres = []
    for index, child in enumerate(below):
        if index:
            running += _gap(below[index - 1], child, context)
        centres.append(_centre(child, running, context))
        running += context.extents[child.id]
    context.centres[idea.id] = (centres[0] + centres[-1]) / 2
    return context.centres[idea.id]


def _with_columns(
    spec: MindSpec, scale: MindScale, centres: dict[str, float], origin: tuple[float, float]
) -> dict[str, Box]:
    """Turn the centre y of every item into a box: add the column it is in, and shift the map."""
    reach = _reach(spec, scale)
    middle_x = origin[0] + reach
    top = min(
        [
            centre - size_of(level_of(idea, spec), scale)[1] / 2
            for idea in spec.ideas[1:]
            for centre in [centres[idea.id]]
        ]
        + [-scale.centre[1] / 2]
    )
    shift = origin[1] - top
    centre_box = Box(middle_x - scale.centre[0] / 2, shift - scale.centre[1] / 2, *scale.centre)
    boxes = {spec.ideas[0].id: centre_box}
    for idea in spec.ideas[1:]:
        width, height = size_of(level_of(idea, spec), scale)
        x = _column_x(idea, spec, scale, middle_x)
        boxes[idea.id] = Box(x, centres[idea.id] + shift - height / 2, width, height)
    return boxes


def _level_widths(spec: MindSpec, scale: MindScale) -> list[float]:
    """Return the width of each column from the branches outwards."""
    return [size_of(level_of(idea, spec), scale)[0] for idea in _first_of_each_depth(spec)]


def _first_of_each_depth(spec: MindSpec) -> list[Idea]:
    """Return one item of each depth from 1 down, to read the width of its column."""
    found: dict[int, Idea] = {}
    for idea in spec.ideas[1:]:
        found.setdefault(idea.depth, idea)
    return [found[depth] for depth in sorted(found)]


def _reach(spec: MindSpec, scale: MindScale) -> float:
    """Return how far from the middle of the topic the outermost column reaches."""
    widths = _level_widths(spec, scale)
    return (
        scale.centre[0] / 2 + scale.centre_gap + sum(widths) + scale.column_gap * (len(widths) - 1)
    )


def _column_x(idea: Idea, spec: MindSpec, scale: MindScale, middle_x: float) -> float:
    """Return the left edge of the column an item is in, on its side of the topic."""
    widths = _level_widths(spec, scale)
    inner = scale.centre[0] / 2 + scale.centre_gap
    before = sum(widths[: idea.depth - 1]) + scale.column_gap * (idea.depth - 1)
    width = widths[idea.depth - 1]
    if idea.side is Side.LEFT:
        return middle_x - inner - before - width
    return middle_x + inner + before
