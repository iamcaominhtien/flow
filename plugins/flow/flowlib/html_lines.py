"""Draw the lines of a scene as SVG paths: their dashes, animation, arrowheads and tails."""

import math

from .markup import esc, fmt
from .model import Edge, Head, Point, Role
from .theme import Theme

DEFAULT_DASH = "6 5"  # for a line that is dashed by choice, not by its role
OPEN_HEAD_STROKE = 1  # in marker units, so it grows with the line width
HEAD_MARKERS = (Head.FILLED, Head.OPEN, Head.DOT)


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
    """Return the points to draw: the route with each marked end pulled back by ``gap``."""
    route = list(edge.points)
    if edge.head is not Head.NONE:
        route = _pull_back(tuple(route), gap)
    if edge.tail is not Head.NONE:
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
    return "<defs>" + "".join(markers) + "</defs>"


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
