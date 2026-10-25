"""The outline of each flowchart shape, drawn as SVG to fill a box of a given size."""

from collections.abc import Callable

from .markup import fmt
from .model import Shape
from .theme import ShapeColors

STROKE_WIDTH_PX = 2
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
