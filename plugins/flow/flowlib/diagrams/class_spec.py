"""Read and check the spec of a UML class diagram.

The JSON format::

    {"type": "class", "title": "...", "desc": "...",
     "classes": [{"id", "label", "kind": "class|abstract|interface", "stereotype", "tone",
                  "attributes": ["+name: String"], "operations": ["+pay(p: Payment): bool"],
                  "at": [row, column]}],
     "relations": [{"from", "to", "label", "from_label", "to_label",
                    "style": "association|navigable|composition|aggregation|inheritance|
                              implements|dependency"}]}

``methods`` is accepted for ``operations``. ``at`` may use half columns (``[2, 0.5]``).
"""

from dataclasses import dataclass
from enum import StrEnum

from ..model import Head, Tone
from ..reader import Reader, SpecError, is_number, suggestion

SPEC_KEYS = {"type", "title", "desc", "theme", "classes", "relations"}
CLASS_KEYS = {
    "id", "label", "kind", "stereotype", "tone", "attributes", "operations", "methods", "at",
}  # fmt: skip
RELATION_KEYS = {"from", "to", "label", "from_label", "to_label", "style"}
AT_LENGTH = 2
INTERFACE_STEREOTYPE = "«interface»"


class ClassKind(StrEnum):
    """What a class box is: a plain class, an abstract one (italic name) or an interface."""

    CLASS = "class"
    ABSTRACT = "abstract"
    INTERFACE = "interface"


class RelationStyle(StrEnum):
    """How two classes relate; decides the line and its two ends."""

    ASSOCIATION = "association"
    NAVIGABLE = "navigable"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    INHERITANCE = "inheritance"
    IMPLEMENTS = "implements"
    DEPENDENCY = "dependency"


@dataclass(frozen=True)
class LineEnds:
    """How a relation style is drawn: dashed or solid and what sits at each end."""

    head: Head
    tail: Head = Head.NONE
    is_dashed: bool = False


LINE_ENDS: dict[RelationStyle, LineEnds] = {
    RelationStyle.ASSOCIATION: LineEnds(Head.NONE),
    RelationStyle.NAVIGABLE: LineEnds(Head.OPEN),
    RelationStyle.COMPOSITION: LineEnds(Head.NONE, Head.DIAMOND_FILLED),
    RelationStyle.AGGREGATION: LineEnds(Head.NONE, Head.DIAMOND),
    RelationStyle.INHERITANCE: LineEnds(Head.TRIANGLE),
    RelationStyle.IMPLEMENTS: LineEnds(Head.TRIANGLE, is_dashed=True),
    RelationStyle.DEPENDENCY: LineEnds(Head.OPEN, is_dashed=True),
}
HIERARCHY_STYLES = (RelationStyle.INHERITANCE, RelationStyle.IMPLEMENTS)  # to is the parent


@dataclass(frozen=True)
class ClassBox:
    """One class: its name, its kind and its two compartments."""

    id: str
    name: str
    kind: ClassKind
    stereotype: str
    tone: Tone | None
    attributes: tuple[str, ...]
    operations: tuple[str, ...]
    at: tuple[float, float] | None


@dataclass(frozen=True)
class Relation:
    """One relationship between two classes, with the numbers at its ends."""

    source: str
    target: str
    label: str
    style: RelationStyle
    source_count: str
    target_count: str


@dataclass(frozen=True)
class ClassSpec:
    """A checked class diagram."""

    title: str | None
    description: str | None
    classes: tuple[ClassBox, ...]
    relations: tuple[Relation, ...]


def read_spec(raw: object) -> ClassSpec:
    """Check a class spec.

    Args:
        raw: The result of ``json.loads`` on a ``class`` spec.

    Returns:
        The checked spec.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    items = raw.get("classes", [])
    built = [
        _class(item, f"classes[{index}]", read)
        for index, item in enumerate(items if isinstance(items, list) else [])
    ]
    boxes = {box.id: box for box in built if box is not None}
    if not boxes:
        read.report("spec", "'classes' must list at least one class")
    rows = raw.get("relations", [])
    relations = [
        _relation(item, f"relations[{index}]", read, set(boxes))
        for index, item in enumerate(rows if isinstance(rows, list) else [])
    ]
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    if read.problems:
        raise SpecError(read.problems)
    return ClassSpec(
        title, description, tuple(boxes.values()), tuple(r for r in relations if r is not None)
    )


def _members(raw: dict, keys: tuple[str, ...], where: str, read: Reader) -> tuple[str, ...]:
    """Read a list of member strings from the first of ``keys`` that is present."""
    key = next((name for name in keys if name in raw), None)
    if key is None:
        return ()
    items = raw[key]
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        read.report(where, f"'{key}' must be a list of strings")
        return ()
    return tuple(items)


def _class(raw: object, where: str, read: Reader) -> ClassBox | None:
    """Build one class, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, CLASS_KEYS, where)
    identifier = read.identifier(raw, where)
    kind = read.enum(ClassKind, raw, "kind", where) or ClassKind.CLASS
    at = raw.get("at")
    if at is not None and not (
        isinstance(at, list) and len(at) == AT_LENGTH and all(is_number(each) for each in at)
    ):
        read.report(where, "'at' must be [row, column]")
        at = None
    stereotype = read.text(raw, "stereotype", where)
    if stereotype is None and kind is ClassKind.INTERFACE:
        stereotype = INTERFACE_STEREOTYPE
    return ClassBox(
        id=identifier,
        name=read.text(raw, "label", where) or identifier,
        kind=kind,
        stereotype=stereotype or "",
        tone=read.enum(Tone, raw, "tone", where),
        attributes=_members(raw, ("attributes",), where, read),
        operations=_members(raw, ("operations", "methods"), where, read),
        at=(float(at[0]), float(at[1])) if at else None,
    )


def _relation(raw: object, where: str, read: Reader, known: set[str]) -> Relation | None:
    """Build one relation, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, RELATION_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in known:
            read.report(
                where, f"'{key}' names '{name}', which is not a class{suggestion(name, known)}"
            )
        ends.append(name if name in known else "")
    return Relation(
        source=ends[0],
        target=ends[1],
        label=read.text(raw, "label", where) or "",
        style=read.enum(RelationStyle, raw, "style", where) or RelationStyle.ASSOCIATION,
        source_count=read.text(raw, "from_label", where) or "",
        target_count=read.text(raw, "to_label", where) or "",
    )
