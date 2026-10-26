"""Draw the lines of a scene as SVG paths: their dashes, animation, arrowheads and tails."""

import math

from .markup import esc, fmt
from .model import Edge, Head, Point, Role
from .theme import Theme

DEFAULT_DASH = "6 5"  # for a line that is dashed by choice, not by its role
OPEN_HEAD_STROKE = 1  # in marker units, so it grows with the line width
HEAD_MARKERS = (Head.FILLED, Head.OPEN, Head.DOT)
# Symbol heads (UML and entity-relationship) are drawn in pixels, whatever the line width. Each
# shape is a list of SVG parts in a box 24 px high whose x runs from -24 to 0, where the line
# ends at x = 0 and y = 12. ``{c}`` stands for the line colour and ``{w}`` for white.
SYMBOL_BOX_PX = 24
SYMBOL_MIDDLE_PX = 12
LINE = 'stroke="{c}" stroke-width="2"'
CROWS_FOOT = f'<path d="M-18 12L0 2M-18 12H0M-18 12L0 22" fill="none" {LINE}/>'
ONE_BAR = f'<path d="M-9 1V23" {LINE}/>'
DIAMOND_PATH = "M0 12L-8 6L-16 12L-8 18Z"
SYMBOL_SHAPES: dict[Head, str] = {
    Head.TRIANGLE: f'<path d="M0 12L-14 5V19Z" fill="{{w}}" {LINE}/>',
    Head.DIAMOND: f'<path d="{DIAMOND_PATH}" fill="{{w}}" {LINE}/>',
    Head.DIAMOND_FILLED: f'<path d="{DIAMOND_PATH}" fill="{{c}}" {LINE}/>',
    Head.ONE: ONE_BAR,
    Head.MANY: CROWS_FOOT,
    Head.ONE_ONLY: f'<path d="M-8 1V23M-15 1V23" {LINE}/>',
    Head.ZERO_ONE: f'<circle cx="-21" cy="12" r="5" fill="{{w}}" {LINE}/>{ONE_BAR}',
    Head.ZERO_MANY: f'<circle cx="-24" cy="12" r="5" fill="{{w}}" {LINE}/>{CROWS_FOOT}',
    Head.ONE_MANY: f'<path d="M-22 1V23" {LINE}/>{CROWS_FOOT}',
}
WHITE = "#FFFFFF"


def _pull_back(points: tuple[Point, ...], gap: float) -> list[Point]:
    """Shorten the last segment so the arrowhead tip touches the box it points at.

    Args:
        points: The route of a line, at least two points.
        gap: How far to pull the end back, in pixels.

    Returns:
        A new list of points. The route is returned as it is when its last segment is not
        longer than ``gap``.
    """
    (start_x, start_y), (end_x, end_y) = points[-2], points[-1]
    length = math.hypot(end_x - start_x, end_y - start_y)
    if length <= gap:
        return list(points)
    kept = (length - gap) / length
    pulled_back = (start_x + (end_x - start_x) * kept, start_y + (end_y - start_y) * kept)
    return [*points[:-1], pulled_back]


def _route(edge: Edge, gap: float) -> list[Point]:
    """Return the points to draw: the route with each arrowhead end pulled back by ``gap``.

    Symbol heads sit on the end of the line and are not pulled back.
    """
    route = list(edge.points)
    if edge.head in HEAD_MARKERS:
        route = _pull_back(tuple(route), gap)
    if edge.tail in HEAD_MARKERS:
        route = _pull_back(tuple(reversed(route)), gap)[::-1]
    return route


def _marker_url(role: Role, head: Head) -> str:
    """Return the ``url(#...)`` reference of the marker for a role and head."""
    return f"url(#head-{role.value}-{head.value})"


def edge_html(edge: Edge, theme: Theme) -> str:
    """Draw one line as an SVG path, with its dash, animation class, head and tail.

    Args:
        edge: The line to draw.
        theme: The design tokens.

    Returns:
        A ``path`` element.
    """
    line = theme.roles[edge.role]
    route = _route(edge, line.gap)
    attributes = {
        "d": "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in route),
        "stroke": line.color,
        "stroke-width": fmt(line.width),
        "fill": "none",
        "stroke-linejoin": "round",
    }
    dash = line.dash or (DEFAULT_DASH if edge.dashed else None)
    if dash:
        attributes["stroke-dasharray"] = dash
    if line.animation:
        attributes["class"] = line.animation.value
    if edge.head is not Head.NONE:
        attributes["marker-end"] = _marker_url(edge.role, edge.head)
    if edge.tail is not Head.NONE:
        attributes["marker-start"] = _marker_url(edge.role, edge.tail)
    text = " ".join(f'{name}="{esc(value)}"' for name, value in attributes.items())
    return f'<path data-id="{esc(edge.id)}" {text}/>'


def _head_shape(head: Head, size: float, color: str) -> str:
    """Return the SVG shape of one arrowhead, drawn pointing right with its tip at ``size``."""
    middle = size / 2
    if head is Head.FILLED:
        return (
            f'<path d="M0 0 L{fmt(size)} {fmt(middle)} L0 {fmt(size)} Z" '
            f'fill="{color}" stroke="none"/>'
        )
    if head is Head.OPEN:
        return (
            f'<path d="M0 0 L{fmt(size)} {fmt(middle)} L0 {fmt(size)}" fill="none" '
            f'stroke="{color}" stroke-width="{OPEN_HEAD_STROKE}"/>'
        )
    return (
        f'<circle cx="{fmt(middle)}" cy="{fmt(middle)}" r="{fmt(middle)}" '
        f'fill="{color}" stroke="none"/>'
    )


def arrowheads(theme: Theme) -> str:
    """Return the SVG ``defs`` with one marker per line role and head shape.

    The ``auto-start-reverse`` orientation lets the same marker serve as a tail.

    Args:
        theme: The design tokens.

    Returns:
        A ``defs`` element.
    """
    markers = []
    for role, line in theme.roles.items():
        size, middle = line.head_size, line.head_size / 2
        for head in HEAD_MARKERS:
            markers.append(
                f'<marker id="head-{role.value}-{head.value}" orient="auto-start-reverse" '
                f'markerWidth="{fmt(size)}" markerHeight="{fmt(size)}" refX="{fmt(middle)}" '
                f'refY="{fmt(middle)}" overflow="visible">'
                f"{_head_shape(head, size, line.color)}</marker>"
            )
    return "<defs>" + "".join(markers + _symbol_markers(theme)) + "</defs>"


def _symbol_markers(theme: Theme) -> list[str]:
    """Return the markers for symbol heads, one per line role and symbol."""
    markers = []
    for role, line in theme.roles.items():
        for head, shape in SYMBOL_SHAPES.items():
            body = shape.format(c=line.color, w=WHITE)
            markers.append(
                f'<marker id="head-{role.value}-{head.value}" orient="auto-start-reverse" '
                f'markerUnits="userSpaceOnUse" markerWidth="{SYMBOL_BOX_PX}" '
                f'markerHeight="{SYMBOL_BOX_PX}" '
                f'viewBox="-{SYMBOL_BOX_PX} 0 {SYMBOL_BOX_PX} {SYMBOL_BOX_PX}" '
                f'refX="0" refY="{SYMBOL_MIDDLE_PX}" overflow="visible">{body}</marker>'
            )
    return markers


def lines_layer(edges: tuple[Edge, ...], theme: Theme, size: tuple[float, float]) -> str:
    """Draw some lines in one SVG layer that covers the whole scene.

    Args:
        edges: The lines to draw in this layer.
        theme: The design tokens.
        size: The width and height of the scene.

    Returns:
        An ``svg`` element, or an empty string when there are no lines.
    """
    if not edges:
        return ""
    width, height = fmt(size[0]), fmt(size[1])
    paths = "".join(edge_html(edge, theme) for edge in edges)
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'style="position:absolute;left:0;top:0;overflow:visible" aria-hidden="true">'
        f"{arrowheads(theme)}{paths}</svg>"
    )
