"""Render a scene as one self-contained HTML file: boxes, inline SVG and CSS animation."""

from .html_lines import lines_layer
from .html_nodes import node_html
from .markup import esc, fmt, px, tag
from .model import Divider, EdgeLabel, Frame, FrameVariant, Role, Scene, Shape
from .theme import Theme, load_theme

FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800"
    "&family=JetBrains+Mono:wght@400;500&display=swap"
)

# Text inside a node
LINE_HEIGHT_FACTOR = 1.25
NODE_TEXT_WEIGHT = 600
NOTE_TEXT_WEIGHT = 400
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

LANE_BORDER_PX = 1  # the thin outline of a swimlane
LANE_TAB_FONT_SIZE_PX = 13

# Fragment frame
FRAGMENT_RADIUS_PX = 8
FRAGMENT_TAG_HEIGHT_PX = 18
FRAGMENT_TAG_PADDING_X_PX = 10
FRAGMENT_TAG_RADIUS_PX = 8
FRAGMENT_FONT_SIZE_PX = 11
FRAGMENT_GAP_PX = 8
FRAGMENT_GUARD_INSET_PX = 10
FRAGMENT_GUARD_DROP_PX = 2

# Label chip on a line
NUMBER_SIZE_PX = 16
NUMBER_GAP_PX = 6
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


def _frame_html(frame: Frame, theme: Theme) -> str:
    """Draw one frame: a tinted area with a label pill, or a fragment with a tag and a guard."""
    if frame.variant is FrameVariant.FRAGMENT:
        return _fragment_html(frame, theme)
    if frame.variant is FrameVariant.LANE:
        return _lane_html(frame, theme)
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


def _lane_html(frame: Frame, theme: Theme) -> str:
    """Draw a swimlane: a lightly tinted band with its name on a dark tab at the start.

    The tab is at the left of a lane that is wider than it is tall, and at the top of a tall one.
    """
    tone = theme.tones[frame.tone]
    area = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "width": px(frame.width),
        "height": px(frame.height),
        "box-sizing": "border-box",
        "background": tone.lane,
        "border": f"{px(LANE_BORDER_PX)} solid {tone.pill}",
    }
    html = tag("div", area, data_id=frame.id)
    tab_size = load_theme().layout.lane_tab
    is_row = frame.width >= frame.height
    tab = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "width": px(tab_size if is_row else frame.width),
        "height": px(frame.height if is_row else tab_size),
        "box-sizing": "border-box",
        "background": tone.accent,
        "color": "#FFFFFF",
        "font-size": px(LANE_TAB_FONT_SIZE_PX),
        "font-weight": "700",
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        "text-align": "center",
        "overflow": "hidden",
    }
    if is_row:
        tab["writing-mode"] = "vertical-rl"
        tab["transform"] = "rotate(180deg)"
        tab["transform-origin"] = "center"
    return html + tag("div", tab, esc(frame.label or ""))


def _mono_font(theme: Theme) -> str:
    """Return the CSS ``font`` shorthand for guard text: small monospace on a tag-high line."""
    return (
        f"{px(FRAGMENT_FONT_SIZE_PX)}/{px(FRAGMENT_TAG_HEIGHT_PX)} '{theme.fonts.mono}',monospace"
    )


def _fragment_html(frame: Frame, theme: Theme) -> str:
    """Draw a fragment frame: a bordered area, a tag tab, the guard, and the dividers."""
    tone = theme.tones[frame.tone]
    area = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "width": px(frame.width),
        "height": px(frame.height),
        "box-sizing": "border-box",
        "background": tone.box,
        "border": f"{px(FRAME_BORDER_PX)} solid {tone.stroke}",
        "border-radius": px(FRAGMENT_RADIUS_PX),
    }
    html = tag("div", area, data_id=frame.id)
    tab = {
        "padding": f"0 {px(FRAGMENT_TAG_PADDING_X_PX)}",
        "height": px(FRAGMENT_TAG_HEIGHT_PX),
        "line-height": px(FRAGMENT_TAG_HEIGHT_PX),
        "background": "#FFFFFF",
        "border": f"1px solid {tone.stroke}",
        "border-top": "none",
        "border-left": "none",
        "border-radius": f"0 0 {px(FRAGMENT_TAG_RADIUS_PX)} 0",
        "font-size": px(FRAGMENT_FONT_SIZE_PX),
        "font-weight": "700",
        "color": theme.ink,
    }
    guard = {
        "font": _mono_font(theme),
        "color": theme.slate,
    }
    head = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(frame.y),
        "display": "flex",
        "gap": px(FRAGMENT_GAP_PX),
    }
    inner = tag("div", tab, esc(frame.label or ""))
    if frame.guard:
        inner += tag("div", guard, esc(f"[{frame.guard}]"))
    html += tag("div", head, inner)
    for divider in frame.dividers:
        html += _divider_html(frame, divider, theme)
    return html


def _divider_html(frame: Frame, divider: Divider, theme: Theme) -> str:
    """Draw a dashed line across a fragment, with the guard of the part below it."""
    line = {
        **ABSOLUTE,
        "left": px(frame.x),
        "top": px(divider.y),
        "width": px(frame.width),
        "border-top": f"1px dashed {theme.tones[frame.tone].stroke}",
    }
    text = {
        **ABSOLUTE,
        "left": px(frame.x + FRAGMENT_GUARD_INSET_PX),
        "top": px(divider.y + FRAGMENT_GUARD_DROP_PX),
        "font": _mono_font(theme),
        "color": theme.slate,
    }
    return tag("div", line) + tag("div", text, esc(f"[{divider.guard}]"))


def _number_html(number: str, theme: Theme) -> str:
    """Draw the small dark circle that holds a step number inside a label."""
    style = {
        "display": "inline-block",
        "min-width": px(NUMBER_SIZE_PX),
        "height": px(NUMBER_SIZE_PX),
        "margin-right": px(NUMBER_GAP_PX),
        "border-radius": px(PILL_RADIUS_PX),
        "background": theme.badge.background,
        "color": theme.badge.foreground,
        "font": f"700 10px/{px(NUMBER_SIZE_PX)} '{theme.fonts.mono}',monospace",
        "text-align": "center",
        "vertical-align": "middle",
    }
    return tag("span", style, esc(number))


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
    number = _number_html(label.number, theme) if label.number else ""
    return tag("div", style, number + esc(label.text))


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


def render(scene: Scene) -> str:
    """Return the HTML text of a scene.

    Args:
        scene: A scene from ``scene.parse`` or ``scene.load``.

    Returns:
        A complete HTML document with no script and no file besides the web fonts.
    """
    theme = load_theme()
    size = (scene.width, scene.height)
    underlay = tuple(edge for edge in scene.edges if edge.role is Role.LIFELINE)
    overlay = tuple(edge for edge in scene.edges if edge.role is not Role.LIFELINE)
    layers = [_frame_html(frame, theme) for frame in scene.frames]
    layers.append(lines_layer(underlay, theme, size))
    layers += [node_html(node, theme) for node in scene.nodes]
    layers.append(lines_layer(overlay, theme, size))
    layers += [_label_chip_html(edge.label, theme) for edge in scene.edges if edge.label]
    layers += [_label_chip_html(extra, theme) for edge in scene.edges for extra in edge.extras]
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
