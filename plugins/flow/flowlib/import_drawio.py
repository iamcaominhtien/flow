"""Read a ``.drawio`` file into a scene, as well as the shapes and lines allow.

The file may be one Flow wrote or one drawn by hand in draw.io. Top-level boxes become nodes
(the shape is guessed from the style), swimlanes become frames, and connected edges become
lines. Whatever cannot be carried over is counted in the notes the caller shows to the user.
"""

import base64
import html
import re
import urllib.parse
import zlib
from dataclasses import dataclass, field, replace
from pathlib import Path
from xml.etree import ElementTree as ET

from .canvas import fit_canvas
from .drawio_common import FRAME_LABEL_PREFIX
from .geometry import border_point, center_of
from .import_screen import (
    CHIP_PREFIX,
    attach_words,
    is_edge_words,
    is_screen_part,
    label_kind,
    line_role,
    screen_node,
    words_kind,
)
from .model import (
    Edge,
    EdgeLabel,
    Frame,
    Head,
    Node,
    Point,
    Row,
    Scene,
    Shape,
    Tone,
)
from .reader import SpecError
from .theme import load_theme

TITLE_CELL_ID = "title"
DESCRIPTION_CELL_ID = "description"
LAYER_IDS = {"0", "1"}
BORDER_TOLERANCE_PX = 1.0
MARGIN_PX = 64.0
TITLE_ROOM_PX = 100.0
MARK_MAX_SIZE_PX = 48.0
PILL_ARC_PERCENT = 50
DEFAULT_FONT_SIZE_PX = 13.0
ARROW_NAMES = {
    "ERone": Head.ONE,
    "ERmany": Head.MANY,
    "ERmandOne": Head.ONE_ONLY,
    "ERzeroToOne": Head.ZERO_ONE,
    "ERzeroToMany": Head.ZERO_MANY,
    "ERoneToMany": Head.ONE_MANY,
    "none": Head.NONE,
}
SHAPE_NAMES = {
    "parallelogram": Shape.IO,
    "document": Shape.DOCUMENT,
    "hexagon": Shape.PREPARATION,
    "process": Shape.SUBPROCESS,
    "cylinder3": Shape.CYLINDER,
    "cylinder": Shape.CYLINDER,
    "actor": Shape.ACTOR,
    "umlActor": Shape.ACTOR,
}
Box = tuple[float, float, float, float]  # x, y, width, height
LINE_BREAK = re.compile(r"<br\s*/?>|</div>|</p>", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")
CHIP_SPAN = re.compile(r'<span style="background:[^"]*">([A-Z]{2})</span>')  # a key chip in a row
TABLE_CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
ROW_COLUMNS = 2
KEYED_ROW_COLUMNS = 3  # a row of a table that has a key column starts with the chips


@dataclass(frozen=True)
class ImportResult:
    """A scene read from a file, and what could not be carried over."""

    scene: Scene
    notes: tuple[str, ...]


def parse_style(style: str) -> dict[str, str]:
    """Split a draw.io style string into pairs; a bare word gets the value ``""``.

    Args:
        style: The ``style`` attribute of a cell, such as ``rounded=1;fillColor=#fff;ellipse;``.

    Returns:
        Key to value.
    """
    pairs = {}
    for part in style.split(";"):
        if not part:
            continue
        key, _, value = part.partition("=")
        pairs[key] = value
    return pairs


def plain_lines(value: str) -> tuple[str, ...]:
    """Turn a cell value, which may hold HTML, into lines of plain text.

    Args:
        value: The ``value`` attribute of a cell.

    Returns:
        The non-empty lines.
    """
    text = html.unescape(TAG.sub("", LINE_BREAK.sub("\n", value)))
    return tuple(line.strip() for line in text.splitlines() if line.strip())


def read_graph(path: Path) -> ET.Element:
    """Return the ``mxGraphModel`` of the first page of a file, unpacking it when compressed.

    Args:
        path: A ``.drawio`` file.

    Returns:
        The ``mxGraphModel`` element.

    Raises:
        SpecError: If the file is not XML or holds no diagram.
    """
    try:
        document = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError as error:
        raise SpecError([f"{path} is not XML: {error}"]) from error
    diagram = document if document.tag == "diagram" else document.find("diagram")
    if document.tag == "mxGraphModel":
        return document
    if diagram is None:
        raise SpecError([f"{path} holds no diagram"])
    model = diagram.find("mxGraphModel")
    if model is not None:
        return model
    return _unpack(diagram.text or "", path)


def _unpack(packed: str, path: Path) -> ET.Element:
    """Decode the compressed text draw.io stores inside a ``diagram`` element."""
    try:
        inflated = zlib.decompress(base64.b64decode(packed.strip()), -zlib.MAX_WBITS)
        return ET.fromstring(urllib.parse.unquote(inflated.decode("utf-8")))
    except (ValueError, zlib.error, ET.ParseError) as error:
        raise SpecError([f"{path}: the diagram is not readable ({error})"]) from error


def _bounds(cell: ET.Element) -> Box | None:
    """Return a cell's x, y, width and height as written, or None when it has no geometry."""
    geometry = cell.find("mxGeometry")
    if geometry is None:
        return None
    x, y, width, height = (float(geometry.get(key, 0)) for key in ("x", "y", "width", "height"))
    return (x, y, width, height)


def _shape_of(style: dict[str, str], width: float, height: float) -> Shape:
    """Guess the flowchart shape that looks most like a draw.io style."""
    if style.get("flowFork") == "1":
        return Shape.FORK
    if "rhombus" in style:
        return Shape.DECISION
    if "ellipse" in style:
        small = max(width, height) <= MARK_MAX_SIZE_PX
        return Shape.CONNECTOR if small else Shape.ELLIPSE
    named = SHAPE_NAMES.get(style.get("shape", ""))
    if named is not None:
        return named
    if style.get("rounded") == "1" and style.get("arcSize") == str(PILL_ARC_PERCENT):
        return Shape.TERMINATOR
    return Shape.PROCESS


def _tone_of(fill: str | None) -> Tone | None:
    """Return the tone whose box colour is ``fill``, or None."""
    if fill is None:
        return None
    for tone, colors in load_theme().tones.items():
        if colors.box.lower() == fill.lower():
            return tone
    return None


def _is_label_only(style: dict[str, str]) -> bool:
    """Tell a free text cell from a box: it has a text style or no outline and no fill."""
    return "text" in style or (
        style.get("strokeColor") == "none" and style.get("fillColor", "none") == "none"
    )


def _node(cell: ET.Element, style: dict[str, str], box: Box) -> Node:
    """Build a node from a vertex cell that sits at ``box``."""
    x, y, width, height = box
    return Node(
        id=cell.get("id", ""),
        shape=_shape_of(style, width, height),
        x=x,
        y=y,
        width=width,
        height=height,
        text=plain_lines(cell.get("value", "")),
        icon=None,
        tone=_tone_of(style.get("fillColor")),
        number=None,
        font_size=float(style.get("fontSize", DEFAULT_FONT_SIZE_PX)),
    )


def _frame_label_cell(cell: ET.Element, cells: dict[str, ET.Element]) -> ET.Element | None:
    """Return the pill cell that holds the name of a container cell, if the file has one."""
    return cells.get(f"{FRAME_LABEL_PREFIX}{cell.get('id', '')}")


def _is_frame_label(cell: ET.Element, cells: dict[str, ET.Element]) -> bool:
    """Tell a pill cell that names a container; the frame holds its text."""
    ident = cell.get("id", "")
    return ident.startswith(FRAME_LABEL_PREFIX) and ident.removeprefix(FRAME_LABEL_PREFIX) in cells


def _frame(cell: ET.Element, style: dict[str, str], box: Box) -> Frame:
    """Build a frame from a container cell that sits at ``box``."""
    x, y, width, height = box
    lines = plain_lines(cell.get("value", ""))
    return Frame(
        id=cell.get("id", ""),
        x=x,
        y=y,
        width=width,
        height=height,
        label=lines[0] if lines else None,
        tone=_tone_of(style.get("fillColor")) or Tone.GRAY,
    )


def _terminal_point(cell: ET.Element, name: str, offset: Point) -> Point | None:
    """Return the ``sourcePoint`` or ``targetPoint`` of an edge, moved by ``offset``."""
    point = cell.find(f"mxGeometry/mxPoint[@as='{name}']")
    if point is None:
        return None
    return (float(point.get("x", 0)) + offset[0], float(point.get("y", 0)) + offset[1])


def _waypoints(cell: ET.Element, offset: Point) -> list[Point]:
    """Return the bend points of an edge, moved by ``offset``."""
    return [
        (float(point.get("x", 0)) + offset[0], float(point.get("y", 0)) + offset[1])
        for point in cell.findall("mxGeometry/Array/mxPoint")
    ]


def _route(cell: ET.Element, nodes: dict[str, Node], offset: Point) -> tuple[Point, ...] | None:
    """Return the points of an edge from box border to box border, or None if it has no ends."""
    source, target = nodes.get(cell.get("source", "")), nodes.get(cell.get("target", ""))
    bends = _waypoints(cell, offset)
    start = _terminal_point(cell, "sourcePoint", offset)
    end = _terminal_point(cell, "targetPoint", offset)
    if source is not None and not _is_on_border(start, source):
        aim = bends[0] if bends else (center_of(target) if target else end)
        start = border_point(source, aim) if aim else None
    if target is not None and not _is_on_border(end, target):
        aim = bends[-1] if bends else (center_of(source) if source else start)
        end = border_point(target, aim) if aim else None
    if start is None or end is None:
        return None
    return (start, *bends, end)


def _is_on_border(point: Point | None, node: Node) -> bool:
    """Tell whether a point lies on the border of a node, as the ends of a Flow line do."""
    if point is None:
        return False
    inside_x = node.x - BORDER_TOLERANCE_PX <= point[0] <= node.x + node.width + BORDER_TOLERANCE_PX
    inside_y = (
        node.y - BORDER_TOLERANCE_PX <= point[1] <= node.y + node.height + BORDER_TOLERANCE_PX
    )
    near_x = min(abs(point[0] - node.x), abs(point[0] - node.x - node.width)) <= BORDER_TOLERANCE_PX
    near_y = (
        min(abs(point[1] - node.y), abs(point[1] - node.y - node.height)) <= BORDER_TOLERANCE_PX
    )
    return inside_x and inside_y and (near_x or near_y)


def _middle(points: tuple[Point, ...]) -> Point:
    """Return the centre of the middle segment of a line."""
    index = (len(points) - 1) // 2
    (x1, y1), (x2, y2) = points[index], points[index + 1]
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def _edge(cell: ET.Element, nodes: dict[str, Node], offset: Point) -> Edge | None:
    """Build an edge from an edge cell, or None when its ends are not placed."""
    style = parse_style(cell.get("style", ""))
    points = _route(cell, nodes, offset)
    if points is None:
        return None
    lines = plain_lines(cell.get("value", ""))
    middle = _middle(points)
    label = EdgeLabel(" ".join(lines), middle, label_kind(style)) if lines else None
    return Edge(
        id=cell.get("id", ""),
        role=line_role(style),
        points=points,
        label=label,
        source=cell.get("source") if cell.get("source") in nodes else None,
        target=cell.get("target") if cell.get("target") in nodes else None,
        head=ARROW_NAMES.get(style.get("endArrow", "classic"), Head.FILLED),
        tail=ARROW_NAMES.get(style.get("startArrow", "none"), Head.NONE),
        dashed=style.get("dashed") == "1",
    )


def _table_rows(cells: list[ET.Element]) -> tuple[Row, ...]:
    """Read the rows of a table node from its child cells.

    A row is a one-line table of two or three cells: the key chips (when the table has a key
    column), the name, and the type on the right.
    """
    rows = []
    for cell in cells:
        value = cell.get("value", "")
        flags = tuple(CHIP_SPAN.findall(value))
        columns = [plain_lines(CHIP_SPAN.sub("", match)) for match in TABLE_CELL.findall(value)]
        if len(columns) == KEYED_ROW_COLUMNS:
            columns = columns[1:]
        if len(columns) == ROW_COLUMNS:
            rows.append(Row(" ".join(columns[0]).strip(), " ".join(columns[1]), flags))
        else:
            rows.append(Row(" ".join(plain_lines(CHIP_SPAN.sub("", value))).strip(), flags=flags))
    return tuple(rows)


@dataclass
class _Import:
    """What is collected while the cells of a file are read."""

    cells: dict[str, ET.Element]
    offset: Point = (0.0, 0.0)
    nodes: dict[str, Node] = field(default_factory=dict)
    frames: list[Frame] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    skipped_images: int = 0

    def children(self, parent: ET.Element) -> list[ET.Element]:
        """Return the vertex cells whose parent is a cell."""
        return [
            cell
            for cell in self.cells.values()
            if cell.get("parent") == parent.get("id") and cell.get("vertex") == "1"
        ]

    def box(self, cell: ET.Element) -> Box:
        """Return where a cell sits on the page, adding the position of the cells around it."""
        x, y, width, height = _bounds(cell) or (0.0, 0.0, 0.0, 0.0)
        parent = self.cells.get(cell.get("parent", ""))
        while parent is not None and parent.get("id") not in LAYER_IDS:
            outer = _bounds(parent) or (0.0, 0.0, 0.0, 0.0)
            x, y = x + outer[0], y + outer[1]
            parent = self.cells.get(parent.get("parent", ""))
        return (x + self.offset[0], y + self.offset[1], width, height)

    def add_vertex(self, cell: ET.Element) -> None:
        """Turn one vertex cell into a node or a frame, or note why it is left out."""
        style = parse_style(cell.get("style", ""))
        rows = [c for c in self.children(cell) if _is_table_row(c, self.cells)]
        if "swimlane" in style and rows:
            node = _node(cell, style, self.box(cell))
            self.nodes[node.id] = replace(node, shape=Shape.TABLE, sections=(_table_rows(rows),))
        elif "swimlane" in style or style.get("container") == "1":
            self.frames.append(_frame(cell, style, self.box(cell)))
            pill = _frame_label_cell(cell, self.cells)
            if pill is not None:
                label = plain_lines(pill.get("value", ""))
                self.frames[-1] = replace(self.frames[-1], label=label[0] if label else None)
        elif "image" in style.get("shape", ""):
            self.skipped_images += 1
        elif _is_label_only(style):
            self.notes.append(f"skipped the free text '{cell.get('value', '')[:30]}'")
        else:
            node = screen_node(_node(cell, style, self.box(cell)), style)
            self.nodes[node.id] = node


def _is_table_row(cell: ET.Element, cells: dict[str, ET.Element]) -> bool:
    """Tell a cell that is a row of a table, which the table node already holds."""
    parent = cells.get(cell.get("parent", ""))
    if parent is None or parent.get("id") in LAYER_IDS:
        return False
    return "swimlane" in parse_style(parent.get("style", "")) and _is_label_only(
        parse_style(cell.get("style", ""))
    )


def _origin(cells: list[ET.Element], has_title: bool) -> Point:
    """Return the offset that puts the top-left of the drawing at the page margin."""
    boxes = [bounds for cell in cells if (bounds := _bounds(cell))]
    top = MARGIN_PX + (TITLE_ROOM_PX if has_title else 0)
    if not boxes:
        return (0.0, 0.0)
    return (MARGIN_PX - min(box[0] for box in boxes), top - min(box[1] for box in boxes))


def _with_chips(cells: dict[str, ET.Element], nodes: dict[str, Node]) -> dict[str, Node]:
    """Give each node the chip that hangs on it, such as the event that decides a decision."""
    result = dict(nodes)
    for cell in cells.values():
        node = result.get(cell.get("parent", ""))
        box = _bounds(cell)
        if node is None or box is None or not cell.get("id", "").startswith(CHIP_PREFIX):
            continue
        text = " ".join(plain_lines(cell.get("value", "")))
        kind = label_kind(parse_style(cell.get("style", "")))
        at = (box[0] + box[2] / 2, box[1] + box[3] / 2)
        result[node.id] = replace(node, chip=EdgeLabel(text, at, kind))
    return result


def _edge_words(cells: dict[str, ET.Element], offset: Point) -> list[tuple[str, EdgeLabel]]:
    """Read the guard and effect text cells that are named after a line.

    Returns:
        The id of each line with the label found for it, placed on the page.
    """
    found = []
    for cell in cells.values():
        if cell.get("vertex") != "1" or not is_edge_words(cell):
            continue
        box = _bounds(cell)
        if box is None:
            continue
        centre = (box[0] + box[2] / 2 + offset[0], box[1] + box[3] / 2 + offset[1])
        style = parse_style(cell.get("style", ""))
        text = " ".join(plain_lines(cell.get("value", "")))
        owner = cell.get("id", "").rsplit("-end", 1)[0]
        found.append((owner, EdgeLabel(text, centre, words_kind(style))))
    return found


def convert(path: Path) -> ImportResult:
    """Read a ``.drawio`` file into a scene.

    Args:
        path: The file; a Flow file, or any draw.io file with boxes, containers and edges.

    Returns:
        The scene, and notes on what was skipped or guessed.

    Raises:
        SpecError: If the file cannot be read or holds nothing that can be drawn.
    """
    cells = {cell.get("id", ""): cell for cell in read_graph(path).iter("mxCell")}
    vertices = [c for c in cells.values() if c.get("vertex") == "1"]
    text_ids = (TITLE_CELL_ID, DESCRIPTION_CELL_ID)
    drawn = [
        c
        for c in vertices
        if c.get("id") not in text_ids
        and not _is_table_row(c, cells)
        and not _is_frame_label(c, cells)
        and not is_screen_part(c, cells, parse_style)
        and not is_edge_words(c)
    ]
    top_level = [c for c in drawn if c.get("parent") in LAYER_IDS]
    texts = {name: plain_lines(cells[name].get("value", "")) for name in text_ids if name in cells}
    state = _Import(cells, _origin(top_level, bool(texts.get(TITLE_CELL_ID))))
    for cell in drawn:
        state.add_vertex(cell)
    if not state.nodes:
        raise SpecError([f"{path} holds no boxes that can be drawn"])
    if state.skipped_images:
        state.notes.append(f"skipped {state.skipped_images} images (icons are not read back)")
    edges = []
    for cell in (c for c in cells.values() if c.get("edge") == "1"):
        edge = _edge(cell, state.nodes, state.offset)
        if edge is None:
            state.notes.append(f"skipped the edge '{cell.get('id')}': its ends are not placed")
        else:
            edges.append(edge)
    edges = attach_words(edges, _edge_words(cells, state.offset))
    state.nodes = _with_chips(cells, state.nodes)
    scene = Scene(
        width=0,
        height=0,
        title=" ".join(texts[TITLE_CELL_ID]) if texts.get(TITLE_CELL_ID) else None,
        description=" ".join(texts[DESCRIPTION_CELL_ID])
        if texts.get(DESCRIPTION_CELL_ID)
        else None,
        frames=tuple(state.frames),
        nodes=tuple(state.nodes.values()),
        edges=tuple(edges),
    )
    return ImportResult(fit_canvas(scene), tuple(state.notes))
