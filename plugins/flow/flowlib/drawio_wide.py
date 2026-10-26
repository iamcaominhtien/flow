"""The draw.io cells of the illustrated architecture card: a pill, a detail and an icon."""

import base64
import xml.etree.ElementTree as ET

from .drawio_common import FLOW_SHAPE_KEY, FONT_BOLD, add_geometry, add_vertex, style_string
from .html_wide import (
    DETAIL_GAP_PX,
    DETAIL_WIDTH_FRACTION,
    ICON_RIGHT_PX,
    PADDING_PX,
    PILL_HEIGHT_PX,
    PILL_PADDING_PX,
)
from .markup import esc, fmt
from .model import Node, Tone
from .sizing import estimate_text_width
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
PILL_ARC_PERCENT = 50


def wide_style(node: Node) -> dict[str, object]:
    """Return the style pairs that mark an illustrated card, so the importer reads it back."""
    return {FLOW_SHAPE_KEY: node.shape.value, "fontStyle": 0}


def add_wide_parts(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the pill, the detail text and the icon of an illustrated architecture card."""
    parent = f"node-{node.id}"
    _add_pill(root, node, theme, parent)
    _add_detail(root, node, theme, parent)
    _add_icon(root, node, theme, parent)


def _add_pill(root: ET.Element, node: Node, theme: Theme, parent: str) -> None:
    """Add the name of the card as a pill at its top left."""
    shape = theme.shapes[node.shape]
    style = style_string(
        {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "html": 1,
            "fillColor": theme.tones[node.tone or Tone.GRAY].pill,
            "strokeColor": shape.stroke,
            "strokeWidth": fmt(shape.stroke_width),
            "fontColor": theme.ink,
            "fontStyle": FONT_BOLD,
            "fontSize": fmt(node.font_size),
            "fontFamily": theme.fonts.sans,
        }
    )
    name = " ".join(node.text)
    cell = add_vertex(root, f"pill-{node.id}", esc(name), style)
    cell.set("parent", parent)
    width = estimate_text_width(name, theme.layout, node.font_size) + 2 * PILL_PADDING_PX
    add_geometry(cell, (PADDING_PX, PADDING_PX, width, PILL_HEIGHT_PX))


def _add_detail(root: ET.Element, node: Node, theme: Theme, parent: str) -> None:
    """Add the detail line under the pill."""
    if not node.detail:
        return
    style = style_string(
        {
            "text": "",
            "html": 1,
            "whiteSpace": "wrap",
            "align": "left",
            "verticalAlign": "top",
            "strokeColor": "none",
            "fillColor": "none",
            "fontSize": fmt(theme.layout.detail_font_size),
            "fontColor": theme.slate,
            "fontFamily": theme.fonts.sans,
            "spacingLeft": 0,
            "spacingTop": 0,
        }
    )
    cell = add_vertex(root, f"detail-{node.id}", "<br>".join(esc(t) for t in node.detail), style)
    cell.set("parent", parent)
    top = PADDING_PX + PILL_HEIGHT_PX + DETAIL_GAP_PX
    box = (PADDING_PX, top, node.width * DETAIL_WIDTH_FRACTION, theme.layout.detail_line_height)
    add_geometry(cell, box)


def _add_icon(root: ET.Element, node: Node, theme: Theme, parent: str) -> None:
    """Add the large icon at the right of the card."""
    if node.icon is None:
        return
    size = theme.architecture.card_icon_size
    attrs = f'xmlns="{SVG_NAMESPACE}"'
    if has_detailed_icon(node.icon):
        stroke = theme.tones[node.tone or Tone.GRAY].stroke
        svg = detailed_icon_svg(node.icon, size, stroke, attrs)
    else:
        svg = icon_svg(node.icon, size, theme.shapes[node.shape].stroke, attrs)
    image = "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()
    cell = add_vertex(root, f"icon-{node.id}", "", style_string({"shape": "image", "image": image}))
    cell.set("parent", parent)
    add_geometry(cell, (node.width - ICON_RIGHT_PX - size, (node.height - size) / 2, size, size))
