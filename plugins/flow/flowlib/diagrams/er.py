"""The entity-relationship diagram: tables with columns, joined by lines with crow's feet.

The JSON format::

    {"type": "er", "title": "...", "desc": "...",
     "tables": [{"id", "name", "icon", "tone", "at": [row, column],
                 "columns": [{"name", "type", "flags": ["pk", "fk", "uq", "null"]}]}],
     "relations": [{"from": "table", "to": "table", "from_column", "to_column",
                    "from_end": "one|zero_one|one_many|zero_many",
                    "to_end": "one|zero_one|one_many|zero_many",
                    "label", "style": "solid|logical", "main": true}]}

A relation reads from the "one" side to the "many" side by default. A many-to-many relation is
stored as two relations and a junction table.
"""

from dataclasses import replace
from enum import StrEnum
from itertools import pairwise
from typing import Any

from ..canvas import fit_canvas
from ..model import (
    Direction,
    Edge,
    EdgeLabel,
    Frame,
    Head,
    Node,
    Point,
    Role,
    Row,
    Scene,
    Shape,
    Tone,
)
from ..reader import Reader, SpecError, suggestion
from ..spec import Spec, SpecEdge, SpecNode, check_explicit_cells
from ..theme import LayoutRules, icon_names, load_theme
from . import flowchart

ER = "er"
SPEC_KEYS = {"type", "title", "desc", "tables", "relations", "style", "domain_frames"}
TABLE_KEYS = {"id", "name", "icon", "tone", "columns", "at", "domain", "see"}
COLUMN_KEYS = {"name", "type", "flags"}
RELATION_KEYS = {
    "from", "to", "from_column", "to_column", "from_end", "to_end", "label", "style", "main",
}  # fmt: skip
AT_LENGTH = 2
TABLE_GAP_PX = 160  # room for two cardinality marks and a label between two tables
ROW_INSET_PX = 1  # the header border, between the header and the first row
MIN_STRAIGHT_POINTS = 2
DOMAIN_FRAME_PADDING_PX = 28
DOMAIN_FRAME_TOP_PX = 56  # room above the tables for the name pill
DOMAIN_FRAME_CEILING_PX = 128  # the lowest a frame may start without touching the description
SELF_LOOP_LABEL_GAP_PX = 6  # between a self reference and its label
SELF_LOOP_PX = 48  # how far a self reference sticks out of its table
NULLABLE_MARK = "?"
TABLE_ICON = "table"  # the icon of an illustrated table that names none


class Cardinality(StrEnum):
    """How many rows of a table take part in a relation, at one end of the line."""

    ONE = "one"
    ZERO_ONE = "zero_one"
    ONE_MANY = "one_many"
    ZERO_MANY = "zero_many"


class RelationStyle(StrEnum):
    """A solid line is enforced by the database; a logical one only by the application.

    A subtype line joins a parent (``from``) to a child that shares its key; a hollow triangle
    marks the parent.
    """

    SOLID = "solid"
    LOGICAL = "logical"
    SUBTYPE = "subtype"


class Flag(StrEnum):
    """A property of a column."""

    PK = "pk"
    FK = "fk"
    UQ = "uq"
    NULL = "null"


HEAD_OF_CARDINALITY = {
    Cardinality.ONE: Head.ONE_ONLY,
    Cardinality.ZERO_ONE: Head.ZERO_ONE,
    Cardinality.ONE_MANY: Head.ONE_MANY,
    Cardinality.ZERO_MANY: Head.ZERO_MANY,
}


def _column_row(raw: dict[str, Any], read: Reader, where: str) -> Row:
    """Build one table row from a column.

    The key flags (``PK``, ``FK``, ``UQ``) become chips before the name; the type goes on the
    right, with a question mark when the column may be empty.
    """
    read.check_keys(raw, COLUMN_KEYS, where)
    flags = raw.get("flags", [])
    chips, is_nullable = [], False
    for index, flag in enumerate(flags if isinstance(flags, list) else []):
        member = read.enum(Flag, {"flags": flag}, "flags", f"{where}.flags[{index}]")
        if member is Flag.NULL:
            is_nullable = True
        elif member is not None:
            chips.append(member.value.upper())
    kind = read.text(raw, "type", where) or ""
    right = kind + NULLABLE_MARK if is_nullable and kind else kind
    return Row(left=read.text(raw, "name", where) or "", right=right, flags=tuple(chips))


def _table(raw: object, where: str, read: Reader, icons: set[str]) -> SpecNode | None:
    """Build one table as a node whose rows are its columns."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, TABLE_KEYS, where)
    icon = raw.get("icon")
    if icon is not None and icon not in icons:
        read.report(where, f"unknown icon '{icon}'; use one of: {', '.join(sorted(icons))}")
    columns = raw.get("columns", [])
    rows = [
        _column_row(item, read, f"{where}.columns[{index}]")
        for index, item in enumerate(columns if isinstance(columns, list) else [])
        if isinstance(item, dict)
    ]
    identifier = read.identifier(raw, where)
    at = raw.get("at")
    if at is not None and not (isinstance(at, list) and len(at) == AT_LENGTH):
        read.report(where, "'at' must be [row, column]")
        at = None
    return SpecNode(
        id=identifier,
        kind=Shape.TABLE,
        text=read.text(raw, "name", where) or identifier,
        icon=icon,
        tone=read.enum(Tone, raw, "tone", where),
        number=None,
        side=None,
        lane=None,
        sections=(tuple(rows),),
        at=(int(at[0]), int(at[1])) if at else None,
        caption=read.text(raw, "see", where),
        dashed=raw.get("see") is not None,
    )


def _relation_role(is_main: bool, style: RelationStyle) -> Role:
    """Pick the line role: the animated main path, a dashed slate logical link, or a plain line."""
    if is_main:
        return Role.MAIN
    return Role.LOGICAL if style is RelationStyle.LOGICAL else Role.NEXT


def _relation(
    raw: object, where: str, read: Reader, tables: dict[str, SpecNode]
) -> SpecEdge | None:
    """Build one relation as an edge with a symbol at each end."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, RELATION_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in tables:
            read.report(
                where, f"'{key}' names '{name}', which is not a table{suggestion(name, tables)}"
            )
        ends.append(name if name in tables else "")
        column = raw.get(f"{key}_column")
        known = {row.left for row in tables[name].sections[0]} if name in tables else set()
        if column is not None and column not in known:
            read.report(
                where, f"'{key}_column' names '{column}', which is not a column of '{name}'"
            )
    style = read.enum(RelationStyle, raw, "style", where) or RelationStyle.SOLID
    start = read.enum(Cardinality, raw, "from_end", where) or Cardinality.ONE
    end = read.enum(Cardinality, raw, "to_end", where) or Cardinality.ZERO_MANY
    is_subtype = style is RelationStyle.SUBTYPE
    return SpecEdge(
        source=ends[0],
        target=ends[1],
        role=_relation_role(raw.get("main") is True, style),
        label=read.text(raw, "label", where),
        head=Head.NONE if is_subtype else HEAD_OF_CARDINALITY[end],
        tail=Head.TRIANGLE if is_subtype else HEAD_OF_CARDINALITY[start],
        dashed=style is RelationStyle.LOGICAL,
    )


def _with_card(table: SpecNode, is_illustrated: bool) -> SpecNode:
    """Return the table as an illustrated one (tall header, large icon) when the spec asks."""
    if not is_illustrated:
        return table
    return replace(table, card=True, icon=table.icon or TABLE_ICON)


def to_spec(raw: object) -> Spec:
    """Check an ER spec and turn it into the description the layout works on.

    Args:
        raw: The result of ``json.loads`` on an ER spec.

    Returns:
        The tables as nodes and the relations as edges.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    icons = icon_names()
    built = [
        _table(item, f"tables[{index}]", read, icons)
        for index, item in enumerate(raw.get("tables", []))
    ]
    tables = {node.id: node for node in built if node is not None}
    check_explicit_cells(tables.values(), read)
    if not tables:
        read.report("spec", "'tables' must list at least one table")
    relations = [
        _relation(item, f"relations[{index}]", read, tables)
        for index, item in enumerate(raw.get("relations", []))
    ]
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    illustrated = read.illustrated(raw, "spec")
    if read.problems:
        raise SpecError(read.problems)
    return Spec(
        title=title,
        description=description,
        direction=Direction.DOWN,
        lanes=(),
        nodes=tuple(_with_card(table, illustrated) for table in tables.values()),
        edges=tuple(edge for edge in relations if edge is not None),
        illustrated=illustrated,
    )


def _with_domain_frames(scene: Scene, raw: dict[str, Any]) -> Scene:
    """Draw a dashed tinted frame with a name pill around the tables of each domain.

    A frame is the bounding box of its tables with room for the pill above. The whole scene
    moves down when a frame would otherwise rise into the title. Tables of one domain should
    sit side by side in the grid, so that no frame covers a table of another domain.
    """
    domains: dict[str, list[Node]] = {}
    tones: dict[str, Tone] = {}
    by_id = {node.id: node for node in scene.nodes}
    for table in raw.get("tables", []):
        domain, node = table.get("domain"), by_id.get(table.get("id"))
        if domain and node is not None:
            domains.setdefault(domain, []).append(node)
            tones.setdefault(domain, node.tone or Tone.GRAY)
    frames = []
    for domain, nodes in domains.items():
        left = min(node.x for node in nodes) - DOMAIN_FRAME_PADDING_PX
        top = min(node.y for node in nodes) - DOMAIN_FRAME_TOP_PX
        right = max(node.x + node.width for node in nodes) + DOMAIN_FRAME_PADDING_PX
        bottom = max(node.y + node.height for node in nodes) + DOMAIN_FRAME_PADDING_PX
        frames.append(
            Frame(f"domain-{domain}", left, top, right - left, bottom - top, domain, tones[domain])
        )
    if not frames:
        return scene
    drop = max(0.0, DOMAIN_FRAME_CEILING_PX - min(frame.y for frame in frames))
    return fit_canvas(_moved_down(replace(scene, frames=(*scene.frames, *frames)), drop))


def _moved_down(scene: Scene, drop: float) -> Scene:
    """Move everything in a scene down by ``drop`` pixels."""
    if not drop:
        return scene
    nodes = tuple(replace(node, y=node.y + drop) for node in scene.nodes)
    frames = tuple(replace(frame, y=frame.y + drop) for frame in scene.frames)
    edges = tuple(
        replace(
            edge,
            points=tuple((x, y + drop) for x, y in edge.points),
            label=replace(edge.label, at=(edge.label.at[0], edge.label.at[1] + drop))
            if edge.label
            else None,
        )
        for edge in scene.edges
    )
    return replace(scene, nodes=nodes, frames=frames, edges=edges)


def _row_y(node: Node, column: str | None, rules: LayoutRules) -> float | None:
    """Return the y of the middle of a column's row in a table, or None for an unknown column."""
    header = rules.table_card_header_height if node.card else rules.table_header_height
    for index, row in enumerate(node.sections[0] if node.sections else ()):
        if row.left == column:
            return node.y + header + ROW_INSET_PX + (index + 0.5) * rules.table_row_height
    return None


def _move_end(points: tuple[Point, ...], y: float, is_start: bool) -> tuple[Point, ...]:
    """Move one end of a line to height ``y`` when the line meets a side of its table.

    The points that run level with that end move with it, so the segment stays horizontal and the
    first vertical segment of the route is simply longer or shorter. A line that is one level
    run from end to end gets a jog in the middle.
    """
    ends = list(points if is_start else reversed(points))
    level = ends[0][1]
    run = 0
    while run < len(ends) and ends[run][1] == level:
        run += 1
    if run < MIN_STRAIGHT_POINTS or ends[0][0] == ends[1][0]:
        return points
    if run == len(ends):
        middle = (ends[0][0] + ends[-1][0]) / 2
        ends = [(ends[0][0], y), (middle, y), (middle, level), ends[-1]]
    else:
        ends[:run] = [(x, y) for x, _ in ends[:run]]
    return tuple(ends if is_start else reversed(ends))


def _attach_to_rows(scene: Scene, raw: object) -> Scene:
    """Make each line leave and enter a table at the row of the column it joins.

    The design draws a relation from the row of its foreign key. A line that meets the top or
    the bottom of a table is left as it is.
    """
    rules = load_theme().layout
    nodes = {node.id: node for node in scene.nodes}
    relations = raw.get("relations", []) if isinstance(raw, dict) else []
    edges = []
    for edge, relation in zip(scene.edges, relations, strict=True):
        if edge.source == edge.target:
            edges.append(_self_loop(edge, nodes[edge.source], relation, rules))
            continue
        points = edge.points
        for key, is_start in (("from_column", True), ("to_column", False)):
            node = nodes[edge.source if is_start else edge.target]
            row_y = _row_y(node, relation.get(key), rules)
            if row_y is not None:
                points = _move_end(points, row_y, is_start)
        edges.append(replace(edge, points=points, label=_relabelled(edge.label, points)))
    return fit_canvas(replace(scene, edges=tuple(edges)))


def _self_loop(edge: Edge, node: Node, relation: dict[str, Any], rules: LayoutRules) -> Edge:
    """Draw a table that points at itself as a loop at its right side.

    The loop leaves at the row of ``from_column`` and comes back at the row of ``to_column``;
    without them it uses a third and two thirds of the table's height.
    """
    right = node.x + node.width
    first = _row_y(node, relation.get("from_column"), rules) or node.y + node.height / 3
    second = _row_y(node, relation.get("to_column"), rules) or node.y + 2 * node.height / 3
    out = right + SELF_LOOP_PX
    points = ((right, first), (out, first), (out, second), (right, second))
    label = None
    if edge.label:
        chip = len(edge.label.text) * rules.chip_char_width_em * rules.chip_font_size
        beside = out + SELF_LOOP_LABEL_GAP_PX + (chip + rules.chip_padding_x) / 2
        label = replace(edge.label, at=(beside, (first + second) / 2))
    return replace(edge, points=points, label=label)


def _relabelled(label: EdgeLabel | None, points: tuple[Point, ...]) -> EdgeLabel | None:
    """Put a label back on the middle of the longest segment of a line that was changed."""
    if label is None:
        return None
    segments = list(pairwise(points))
    start, end = max(segments, key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))
    return replace(label, at=((start[0] + end[0]) / 2, (start[1] + end[1]) / 2))


def layout_raw(raw: object) -> Scene:
    """Lay out an ER diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on an ER spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    rules = load_theme().layout
    wide = replace(
        rules,
        gap_vertical=TABLE_GAP_PX,
        gap_vertical_labelled=TABLE_GAP_PX,
        gap_horizontal=TABLE_GAP_PX,
        gap_horizontal_labelled=TABLE_GAP_PX,
    )
    scene = _attach_to_rows(flowchart.layout(to_spec(raw), wide), raw)
    if isinstance(raw, dict) and raw.get("domain_frames") is True:
        return _with_domain_frames(scene, raw)
    return scene
