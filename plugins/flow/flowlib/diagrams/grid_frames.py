"""Shared geometry of the diagrams that draw frames around parts: growing, moving and pills."""

from dataclasses import replace

from ..check import Rect
from ..html_zones import pill_width
from ..model import Frame, Node, Shape
from ..theme import Theme

PILL_CLEARANCE_PX = 6  # no line comes this close to the pill of a frame


def grown(rect: Rect, by: float) -> Rect:
    """Return a rectangle grown by the same amount on every side."""
    return Rect(rect.left - by, rect.top - by, rect.right + by, rect.bottom + by)


def union(rects: list[Rect]) -> Rect:
    """Return the smallest rectangle that holds every rectangle of a list."""
    return Rect(
        min(rect.left for rect in rects),
        min(rect.top for rect in rects),
        max(rect.right for rect in rects),
        max(rect.bottom for rect in rects),
    )


def shift_into_canvas(
    nodes: dict[str, Node], frames: list[Frame], theme: Theme
) -> tuple[dict[str, Node], list[Frame]]:
    """Move everything so that the leftmost box or frame is one margin from the canvas edge.

    Args:
        nodes: The boxes by id.
        frames: The frames.
        theme: The design tokens.

    Returns:
        The moved boxes and frames; the top leaves room for the title and for a pill that
        sticks out over the top edge of a frame.
    """
    layout_rules = theme.layout
    pill_over = theme.cloud.pill_height / 2
    left = min([node.x for node in nodes.values()] + [frame.x for frame in frames])
    top = min([node.y for node in nodes.values()] + [frame.y - pill_over for frame in frames])
    shift_x = layout_rules.margin - left
    shift_y = layout_rules.title_block_height + layout_rules.margin - top
    moved_nodes = {key: replace(n, x=n.x + shift_x, y=n.y + shift_y) for key, n in nodes.items()}
    moved_frames = [replace(f, x=f.x + shift_x, y=f.y + shift_y) for f in frames]
    return moved_nodes, moved_frames


def pill_rect(frame: Frame, theme: Theme) -> Rect:
    """Return the area of the pill of a frame, which no line may cross."""
    rules = theme.cloud
    left = frame.x + rules.pill_inset - PILL_CLEARANCE_PX
    top = frame.y - rules.pill_height / 2 - PILL_CLEARANCE_PX
    width = pill_width(frame.label or "", theme) + 2 * PILL_CLEARANCE_PX
    return Rect(left, top, left + width, top + rules.pill_height + 2 * PILL_CLEARANCE_PX)


def frame_node(frame: Frame) -> Node:
    """Return a frame as a node of its size, so that a line can start or end on its edge."""
    return Node(
        id=frame.id,
        shape=Shape.PROCESS,
        x=frame.x,
        y=frame.y,
        width=frame.width,
        height=frame.height,
        text=(),
        icon=None,
        tone=None,
        number=None,
        font_size=0,
    )
