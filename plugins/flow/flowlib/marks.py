"""The small BPMN marks inside events, tasks and gateways, and where each one sits.

Every mark is drawn in a 24 by 24 box. The HTML renderer inlines the SVG; the draw.io renderer
turns the same SVG into an image cell, so both outputs show the same drawing.
"""

from dataclasses import dataclass

from .markup import fmt
from .model import Marker, Node, Shape

MARK_GRID = 24  # the side of the box every mark is drawn in
MARK_STROKE_WIDTH = 2
BOLD_STROKE_WIDTH = 3
EVENT_SHAPES = (Shape.START, Shape.END, Shape.INTERMEDIATE)
TASK_SHAPES = (Shape.TASK,)
EVENT_MARK_FRACTION = 0.6  # the mark is this fraction of the event's diameter
GATEWAY_MARK_FRACTION = 0.5
TOP_LEFT_MARKERS = (
    Marker.USER,
    Marker.SERVICE,
    Marker.MANUAL,
    Marker.MESSAGE,
    Marker.MESSAGE_FILLED,
)  # the marks that name the kind of a task, drawn in its top-left corner
BOTTOM_MARKERS = (Marker.LOOP, Marker.MULTI_INSTANCE, Marker.SUBPROCESS)

ENVELOPE = '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 8l9 6 9-6"/>'
RING_PENTAGON = (
    '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="8"/>'
    '<path d="M12 7.5l4 3-1.5 4.8h-5L8 10.5z"/>'
)
SHAPES: dict[Marker, str] = {
    Marker.MESSAGE: ENVELOPE,
    Marker.MESSAGE_FILLED: ENVELOPE,
    Marker.TIMER: (
        '<circle cx="12" cy="12" r="9"/><path d="M12 6.5V12l3.5 2.5"/>'
        '<path d="M12 3v2M12 19v2M3 12h2M19 12h2"/>'
    ),
    Marker.ERROR: '<path d="M14 2L6 13.5h5L9.5 22 18 10h-5z"/>',
    Marker.SIGNAL: '<path d="M12 4L21 19H3z"/>',
    Marker.USER: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>',
    Marker.SERVICE: (
        '<circle cx="12" cy="12" r="3.5"/>'
        '<path d="M12 2v4M12 18v4M2 12h4M18 12h4M5 5l3 3M16 16l3 3M19 5l-3 3M8 16l-3 3"/>'
    ),
    Marker.MANUAL: (
        '<path d="M7 13V6.5a1.5 1.5 0 0 1 3 0V12M10 12V4.5a1.5 1.5 0 0 1 3 0V12'
        "M13 12V5.5a1.5 1.5 0 0 1 3 0V13M16 13V8.5a1.5 1.5 0 0 1 3 0V15c0 4.5-3 6.5-6.5 6.5"
        'S7 19 6 16l-2-3.5a1.5 1.5 0 0 1 3-1.5"/>'
    ),
    Marker.CROSS: '<path d="M6 6l12 12M18 6L6 18"/>',
    Marker.PLUS: '<path d="M12 4v16M4 12h16"/>',
    Marker.CIRCLE: '<circle cx="12" cy="12" r="8"/>',
    Marker.EVENT_BASED: RING_PENTAGON,
    Marker.LOOP: '<path d="M19 12a7 7 0 1 1-2.5-5.4M19 4v4.5h-4.5"/>',
    Marker.MULTI_INSTANCE: '<path d="M7 5v14M12 5v14M17 5v14"/>',
    Marker.SUBPROCESS: (
        '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 7v10M7 12h10"/>'
    ),
}
BOLD_MARKERS = (Marker.CROSS, Marker.PLUS, Marker.CIRCLE, Marker.MULTI_INSTANCE)
FILLED_MARKERS = (Marker.ERROR, Marker.MESSAGE_FILLED)  # drawn solid, in the line colour


@dataclass(frozen=True)
class MarkSlot:
    """One mark placed in a node: its box, in pixels from the top-left corner of the node."""

    marker: Marker
    x: float
    y: float
    size: float


def mark_svg(marker: Marker, size: float, stroke: str, attrs: str = "") -> str:
    """Draw one mark as an ``svg`` element.

    Args:
        marker: Which mark.
        size: The drawn width and height in pixels.
        stroke: The line colour, also the fill of a solid mark.
        attrs: Extra attributes for the element, such as a ``style`` or ``xmlns``.

    Returns:
        The ``svg`` element.
    """
    width = BOLD_STROKE_WIDTH if marker in BOLD_MARKERS else MARK_STROKE_WIDTH
    fill = stroke if marker in FILLED_MARKERS else "none"
    return (
        f'<svg width="{fmt(size)}" height="{fmt(size)}" viewBox="0 0 {MARK_GRID} {MARK_GRID}" '
        f'{attrs} fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f"{SHAPES[marker]}</svg>"
    )


def mark_slots(node: Node, marker_size: float, inset: float, gap: float) -> list[MarkSlot]:
    """Say where each mark of a node goes.

    An event or a gateway shows its marks in the middle. A task shows the mark that names its
    kind in the top-left corner, and the repeat and sub-process marks side by side at the bottom.

    Args:
        node: The node, with its markers.
        marker_size: The side of a task mark in pixels.
        inset: How far a task mark is from the corner.
        gap: The space between two marks at the bottom.

    Returns:
        One slot per marker, in the order of ``node.markers``.
    """
    if node.shape in EVENT_SHAPES:
        return _centred(node, EVENT_MARK_FRACTION)
    if node.shape is Shape.DECISION:
        return _centred(node, GATEWAY_MARK_FRACTION)
    top_left = [m for m in node.markers if m in TOP_LEFT_MARKERS]
    bottom = [m for m in node.markers if m in BOTTOM_MARKERS]
    slots = [MarkSlot(marker, inset, inset, marker_size) for marker in top_left]
    total = len(bottom) * marker_size + max(len(bottom) - 1, 0) * gap
    left = (node.width - total) / 2
    for index, marker in enumerate(bottom):
        x = left + index * (marker_size + gap)
        slots.append(MarkSlot(marker, x, node.height - marker_size - inset, marker_size))
    return slots


def _centred(node: Node, fraction: float) -> list[MarkSlot]:
    """Place every mark of a node in its middle, sized as a fraction of its smaller side."""
    size = min(node.width, node.height) * fraction
    x, y = (node.width - size) / 2, (node.height - size) / 2
    return [MarkSlot(marker, x, y, size) for marker in node.markers]
