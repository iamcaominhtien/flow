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

from enum import StrEnum
from typing import Any

from ..model import Direction, Head, Role, Row, Scene, Shape, Tone
from ..reader import Reader, SpecError, suggestion
from ..spec import Spec, SpecEdge, SpecNode
from ..theme import load_icons
from . import flowchart

ER = "er"
SPEC_KEYS = {"type", "title", "desc", "tables", "relations"}
TABLE_KEYS = {"id", "name", "icon", "tone", "columns", "at"}
COLUMN_KEYS = {"name", "type", "flags"}
RELATION_KEYS = {
    "from", "to", "from_column", "to_column", "from_end", "to_end", "label", "style", "main",
}  # fmt: skip
AT_LENGTH = 2


class Cardinality(StrEnum):
    """How many rows of a table take part in a relation, at one end of the line."""

    ONE = "one"
    ZERO_ONE = "zero_one"
    ONE_MANY = "one_many"
    ZERO_MANY = "zero_many"


class RelationStyle(StrEnum):
    """A solid line is enforced by the database; a logical one only by the application."""

    SOLID = "solid"
    LOGICAL = "logical"


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
    """Build one table row from a column: the name on the left, the type and flags on the right."""
    read.check_keys(raw, COLUMN_KEYS, where)
    flags = raw.get("flags", [])
    names = []
    for index, flag in enumerate(flags if isinstance(flags, list) else []):
        member = read.enum(Flag, {"flags": flag}, "flags", f"{where}.flags[{index}]")
        if member is not None:
            names.append(member.value.upper())
    right = " ".join(part for part in [read.text(raw, "type", where) or "", *names] if part)
    return Row(left=read.text(raw, "name", where) or "", right=right)


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
    )


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
    return SpecEdge(
        source=ends[0],
        target=ends[1],
        role=Role.MAIN if raw.get("main") is True else Role.NEXT,
        label=read.text(raw, "label", where),
        head=HEAD_OF_CARDINALITY[end],
        tail=HEAD_OF_CARDINALITY[start],
        dashed=style is RelationStyle.LOGICAL,
    )


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
    icons = set(load_icons())
    built = [
        _table(item, f"tables[{index}]", read, icons)
        for index, item in enumerate(raw.get("tables", []))
    ]
    tables = {node.id: node for node in built if node is not None}
    if not tables:
        read.report("spec", "'tables' must list at least one table")
    relations = [
        _relation(item, f"relations[{index}]", read, tables)
        for index, item in enumerate(raw.get("relations", []))
    ]
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    if read.problems:
        raise SpecError(read.problems)
    return Spec(
        title=title,
        description=description,
        direction=Direction.DOWN,
        lanes=(),
        nodes=tuple(tables.values()),
        edges=tuple(edge for edge in relations if edge is not None),
    )


def layout_raw(raw: object) -> Scene:
    """Lay out an ER diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on an ER spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return flowchart.layout(to_spec(raw))
