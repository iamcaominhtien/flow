"""The draw.io cells of the data flow shapes, the BPMN marks and the pool and opened frames.

The cells that sit on a node (a strip, an id cell, an icon, a mark) are children of the node's
cell, so they move with it. Our own style keys (``flowShape``, ``flowMarkers``, ``flowFrame``)
let the importer read the shape back.
"""

import base64
import xml.etree.ElementTree as ET

from .drawio_common import (
    FLOW_FRAME_KEY,
    FLOW_HOST_KEY,
    FLOW_MARKERS_KEY,
    FLOW_SHAPE_KEY,
    FONT_BOLD,
    add_geometry,
    add_vertex,
    style_string,
)
from .drawio_zones import add_zone_frame
from .html_zones import ZONE_VARIANTS
from .marks import mark_slots, mark_svg
from .markup import esc, fmt
from .model import Frame, FrameVariant, Node, Shape, Tone
from .sizing import estimate_text_width
from .theme import Theme, detailed_icon_svg, has_detailed_icon, icon_svg

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
NOTATION_SHAPES = (Shape.TASK, Shape.START, Shape.END, Shape.INTERMEDIATE)  # round trip by key
PILL_ARC_PERCENT = 50
STRIP_INSET_PX = 2
STRIP_TEXT_INSET_PX = 8
CARD_PADDING_PX = 16
CARD_PILL_HEIGHT_PX = 26
CARD_PILL_PADDING_PX = 12
CARD_ICON_PX = 64
STORE_ICON_PX = 52
CARD_TEXT_GAP_PX = 10
CARD_DETAIL_FRACTION = 0.55
PLAIN_ICON_RIGHT_PX = 16
ID_SPAN_STYLE = "font-size:{size}px;font-weight:normal;color:{color}"
DETAIL_SPAN_STYLE = "font-size:{size}px;font-weight:normal;color:{color}"
BAND_FONT_SIZE_PX = 13
BAND_STROKE_WIDTH_PX = 1.5
SYSTEM_ARC_PERCENT = 3
SYSTEM_LABEL_INSET_PX = 20
SYSTEM_FONT_SIZE_PX = 15
OPENED_PILL_FONT_SIZE_PX = 11
OPENED_PILL_PADDING_PX = 12
OPENED_DASH_PATTERN = "4 3"
POOL_ARC_PERCENT = 4


def _data_uri(svg: str) -> str:
    """Return the ``image`` style value of an SVG: a data URI without the ``base64`` keyword."""
    return "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()


def _image_cell(root: ET.Element, cell_id: str, parent: str, svg: str) -> ET.Element:
    """Add an image cell, as a child of ``parent``, that shows an SVG."""
    cell = add_vertex(root, cell_id, "", style_string({"shape": "image", "image": _data_uri(svg)}))
    cell.set("parent", parent)
    return cell


def _tone(node: Node) -> Tone:
    """Return the tone of a node, gray when it has none."""
    return node.tone or Tone.GRAY


def dfd_style(node: Node, theme: Theme) -> dict[str, object]:
    """Return the style pairs that place the label of a data flow node and mark its shape.

    Args:
        node: A process, a store or an entity with an id.
        theme: The design tokens.

    Returns:
        Style pairs to add to the node's style.
    """
    rules = theme.dfd
    pairs: dict[str, object] = {FLOW_SHAPE_KEY: node.shape.value, "verticalAlign": "middle"}
    if node.card:
        return {**pairs, "fontStyle": 0}
    if node.shape is Shape.DFD_PROCESS:
        pairs["spacingTop"] = rules.strip_height
    elif node.shape is Shape.DFD_STORE:
        pairs.update({"align": "left", "spacingLeft": rules.id_cell_width + CARD_PADDING_PX})
    else:
        left = rules.entity_text_left if node.icon else CARD_PADDING_PX
        pairs.update({"align": "left", "spacingLeft": left})
    return pairs


def dfd_value(node: Node, theme: Theme) -> str:
    """Return the label of a data flow node: its name, with an id or a detail on a small line."""
    if node.card:
        return ""
    name = "<br>".join(esc(line) for line in node.text)
    if node.shape is Shape.DFD_STORE:
        return name
    small = ID_SPAN_STYLE.format(size=theme.dfd.entity_id_font_size, color=theme.slate)
    if node.shape is Shape.ENTITY:
        return f'<span style="{small}">{esc(node.number or "")}</span><br>{name}'
    if not node.detail:
        return name
    detail = DETAIL_SPAN_STYLE.format(size=theme.layout.detail_font_size, color=theme.slate)
    lines = "<br>".join(esc(line) for line in node.detail)
    return f'{name}<br><span style="{detail}">{lines}</span>'


def add_dfd_parts(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the child cells of a data flow node: strip or id cell, and the card parts or icon."""
    if node.shape is Shape.DFD_PROCESS:
        _add_strip(root, node, theme)
    elif node.shape is Shape.DFD_STORE:
        _add_id_cell(root, node, theme)
    if node.card:
        _add_card(root, node, theme)
    elif node.icon:
        _add_plain_icon(root, node, theme)


def _text_cell_style(theme: Theme, size: float, bold: bool) -> str:
    """Return the style of a text-only child cell."""
    return style_string(
        {
            "text": "",
            "html": 1,
            "whiteSpace": "wrap",
            "align": "left",
            "verticalAlign": "middle",
            "strokeColor": "none",
            "fillColor": "none",
            "fontSize": fmt(size),
            "fontStyle": FONT_BOLD if bold else 0,
            "fontColor": theme.ink,
            "fontFamily": theme.fonts.sans,
        }
    )


def _add_strip(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the header strip of a process, with its number as the label."""
    tone = theme.tones[_tone(node)]
    style = style_string(
        {
            "shape": "partialRectangle",
            "top": 0,
            "left": 0,
            "right": 0,
            "bottom": 1,
            "html": 1,
            "align": "left",
            "verticalAlign": "middle",
            "spacingLeft": STRIP_TEXT_INSET_PX,
            "fillColor": tone.pill,
            "strokeColor": theme.shapes[node.shape].stroke,
            "strokeWidth": fmt(theme.shapes[node.shape].stroke_width),
            "fontSize": fmt(theme.dfd.id_font_size),
            "fontStyle": FONT_BOLD,
            "fontColor": theme.ink,
            "fontFamily": theme.fonts.mono,
        }
    )
    cell = add_vertex(root, f"strip-{node.id}", esc(node.number or ""), style)
    cell.set("parent", f"node-{node.id}")
    add_geometry(
        cell,
        (
            STRIP_INSET_PX,
            STRIP_INSET_PX,
            node.width - 2 * STRIP_INSET_PX,
            theme.dfd.strip_height - STRIP_INSET_PX,
        ),
    )


def _add_id_cell(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the id cell of a store: a tinted block at the left with the id in it."""
    tone = theme.tones[_tone(node)]
    style = style_string(
        {
            "shape": "partialRectangle",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "right": 1,
            "html": 1,
            "fillColor": tone.pill,
            "strokeColor": theme.shapes[node.shape].stroke,
            "strokeWidth": fmt(theme.shapes[node.shape].stroke_width),
            "fontSize": fmt(theme.dfd.id_font_size),
            "fontStyle": FONT_BOLD,
            "fontColor": theme.ink,
            "fontFamily": theme.fonts.mono,
        }
    )
    cell = add_vertex(root, f"strip-{node.id}", esc(node.number or ""), style)
    cell.set("parent", f"node-{node.id}")
    add_geometry(cell, (STRIP_INSET_PX, STRIP_INSET_PX, theme.dfd.id_cell_width, node.height - 4))


def _icon_svg(node: Node, theme: Theme, size: float) -> str:
    """Return the SVG of the icon of a node, detailed on a card when there is a detailed one."""
    icon = node.icon or ""
    attrs = f'xmlns="{SVG_NAMESPACE}"'
    if (node.card or node.shape is Shape.ENTITY) and has_detailed_icon(icon):
        return detailed_icon_svg(icon, size, theme.tones[_tone(node)].stroke, attrs)
    return icon_svg(icon, size, theme.shapes[node.shape].stroke, attrs)


def _add_plain_icon(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the small icon of a plain node: at the left of an entity, at the right of a store."""
    rules = theme.dfd
    size = rules.entity_icon
    if node.shape is Shape.ENTITY:
        left = CARD_PADDING_PX
    else:
        left = node.width - PLAIN_ICON_RIGHT_PX - size
    top = rules.strip_height + (node.height - rules.strip_height - size) / 2
    if node.shape is not Shape.DFD_PROCESS:
        top = (node.height - size) / 2
    cell = _image_cell(root, f"icon-{node.id}", f"node-{node.id}", _icon_svg(node, theme, size))
    add_geometry(cell, (left, top, size, size))


def _add_card(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the pill, the small text and the large icon of an illustrated data flow node."""
    parent = f"node-{node.id}"
    is_process = node.shape is Shape.DFD_PROCESS
    is_store = node.shape is Shape.DFD_STORE
    top = theme.dfd.strip_height + 2 if is_process else 0
    if is_store:
        _add_store_card_name(root, node, theme)
    else:
        _add_pill(root, node, theme, top + CARD_PADDING_PX - 2)
        lines = node.detail if is_process else (node.number or "",)
        _add_card_lines(root, node, theme, (top + CARD_PADDING_PX + CARD_PILL_HEIGHT_PX, lines))
    size = STORE_ICON_PX if is_store else CARD_ICON_PX
    if node.icon:
        cell = _image_cell(root, f"icon-{node.id}", parent, _icon_svg(node, theme, size))
        icon_top = top + (node.height - top - size) / 2
        add_geometry(cell, (node.width - CARD_PADDING_PX - size, icon_top, size, size))


def _add_store_card_name(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add the name of an illustrated store, left of its icon and right of its id cell."""
    style = _text_cell_style(theme, node.font_size, bold=True)
    cell = add_vertex(root, f"pill-{node.id}", esc(" ".join(node.text)), style)
    cell.set("parent", f"node-{node.id}")
    left = theme.dfd.id_cell_width + CARD_PADDING_PX
    add_geometry(cell, (left, 0, node.width - left - STORE_ICON_PX - CARD_PADDING_PX, node.height))


def _add_pill(root: ET.Element, node: Node, theme: Theme, top: float) -> None:
    """Add the name of a card as a pill at its left."""
    tone = theme.tones[_tone(node)]
    style = style_string(
        {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "html": 1,
            "fillColor": tone.pill,
            "strokeColor": theme.shapes[node.shape].stroke,
            "strokeWidth": fmt(theme.shapes[node.shape].stroke_width),
            "fontColor": theme.ink,
            "fontSize": fmt(node.font_size),
            "fontStyle": FONT_BOLD,
            "fontFamily": theme.fonts.sans,
        }
    )
    name = " ".join(node.text)
    width = estimate_text_width(name, theme.layout, node.font_size) + 2 * CARD_PILL_PADDING_PX
    cell = add_vertex(root, f"pill-{node.id}", esc(name), style)
    cell.set("parent", f"node-{node.id}")
    add_geometry(cell, (CARD_PADDING_PX, top, width, CARD_PILL_HEIGHT_PX))


def _add_card_lines(
    root: ET.Element, node: Node, theme: Theme, where: tuple[float, tuple[str, ...]]
) -> None:
    """Add the small text under the pill of a card.

    Args:
        root: The ``root`` element of the diagram.
        node: The card.
        theme: The design tokens.
        where: The top of the pill's bottom edge and the lines of text.
    """
    top, lines = where
    if not any(lines):
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
        }
    )
    cell = add_vertex(root, f"detail-{node.id}", "<br>".join(esc(line) for line in lines), style)
    cell.set("parent", f"node-{node.id}")
    width = node.width * CARD_DETAIL_FRACTION
    add_geometry(cell, (CARD_PADDING_PX, top + CARD_TEXT_GAP_PX, width, node.height - top))


def marks_style(node: Node) -> dict[str, object]:
    """Return the style pairs that record the BPMN shape, marks and task of a node, or nothing."""
    pairs: dict[str, object] = {}
    if node.shape in NOTATION_SHAPES or node.markers:
        pairs[FLOW_SHAPE_KEY] = node.shape.value
    if node.markers:
        pairs[FLOW_MARKERS_KEY] = ",".join(marker.value for marker in node.markers)
    if node.host:
        pairs[FLOW_HOST_KEY] = node.host
    return pairs


def add_marks(root: ET.Element, node: Node, theme: Theme) -> None:
    """Add each BPMN mark of a node as an image cell inside it."""
    rules = theme.bpmn
    stroke = theme.ink if node.shape is Shape.TASK else theme.shapes[node.shape].stroke
    slots = mark_slots(node, rules.marker_extent, rules.task_marker_inset, rules.bottom_marker_gap)
    for index, slot in enumerate(slots):
        svg = mark_svg(slot.marker, slot.size, (stroke, theme.paper), f'xmlns="{SVG_NAMESPACE}"')
        cell = _image_cell(root, f"mark-{node.id}-{index}", f"node-{node.id}", svg)
        add_geometry(cell, (slot.x, slot.y, slot.size, slot.size))


def add_band_frame(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a pool, a black-box pool or an opened-process frame."""
    if frame.variant in ZONE_VARIANTS:
        add_zone_frame(root, frame, theme)
    elif frame.variant is FrameVariant.POOL:
        _add_pool(root, frame, theme)
    elif frame.variant is FrameVariant.BLACK_BOX:
        _add_black_box(root, frame, theme)
    elif frame.variant is FrameVariant.SYSTEM:
        _add_system(root, frame, theme)
    else:
        _add_opened(root, frame, theme)


def _add_pool(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a pool: a white box and a coloured band on its left with the name written upright."""
    box = style_string(
        {
            FLOW_FRAME_KEY: frame.variant.value,
            "rounded": 0,
            "html": 1,
            "fillColor": theme.paper,
            "strokeColor": theme.ink,
            "strokeWidth": BAND_STROKE_WIDTH_PX,
        }
    )
    add_geometry(
        add_vertex(root, f"frame-{frame.id}", "", box),
        (frame.x, frame.y, frame.width, frame.height),
    )
    band = style_string(
        {
            "rounded": 0,
            "html": 1,
            "fillColor": theme.tones[frame.tone].pill,
            "strokeColor": theme.ink,
            "strokeWidth": BAND_STROKE_WIDTH_PX,
            "fontColor": theme.ink,
            "fontStyle": FONT_BOLD,
            "fontSize": BAND_FONT_SIZE_PX,
            "fontFamily": theme.fonts.sans,
            "horizontal": 0,
            "whiteSpace": "wrap",
        }
    )
    cell = add_vertex(root, f"tab-{frame.id}", esc(frame.label or ""), band)
    add_geometry(cell, (frame.x, frame.y, theme.bpmn.band_width, frame.height))


def _add_black_box(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a black-box pool: a filled, rounded bar with its name in the middle."""
    style = style_string(
        {
            FLOW_FRAME_KEY: frame.variant.value,
            "rounded": 1,
            "arcSize": POOL_ARC_PERCENT,
            "html": 1,
            "fillColor": theme.tones[frame.tone].pill,
            "strokeColor": theme.ink,
            "strokeWidth": BAND_STROKE_WIDTH_PX,
            "fontColor": theme.ink,
            "fontStyle": FONT_BOLD,
            "fontSize": BAND_FONT_SIZE_PX,
            "fontFamily": theme.fonts.sans,
        }
    )
    cell = add_vertex(root, f"frame-{frame.id}", esc(frame.label or ""), style)
    add_geometry(cell, (frame.x, frame.y, frame.width, frame.height))


def _add_system(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add the system of a use case diagram: a white container whose name is at its top left."""
    style = style_string(
        {
            FLOW_FRAME_KEY: frame.variant.value,
            "rounded": 1,
            "arcSize": SYSTEM_ARC_PERCENT,
            "container": 1,
            "collapsible": 0,
            "html": 1,
            "align": "left",
            "verticalAlign": "top",
            "spacingLeft": SYSTEM_LABEL_INSET_PX,
            "spacingTop": SYSTEM_LABEL_INSET_PX // 2,
            "fillColor": theme.paper,
            "strokeColor": theme.ink,
            "strokeWidth": BAND_STROKE_WIDTH_PX,
            "fontColor": theme.ink,
            "fontStyle": FONT_BOLD,
            "fontSize": SYSTEM_FONT_SIZE_PX,
            "fontFamily": theme.fonts.sans,
        }
    )
    cell = add_vertex(root, f"frame-{frame.id}", esc(frame.label or ""), style)
    add_geometry(cell, (frame.x, frame.y, frame.width, frame.height))


def _add_opened(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add the dashed frame of an opened process, and its name in a pill on the bottom edge."""
    tone = theme.tones[frame.tone]
    style = style_string(
        {
            FLOW_FRAME_KEY: frame.variant.value,
            "rounded": 1,
            "arcSize": POOL_ARC_PERCENT,
            "dashed": 1,
            "dashPattern": OPENED_DASH_PATTERN,
            "container": 1,
            "collapsible": 0,
            "html": 1,
            "fillColor": tone.lane,
            "strokeColor": tone.stroke,
            "strokeWidth": BAND_STROKE_WIDTH_PX,
        }
    )
    add_geometry(
        add_vertex(root, f"frame-{frame.id}", "", style),
        (frame.x, frame.y, frame.width, frame.height),
    )
    rules = theme.dfd
    pill_style = style_string(
        {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "html": 1,
            "fillColor": tone.accent,
            "strokeColor": "none",
            "fontColor": theme.on_accent,
            "fontStyle": FONT_BOLD,
            "fontSize": OPENED_PILL_FONT_SIZE_PX,
            "fontFamily": theme.fonts.sans,
        }
    )
    label = frame.label or ""
    width = estimate_text_width(label, theme.layout, OPENED_PILL_FONT_SIZE_PX)
    width += 2 * OPENED_PILL_PADDING_PX
    cell = add_vertex(root, f"label-frame-{frame.id}", esc(label), pill_style)
    top = frame.y + frame.height - rules.frame_pill_height / 2
    add_geometry(cell, (frame.x + rules.frame_pill_inset, top, width, rules.frame_pill_height))
