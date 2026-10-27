"""Helpers shared by the parts of the draw.io renderer: styles, cells and geometry."""

import xml.etree.ElementTree as ET

from .markup import fmt

Bounds = tuple[float, float, float, float]  # x, y, width, height

ROOT_CELL_ID = "0"
LAYER_CELL_ID = "1"
FRAME_LABEL_PREFIX = "label-"  # a frame's name is a pill cell with this id prefix + the frame's id
FONT_BOLD = 1  # the draw.io ``fontStyle`` bit for bold
BOLD_FROM_WEIGHT = 600  # draw.io has no weights: a text of this weight or more is bold


def font_style(weight: int) -> int:
    """Return the draw.io ``fontStyle`` for a font weight: bold from 600, regular below."""
    return FONT_BOLD if weight >= BOLD_FROM_WEIGHT else 0


def style_string(parts: dict[str, object]) -> str:
    """Join style pairs into a draw.io style string, which ends with a semicolon.

    A pair whose value is empty is written as a bare key (``rhombus;``), which is how draw.io
    writes a shape name or a flag.
    """
    return "".join(f"{key}={value};" if value != "" else f"{key};" for key, value in parts.items())


def add_geometry(parent: ET.Element, bounds: Bounds) -> None:
    """Add the rectangle of a vertex cell, given as ``(x, y, width, height)``."""
    x, y, width, height = bounds
    ET.SubElement(
        parent,
        "mxGeometry",
        {"x": fmt(x), "y": fmt(y), "width": fmt(width), "height": fmt(height), "as": "geometry"},
    )


def add_vertex(root: ET.Element, cell_id: str, value: str, style: str) -> ET.Element:
    """Add a vertex cell to the diagram's layer and return it, so that its geometry can be added.

    Args:
        root: The ``root`` element of the diagram.
        cell_id: A unique cell id.
        value: The label, already escaped for HTML.
        style: The draw.io style string.

    Returns:
        The new ``mxCell`` element.
    """
    attributes = {"id": cell_id, "value": value, "style": style, "vertex": "1"}
    attributes["parent"] = LAYER_CELL_ID
    return ET.SubElement(root, "mxCell", attributes)


FLOW_SHAPE_KEY = "flowShape"  # a style key of ours: the Flow shape a cell was drawn from
FLOW_MARKERS_KEY = "flowMarkers"  # a style key of ours: the BPMN marks of a node, comma-joined
FLOW_FRAME_KEY = "flowFrame"  # a style key of ours: the frame variant a cell was drawn from
FLOW_HOST_KEY = "flowHost"  # a style key of ours: the id of the task a boundary event sits on
FLOW_ROLE_KEY = "flowRole"  # a style key of ours: the role of a line of a planning diagram
