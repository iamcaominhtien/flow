"""The draw.io cells of a C4 box: one text cell with the icon as a child cell.

The label holds the name, the ``[Kind: technology]`` line and the sentence, so that a person
editing the file in draw.io changes the text and not a pile of loose cells. The importer reads
the three lines back.
"""

import base64
import xml.etree.ElementTree as ET

from .drawio_common import FLOW_SHAPE_KEY, add_geometry, add_vertex, style_string
from .markup import esc, fmt
from .model import Node, Shape, Tone
from .shapes import PERSON_RADIUS_PX
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
HEADING_STYLE = "margin-left:{indent}px;height:{height}px"
NAME_STYLE = "font-size:{size}px;font-weight:bold"
MONO_STYLE = "font-family:{family};font-size:{size}px;font-weight:normal;color:{color}"
TEXT_STYLE = "font-size:{size}px;font-weight:normal"


def c4_style(node: Node, theme: Theme) -> dict[str, object]:
    """Return the style pairs that place the text of a C4 box and mark its shape.

    Args:
        node: A C4 box.
        theme: The design tokens.

    Returns:
        Style pairs to add to the node's style.
    """
    rules = theme.c4
    pairs: dict[str, object] = {
        FLOW_SHAPE_KEY: node.shape.value,
        "align": "left",
        "verticalAlign": "top",
        "spacingLeft": rules.padding,
        "spacingRight": rules.padding,
        "spacingTop": rules.name_top - rules.padding,
        "fontStyle": 0,
        "fontSize": fmt(rules.text_font_size),
    }
    if node.shape is Shape.C4_PERSON:
        pairs["arcSize"] = 2 * PERSON_RADIUS_PX
    return pairs


def c4_value(node: Node, theme: Theme) -> str:
    """Return the label of a C4 box: name, technology line and sentence."""
    rules = theme.c4
    indent = (rules.text_left if node.icon else rules.padding) - rules.padding
    height = rules.text_top - rules.name_top
    name_style = NAME_STYLE.format(size=fmt(rules.name_font_size))
    mono_style = MONO_STYLE.format(
        family=theme.fonts.mono, size=fmt(rules.tech_font_size), color=theme.slate
    )
    heading = (
        f'<div style="{HEADING_STYLE.format(indent=fmt(indent), height=fmt(height))}">'
        f'<span style="{name_style}">{esc(" ".join(node.text))}</span><br>'
        f'<span style="{mono_style}">{esc(node.technology)}</span></div>'
    )
    text_style = TEXT_STYLE.format(size=fmt(rules.text_font_size))
    sentence = "<br>".join(esc(line) for line in node.detail)
    return f'{heading}<div style="{text_style}">{sentence}</div>'


def add_c4_icon(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the icon of a C4 box as a child cell at its top left."""
    if node.icon is None:
        return
    rules = theme.c4
    attrs = f'xmlns="{SVG_NAMESPACE}"'
    if has_detailed_icon(node.icon):
        stroke = theme.tones[node.tone or Tone.GRAY].stroke
        svg = detailed_icon_svg(node.icon, rules.icon_size, stroke, attrs)
    else:
        svg = icon_svg(node.icon, rules.icon_size, theme.shapes[node.shape].stroke, attrs)
    image = "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()
    cell = add_vertex(root, f"icon-{node.id}", "", style_string({"shape": "image", "image": image}))
    cell.set("parent", f"node-{node.id}")
    add_geometry(cell, (rules.padding, rules.padding, rules.icon_size, rules.icon_size))
