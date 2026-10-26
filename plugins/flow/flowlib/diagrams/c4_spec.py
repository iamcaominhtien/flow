"""Read and check a C4 diagram spec: kinds, levels, the box that is opened and the lines.

The JSON format::

    {"type": "c4", "title": "...", "desc": "...", "level": 1,
     "opens": {"spec": "context.spec.json", "element": "platform", "label": "...", "tone": "..."},
     "elements": [{"id", "label", "kind": "person|system|external|container|database|component",
                   "technology", "description", "icon", "tone", "at": [row, column]}],
     "relations": [{"from", "to", "label", "protocol", "kind": "call|main|event",
                    "main": true}]}

The level is read from the kinds: a ``component`` makes level 3, a ``container`` or a
``database`` level 2, anything else level 1. ``level`` may state it, and is then checked.
``opens`` makes the diagram the zoom of one box of the level above: ``spec`` names the file of
that level and ``element`` the box in it. An element with the id of an element of that level
is the same neighbour, and takes what the spec leaves out from it. Without ``spec`` the frame
takes its name from ``label`` and its tint from ``tone``.
"""

import json
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

from ..model import Tone
from ..reader import Reader, SpecError, suggestion
from ..theme import icon_names

SPEC_KEYS = {"type", "title", "desc", "level", "opens", "elements", "relations", "theme", "style"}
ELEMENT_KEYS = {"id", "label", "kind", "technology", "description", "icon", "tone", "at"}
RELATION_KEYS = {"from", "to", "label", "protocol", "kind", "main"}
OPENS_KEYS = {"spec", "element", "label", "tone"}
AT_LENGTH = 2
LEVELS = (1, 2, 3)
CONTEXT_LEVEL, CONTAINER_LEVEL, COMPONENT_LEVEL = LEVELS
MAX_ELEMENTS = 15  # past this, zoom into a part instead of drawing more (design 12 section 6)


class Kind(StrEnum):
    """What a box of a C4 diagram is."""

    PERSON = "person"
    SYSTEM = "system"
    EXTERNAL = "external"
    CONTAINER = "container"
    DATABASE = "database"
    COMPONENT = "component"


class LineKind(StrEnum):
    """What a relation is: a plain call, the main route, or an event."""

    CALL = "call"
    MAIN = "main"
    EVENT = "event"


KIND_NAMES: dict[Kind, str] = {
    Kind.PERSON: "Person",
    Kind.SYSTEM: "Software system",
    Kind.EXTERNAL: "External system",
    Kind.CONTAINER: "Container",
    Kind.DATABASE: "Container",
    Kind.COMPONENT: "Component",
}
KIND_ICONS: dict[Kind, str] = {
    Kind.PERSON: "user",
    Kind.SYSTEM: "server",
    Kind.EXTERNAL: "cloud",
    Kind.CONTAINER: "server",
    Kind.DATABASE: "database",
    Kind.COMPONENT: "code",
}
KIND_TONES: dict[Kind, Tone] = {
    Kind.PERSON: Tone.BLUE,
    Kind.SYSTEM: Tone.VIOLET,
    Kind.EXTERNAL: Tone.GRAY,
    Kind.CONTAINER: Tone.BLUE,
    Kind.DATABASE: Tone.BLUE,
    Kind.COMPONENT: Tone.BLUE,
}
LEVEL_KINDS: dict[int, set[Kind]] = {
    CONTEXT_LEVEL: {Kind.PERSON, Kind.SYSTEM, Kind.EXTERNAL},
    CONTAINER_LEVEL: {Kind.PERSON, Kind.EXTERNAL, Kind.CONTAINER, Kind.DATABASE},
    COMPONENT_LEVEL: {Kind.PERSON, Kind.EXTERNAL, Kind.CONTAINER, Kind.DATABASE, Kind.COMPONENT},
}
INSIDE_KINDS: dict[int, set[Kind]] = {
    CONTEXT_LEVEL: set(),
    CONTAINER_LEVEL: {Kind.CONTAINER, Kind.DATABASE},
    COMPONENT_LEVEL: {Kind.COMPONENT},
}
OPENED_KINDS: dict[int, set[Kind]] = {
    CONTAINER_LEVEL: {Kind.SYSTEM},
    COMPONENT_LEVEL: {Kind.CONTAINER, Kind.DATABASE},
}
FRAME_KIND_NAMES: dict[int, str] = {
    CONTAINER_LEVEL: "Software system",
    COMPONENT_LEVEL: "Container",
}
FRAME_TONE = Tone.VIOLET


@dataclass(frozen=True)
class Element:
    """One box: a person, a system, a container or a component."""

    id: str
    kind: Kind | None  # None until read from the level above, or defaulted to a container
    label: str
    technology: str = ""
    description: str = ""
    icon: str | None = None
    tone: Tone | None = None
    at: tuple[float, float] | None = None
    is_outside: bool = False  # a neighbour that belongs to the level above

    @property
    def type_line(self) -> str:
        """Return the mono line under the name: ``[Kind]`` or ``[Kind: technology]``."""
        name = KIND_NAMES[self.kind]
        return f"[{name}: {self.technology}]" if self.technology else f"[{name}]"


@dataclass(frozen=True)
class Relation:
    """One arrow, from the box that starts the call to the one that receives it."""

    source: str
    target: str
    label: str
    protocol: str = ""
    kind: LineKind = LineKind.CALL

    @property
    def text(self) -> str:
        """Return what the line says: the verb phrase and, after a comma, the protocol."""
        return ", ".join(part for part in (self.label, self.protocol) if part)


@dataclass(frozen=True)
class Opened:
    """The box of the level above that this diagram opens, as the frame that holds the parts."""

    label: str
    tone: Tone


@dataclass(frozen=True)
class C4Spec:
    """A checked C4 diagram."""

    title: str | None
    description: str | None
    level: int
    elements: tuple[Element, ...]
    relations: tuple[Relation, ...]
    opened: Opened | None = None

    def is_inside(self, element: Element) -> bool:
        """Tell whether an element is a part of the opened box, drawn inside the frame."""
        return element.kind in INSIDE_KINDS[self.level] and not element.is_outside


def read_spec(raw: object, source_dir: Path | None = None) -> C4Spec:
    """Check a C4 spec and turn it into the description the layout uses.

    Args:
        raw: The result of ``json.loads`` on the spec.
        source_dir: The folder of the spec file, where ``opens`` looks for the level above.

    Returns:
        The checked spec.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    _check_style(raw, read)
    elements = _read_elements(raw.get("elements", []), read)
    level = _level_of(raw, elements, read)
    spec = C4Spec(
        title=read.text(raw, "title", "spec"),
        description=read.text(raw, "desc", "spec"),
        level=level,
        elements=tuple(elements),
        relations=(),
    )
    spec = _resolve_kinds(_open(spec, raw.get("opens"), source_dir, read))
    by_id = {element.id: element for element in spec.elements}
    relations = _read_relations(raw.get("relations", []), (by_id, level), read)
    spec = replace(spec, relations=tuple(relations))
    problems = [*read.problems, *check_diagram(spec)]
    if problems:
        raise SpecError(problems)
    return _with_defaults(spec)


def _resolve_kinds(spec: C4Spec) -> C4Spec:
    """Make a box whose kind nobody gave a container, the commonest box."""
    elements = tuple(
        e if e.kind is not None else replace(e, kind=Kind.CONTAINER) for e in spec.elements
    )
    return replace(spec, elements=elements)


def _check_style(raw: dict[str, Any], read: Reader) -> None:
    """Report an illustrated style: C4 is drawn plain only."""
    if raw.get("style", "plain") != "plain":
        read.report("spec", "'style' must be 'plain': a C4 diagram has no illustrated style")


def _read_elements(raw: object, read: Reader) -> list[Element]:
    """Read the elements; an item that is not valid is reported and left out."""
    if not isinstance(raw, list) or not raw:
        read.report("spec", "'elements' must list at least one element")
        return []
    built = [_element(item, f"elements[{index}]", read) for index, item in enumerate(raw)]
    return [element for element in built if element is not None]


def _element(raw: object, where: str, read: Reader) -> Element | None:
    """Build one element, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ELEMENT_KEYS, where)
    icon = raw.get("icon")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    at = raw.get("at")
    if at is not None and not (isinstance(at, list) and len(at) == AT_LENGTH):
        read.report(where, "'at' must be [row, column]")
        at = None
    return Element(
        id=read.identifier(raw, where),
        kind=read.enum(Kind, raw, "kind", where),
        label=read.text(raw, "label", where) or "",
        technology=read.text(raw, "technology", where) or "",
        description=read.text(raw, "description", where) or "",
        icon=icon,
        tone=read.enum(Tone, raw, "tone", where),
        at=(at[0], at[1]) if at else None,
    )


def _read_relations(
    raw: object, context: tuple[dict[str, Element], int], read: Reader
) -> list[Relation]:
    """Read the relations; each end must name an element."""
    items = raw if isinstance(raw, list) else []
    relations = []
    for index, item in enumerate(items):
        relation = _relation(item, f"relations[{index}]", context, read)
        if relation is not None:
            relations.append(relation)
    return relations


def _relation(
    raw: object, where: str, context: tuple[dict[str, Element], int], read: Reader
) -> Relation | None:
    """Build one relation, or report why it cannot be built."""
    by_id, level = context
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, RELATION_KEYS, where)
    ends = [_end(raw, key, (where, by_id), read) for key in ("from", "to")]
    kind = LineKind.MAIN if raw.get("main") is True else read.enum(LineKind, raw, "kind", where)
    kind = kind or LineKind.CALL
    label, protocol = read.text(raw, "label", where), read.text(raw, "protocol", where)
    if ends[0] is None or ends[1] is None:
        return None
    kinds = (by_id[ends[0]].kind, by_id[ends[1]].kind)
    problem = _what_is_missing(level, (label, protocol), (kind, kinds))
    if problem:
        read.report(where, problem)
    return Relation(ends[0], ends[1], label or "", protocol or "", kind)


def _end(
    raw: dict[str, Any], key: str, place: tuple[str, dict[str, Element]], read: Reader
) -> str | None:
    """Return the id at one end of a relation, or None after reporting a name that is no element."""
    where, by_id = place
    name = raw.get(key)
    if name in by_id:
        return name
    read.report(where, f"'{key}' names '{name}', which is not an element{suggestion(name, by_id)}")
    return None


def _what_is_missing(
    level: int, said: tuple[str | None, str | None], line: tuple[LineKind, tuple[Kind, Kind]]
) -> str:
    """Return what a relation lacks: a verb phrase, and between two containers how they talk."""
    label, protocol = said
    kind, ends = line
    if level == CONTEXT_LEVEL and not label:
        return "needs a 'label': what the box that starts it does with the other, as a verb phrase"
    if not label and not protocol:
        return "needs a 'label' (a verb phrase) or a 'protocol' (HTTPS, SQL, gRPC...)"
    is_free = kind is LineKind.EVENT or Kind.PERSON in ends or level != CONTAINER_LEVEL
    if not protocol and not is_free:
        return "needs a 'protocol' (HTTPS, SQL, gRPC...): say how the two containers talk"
    return ""


def _level_of(raw: dict[str, Any], elements: list[Element], read: Reader) -> int:
    """Return the level the spec asks for, or the one its elements show."""
    asked = raw.get("level")
    if asked is not None and asked not in LEVELS:
        read.report("spec", "'level' must be 1, 2 or 3")
    if asked in LEVELS:
        return asked
    kinds = {element.kind for element in elements if element.kind}
    if Kind.COMPONENT in kinds:
        return COMPONENT_LEVEL
    if kinds & {Kind.CONTAINER, Kind.DATABASE}:
        return CONTAINER_LEVEL
    return CONTEXT_LEVEL


def _open(spec: C4Spec, raw: object, source_dir: Path | None, read: Reader) -> C4Spec:
    """Apply ``opens``: the frame, and the neighbours as the level above drew them."""
    if raw is None:
        return spec
    if not isinstance(raw, dict):
        read.report("opens", "must be an object")
        return spec
    read.check_keys(raw, OPENS_KEYS, "opens")
    if spec.level == CONTEXT_LEVEL:
        read.report("opens", "a context diagram opens nothing: it is level 1")
        return spec
    parent = _read_parent(raw, source_dir, read)
    if parent is None:
        return replace(spec, opened=_named_frame(raw, spec.level, read))
    return _inherit(spec, parent, raw, read)


def _named_frame(raw: dict[str, Any], level: int, read: Reader) -> Opened | None:
    """Return the frame that ``opens`` describes by itself, without a file."""
    label = read.text(raw, "label", "opens")
    if not label:
        read.report("opens", "needs a 'spec' and an 'element', or a 'label' for the frame")
        return None
    tone = read.enum(Tone, raw, "tone", "opens") or FRAME_TONE
    return Opened(f"{label} [{FRAME_KIND_NAMES[level]}]", tone)


def _read_parent(raw: dict[str, Any], source_dir: Path | None, read: Reader) -> C4Spec | None:
    """Read the level above that ``opens`` names, or None when it names no file."""
    name = raw.get("spec")
    if name is None:
        return None
    if not isinstance(name, str):
        read.report("opens", "'spec' must be the file name of the level above")
        return None
    path = (source_dir or Path()) / name
    try:
        return read_spec(json.loads(path.read_text(encoding="utf-8")), path.parent)
    except (OSError, ValueError) as error:
        read.report("opens", f"cannot read the level above, '{name}': {error}")
    except SpecError as error:
        read.report("opens", f"the level above, '{name}', is not valid: {error.problems[0]}")
    return None


def _inherit(spec: C4Spec, parent: C4Spec, raw: dict[str, Any], read: Reader) -> C4Spec:
    """Fill the neighbours from the level above, and take the frame from the opened box."""
    opened = _opened_element(spec, parent, raw.get("element"), read)
    known = {element.id: element for element in parent.elements}
    opened_id = opened.id if opened else None
    elements = tuple(
        _same_as_above(element, known[element.id])
        if element.id in known and element.id != opened_id
        else element
        for element in spec.elements
    )
    if opened is None:
        return replace(spec, elements=elements)
    tone = opened.tone or KIND_TONES[opened.kind]
    frame = Opened(f"{opened.label} [{FRAME_KIND_NAMES[spec.level]}]", tone)
    return replace(spec, elements=elements, opened=frame)


def _opened_element(spec: C4Spec, parent: C4Spec, name: object, read: Reader) -> Element | None:
    """Return the box of the level above that is opened; report when it is not one."""
    allowed = OPENED_KINDS[spec.level]
    candidates = {e.id: e for e in parent.elements if e.kind in allowed}
    if name in candidates:
        return candidates[name]
    names = ", ".join(sorted(candidates)) or "none"
    read.report(
        "opens", f"'element' names '{name}', which is not a box that can be opened (use: {names})"
    )
    return None


def _same_as_above(element: Element, above: Element) -> Element:
    """Return an element that is also on the level above, with what it leaves out filled in."""
    return replace(
        element,
        kind=above.kind,
        label=element.label or above.label,
        technology=element.technology or above.technology,
        description=element.description or above.description,
        icon=element.icon or above.icon,
        tone=element.tone or above.tone,
        is_outside=True,
    )


def check_diagram(spec: C4Spec) -> list[str]:
    """Report every rule a C4 diagram breaks, in plain sentences.

    Args:
        spec: The spec.

    Returns:
        One sentence per problem; empty when the diagram is allowed.
    """
    problems = [_wrong_level(element, spec.level) for element in spec.elements]
    problems += [_unnamed(element) for element in spec.elements]
    problems += _frame_problems(spec)
    problems += _count_problems(spec)
    return [problem for problem in problems if problem]


def _wrong_level(element: Element, level: int) -> str:
    """Return the problem of a box that does not belong on this level, or ''."""
    if element.kind in LEVEL_KINDS[level]:
        return ""
    return (
        f"element '{element.id}' is a {element.kind.value}, which level {level} does not draw: "
        "one diagram answers one question, so never mix levels in one picture"
    )


def _unnamed(element: Element) -> str:
    """Return the problem of a box that has no name, or ''."""
    if element.label:
        return ""
    return f"element '{element.id}' needs a 'label': its name, without the technology"


def _frame_problems(spec: C4Spec) -> list[str]:
    """Report a context diagram with no single system, or a zoomed one with no parts."""
    kinds = [element.kind for element in spec.elements]
    if spec.level == CONTEXT_LEVEL and kinds.count(Kind.SYSTEM) != 1:
        return ["level 1 draws exactly one software system: the box that the diagram is about"]
    if spec.level != CONTEXT_LEVEL and not any(spec.is_inside(e) for e in spec.elements):
        return [f"level {spec.level} needs at least one box inside the frame"]
    return []


def _count_problems(spec: C4Spec) -> list[str]:
    """Report a diagram with more boxes than a reader can take in (the parts, when it is a zoom)."""
    drawn = [e for e in spec.elements if spec.is_inside(e)] if spec.opened or spec.level > 1 else []
    count = len(drawn) if drawn else len(spec.elements)
    if count <= MAX_ELEMENTS:
        return []
    return [f"{count} boxes is too many (at most {MAX_ELEMENTS}): zoom into a part instead"]


def _with_defaults(spec: C4Spec) -> C4Spec:
    """Give every box the icon and the tint of its kind when the spec leaves them out."""
    elements = tuple(
        replace(
            element,
            icon=element.icon or KIND_ICONS[element.kind],
            tone=element.tone or KIND_TONES[element.kind],
        )
        for element in spec.elements
    )
    return replace(spec, elements=elements)
