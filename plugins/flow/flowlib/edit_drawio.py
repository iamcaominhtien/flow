"""Change an existing ``.drawio`` file in place: move, resize, rename, recolour, add and delete.

The file is edited as XML, so everything an operation does not name stays as it was: other
pages, styles, custom shapes and cells this module does not understand. A list of operations is
checked as a whole before the first one runs.

An operation is a JSON object with an ``op``:

    {"op": "set_text", "id": "node-api", "text": "API v2"}
    {"op": "move", "id": "node-api", "x": 300, "y": 120}
    {"op": "resize", "id": "node-api", "width": 200, "height": 64}
    {"op": "tone", "id": "node-api", "tone": "green"}
    {"op": "set_style", "id": "node-api", "key": "dashed", "value": "1"}   (null removes a key)
    {"op": "delete", "id": "node-api"}
    {"op": "add_node", "id": "cache", "text": "Cache", "x": 400, "y": 200,
     "shape": "process", "tone": "blue"}
    {"op": "add_edge", "id": "api-cache", "from": "node-api", "to": "node-cache", "label": "reads"}
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .drawio_common import style_string
from .import_drawio import parse_style, read_graph
from .markup import esc, fmt
from .model import DEFAULT_FONT_SIZE_PX, Node, Role, Shape, Tone
from .reader import SpecError, suggestion
from .render_drawio import add_node
from .theme import Theme, load_theme

DEFAULT_WIDTH_PX = 160.0
DEFAULT_HEIGHT_PX = 56.0
MAX_OPERATIONS = 200
OP_KEYS = {
    "set_text": {"id", "text"},
    "move": {"id", "x", "y"},
    "resize": {"id", "width", "height"},
    "tone": {"id", "tone"},
    "set_style": {"id", "key", "value"},
    "delete": {"id"},
    "add_node": {"id", "text", "x", "y", "width", "height", "shape", "tone"},
    "add_edge": {"id", "from", "to", "label", "dashed"},
}
EXISTING_ID_OPS = {"set_text", "move", "resize", "tone", "set_style", "delete"}


@dataclass
class _Session:
    """The model being edited and what is known about it while operations are checked or run."""

    root: ET.Element
    theme: Theme
    cells: dict[str, ET.Element]
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def cell(self, name: object) -> ET.Element | None:
        """Return the cell with an id, or the one that Flow would have named ``node-<id>``."""
        if not isinstance(name, str):
            return None
        found = self.cells.get(name)
        return found if found is not None else self.cells.get(f"node-{name}")


def _children_of(session: _Session, parent_id: str) -> list[ET.Element]:
    """Return the cells whose parent is the cell with an id."""
    return [cell for cell in session.cells.values() if cell.get("parent") == parent_id]


def _bounds_of(cell: ET.Element) -> ET.Element:
    """Return the ``mxGeometry`` of a cell, adding an empty one when it has none."""
    geometry = cell.find("mxGeometry")
    if geometry is None:
        geometry = ET.SubElement(cell, "mxGeometry", {"as": "geometry"})
    return geometry


def _reroute_edges(session: _Session, cell_id: str) -> None:
    """Drop the stored bends of the edges that touch a cell, so draw.io routes them again."""
    for edge in session.cells.values():
        if edge.get("edge") != "1" or cell_id not in (edge.get("source"), edge.get("target")):
            continue
        geometry = edge.find("mxGeometry")
        if geometry is not None:
            for bends in geometry.findall("Array"):
                geometry.remove(bends)
        style = parse_style(edge.get("style", ""))
        style.pop("edgeStyle", None)
        style["edgeStyle"] = "orthogonalEdgeStyle"
        edge.set("style", style_string(style))
        session.notes.append(f"the line '{edge.get('id')}' will be routed again by draw.io")


def _set_text(session: _Session, op: dict[str, Any]) -> None:
    """Replace the label of a cell; HTML labels get the text escaped, with line breaks kept."""
    cell = session.cell(op["id"])
    assert cell is not None
    style = parse_style(cell.get("style", ""))
    lines = str(op["text"]).split("\n")
    cell.set("value", "<br>".join(esc(line) for line in lines) if "html" in style else op["text"])


def _move(session: _Session, op: dict[str, Any]) -> None:
    """Move a cell; the cells inside it move with it, and its lines are routed again."""
    cell = session.cell(op["id"])
    assert cell is not None
    geometry = _bounds_of(cell)
    geometry.set("x", fmt(op["x"]))
    geometry.set("y", fmt(op["y"]))
    _reroute_edges(session, cell.get("id", ""))


def _resize(session: _Session, op: dict[str, Any]) -> None:
    """Change the size of a cell; its lines are routed again."""
    cell = session.cell(op["id"])
    assert cell is not None
    geometry = _bounds_of(cell)
    geometry.set("width", fmt(op["width"]))
    geometry.set("height", fmt(op["height"]))
    _reroute_edges(session, cell.get("id", ""))


def _tone(session: _Session, op: dict[str, Any]) -> None:
    """Give a cell the fill of one of Flow's tones."""
    cell = session.cell(op["id"])
    assert cell is not None
    style = parse_style(cell.get("style", ""))
    style["fillColor"] = session.theme.tones[Tone(op["tone"])].box
    cell.set("style", style_string(style))


def _set_style(session: _Session, op: dict[str, Any]) -> None:
    """Set or remove one key of the style of a cell."""
    cell = session.cell(op["id"])
    assert cell is not None
    style = parse_style(cell.get("style", ""))
    if op.get("value") is None:
        style.pop(op["key"], None)
    else:
        style[op["key"]] = str(op["value"])
    cell.set("style", style_string(style))


def _delete(session: _Session, op: dict[str, Any]) -> None:
    """Delete a cell, the cells inside it, and every line that ends on one of them."""
    cell = session.cell(op["id"])
    assert cell is not None
    doomed = {cell.get("id", "")}
    queue = [cell.get("id", "")]
    while queue:
        for child in _children_of(session, queue.pop()):
            doomed.add(child.get("id", ""))
            queue.append(child.get("id", ""))
    for edge in list(session.cells.values()):
        if edge.get("edge") == "1" and {edge.get("source"), edge.get("target")} & doomed:
            doomed.add(edge.get("id", ""))
    for name in doomed:
        found = session.cells.pop(name, None)
        if found is not None:
            session.root.remove(found)
    session.notes.append(f"deleted {len(doomed)} cells with '{op['id']}'")


def _add_node(session: _Session, op: dict[str, Any]) -> None:
    """Add a box in Flow's style at a position."""
    shape = Shape(op.get("shape", Shape.PROCESS.value))
    tone = Tone(op["tone"]) if op.get("tone") else None
    node = Node(
        id=op["id"],
        shape=shape,
        x=op["x"],
        y=op["y"],
        width=op.get("width", DEFAULT_WIDTH_PX),
        height=op.get("height", DEFAULT_HEIGHT_PX),
        text=tuple(str(op["text"]).split("\n")),
        icon=None,
        tone=tone,
        number=None,
        font_size=DEFAULT_FONT_SIZE_PX,
    )
    add_node(session.root, node, session.theme)
    session.cells[f"node-{op['id']}"] = session.root[-1]


def _add_edge(session: _Session, op: dict[str, Any]) -> None:
    """Add a line between two cells; draw.io routes it."""
    line = session.theme.roles[Role.NEXT]
    style = {
        "edgeStyle": "orthogonalEdgeStyle",
        "html": 1,
        "rounded": 0,
        "strokeColor": line.color,
        "strokeWidth": fmt(line.width),
        "endArrow": "classic",
        "fontFamily": session.theme.fonts.sans,
    }
    if op.get("dashed"):
        style["dashed"] = 1
    source, target = session.cell(op["from"]), session.cell(op["to"])
    assert source is not None
    assert target is not None
    attributes = {
        "id": f"edge-{op['id']}",
        "value": esc(op.get("label", "")),
        "style": style_string(style),
        "edge": "1",
        "parent": "1",
        "source": source.get("id", ""),
        "target": target.get("id", ""),
    }
    cell = ET.SubElement(session.root, "mxCell", attributes)
    ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    session.cells[attributes["id"]] = cell


HANDLERS = {
    "set_text": _set_text,
    "move": _move,
    "resize": _resize,
    "tone": _tone,
    "set_style": _set_style,
    "delete": _delete,
    "add_node": _add_node,
    "add_edge": _add_edge,
}


def _check_number(op: dict[str, Any], key: str, where: str, session: _Session) -> None:
    """Report a field that must be a number."""
    value = op.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool):
        session.problems.append(f"{where}: '{key}' must be a number")


def _check_references(op: dict[str, Any], where: str, session: _Session) -> None:
    """Report an id that names no cell, with a suggestion, and ids that are used twice."""
    kind = op["op"]
    names = ("id",) if kind in EXISTING_ID_OPS else ("from", "to") if kind == "add_edge" else ()
    for key in names:
        if session.cell(op.get(key)) is None:
            hint = suggestion(op.get(key), session.cells)
            session.problems.append(f"{where}: '{key}' names '{op.get(key)}', not a cell{hint}")
    if kind in ("add_node", "add_edge"):
        prefix = "node-" if kind == "add_node" else "edge-"
        if not isinstance(op.get("id"), str) or f"{prefix}{op.get('id')}" in session.cells:
            session.problems.append(f"{where}: 'id' must be a new text id")


def _check_values(op: dict[str, Any], where: str, session: _Session) -> None:
    """Report numbers, tones and shapes that are not valid for the operation."""
    for key in {"x", "y", "width", "height"} & OP_KEYS[op["op"]]:
        if key in op or key in ("x", "y"):
            _check_number(op, key, where, session)
    if "tone" in OP_KEYS[op["op"]] and op.get("tone") not in {*(t.value for t in Tone), None}:
        session.problems.append(f"{where}: unknown tone '{op.get('tone')}'")
    if op["op"] == "tone" and op.get("tone") is None:
        session.problems.append(f"{where}: 'tone' is required")
    if op["op"] == "add_node" and op.get("shape", "process") not in {s.value for s in Shape}:
        session.problems.append(f"{where}: unknown shape '{op.get('shape')}'")
    if op["op"] in ("set_text", "add_node") and not isinstance(op.get("text"), str):
        session.problems.append(f"{where}: 'text' must be text")
    if op["op"] == "set_style" and not isinstance(op.get("key"), str):
        session.problems.append(f"{where}: 'key' must be text")


def _name_of(operation: object) -> object:
    """Return the ``op`` of an operation for a message, or the value itself if it is no object."""
    return operation.get("op") if isinstance(operation, dict) else operation


def _check(operation: object, index: int, session: _Session) -> bool:
    """Check one operation against the model as it will be when the operation runs."""
    where = f"operations[{index}]"
    if not isinstance(operation, dict) or operation.get("op") not in OP_KEYS:
        known = ", ".join(OP_KEYS)
        session.problems.append(f"{where}: unknown op '{_name_of(operation)}'; use one of: {known}")
        return False
    extra = set(operation) - OP_KEYS[operation["op"]] - {"op"}
    if extra:
        session.problems.append(f"{where}: unknown keys {sorted(extra)}")
    before = len(session.problems)
    _check_references(operation, where, session)
    _check_values(operation, where, session)
    return len(session.problems) == before


def apply_operations(path: Path, operations: object) -> tuple[ET.Element, list[str]]:
    """Check a list of operations and run them on the first page of a file.

    Args:
        path: The ``.drawio`` file.
        operations: The parsed JSON list of operations.

    Returns:
        The ``mxfile`` element after the edits, and notes about side effects such as lines that
        will be routed again.

    Raises:
        SpecError: With every problem found; nothing is changed in that case.
    """
    model = read_graph(path)
    root = model.find("root")
    if root is None:
        raise SpecError([f"{path} holds no diagram"])
    session = _Session(root, load_theme(), {c.get("id", ""): c for c in root.iter("mxCell")})
    if not isinstance(operations, list) or not operations:
        raise SpecError(["the operations must be a non-empty JSON list"])
    if len(operations) > MAX_OPERATIONS:
        raise SpecError([f"at most {MAX_OPERATIONS} operations at a time"])
    for index, operation in enumerate(operations):
        if _check(operation, index, session):
            HANDLERS[operation["op"]](session, operation)
    if session.problems:
        raise SpecError(session.problems)
    return model, session.notes


def write_edited(source: Path, model: ET.Element, destination: Path) -> None:
    """Write an edited model into a copy of the source file, keeping its other pages.

    Args:
        source: The original file.
        model: The edited ``mxGraphModel``.
        destination: The file to write; it may be the source itself.
    """
    document = ET.fromstring(source.read_text(encoding="utf-8"))
    diagram = document if document.tag == "diagram" else document.find("diagram")
    if document.tag == "mxGraphModel":
        document = model
    elif diagram is not None:
        for old in diagram.findall("mxGraphModel"):
            diagram.remove(old)
        diagram.text = None
        diagram.append(model)
    ET.indent(document)
    destination.write_text(ET.tostring(document, encoding="unicode") + "\n", encoding="utf-8")
