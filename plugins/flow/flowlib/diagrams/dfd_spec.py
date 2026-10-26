"""Read and check a data flow diagram spec: ids, levels, forbidden links and balancing.

The JSON format::

    {"type": "dfd", "title": "...", "desc": "...", "style": "plain|illustrated", "level": 0,
     "opens": {"spec": "level1.spec.json", "process": "deliver"},
     "elements": [{"id", "label", "kind": "process|external|store", "detail", "icon", "tone",
                   "number", "at": [row, column]}],
     "flows": [{"from", "to", "label", "main": true, "status": true, "of": "label above"}]}

Numbers are given when the author sets ``number`` and made up when not: ``E1`` for an outside
party, ``D1`` for a store, ``1.0`` for a process of level 1, ``4.1`` for a process inside the
process ``4.0`` that ``opens`` names. A number is never used twice, so a number the author sets
is skipped by the ones that are made up.

``opens`` makes the spec a level 2 diagram: it names the spec of level 1 and the process in it
that this diagram opens. An element of this spec with the id of an element of level 1 is the
same neighbour there, and takes what the spec leaves out (label, number, icon, tone) from it.
Every flow that crossed the opened process must still cross it, from the same neighbour, in the
same direction, with the same label or as a part of it (``of`` names the label above).
"""

import json
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

from ..model import Tone
from ..reader import Reader, SpecError, suggestion
from ..theme import icon_names

SPEC_KEYS = {"type", "title", "desc", "style", "level", "opens", "elements", "flows", "theme"}
ELEMENT_KEYS = {"id", "label", "kind", "detail", "icon", "tone", "number", "at"}
FLOW_KEYS = {"from", "to", "label", "main", "status", "of"}
OPENS_KEYS = {"spec", "process"}
AT_LENGTH = 2
ENTITY_PREFIX = "E"
STORE_PREFIX = "D"
CONTEXT_NUMBER = "0"
LEVELS = (0, 1, 2)
CONTEXT_LEVEL, TOP_LEVEL, OPENED_LEVEL = LEVELS
PROCESS_TONES = (Tone.BLUE, Tone.AMBER, Tone.GREEN, Tone.TEAL, Tone.VIOLET)
ENTITY_TONE = Tone.GRAY
STORE_TONE = Tone.VIOLET
CONTEXT_TONE = Tone.VIOLET


class Kind(StrEnum):
    """What a box of a data flow diagram is."""

    EXTERNAL = "external"
    PROCESS = "process"
    STORE = "store"


@dataclass(frozen=True)
class Element:
    """One box: an outside party, a process or a data store."""

    id: str
    kind: Kind
    label: str
    detail: str = ""
    icon: str | None = None
    tone: Tone | None = None
    number: str | None = None
    at: tuple[float, float] | None = None
    is_outside: bool = False  # a neighbour that belongs to the level above (drawn for reference)


@dataclass(frozen=True)
class Flow:
    """Data moving from one box to another."""

    source: str
    target: str
    label: str
    is_main: bool = False
    is_status: bool = False
    part_of: str | None = None


@dataclass(frozen=True)
class Opened:
    """The process of the level above that this diagram opens."""

    id: str
    number: str
    label: str
    tone: Tone


@dataclass(frozen=True)
class DfdSpec:
    """A checked data flow diagram, with every element numbered and toned."""

    title: str | None
    description: str | None
    level: int
    illustrated: bool
    elements: tuple[Element, ...]
    flows: tuple[Flow, ...]
    opened: Opened | None = None


def read_spec(raw: object, source_dir: Path | None = None) -> DfdSpec:
    """Check a data flow diagram spec and turn it into the description the layout uses.

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
    elements = _read_elements(raw.get("elements", []), read)
    by_id = {element.id: element for element in elements}
    flows = _read_flows(raw.get("flows", []), by_id, read)
    parent = _read_parent(raw.get("opens"), source_dir, read)
    spec = DfdSpec(
        title=read.text(raw, "title", "spec"),
        description=read.text(raw, "desc", "spec"),
        level=OPENED_LEVEL if parent else _level_of(raw, elements, read),
        illustrated=read.illustrated(raw, "spec"),
        elements=tuple(elements),
        flows=tuple(flows),
    )
    if read.problems:
        raise SpecError(read.problems)
    spec = _inherit(spec, parent, raw.get("opens"), read) if parent else spec
    problems = [*read.problems, *check_diagram(spec)]
    if parent:
        problems += check_balance(spec, parent)
    if problems:
        raise SpecError(problems)
    return number_and_tone(spec)


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
    identifier = read.identifier(raw, where)
    icon = raw.get("icon")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    at = raw.get("at")
    if at is not None and not (isinstance(at, list) and len(at) == AT_LENGTH):
        read.report(where, "'at' must be [row, column]")
        at = None
    return Element(
        id=identifier,
        kind=read.enum(Kind, raw, "kind", where) or Kind.PROCESS,
        label=read.text(raw, "label", where) or "",
        detail=read.text(raw, "detail", where) or "",
        icon=icon,
        tone=read.enum(Tone, raw, "tone", where),
        number=read.text(raw, "number", where),
        at=(at[0], at[1]) if at else None,
    )


def _read_flows(raw: object, by_id: dict[str, Element], read: Reader) -> list[Flow]:
    """Read the flows; each end must name an element and each flow needs a label."""
    items = raw if isinstance(raw, list) else []
    flows = []
    for index, item in enumerate(items):
        flow = _flow(item, f"flows[{index}]", by_id, read)
        if flow is not None:
            flows.append(flow)
    return flows


def _flow(raw: object, where: str, by_id: dict[str, Element], read: Reader) -> Flow | None:
    """Build one flow, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, FLOW_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in by_id:
            read.report(
                where, f"'{key}' names '{name}', which is not an element{_hint(name, by_id)}"
            )
        ends.append(name)
    label = read.text(raw, "label", where)
    if not label:
        read.report(where, "needs a 'label': the data that moves, as a noun phrase")
    if ends[0] not in by_id or ends[1] not in by_id or not label:
        return None
    return Flow(
        source=ends[0],
        target=ends[1],
        label=label,
        is_main=raw.get("main") is True,
        is_status=raw.get("status") is True,
        part_of=read.text(raw, "of", where),
    )


def _hint(name: object, by_id: dict[str, Element]) -> str:
    """Return the ``did you mean`` hint for a mistyped id."""
    return suggestion(name, by_id)


def _level_of(raw: dict[str, Any], elements: list[Element], read: Reader) -> int:
    """Return the level the spec asks for, or the one its elements show."""
    asked = raw.get("level")
    if asked is not None and asked not in LEVELS:
        read.report("spec", "'level' must be 0, 1 or 2")
    if asked in LEVELS:
        return asked
    has_store = any(element.kind is Kind.STORE for element in elements)
    processes = [element for element in elements if element.kind is Kind.PROCESS]
    return CONTEXT_LEVEL if len(processes) == 1 and not has_store else TOP_LEVEL


def _read_parent(raw: object, source_dir: Path | None, read: Reader) -> DfdSpec | None:
    """Read the level above that ``opens`` names, or report why it cannot be read."""
    if raw is None:
        return None
    if not isinstance(raw, dict) or not isinstance(raw.get("spec"), str):
        read.report("opens", "must be an object with 'spec' (the file of level 1) and 'process'")
        return None
    read.check_keys(raw, OPENS_KEYS, "opens")
    path = (source_dir or Path()) / raw["spec"]
    try:
        parent_raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        read.report("opens", f"cannot read the level above, '{raw['spec']}': {error}")
        return None
    if isinstance(parent_raw, dict) and "opens" in parent_raw:
        read.report("opens", "the level above must be level 1: do not go past level 2")
        return None
    return read_spec(parent_raw, path.parent)


def _inherit(spec: DfdSpec, parent: DfdSpec, raw: dict[str, Any], read: Reader) -> DfdSpec:
    """Fill the neighbours of the opened process from the level above and mark them as outside."""
    process = _opened_process(parent, raw.get("process"), read)
    known = {element.id: element for element in parent.elements}
    elements = []
    for element in spec.elements:
        above = known.get(element.id)
        elements.append(element if above is None else _outside(element, above, process, read))
    opened = Opened(process.id, process.number or "", process.label, process.tone or ENTITY_TONE)
    return replace(spec, elements=tuple(elements), opened=opened)


def _opened_process(parent: DfdSpec, name: object, read: Reader) -> Element:
    """Return the process of the level above that is opened; report when it is not one."""
    processes = {e.id: e for e in parent.elements if e.kind is Kind.PROCESS}
    if name not in processes:
        read.report("opens", f"'process' names '{name}', which is not a process of level 1")
        raise SpecError(read.problems)
    return processes[name]


def _outside(element: Element, above: Element, process: Element, read: Reader) -> Element:
    """Return an element that is also on the level above, with what it leaves out filled in."""
    if above.id == process.id:
        read.report(f"element '{element.id}'", "is the opened process itself; list its parts")
    if element.kind is not above.kind and element.label:
        read.report(f"element '{element.id}'", f"is a {above.kind.value} on the level above")
    return replace(
        element,
        kind=above.kind,
        label=element.label or above.label,
        detail=element.detail or above.detail,
        icon=element.icon or above.icon,
        tone=element.tone or above.tone,
        number=element.number or above.number,
        is_outside=True,
    )


def check_diagram(spec: DfdSpec) -> list[str]:
    """Report every rule a data flow diagram breaks, in plain sentences.

    Args:
        spec: The spec, with its elements and flows.

    Returns:
        One sentence per problem; empty when the diagram is allowed.
    """
    by_id = {element.id: element for element in spec.elements}
    problems = [_forbidden(flow, by_id) for flow in spec.flows]
    problems += _black_holes(spec)
    problems += _context_rules(spec)
    problems += _duplicate_numbers(spec)
    return [problem for problem in problems if problem]


def _forbidden(flow: Flow, by_id: dict[str, Element]) -> str:
    """Return the problem of a flow between two boxes that may not exchange data, or ''."""
    source, target = by_id[flow.source], by_id[flow.target]
    kinds = {source.kind, target.kind}
    names = f"'{source.label or source.id}' and '{target.label or target.id}'"
    where = f"flow '{flow.label}'"
    if kinds == {Kind.EXTERNAL}:
        return (
            f"{where} joins two external entities, {names}: two outside parties never "
            "exchange data on the diagram, so put the system between them"
        )
    if kinds == {Kind.STORE}:
        return (
            f"{where} joins two data stores, {names}: a store cannot move data by itself, "
            "so show the process that copies it from one to the other"
        )
    if kinds == {Kind.EXTERNAL, Kind.STORE}:
        return (
            f"{where} joins an external entity and a data store, {names}: an entity never "
            "talks to a store directly, so a process must sit between them"
        )
    return ""


def _black_holes(spec: DfdSpec) -> list[str]:
    """Report each inner process that has no flow in or no flow out."""
    problems = []
    for element in spec.elements:
        if element.kind is not Kind.PROCESS or element.is_outside:
            continue
        has_input = any(flow.target == element.id for flow in spec.flows)
        has_output = any(flow.source == element.id for flow in spec.flows)
        name = f"process '{element.label or element.id}'"
        if not has_output:
            problems.append(
                f"{name} has no output (a black hole): every process produces something, "
                "so give it an output flow or remove it"
            )
        if not has_input:
            problems.append(
                f"{name} has no input (a miracle): every process needs data to work on, "
                "so give it an input flow or remove it"
            )
    return problems


def _context_rules(spec: DfdSpec) -> list[str]:
    """Report what a level 0 diagram may not have: stores, or more than one process."""
    if spec.level != CONTEXT_LEVEL:
        return []
    problems = []
    processes = [e for e in spec.elements if e.kind is Kind.PROCESS]
    if len(processes) != 1:
        problems.append(f"level 0 shows the system as one process, but there are {len(processes)}")
    problems += [
        f"level 0 shows only what crosses the border, so the store '{e.label or e.id}' "
        "belongs on level 1"
        for e in spec.elements
        if e.kind is Kind.STORE
    ]
    return problems


def _duplicate_numbers(spec: DfdSpec) -> list[str]:
    """Report a number that two elements both ask for."""
    seen: dict[str, str] = {}
    problems = []
    for element in spec.elements:
        if not element.number:
            continue
        if element.number in seen:
            problems.append(
                f"number '{element.number}' is used by '{seen[element.number]}' and "
                f"'{element.id}': a number is never used twice"
            )
        seen[element.number] = element.id
    return problems


def check_balance(spec: DfdSpec, parent: DfdSpec) -> list[str]:
    """Report each flow that appeared or vanished when the process was opened.

    Args:
        spec: The level 2 diagram, with its neighbours filled in.
        parent: The level 1 diagram it opens.

    Returns:
        One sentence per flow that does not balance.
    """
    opened = spec.opened
    assert opened is not None
    names = {element.id: element.label or element.id for element in parent.elements}
    above = {
        (
            flow.source if flow.target == opened.id else flow.target,
            flow.target == opened.id,
            flow.label,
        )
        for flow in parent.flows
        if opened.id in (flow.source, flow.target)
    }
    inside = {element.id for element in spec.elements if not element.is_outside}
    below = _crossing(spec, inside)
    problems = [
        f"balancing: the flow '{label}' {_describe(neighbour, is_in, names, opened.label)} "
        f"is missing on this level"
        for neighbour, is_in, label in sorted(above)
        if not _is_kept(neighbour, is_in, label, below)
    ]
    problems += [
        f"balancing: the flow '{flow.label}' joins two neighbours of '{opened.label}' and "
        "does not cross it"
        for flow in spec.flows
        if flow.source not in inside and flow.target not in inside
    ]
    problems += [
        f"balancing: the flow '{flow.label}' with '{names.get(neighbour, neighbour)}' was not "
        f"on the level above, where '{opened.label}' had no such flow"
        for neighbour, is_in, flow in below
        if (neighbour, is_in, flow.part_of or flow.label) not in above
        and (neighbour, is_in, flow.label) not in above
    ]
    return problems


def _describe(neighbour: str, is_in: bool, names: dict[str, str], process: str) -> str:
    """Say which way a flow went between a neighbour and the opened process."""
    other = names.get(neighbour, neighbour)
    return f"from '{other}' into '{process}'" if is_in else f"from '{process}' to '{other}'"


def _crossing(spec: DfdSpec, inside: set[str]) -> list[tuple[str, bool, Flow]]:
    """Return the flows between an outside neighbour and an inner box: neighbour, is in, flow."""
    found = []
    for flow in spec.flows:
        if flow.source in inside and flow.target not in inside:
            found.append((flow.target, False, flow))
        elif flow.target in inside and flow.source not in inside:
            found.append((flow.source, True, flow))
    return found


def _is_kept(neighbour: str, is_in: bool, label: str, below: list[tuple[str, bool, Flow]]) -> bool:
    """Tell whether a flow of the level above is still there, whole or as parts."""
    return any(
        near == neighbour and way == is_in and label in (flow.label, flow.part_of)
        for near, way, flow in below
    )


def number_and_tone(spec: DfdSpec) -> DfdSpec:
    """Give every element the number and the tone it will be drawn with.

    Args:
        spec: A checked spec.

    Returns:
        A copy in which every element has a number and a tone.
    """
    used = {element.number for element in spec.elements if element.number}
    counters = {ENTITY_PREFIX: 0, STORE_PREFIX: 0, "process": 0}
    elements = []
    for element in spec.elements:
        number = element.number or _next_number(spec, element, counters, used)
        elements.append(replace(element, number=number, tone=element.tone or _tone(spec, element)))
    return replace(spec, elements=tuple(elements))


def _next_number(spec: DfdSpec, element: Element, counters: dict[str, int], used: set[str]) -> str:
    """Return the next free number for an element, skipping every number in use."""
    key = _counter_key(element)
    while True:
        counters[key] += 1
        number = _format_number(spec, element, counters[key])
        if number not in used:
            used.add(number)
            return number


def _counter_key(element: Element) -> str:
    """Return which counter an element counts on."""
    if element.kind is Kind.EXTERNAL:
        return ENTITY_PREFIX
    return STORE_PREFIX if element.kind is Kind.STORE else "process"


def _format_number(spec: DfdSpec, element: Element, count: int) -> str:
    """Write the number of an element from its count: ``E2``, ``D1``, ``3.0``, ``4.2`` or ``0``."""
    if element.kind is Kind.EXTERNAL:
        return f"{ENTITY_PREFIX}{count}"
    if element.kind is Kind.STORE:
        return f"{STORE_PREFIX}{count}"
    if spec.opened is not None:
        return f"{spec.opened.number.split('.')[0]}.{count}"
    return CONTEXT_NUMBER if spec.level == CONTEXT_LEVEL else f"{count}.0"


def _tone(spec: DfdSpec, element: Element) -> Tone:
    """Return the tone an element has when the spec names none."""
    if element.kind is Kind.EXTERNAL:
        return ENTITY_TONE
    if spec.opened is not None:
        return spec.opened.tone
    if element.kind is Kind.STORE:
        return STORE_TONE
    if spec.level == CONTEXT_LEVEL:
        return CONTEXT_TONE
    processes = [e.id for e in spec.elements if e.kind is Kind.PROCESS]
    return PROCESS_TONES[processes.index(element.id) % len(PROCESS_TONES)]
