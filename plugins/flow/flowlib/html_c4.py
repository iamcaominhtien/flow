"""Draw what sits on the outline of a C4 box as HTML: icon, name, technology line and sentence."""

from .markup import esc, px, tag
from .model import Node, Shape, Tone
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

ABSOLUTE = {"position": "absolute"}
NAME_WEIGHT = 700
C4_SHAPES = (Shape.C4_BOX, Shape.C4_PERSON)


def is_c4_node(node: Node) -> bool:
    """Tell whether a node is a box of a C4 diagram."""
    return node.shape in C4_SHAPES


def c4_html(node: Node, theme: Theme) -> str:
    """Draw the inside of a C4 box.

    Args:
        node: A box with ``text`` (the name), ``technology`` and ``detail`` (the sentence).
        theme: The design tokens.

    Returns:
        The markup that goes into the box after its outline.
    """
    return _icon_html(node, theme) + _heading_html(node, theme) + _sentence_html(node, theme)


def _icon_html(node: Node, theme: Theme) -> str:
    """Draw the icon at the top left, detailed when the library has a detailed drawing."""
    if node.icon is None:
        return ""
    rules = theme.c4
    place = f'style="position:absolute;left:{px(rules.padding)};top:{px(rules.padding)}"'
    if has_detailed_icon(node.icon):
        stroke = theme.tones[node.tone or Tone.GRAY].stroke
        return detailed_icon_svg(node.icon, rules.icon_size, stroke, place)
    return icon_svg(node.icon, rules.icon_size, theme.shapes[node.shape].stroke, place)


def _heading_html(node: Node, theme: Theme) -> str:
    """Draw the bold name and, under it, the mono ``[Kind: technology]`` line."""
    rules = theme.c4
    box = {
        **ABSOLUTE,
        "left": px(rules.text_left if node.icon else rules.padding),
        "top": px(rules.name_top),
        "right": px(rules.padding),
    }
    name = {"font-size": px(rules.name_font_size), "font-weight": str(NAME_WEIGHT)}
    mono = {
        "font-family": f"'{theme.fonts.mono}',monospace",
        "font-size": px(rules.tech_font_size),
        "color": theme.slate,
        "line-height": px(rules.text_line_height),
    }
    inner = tag("div", {**name, "color": theme.ink}, esc(" ".join(node.text)))
    return tag("div", box, inner + tag("div", mono, esc(node.technology)))


def _sentence_html(node: Node, theme: Theme) -> str:
    """Draw the one sentence about the job of the box."""
    rules = theme.c4
    style = {
        **ABSOLUTE,
        "left": px(rules.padding),
        "top": px(rules.text_top),
        "right": px(rules.padding),
        "font-size": px(rules.text_font_size),
        "line-height": px(rules.text_line_height),
        "color": theme.ink,
    }
    return tag("div", style, "<br>".join(esc(line) for line in node.detail))
