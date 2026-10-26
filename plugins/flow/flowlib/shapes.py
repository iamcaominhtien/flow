"""The outline of each flowchart shape, drawn as SVG to fill a box of a given size."""

from collections.abc import Callable

from .markup import fmt
from .model import Shape
from .theme import ShapeColors

STROKE_WIDTH_PX = 2
BAR_STROKE_WIDTH_PX = 1.5
BAR_RADIUS_PX = 2
NOTE_FOLD_PX = 16
CROSS_INSET_PX = 4
CROSS_STROKE_WIDTH_PX = 2.5
CYLINDER_CAP_PX = 10  # the height of the half-ellipse at the top and bottom of a cylinder
TABLE_RADIUS_PX = 8
ENTITY_RADIUS_PX = 2
START_STROKE_WIDTH_PX = 2
END_STROKE_WIDTH_PX = 5
INTERMEDIATE_RING_GAP_PX = 4
ACTOR_HEAD_FRACTION = 0.12  # head radius as a fraction of the actor's height
ACTOR_NECK_FRACTION = 0.27
ACTOR_HIP_FRACTION = 0.62
ACTOR_ARM_FRACTION = 0.4
ACTOR_FOOT_FRACTION = 0.86
ACTOR_ARM_SPAN_FRACTION = 0.3  # half the arm span as a fraction of the actor's width
ACTOR_STROKE_WIDTH_PX = 2.5
INSET_PX = 1  # keeps the outline inside the box, so the stroke is not clipped
BOX_CORNER_RADIUS_PX = 10
SUBPROCESS_BAR_INSET_PX = 14
PARALLELOGRAM_SLANT_MAX_PX = 18
PARALLELOGRAM_SLANT_DIVISOR = 6  # the slant is a sixth of the width, up to the maximum
HEXAGON_SLANT_MAX_PX = 20
HEXAGON_SLANT_DIVISOR = 5
DOCUMENT_WAVE_FRACTION = 0.2  # height of the wavy bottom edge, as a fraction of the height
DOCUMENT_WAVE_PEAK_FACTOR = 2.2
DOCUMENT_WAVE_CONTROL_FRACTION = 0.75

Drawer = Callable[[float, float, ShapeColors], str]


def _paint(colors: ShapeColors) -> str:
    """Return the SVG attributes that fill and outline a shape."""
    return f'fill="{colors.fill}" stroke="{colors.stroke}" stroke-width="{STROKE_WIDTH_PX}"'


def _pill(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a rounded rectangle with fully round ends."""
    paint = _paint(colors)
    inner_width, inner_height = width - 2 * INSET_PX, height - 2 * INSET_PX
    return (
        f'<rect x="{INSET_PX}" y="{INSET_PX}" width="{fmt(inner_width)}" '
        f'height="{fmt(inner_height)}" rx="{fmt(inner_height / 2)}" {paint}/>'
    )


def _rounded_box(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a rectangle with rounded corners."""
    paint = _paint(colors)
    return (
        f'<rect x="{INSET_PX}" y="{INSET_PX}" width="{fmt(width - 2 * INSET_PX)}" '
        f'height="{fmt(height - 2 * INSET_PX)}" rx="{BOX_CORNER_RADIUS_PX}" {paint}/>'
    )


def _subprocess(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a rounded box with two vertical bars near its sides."""
    left, right = SUBPROCESS_BAR_INSET_PX, width - SUBPROCESS_BAR_INSET_PX
    bottom = height - INSET_PX
    bars = (
        f'<path d="M{left} {INSET_PX}V{fmt(bottom)}M{fmt(right)} {INSET_PX}V{fmt(bottom)}" '
        f'fill="none" stroke="{colors.stroke}" stroke-width="{STROKE_WIDTH_PX}"/>'
    )
    return _rounded_box(width, height, colors) + bars


def _decision(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a diamond."""
    paint = _paint(colors)
    return (
        f'<path d="M{fmt(width / 2)} {INSET_PX}L{fmt(width - INSET_PX)} {fmt(height / 2)}'
        f'L{fmt(width / 2)} {fmt(height - INSET_PX)}L{INSET_PX} {fmt(height / 2)}Z" '
        f'{paint} stroke-linejoin="round"/>'
    )


def _parallelogram(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a parallelogram that leans right."""
    paint = _paint(colors)
    slant = min(PARALLELOGRAM_SLANT_MAX_PX, width / PARALLELOGRAM_SLANT_DIVISOR)
    return (
        f'<path d="M{fmt(slant)} {INSET_PX}H{fmt(width - INSET_PX)}L{fmt(width - slant)} '
        f'{fmt(height - INSET_PX)}H{INSET_PX}Z" {paint} stroke-linejoin="round"/>'
    )


def _document(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a rectangle whose bottom edge is a wave."""
    paint = _paint(colors)
    wave = height * DOCUMENT_WAVE_FRACTION
    peak_y = height - wave * DOCUMENT_WAVE_PEAK_FACTOR
    return (
        f'<path d="M{INSET_PX} {INSET_PX}H{fmt(width - INSET_PX)}V{height - wave:.1f}'
        f"Q{width * DOCUMENT_WAVE_CONTROL_FRACTION:.1f} {peak_y:.1f} {width / 2:.1f} "
        f'{height - wave:.1f}T{INSET_PX} {height - wave:.1f}Z" {paint} '
        'stroke-linejoin="round"/>'
    )


def _hexagon(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a hexagon with pointed left and right ends."""
    paint = _paint(colors)
    slant = min(HEXAGON_SLANT_MAX_PX, width / HEXAGON_SLANT_DIVISOR)
    return (
        f'<path d="M{fmt(slant)} {INSET_PX}H{fmt(width - slant)}L{fmt(width - INSET_PX)} '
        f"{fmt(height / 2)}L{fmt(width - slant)} {fmt(height - INSET_PX)}H{fmt(slant)}"
        f'L{INSET_PX} {fmt(height / 2)}Z" {paint} stroke-linejoin="round"/>'
    )


def _bar(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a thin rectangle, such as an activation bar."""
    return (
        f'<rect x="{INSET_PX}" y="{INSET_PX}" width="{fmt(width - 2 * INSET_PX)}" '
        f'height="{fmt(height - 2 * INSET_PX)}" rx="{BAR_RADIUS_PX}" fill="{colors.fill}" '
        f'stroke="{colors.stroke}" stroke-width="{BAR_STROKE_WIDTH_PX}"/>'
    )


def _note(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a rectangle with a folded top-right corner."""
    paint = _paint(colors)
    fold = NOTE_FOLD_PX
    outline = (
        f'<path d="M{INSET_PX} {INSET_PX}H{fmt(width - fold)}L{fmt(width - INSET_PX)} {fold}'
        f'V{fmt(height - INSET_PX)}H{INSET_PX}Z" {paint} stroke-linejoin="round"/>'
    )
    crease = (
        f'<path d="M{fmt(width - fold)} {INSET_PX}V{fold}H{fmt(width - INSET_PX)}" fill="none" '
        f'stroke="{colors.stroke}" stroke-width="{STROKE_WIDTH_PX}" stroke-linejoin="round"/>'
    )
    return outline + crease


def _text(width: float, height: float, colors: ShapeColors) -> str:
    """Draw nothing: a text node is only its words."""
    return ""


def _cross(width: float, height: float, colors: ShapeColors) -> str:
    """Draw an X, which ends the lifeline of a destroyed participant."""
    low_x, high_x = CROSS_INSET_PX, width - CROSS_INSET_PX
    low_y, high_y = CROSS_INSET_PX, height - CROSS_INSET_PX
    return (
        f'<path d="M{fmt(low_x)} {fmt(low_y)}L{fmt(high_x)} {fmt(high_y)}'
        f'M{fmt(high_x)} {fmt(low_y)}L{fmt(low_x)} {fmt(high_y)}" fill="none" '
        f'stroke="{colors.stroke}" stroke-width="{CROSS_STROKE_WIDTH_PX}" stroke-linecap="round"/>'
    )


def _cylinder(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a can: the symbol of a database."""
    paint = _paint(colors)
    cap, rx = CYLINDER_CAP_PX, width / 2 - INSET_PX
    body = (
        f'<path d="M{INSET_PX} {cap}A{fmt(rx)} {cap} 0 0 1 {fmt(width - INSET_PX)} {cap}'
        f'V{fmt(height - cap)}A{fmt(rx)} {cap} 0 0 1 {INSET_PX} {fmt(height - cap)}Z" {paint}/>'
    )
    lid = (
        f'<path d="M{INSET_PX} {cap}A{fmt(rx)} {cap} 0 0 0 {fmt(width - INSET_PX)} {cap}" '
        f'fill="none" stroke="{colors.stroke}" stroke-width="{STROKE_WIDTH_PX}"/>'
    )
    return body + lid


def _table(width: float, height: float, colors: ShapeColors) -> str:
    """Draw the frame of a table: a white rounded rectangle; the header is drawn on top."""
    return (
        f'<rect x="{INSET_PX}" y="{INSET_PX}" width="{fmt(width - 2 * INSET_PX)}" '
        f'height="{fmt(height - 2 * INSET_PX)}" rx="{TABLE_RADIUS_PX}" {_paint(colors)}/>'
    )


def _entity(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a rectangle with nearly square corners."""
    return (
        f'<rect x="{INSET_PX}" y="{INSET_PX}" width="{fmt(width - 2 * INSET_PX)}" '
        f'height="{fmt(height - 2 * INSET_PX)}" rx="{ENTITY_RADIUS_PX}" {_paint(colors)}/>'
    )


def _store(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a box that is open on the right, the symbol of a data store."""
    return (
        f'<path d="M{fmt(width - INSET_PX)} {INSET_PX}H{INSET_PX}V{fmt(height - INSET_PX)}'
        f'H{fmt(width - INSET_PX)}" {_paint(colors)} stroke-linejoin="round"/>'
    )


def _ring(width: float, height: float, colors: ShapeColors, stroke_width: float) -> str:
    """Draw a circle outline with the given stroke width, inset so that it is not clipped."""
    radius = min(width, height) / 2 - stroke_width / 2
    return (
        f'<circle cx="{fmt(width / 2)}" cy="{fmt(height / 2)}" r="{fmt(radius)}" '
        f'fill="{colors.fill}" stroke="{colors.stroke}" stroke-width="{fmt(stroke_width)}"/>'
    )


def _start(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a thin circle: the start of a flow."""
    return _ring(width, height, colors, START_STROKE_WIDTH_PX)


def _end(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a thick circle: the end of a flow."""
    return _ring(width, height, colors, END_STROKE_WIDTH_PX)


def _intermediate(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a double circle: something that happens in the middle of a flow."""
    inner = _ring(
        width - 2 * INTERMEDIATE_RING_GAP_PX,
        height - 2 * INTERMEDIATE_RING_GAP_PX,
        ShapeColors(fill="none", stroke=colors.stroke),
        START_STROKE_WIDTH_PX,
    )
    gap = INTERMEDIATE_RING_GAP_PX
    shifted = f'<g transform="translate({gap} {gap})">{inner}</g>'
    return _ring(width, height, colors, START_STROKE_WIDTH_PX) + shifted


def _actor(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a stick figure."""
    middle = width / 2
    head = height * ACTOR_HEAD_FRACTION
    neck, hip = height * ACTOR_NECK_FRACTION, height * ACTOR_HIP_FRACTION
    arms, foot = height * ACTOR_ARM_FRACTION, height * ACTOR_FOOT_FRACTION
    span = width * ACTOR_ARM_SPAN_FRACTION
    body = (
        f"M{fmt(middle)} {fmt(neck)}V{fmt(hip)}"
        f"M{fmt(middle - span)} {fmt(arms)}H{fmt(middle + span)}"
        f"M{fmt(middle - span)} {fmt(foot)}L{fmt(middle)} {fmt(hip)}"
        f"L{fmt(middle + span)} {fmt(foot)}"
    )
    return (
        f'<circle cx="{fmt(middle)}" cy="{fmt(head + INSET_PX)}" r="{fmt(head)}" '
        f'fill="{colors.fill}" stroke="{colors.stroke}" stroke-width="{ACTOR_STROKE_WIDTH_PX}"/>'
        f'<path d="{body}" fill="none" stroke="{colors.stroke}" '
        f'stroke-width="{ACTOR_STROKE_WIDTH_PX}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def _ellipse(width: float, height: float, colors: ShapeColors) -> str:
    """Draw an ellipse that fills the box."""
    return (
        f'<ellipse cx="{fmt(width / 2)}" cy="{fmt(height / 2)}" rx="{fmt(width / 2 - INSET_PX)}" '
        f'ry="{fmt(height / 2 - INSET_PX)}" {_paint(colors)}/>'
    )


def _circle(width: float, height: float, colors: ShapeColors) -> str:
    """Draw a circle that fits the smaller side."""
    paint = _paint(colors)
    radius = min(width, height) / 2 - INSET_PX
    return f'<circle cx="{fmt(width / 2)}" cy="{fmt(height / 2)}" r="{fmt(radius)}" {paint}/>'


DRAWERS: dict[Shape, Drawer] = {
    Shape.TERMINATOR: _pill,
    Shape.FAIL: _pill,
    Shape.PROCESS: _rounded_box,
    Shape.SUBPROCESS: _subprocess,
    Shape.DECISION: _decision,
    Shape.IO: _parallelogram,
    Shape.DOCUMENT: _document,
    Shape.PREPARATION: _hexagon,
    Shape.CONNECTOR: _circle,
    Shape.BAR: _bar,
    Shape.NOTE: _note,
    Shape.TEXT: _text,
    Shape.CROSS: _cross,
    Shape.TABLE: _table,
    Shape.CYLINDER: _cylinder,
    Shape.ENTITY: _entity,
    Shape.STORE: _store,
    Shape.START: _start,
    Shape.END: _end,
    Shape.INTERMEDIATE: _intermediate,
    Shape.ACTOR: _actor,
    Shape.ELLIPSE: _ellipse,
}


def outline_svg(shape: Shape, width: float, height: float, colors: ShapeColors) -> str:
    """Return the SVG that draws a shape to fill a box.

    Args:
        shape: Which outline to draw.
        width: Box width in pixels.
        height: Box height in pixels.
        colors: Fill and outline colours.

    Returns:
        An ``svg`` element positioned at the top-left of its parent box.
    """
    body = DRAWERS[shape](width, height, colors)
    return (
        f'<svg width="{fmt(width)}" height="{fmt(height)}" viewBox="0 0 {fmt(width)} '
        f'{fmt(height)}" preserveAspectRatio="none" '
        'style="position:absolute;left:0;top:0;overflow:visible" aria-hidden="true">'
        f"{body}</svg>"
    )
