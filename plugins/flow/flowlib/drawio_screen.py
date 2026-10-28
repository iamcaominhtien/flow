"""Draw a screen of a screen flow as draw.io cells: the frame, and each part as a child cell.

The frame cell carries the whole screen view in a ``flowScreen`` style word, so that the file can be
read back into a scene (``import_drawio``). The parts are child cells, so that they move with it.
"""

import base64
import xml.etree.ElementTree as ET

from .drawio_common import FONT_BOLD, add_geometry, add_vertex, style_string
from .markup import esc, fmt
from .model import EdgeLabel, Node, Tone
from .screen_part import Part, PartKind
from .screen_parts import screen_parts
from .screen_scene import encode_screen
from .theme import Theme, icon_svg

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
SCREEN_STYLE_KEY = "flowScreen"
TONE_STYLE_KEY = "flowTone"  # the colour of the zone, which the id chip takes
DASH_PATTERN = "4 3"
IMAGE_KINDS = (PartKind.ICON, PartKind.PATH, PartKind.HATCH)  # parts drawn as one SVG picture
ARC_START = 0.75  # of a full turn, measured clockwise from the right: the top of the circle
ARC_END = 0.0
HATCH_ANGLE_DEG = 45
CHIP_CHAR_WIDTH_PX = 6.6
CHIP_PADDING_PX = 16
CHIP_ICON_ROOM_PX = 16
CHIP_HEIGHT_PX = 20
PILL_ARC_PERCENT = 50


def screen_style(node: Node, theme: Theme) -> str:
    """Return the style of the frame cell of a screen: its border, its fill and its packed view."""
    assert node.screen is not None
    frame = screen_parts(node, theme)[0]
    pairs = {"html": 1, **_paint_pairs(frame), SCREEN_STYLE_KEY: encode_screen(node.screen)}
    if node.tone is not None:
        pairs[TONE_STYLE_KEY] = node.tone.value
    return style_string(pairs)


def add_screen_parts(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add every part of a screen, except its frame, as a child cell of the frame cell.

    Args:
        root: The ``root`` element of the diagram.
        node: A node with a ``screen`` view.
        theme: The design tokens.
    """
    parent = f"node-{node.id}"
    for index, part in enumerate(screen_parts(node, theme)[1:], start=1):
        cell = add_vertex(root, f"part-{node.id}-{index}", _value(part), _part_style(part, theme))
        cell.set("parent", parent)
        add_geometry(cell, part.bounds)


def add_node_chip(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the chip that hangs on a node, such as the system event of a decision."""
    assert node.chip is not None
    chip = node.chip
    width = _chip_width(chip)
    colors = theme.chips[chip.kind]
    style = style_string(
        {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "html": 1,
            "whiteSpace": "nowrap",
            "fillColor": colors.background,
            "strokeColor": "none",
            "fontColor": colors.foreground,
            "fontSize": fmt(theme.type_scale.edge.size),
            "fontStyle": FONT_BOLD,
            "fontFamily": theme.fonts.sans,
        }
    )
    cell = add_vertex(root, f"chip-{node.id}", chip_value(chip, theme), style)
    cell.set("parent", f"node-{node.id}")
    add_geometry(
        cell, (chip.at[0] - width / 2, chip.at[1] - CHIP_HEIGHT_PX / 2, width, CHIP_HEIGHT_PX)
    )


def chip_value(label: EdgeLabel, theme: Theme) -> str:
    """Return the label text of a chip as HTML: its icon, when it has one, then its text."""
    if label.icon is None:
        return esc(label.text)
    svg = icon_svg(
        label.icon,
        theme.screen.trigger_icon,
        theme.chips[label.kind].foreground,
        f'xmlns="{SVG_NAMESPACE}"',
    )
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    size = fmt(theme.screen.trigger_icon)
    picture = f'<img src="{uri}" width="{size}" height="{size}" style="vertical-align:middle">'
    return f"{picture}&nbsp;{esc(label.text)}"


def _chip_width(label: EdgeLabel) -> float:
    """Estimate the width of a chip from its text."""
    icon = CHIP_ICON_ROOM_PX if label.icon else 0
    return len(label.text) * CHIP_CHAR_WIDTH_PX + CHIP_PADDING_PX + icon


def _value(part: Part) -> str:
    """Return the label of a part: only a text has one."""
    return esc(part.text) if part.kind is PartKind.TEXT else ""


def _paint_pairs(part: Part) -> dict[str, object]:
    """Return the style pairs of the fill, the border and the corners of a rectangle."""
    pairs: dict[str, object] = {
        "fillColor": part.fill or "none",
        "strokeColor": part.stroke or "none",
        "strokeWidth": fmt(part.stroke_width),
    }
    if part.radius:
        pairs.update({"rounded": 1, "absoluteArcSize": 1, "arcSize": fmt(2 * part.radius)})
    if part.is_dashed:
        pairs.update({"dashed": 1, "dashPattern": DASH_PATTERN})
    if part.opacity < 1:
        pairs["fillOpacity"] = fmt(part.opacity * 100)
    return pairs


def _part_style(part: Part, theme: Theme) -> str:
    """Return the style of the child cell that draws a part."""
    if part.kind is PartKind.TEXT:
        return _text_style(part, theme)
    if part.kind is PartKind.CIRCLE:
        return style_string({"ellipse": "", "html": 1, **_paint_pairs(part)})
    if part.kind is PartKind.ARC:
        arc = {"shape": "mxgraph.basic.arc", "startAngle": ARC_START, "endAngle": ARC_END}
        return style_string(
            {
                **arc,
                "fillColor": "none",
                "strokeColor": part.stroke,
                "strokeWidth": fmt(part.stroke_width),
            }
        )
    if part.kind is PartKind.IMAGE:
        return _screenshot_style(part)
    if part.kind in IMAGE_KINDS:
        return _image_style(_part_uri(part, theme))
    return style_string({"html": 1, **_paint_pairs(part)})


def _part_uri(part: Part, theme: Theme) -> str:
    """Return the picture of an icon, a path or a hatched block as a data URI."""
    if part.kind is PartKind.ICON:
        return _icon_uri(part)
    if part.kind is PartKind.PATH:
        return _path_uri(part)
    return _hatch_uri(part, theme)


def _text_style(part: Part, theme: Theme) -> str:
    """Return the style of a text cell: no box, one line, bold or regular."""
    family = theme.fonts.mono if part.is_mono else theme.fonts.sans
    return style_string(
        {
            "text": "",
            "html": 1,
            "align": part.align.value,
            "verticalAlign": "middle",
            "whiteSpace": "nowrap",
            "spacing": 0,
            "strokeColor": "none",
            "fillColor": "none",
            "fontSize": fmt(part.font_size),
            "fontStyle": FONT_BOLD if part.is_bold else 0,
            "fontColor": part.color,
            "fontFamily": family,
        }
    )


def _image_style(uri: str) -> str:
    """Return the style of a cell that shows an image stretched over its box."""
    return style_string({"shape": "image", "image": uri, "imageAspect": 0})


def _screenshot_style(part: Part) -> str:
    """Return the style of a screenshot: the PNG kept in proportion, from the top, with a border.

    draw.io cannot cut an image, so a screenshot taller than its box is shrunk to fit inside it.
    """
    pairs = {
        "shape": "image",
        "image": "data:image/png," + part.image,
        "imageAspect": 1,
        "imageVerticalAlign": "top",
        "imageBorder": part.stroke or "none",
    }
    return style_string(pairs)


def _icon_uri(part: Part) -> str:
    """Return the image of an icon part as a data URI that has no semicolon."""
    svg = icon_svg(part.icon, part.bounds[2], part.stroke or "", f'xmlns="{SVG_NAMESPACE}"')
    return "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()


def _path_uri(part: Part) -> str:
    """Return a path part as an SVG image: a stroked outline in a box of its own size."""
    _, _, width, height = part.bounds
    paint = (
        f'fill="{part.fill or "none"}" stroke="{part.stroke or "none"}" '
        f'stroke-width="{fmt(part.stroke_width)}" stroke-linecap="round" stroke-linejoin="round"'
    )
    svg = (
        f'<svg xmlns="{SVG_NAMESPACE}" width="{fmt(width)}" height="{fmt(height)}" '
        f'viewBox="0 0 {fmt(width)} {fmt(height)}"><path d="{part.path}" {paint}/></svg>'
    )
    return "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()


def _hatch_uri(part: Part, theme: Theme) -> str:
    """Return the hatched block as an SVG image: stripes in a dashed outline."""
    _, _, width, height = part.bounds
    stripe = theme.screen.hatch_stripe
    light = theme.tones[Tone.GRAY].box
    pattern = (
        f'<pattern id="h" width="{fmt(2 * stripe)}" height="{fmt(2 * stripe)}" '
        f'patternUnits="userSpaceOnUse" patternTransform="rotate({HATCH_ANGLE_DEG})">'
        f'<rect width="{fmt(2 * stripe)}" height="{fmt(2 * stripe)}" fill="{light}"/>'
        f'<rect width="{fmt(stripe)}" height="{fmt(2 * stripe)}" fill="{part.fill}"/></pattern>'
    )
    border = (
        f'<rect x="0.5" y="0.5" width="{fmt(width - 1)}" height="{fmt(height - 1)}" '
        f'rx="{fmt(part.radius)}" fill="url(#h)" stroke="{part.stroke}" '
        f'stroke-dasharray="{DASH_PATTERN}"/>'
    )
    svg = (
        f'<svg xmlns="{SVG_NAMESPACE}" width="{fmt(width)}" height="{fmt(height)}" '
        f'viewBox="0 0 {fmt(width)} {fmt(height)}"><defs>{pattern}</defs>{border}</svg>'
    )
    return "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()
