"""Read the data flow shapes, the BPMN marks and the pool frames back from a draw.io file.

Flow writes them with style keys of its own (``flowShape``, ``flowMarkers``, ``flowFrame``) and
child cells for the strip of a process, the id cell of a store, the pill of a card and the
marks. A file that was edited in draw.io keeps those keys, so the shapes come back as shapes.
"""

import html
import re
from dataclasses import replace
from xml.etree import ElementTree as ET

from .drawio_common import FLOW_FRAME_KEY, FLOW_HOST_KEY, FLOW_MARKERS_KEY, FLOW_SHAPE_KEY
from .html_zones import ZONE_VARIANTS
from .model import Frame, FrameVariant, Marker, Node, Shape, Tone
from .theme import load_theme

LAYER_IDS = {"0", "1"}
PART_PREFIXES = ("strip-", "pill-", "detail-", "mark-", "name-", "chip")
BADGE_PREFIX = "badge-"
NODE_PREFIX = "node-"
TAB_PREFIX = "tab-"
FRAME_PREFIX = "frame-"
OPENED_LABEL_PREFIX = "label-frame-"
DFD_SHAPES = (Shape.DFD_PROCESS, Shape.DFD_STORE)
C4_SHAPES = (Shape.C4_BOX, Shape.C4_PERSON)
EXPLAIN_PARTED_SHAPES = (Shape.EXPLAIN_CARD, Shape.ROW_CARD)
CHIP_STEM = re.compile(r"chip(\d+)-")
TYPE_LINE_END = "]"  # the mono ``[Kind: technology]`` line of a C4 box ends here
C4_MIN_LINES = 2
TAG = re.compile(r"<[^>]+>")


def _style(cell: ET.Element) -> dict[str, str]:
    """Split the style of a cell into pairs."""
    pairs = {}
    for part in cell.get("style", "").split(";"):
        key, _, value = part.partition("=")
        if key:
            pairs[key] = value
    return pairs


def is_notation_part(cell: ET.Element, cells: dict[str, ET.Element]) -> bool:
    """Tell a cell that a data flow node, a BPMN node or a pool frame already holds.

    Args:
        cell: Any vertex cell.
        cells: Every cell of the file by id.

    Returns:
        True for a strip, a pill, a detail text or a mark inside a node of ours, for the tab of
        a pool and for the name pill of an opened-process frame.
    """
    ident = cell.get("id", "")
    parent = cells.get(cell.get("parent", ""))
    if parent is not None and parent.get("id") not in LAYER_IDS:
        parent_style = _style(parent)
        is_ours = FLOW_SHAPE_KEY in parent_style or FLOW_MARKERS_KEY in parent_style
        return is_ours and ident.startswith(PART_PREFIXES)
    if ident.startswith(BADGE_PREFIX):
        return NODE_PREFIX + ident.removeprefix(BADGE_PREFIX) in cells
    if ident.startswith(TAB_PREFIX):
        return FLOW_FRAME_KEY in _style(
            cells.get(FRAME_PREFIX + ident.removeprefix(TAB_PREFIX), cell)
        )
    return (
        ident.startswith(OPENED_LABEL_PREFIX)
        and FRAME_PREFIX + ident.removeprefix(OPENED_LABEL_PREFIX) in cells
    )


def is_notation_frame(style: dict[str, str]) -> bool:
    """Tell a cell that was written as a pool, a black-box pool or an opened-process frame."""
    return FLOW_FRAME_KEY in style


def notation_frame(frame: Frame, style: dict[str, str], cells: dict[str, ET.Element]) -> Frame:
    """Give a frame read from a cell its variant and its tone and label.

    Args:
        frame: The frame as read from the plain cell.
        style: The style of the cell.
        cells: Every cell of the file by id.

    Returns:
        The frame as a pool, a black-box pool or an opened-process frame.
    """
    variant = FrameVariant(style[FLOW_FRAME_KEY])
    stem = frame.id.removeprefix(FRAME_PREFIX)
    tab = cells.get(TAB_PREFIX + stem)
    label = frame.label
    if tab is not None:
        label = _text(tab) or label
    pill = cells.get(OPENED_LABEL_PREFIX + stem)
    if pill is not None:
        label = _text(pill) or label
    if variant in ZONE_VARIANTS:
        return _zone_frame(replace(frame, variant=variant, label=label), style)
    if variant is FrameVariant.STRIP:
        return replace(frame, variant=variant, label=label, tone=_pill_tone(pill) or frame.tone)
    return replace(frame, variant=variant, label=label, tone=_pill_tone(tab) or frame.tone)


def _zone_frame(frame: Frame, style: dict[str, str]) -> Frame:
    """Read the tone and the border of a cloud frame or an architecture layer from its style."""
    stroke = style.get("strokeColor", "").lower()
    tone = next(
        (name for name, colors in load_theme().tones.items() if colors.stroke.lower() == stroke),
        frame.tone,
    )
    return replace(frame, tone=tone, is_solid=style.get("dashed") == "0")


def _text(cell: ET.Element) -> str:
    """Return the text of a cell without markup, on one line."""
    return html.unescape(TAG.sub(" ", cell.get("value", ""))).strip()


def _pill_tone(cell: ET.Element | None) -> Tone | None:
    """Return the tone whose pill colour is the fill of a cell, or None."""
    if cell is None:
        return None
    fill = _style(cell).get("fillColor", "").lower()
    for tone, colors in load_theme().tones.items():
        if colors.pill.lower() == fill:
            return tone
    return None


def notation_node(node: Node, cell: ET.Element, cells: dict[str, ET.Element]) -> Node:
    """Give a node read from a plain cell the shape, the marks and the id it was drawn with.

    Args:
        node: The node as read from the plain cell.
        cell: The cell.
        cells: Every cell of the file by id.

    Returns:
        The node with its Flow shape, its BPMN marks, its number and its card text restored.
    """
    style = _style(cell)
    badge = cells.get(BADGE_PREFIX + cell.get("id", "").removeprefix(NODE_PREFIX))
    if badge is not None:
        node = replace(node, number=_text(badge))
    if FLOW_HOST_KEY in style:
        node = replace(node, host=style[FLOW_HOST_KEY])
    if FLOW_MARKERS_KEY in style:
        marks = tuple(Marker(name) for name in style[FLOW_MARKERS_KEY].split(",") if name)
        node = replace(node, markers=marks)
    shape = _flow_shape(style)
    if shape is None:
        return node
    node = replace(node, shape=shape)
    if shape in C4_SHAPES:
        return _c4_parts(node)
    if shape is Shape.WIDE_CARD:
        return _wide_parts(node, cell, cells)
    if shape in EXPLAIN_PARTED_SHAPES:
        return _explain_parts(node, cell, cells)
    return _dfd_parts(node, cell, cells) if _is_dfd(node) else node


def _flow_shape(style: dict[str, str]) -> Shape | None:
    """Return the Flow shape a cell was written from, or None."""
    name = style.get(FLOW_SHAPE_KEY)
    try:
        return Shape(name) if name else None
    except ValueError:
        return None


def _c4_parts(node: Node) -> Node:
    """Read the name, the type line and the sentence of a C4 box from its label."""
    lines = node.text
    if len(lines) < C4_MIN_LINES or not lines[1].startswith("["):
        return node
    type_line, _, rest = lines[1].partition(TYPE_LINE_END)
    sentence = tuple(line for line in (rest.strip(), *lines[2:]) if line)
    return replace(node, text=lines[:1], technology=type_line + TYPE_LINE_END, detail=sentence)


def _wide_parts(node: Node, cell: ET.Element, cells: dict[str, ET.Element]) -> Node:
    """Read the name and the detail of an illustrated architecture card from its parts."""
    stem = cell.get("id", "").removeprefix(NODE_PREFIX)
    pill, detail = cells.get(f"pill-{stem}"), cells.get(f"detail-{stem}")
    name = (_text(pill),) if pill is not None else node.text
    lines = (_text(detail),) if detail is not None else ()
    return replace(node, text=name, detail=lines)


def _explain_parts(node: Node, cell: ET.Element, cells: dict[str, ET.Element]) -> Node:
    """Read the name, the text and the chips of an explainer card or row from its parts."""
    stem = cell.get("id", "").removeprefix(NODE_PREFIX)
    name = cells.get(f"pill-{stem}")
    if name is None:
        name = cells.get(f"name-{stem}")
    detail = cells.get(f"detail-{stem}")
    chips = sorted(
        (int(found.group(1)), _text(part))
        for ident, part in cells.items()
        if (found := CHIP_STEM.match(ident)) and ident.endswith(f"-{stem}")
    )
    is_mono = name is not None and load_theme().fonts.mono in _style(name).get("fontFamily", "")
    return replace(
        node,
        text=(_text(name),) if name is not None else node.text,
        detail=(_text(detail),) if detail is not None else (),
        chips=tuple(text for _index, text in chips),
        is_mono=is_mono,
    )


def _is_dfd(node: Node) -> bool:
    """Tell a node that is one of the three data flow shapes."""
    return node.shape in DFD_SHAPES or node.shape is Shape.ENTITY


def _dfd_parts(node: Node, cell: ET.Element, cells: dict[str, ET.Element]) -> Node:
    """Read the id, the name and the detail of a data flow node from its label and its parts."""
    stem = cell.get("id", "").removeprefix(NODE_PREFIX)
    strip, pill, detail = (cells.get(f"{name}-{stem}") for name in ("strip", "pill", "detail"))
    if pill is not None:
        small = _text(detail) if detail is not None else ""
        if node.shape is Shape.ENTITY:
            return replace(node, card=True, number=small or None, text=(_text(pill),))
        number = _text(strip) if strip is not None else None
        return replace(node, card=True, number=number, text=(_text(pill),), detail=(small,))
    if strip is not None:
        return replace(node, number=_text(strip), text=node.text[:1], detail=node.text[1:])
    return replace(node, number=node.text[0], text=node.text[1:]) if len(node.text) > 1 else node
