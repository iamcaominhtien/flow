"""Render a scene as one self-contained HTML file: boxes, inline SVG and CSS animation."""

import math

from .markup import esc, fmt, px, tag
from .model import ArrowEnd, Edge, EdgeLabel, Frame, Node, Point, Scene, Shape
from .shapes import outline_svg
from .text_area import text_area_width
from .theme import ShapeColors, Theme, load_icons, load_theme

FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800"
    "&family=JetBrains+Mono:wght@400;500&display=swap"
)

# Text inside a node
LINE_HEIGHT_FACTOR = 1.25
NODE_TEXT_WEIGHT = 600
DOCUMENT_LABEL_TRIM_PX = 6  # the wavy bottom of a document leaves less room for text
DOCUMENT_ICON_LIFT_PX = 3

# Icon inside a node
ICON_SIZE_PX = 18
ICON_STROKE_WIDTH = 2
ICON_TEXT_SHIFT_PX = 12  # text moves right by half of that
ICON_LEFT_PX: dict[Shape, float] = {
    Shape.SUBPROCESS: 22,
    Shape.IO: 26,
    Shape.PREPARATION: 24,
}
DEFAULT_ICON_LEFT_PX = 14

# Number badge on a node corner
BADGE_OVERHANG_LEFT_PX = 6
BADGE_OVERHANG_TOP_PX = 10
BADGE_MIN_WIDTH_PX = 22
BADGE_HEIGHT_PX = 20
BADGE_PADDING_X_PX = 6
BADGE_FONT_SIZE_PX = 11

# Frame
FRAME_RADIUS_PX = 16
FRAME_BORDER_PX = 1.5
FRAME_PILL_INSET_X_PX = 16
FRAME_PILL_INSET_Y_PX = 12
PILL_HEIGHT_PX = 22
PILL_PADDING_X_PX = 12
PILL_FONT_SIZE_PX = 12
PILL_RADIUS_PX = 999

# Label chip on a line
CHIP_PADDING = "2px 8px"
CHIP_FONT_SIZE_PX = 11
CHIP_LINE_HEIGHT_PX = 16

# Title block
TITLE_LEFT_PX = 64
TITLE_TOP_PX = 48
TITLE_FONT_SIZE_PX = 24
TITLE_WEIGHT = 600
DESCRIPTION_FONT_SIZE_PX = 13
DESCRIPTION_LINE_HEIGHT_PX = 20
DESCRIPTION_MAX_WIDTH_PX = 900
TITLE_GAP_PX = 8

ABSOLUTE = {"position": "absolute"}
CENTERED_ON_POINT = "translate(-50%,-50%)"


def _icon_html(node: Node, stroke: str) -> str:
    """Draw the icon of a node at its left side, or return nothing if it has none."""
    if node.icon is None:
        return ""
    left = ICON_LEFT_PX.get(node.shape, DEFAULT_ICON_LEFT_PX)
    top = (node.height - ICON_SIZE_PX) / 2
    if node.shape is Shape.DOCUMENT:
        top -= DOCUMENT_ICON_LIFT_PX
    return (
        f'<svg width="{ICON_SIZE_PX}" height="{ICON_SIZE_PX}" viewBox="0 0 24 24" '
        f'style="position:absolute;left:{px(left)};top:{px(top)}" fill="none" '
        f'stroke="{stroke}" stroke-width="{ICON_STROKE_WIDTH}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{load_icons()[node.icon]}</svg>'
    )


def _label_html(node: Node, theme: Theme) -> str:
    """Draw the text of a node, centred in the space the shape leaves for it."""
    if not node.text:
        return ""
    has_icon = node.icon is not None
    width = text_area_width(node.shape, node.width, has_icon)
    shift = ICON_TEXT_SHIFT_PX if has_icon else 0.0
    height = node.height - (DOCUMENT_LABEL_TRIM_PX if node.shape is Shape.DOCUMENT else 0)
    style = {
        **ABSOLUTE,
        "left": px((node.width - width) / 2 + shift),
        "top": "0",
        "width": px(width),
        "height": px(height),
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        "text-align": "center",
        "font-size": px(node.font_size),
        "line-height": px(int(node.font_size * LINE_HEIGHT_FACTOR)),
        "font-weight": str(NODE_TEXT_WEIGHT),
        "color": theme.ink,
    }
    return tag("div", style, "<br>".join(esc(line) for line in node.text))


def _badge_html(node: Node, theme: Theme) -> str:
    """Draw the number badge on the top-left corner of a node, or return nothing."""
    if node.number is None:
        return ""
    style = {
        **ABSOLUTE,
        "left": px(node.x - BADGE_OVERHANG_LEFT_PX),
        "top": px(node.y - BADGE_OVERHANG_TOP_PX),
        "min-width": px(BADGE_MIN_WIDTH_PX),
        "height": px(BADGE_HEIGHT_PX),
        "padding": f"0 {px(BADGE_PADDING_X_PX)}",
        "box-sizing": "border-box",
        "border-radius": px(PILL_RADIUS_PX),
        "background": theme.badge.background,
        "color": theme.badge.foreground,
        "font": f"700 {px(BADGE_FONT_SIZE_PX)}/{px(BADGE_HEIGHT_PX)} "
        f"'{theme.fonts.mono}',monospace",
        "text-align": "center",
    }
    return tag("div", style, esc(node.number))


def _node_html(node: Node, theme: Theme) -> str:
    """Draw one node: its outline, icon and text, and its number badge when it has one."""
    colors = theme.shapes[node.shape]
    if node.tone is not None:
        colors = ShapeColors(fill=theme.tones[node.tone].box, stroke=colors.stroke)
    inside = (
        outline_svg(node.shape, node.width, node.height, colors)
        + _icon_html(node, colors.stroke)
        + _label_html(node, theme)
    )
    box = {
        **ABSOLUTE,
        "left": px(node.x),
        "top": px(node.y),
        "width": px(node.width),
        "height": px(node.height),
    }
    return tag("div", box, inside, data_id=node.id) + _badge_html(node, theme)


def _frame_html(frame: Frame, theme: Theme) -> str:
    """Draw one frame and its label pill."""
    tone = theme.tones[frame.tone]
    area = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "width": px(frame.width),
        "height": px(frame.height),
        "box-sizing": "border-box",
        "background": tone.box,
        "border": f"{px(FRAME_BORDER_PX)} dashed {tone.pill}",
        "border-radius": px(FRAME_RADIUS_PX),
    }
    html = tag("div", area, data_id=frame.id)
    if frame.label:
        pill = {
            **ABSOLUTE,
            "left": px(frame.x + FRAME_PILL_INSET_X_PX),
            "top": px(frame.y + FRAME_PILL_INSET_Y_PX),
            "height": px(PILL_HEIGHT_PX),
            "padding": f"0 {px(PILL_PADDING_X_PX)}",
            "box-sizing": "border-box",
            "border-radius": px(PILL_RADIUS_PX),
            "background": tone.pill,
            "color": theme.ink,
            "font-size": px(PILL_FONT_SIZE_PX),
            "font-weight": "700",
            "line-height": px(PILL_HEIGHT_PX),
            "white-space": "nowrap",
        }
        html += tag("div", pill, esc(frame.label))
    return html


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


def _edge_html(edge: Edge, theme: Theme) -> str:
    """Draw one line as an SVG path, with its dash, animation class and arrowhead."""
    line = theme.roles[edge.role]
    has_arrow = edge.arrow is ArrowEnd.END
    route = _pull_back(edge.points, line.gap) if has_arrow else list(edge.points)
    attributes = {
        "d": "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in route),
        "stroke": line.color,
        "stroke-width": fmt(line.width),
        "fill": "none",
        "stroke-linejoin": "round",
    }
    if line.dash:
        attributes["stroke-dasharray"] = line.dash
    if line.animation:
        attributes["class"] = line.animation.value
    if has_arrow:
        attributes["marker-end"] = f"url(#head-{edge.role.value})"
    text = " ".join(f'{name}="{esc(value)}"' for name, value in attributes.items())
    return f'<path data-id="{esc(edge.id)}" {text}/>'


def _arrowheads(theme: Theme) -> str:
    """Return the SVG ``defs`` with one arrowhead marker per line role."""
    markers = []
    for role, line in theme.roles.items():
        size, middle = line.head_size, line.head_size / 2
        markers.append(
            f'<marker id="head-{role.value}" orient="auto" markerWidth="{fmt(size)}" '
            f'markerHeight="{fmt(size)}" refX="{fmt(middle)}" refY="{fmt(middle)}" '
            f'overflow="visible"><path d="M0 0 L{fmt(size)} {fmt(middle)} L0 {fmt(size)} Z" '
            f'fill="{line.color}" stroke="none"/></marker>'
        )
    return "<defs>" + "".join(markers) + "</defs>"


def _label_chip_html(label: EdgeLabel, theme: Theme) -> str:
    """Draw the chip that names a line, centred on the label position."""
    colors = theme.chips[label.kind]
    style = {
        **ABSOLUTE,
        "left": px(label.at[0]),
        "top": px(label.at[1]),
        "transform": CENTERED_ON_POINT,
        "padding": CHIP_PADDING,
        "border-radius": px(PILL_RADIUS_PX),
        "background": colors.background,
        "color": colors.foreground,
        "font-size": px(CHIP_FONT_SIZE_PX),
        "font-weight": "700",
        "line-height": px(CHIP_LINE_HEIGHT_PX),
        "white-space": "nowrap",
    }
    return tag("div", style, esc(label.text))


def _title_html(scene: Scene, theme: Theme) -> str:
    """Draw the title and the description of a scene, or return nothing without a title."""
    if not scene.title:
        return ""
    title_style = {"font-size": px(TITLE_FONT_SIZE_PX), "font-weight": str(TITLE_WEIGHT)}
    title = tag("div", title_style, esc(scene.title))
    description = ""
    if scene.description:
        style = {
            "font-size": px(DESCRIPTION_FONT_SIZE_PX),
            "line-height": px(DESCRIPTION_LINE_HEIGHT_PX),
            "color": theme.slate,
            "max-width": px(min(scene.width - 2 * TITLE_LEFT_PX, DESCRIPTION_MAX_WIDTH_PX)),
        }
        description = tag("div", style, esc(scene.description))
    block = {
        **ABSOLUTE,
        "left": px(TITLE_LEFT_PX),
        "top": px(TITLE_TOP_PX),
        "display": "flex",
        "flex-direction": "column",
        "gap": px(TITLE_GAP_PX),
    }
    return tag("div", block, title + description)


def _stylesheet(theme: Theme) -> str:
    """Return the page CSS: fonts, and the keyframes of each animated tier."""
    rules = [
        f"body{{margin:0;background:{theme.canvas};font-family:'{theme.fonts.sans}',"
        f"system-ui,sans-serif;color:{theme.ink}}}",
    ]
    for animation, speed in theme.animations.items():
        name = animation.value
        rules.append(f"@keyframes {name}{{to{{stroke-dashoffset:{fmt(speed.dash_offset)}}}}}")
        rules.append(f".{name}{{animation:{name} {fmt(speed.seconds)}s linear infinite}}")
    still = ",".join(f".{animation.value}" for animation in theme.animations)
    rules.append(f"@media (prefers-reduced-motion: reduce){{{still}{{animation:none}}}}")
    return "\n".join(rules)


def _lines_html(scene: Scene, theme: Theme) -> str:
    """Draw all lines in one SVG layer that covers the whole scene."""
    width, height = fmt(scene.width), fmt(scene.height)
    paths = "".join(_edge_html(edge, theme) for edge in scene.edges)
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'style="position:absolute;left:0;top:0;overflow:visible" aria-hidden="true">'
        f"{_arrowheads(theme)}{paths}</svg>"
    )


def render(scene: Scene) -> str:
    """Return the HTML text of a scene.

    Args:
        scene: A scene from ``scene.parse`` or ``scene.load``.

    Returns:
        A complete HTML document with no script and no file besides the web fonts.
    """
    theme = load_theme()
    layers = [_frame_html(frame, theme) for frame in scene.frames]
    layers += [_node_html(node, theme) for node in scene.nodes]
    layers.append(_lines_html(scene, theme))
    layers += [_label_chip_html(edge.label, theme) for edge in scene.edges if edge.label]
    layers.append(_title_html(scene, theme))
    canvas = {
        "position": "relative",
        "width": px(scene.width),
        "height": px(scene.height),
        "background": theme.canvas,
        "overflow": "hidden",
    }
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{esc(scene.title or 'Diagram')}</title>\n"
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        f'<link href="{FONTS_URL}" rel="stylesheet">\n'
        f"<style>\n{_stylesheet(theme)}\n</style>\n</head>\n<body>\n"
        f"{tag('div', canvas, chr(10).join(layers))}\n</body>\n</html>\n"
    )
