"""Read and check a BPMN spec: pools, lanes, events, tasks, gateways and flows.

The JSON format::

    {"type": "bpmn", "title": "...", "desc": "...",
     "zones": [{"id", "label", "tone", "parent", "black_box": true}],
     "elements": [{"id", "label", "kind", "zone", "tone", "trigger", "repeat", "attached_to",
                   "interrupting": false, "column", "row", "number"}],
     "flows": [{"from", "to", "label", "style": "sequence|message|return|data", "main": true,
                "failure": true}]}

A zone without ``parent`` is a pool; a zone with a ``parent`` is a lane of that pool. A pool
with ``black_box`` is drawn as a bar with its name only: no element names it as its zone, and a
message flow may start or end on it by naming its id. Time runs left to right.

``kind`` is one of the ``ItemKind`` values: events (``start``, ``end``, ``event``, ``timer``,
``message``, ``error``, ``signal``), tasks (``task``, ``user``, ``service``, ``send``,
``receive``, ``manual``, ``subprocess``), gateways (``gateway``, ``exclusive``, ``parallel``,
``inclusive``, ``event_based``), ``document`` and ``store`` (a data store). ``trigger`` puts a
mark in a start, end or event: ``message``, ``timer``, ``error`` or ``signal``. ``repeat`` is
``loop`` or ``multi`` (one instance per item). ``attached_to`` puts an event on the edge of a
task as a boundary event; ``interrupting`` false draws its ring dashed.
"""

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any

from ..model import Marker, Shape, Tone
from ..reader import Reader, SpecError, suggestion

SPEC_KEYS = {"type", "title", "desc", "zones", "elements", "flows", "style", "direction", "theme"}
ZONE_KEYS = {"id", "label", "tone", "parent", "black_box"}
ITEM_KEYS = {"id", "label", "kind", "zone", "tone", "trigger", "repeat", "attached_to"}
ITEM_KEYS |= {"interrupting", "column", "row", "number"}
LINK_KEYS = {"from", "to", "label", "style", "main", "failure"}
DEFAULT_ZONE_TONE = Tone.GRAY


class ItemKind(StrEnum):
    """What an element of a BPMN diagram is."""

    START = "start"
    END = "end"
    EVENT = "event"
    TIMER = "timer"
    MESSAGE = "message"
    ERROR = "error"
    SIGNAL = "signal"
    TASK = "task"
    USER = "user"
    SERVICE = "service"
    SEND = "send"
    RECEIVE = "receive"
    MANUAL = "manual"
    SUBPROCESS = "subprocess"
    GATEWAY = "gateway"
    EXCLUSIVE = "exclusive"
    PARALLEL = "parallel"
    INCLUSIVE = "inclusive"
    EVENT_BASED = "event_based"
    DOCUMENT = "document"
    STORE = "store"


class Repeat(StrEnum):
    """How a task is repeated."""

    LOOP = "loop"
    MULTI = "multi"


class LinkStyle(StrEnum):
    """What a flow means: the order of work, a message, a return, or data read or written."""

    SEQUENCE = "sequence"
    MESSAGE = "message"
    RETURN = "return"
    DATA = "data"


@dataclass(frozen=True)
class Look:
    """How a kind is drawn: its outline and the marks that name it."""

    shape: Shape
    markers: tuple[Marker, ...] = ()


LOOKS: dict[ItemKind, Look] = {
    ItemKind.START: Look(Shape.START),
    ItemKind.END: Look(Shape.END),
    ItemKind.EVENT: Look(Shape.INTERMEDIATE),
    ItemKind.TIMER: Look(Shape.INTERMEDIATE, (Marker.TIMER,)),
    ItemKind.MESSAGE: Look(Shape.INTERMEDIATE, (Marker.MESSAGE,)),
    ItemKind.ERROR: Look(Shape.INTERMEDIATE, (Marker.ERROR,)),
    ItemKind.SIGNAL: Look(Shape.INTERMEDIATE, (Marker.SIGNAL,)),
    ItemKind.TASK: Look(Shape.TASK),
    ItemKind.USER: Look(Shape.TASK, (Marker.USER,)),
    ItemKind.SERVICE: Look(Shape.TASK, (Marker.SERVICE,)),
    ItemKind.SEND: Look(Shape.TASK, (Marker.MESSAGE_FILLED,)),
    ItemKind.RECEIVE: Look(Shape.TASK, (Marker.MESSAGE,)),
    ItemKind.MANUAL: Look(Shape.TASK, (Marker.MANUAL,)),
    ItemKind.SUBPROCESS: Look(Shape.TASK, (Marker.SUBPROCESS,)),
    ItemKind.GATEWAY: Look(Shape.DECISION),
    ItemKind.EXCLUSIVE: Look(Shape.DECISION, (Marker.CROSS,)),
    ItemKind.PARALLEL: Look(Shape.DECISION, (Marker.PLUS,)),
    ItemKind.INCLUSIVE: Look(Shape.DECISION, (Marker.CIRCLE,)),
    ItemKind.EVENT_BASED: Look(Shape.DECISION, (Marker.EVENT_BASED,)),
    ItemKind.DOCUMENT: Look(Shape.DOCUMENT),
    ItemKind.STORE: Look(Shape.CYLINDER),
}
EVENT_KINDS = (
    ItemKind.START,
    ItemKind.END,
    ItemKind.EVENT,
    ItemKind.TIMER,
    ItemKind.MESSAGE,
    ItemKind.ERROR,
    ItemKind.SIGNAL,
)
TRIGGERABLE_KINDS = (ItemKind.START, ItemKind.END, ItemKind.EVENT)
TASK_KINDS = (
    ItemKind.TASK,
    ItemKind.USER,
    ItemKind.SERVICE,
    ItemKind.SEND,
    ItemKind.RECEIVE,
    ItemKind.MANUAL,
    ItemKind.SUBPROCESS,
)
GATEWAY_KINDS = (
    ItemKind.GATEWAY,
    ItemKind.EXCLUSIVE,
    ItemKind.PARALLEL,
    ItemKind.INCLUSIVE,
    ItemKind.EVENT_BASED,
)
TRIGGER_MARKERS: dict[str, Marker] = {
    "message": Marker.MESSAGE,
    "timer": Marker.TIMER,
    "error": Marker.ERROR,
    "signal": Marker.SIGNAL,
}
REPEAT_MARKERS: dict[Repeat, Marker] = {
    Repeat.LOOP: Marker.LOOP,
    Repeat.MULTI: Marker.MULTI_INSTANCE,
}


@dataclass(frozen=True)
class Lane:
    """A role inside a pool."""

    id: str
    label: str
    tone: Tone


@dataclass(frozen=True)
class Pool:
    """One participant. Without lanes it holds its elements itself."""

    id: str
    label: str
    tone: Tone
    lanes: tuple[Lane, ...] = ()
    is_black_box: bool = False


@dataclass(frozen=True)
class Item:
    """One element: an event, a task, a gateway, a document or a data store."""

    id: str
    kind: ItemKind
    label: str
    pool: str | None
    lane: str | None
    tone: Tone | None = None
    markers: tuple[Marker, ...] = ()
    attached_to: str | None = None
    is_interrupting: bool = True
    column: int | None = None
    row: int | None = None
    number: str | None = None


@dataclass(frozen=True)
class Link:
    """A flow between two elements, or between an element and a black-box pool."""

    source: str
    target: str
    label: str
    style: LinkStyle
    is_main: bool = False
    is_failure: bool = False


@dataclass(frozen=True)
class BpmnSpec:
    """A checked BPMN diagram."""

    title: str | None
    description: str | None
    pools: tuple[Pool, ...]
    items: tuple[Item, ...]
    links: tuple[Link, ...]


def read_spec(raw: object) -> BpmnSpec:
    """Check a BPMN spec and turn it into the description the layout uses.

    Args:
        raw: The result of ``json.loads`` on the spec.

    Returns:
        The checked spec.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    pools, zone_of = _read_zones(raw.get("zones", []), read)
    items = _read_items(raw.get("elements", []), zone_of, read)
    by_id = {item.id: item for item in items}
    links = _read_links(
        raw.get("flows", []), (by_id, {p.id for p in pools if p.is_black_box}), read
    )
    spec = BpmnSpec(
        title=read.text(raw, "title", "spec"),
        description=read.text(raw, "desc", "spec"),
        pools=tuple(pools),
        items=tuple(_with_pools(items, by_id)),
        links=tuple(links),
    )
    if read.illustrated(raw, "spec"):
        read.report("spec", "BPMN has one style: the shapes are the standard, so use 'plain'")
    problems = read.problems or check_diagram(spec)
    if problems:
        raise SpecError(problems)
    return spec


def _read_zones(raw: object, read: Reader) -> tuple[list[Pool], dict[str, tuple[str, str | None]]]:
    """Read the zones as pools and lanes; return them and where each element zone leads."""
    items = raw if isinstance(raw, list) else []
    built = [_zone(item, f"zones[{index}]", read) for index, item in enumerate(items)]
    zones = [zone for zone in built if zone is not None]
    ids = {zone["id"] for zone in zones}
    for zone in zones:
        parent = zone["parent"]
        if parent is not None and parent not in ids:
            read.report(f"zone '{zone['id']}'", f"'parent' names '{parent}', which is not a zone")
    pools: list[Pool] = []
    zone_of: dict[str, tuple[str, str | None]] = {}
    for zone in (z for z in zones if z["parent"] is None):
        lanes = tuple(
            Lane(z["id"], z["label"] or z["id"], z["tone"])
            for z in zones
            if z["parent"] == zone["id"]
        )
        label = zone["label"] or ("" if lanes else zone["id"])
        pools.append(Pool(zone["id"], label, zone["tone"], lanes, zone["black_box"]))
        zone_of[zone["id"]] = (zone["id"], None)
        zone_of.update({lane.id: (zone["id"], lane.id) for lane in lanes})
    _check_zone_depth(zones, read)
    return pools, zone_of


def _zone(raw: object, where: str, read: Reader) -> dict[str, Any] | None:
    """Read one zone into a plain record, or report why it cannot be read."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ZONE_KEYS, where)
    identifier = read.identifier(raw, where)
    return {
        "id": identifier,
        "label": read.text(raw, "label", where),
        "tone": read.enum(Tone, raw, "tone", where) or DEFAULT_ZONE_TONE,
        "parent": raw.get("parent"),
        "black_box": raw.get("black_box") is True,
    }


def _check_zone_depth(zones: list[dict[str, Any]], read: Reader) -> None:
    """Report a lane inside a lane, and a black-box pool that has lanes."""
    parents = {zone["id"]: zone for zone in zones}
    for zone in zones:
        above = parents.get(zone["parent"])
        if above is not None and above["parent"] is not None:
            read.report(f"zone '{zone['id']}'", "a lane cannot hold lanes: a pool has one level")
        if above is not None and above["black_box"]:
            read.report(f"zone '{zone['id']}'", "a black-box pool shows no lanes")


def _read_items(
    raw: object, zone_of: dict[str, tuple[str, str | None]], read: Reader
) -> list[Item]:
    """Read the elements; one that is not valid is reported and left out."""
    if not isinstance(raw, list) or not raw:
        read.report("spec", "'elements' must list at least one element")
        return []
    built = [_item(item, f"elements[{index}]", zone_of, read) for index, item in enumerate(raw)]
    return [item for item in built if item is not None]


def _item(
    raw: object, where: str, zone_of: dict[str, tuple[str, str | None]], read: Reader
) -> Item | None:
    """Build one element, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ITEM_KEYS, where)
    identifier = read.identifier(raw, where)
    kind = read.enum(ItemKind, raw, "kind", where) or ItemKind.TASK
    zone = raw.get("zone")
    if zone is not None and zone not in zone_of:
        read.report(where, f"'zone' names '{zone}', which is not a zone{suggestion(zone, zone_of)}")
    pool, lane = zone_of.get(zone, (None, None)) if zone is not None else (None, None)
    return Item(
        id=identifier,
        kind=kind,
        label=read.text(raw, "label", where) or "",
        pool=pool,
        lane=lane,
        tone=read.enum(Tone, raw, "tone", where),
        markers=_markers(raw, kind, where, read),
        attached_to=raw.get("attached_to"),
        is_interrupting=raw.get("interrupting", True) is not False,
        column=_whole(raw, "column", where, read),
        row=_whole(raw, "row", where, read),
        number=read.text(raw, "number", where),
    )


def _whole(raw: dict[str, Any], key: str, where: str, read: Reader) -> int | None:
    """Read an optional whole number."""
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    read.report(where, f"'{key}' must be a whole number")
    return None


def _markers(raw: dict[str, Any], kind: ItemKind, where: str, read: Reader) -> tuple[Marker, ...]:
    """Return the marks of an element: those of its kind, its trigger and its repeat."""
    marks = list(LOOKS[kind].markers)
    trigger = raw.get("trigger")
    if trigger is not None:
        if kind not in TRIGGERABLE_KINDS:
            read.report(where, "'trigger' belongs to a start, end or event element")
        elif trigger not in TRIGGER_MARKERS:
            read.report(
                where, f"unknown trigger '{trigger}'; use one of: {', '.join(TRIGGER_MARKERS)}"
            )
        else:
            marks.append(TRIGGER_MARKERS[trigger])
    repeat = read.enum(Repeat, raw, "repeat", where)
    if repeat is not None:
        if kind not in TASK_KINDS:
            read.report(where, "'repeat' belongs to a task")
        marks.append(REPEAT_MARKERS[repeat])
    return tuple(marks)


def _read_links(raw: object, known: tuple[dict[str, Item], set[str]], read: Reader) -> list[Link]:
    """Read the flows; each end must name an element, or a black-box pool for a message."""
    items = raw if isinstance(raw, list) else []
    built = [_link(item, f"flows[{index}]", known, read) for index, item in enumerate(items)]
    return [link for link in built if link is not None]


def _link(
    raw: object, where: str, known: tuple[dict[str, Item], set[str]], read: Reader
) -> Link | None:
    """Build one flow, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, LINK_KEYS, where)
    by_id, boxes = known
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in by_id and name not in boxes:
            read.report(
                where, f"'{key}' names '{name}', which is not an element{suggestion(name, by_id)}"
            )
        ends.append(name)
    style = read.enum(LinkStyle, raw, "style", where) or LinkStyle.SEQUENCE
    if (ends[0] not in by_id and ends[0] not in boxes) or (
        ends[1] not in by_id and ends[1] not in boxes
    ):
        return None
    return Link(
        source=ends[0],
        target=ends[1],
        label=read.text(raw, "label", where) or "",
        style=style,
        is_main=raw.get("main") is True,
        is_failure=raw.get("failure") is True,
    )


def _with_pools(items: list[Item], by_id: dict[str, Item]) -> list[Item]:
    """Give a boundary event the pool and lane of its task, and a data store those of its task."""
    resolved = []
    for item in items:
        host = by_id.get(item.attached_to or "")
        if host is not None and item.pool is None:
            item = replace(item, pool=host.pool, lane=host.lane)
        resolved.append(item)
    return resolved


def check_diagram(spec: BpmnSpec) -> list[str]:
    """Report every rule a BPMN diagram breaks, in plain sentences.

    Args:
        spec: The spec, with its elements and flows.

    Returns:
        One sentence per problem; empty when the diagram is allowed.
    """
    problems = _check_zones(spec)
    problems += _check_boundaries(spec)
    problems += _check_flows(spec)
    problems += _check_events(spec)
    return problems


def _check_zones(spec: BpmnSpec) -> list[str]:
    """Report an element in no pool when there are pools, or in a black-box pool or a laned pool."""
    pools = {pool.id: pool for pool in spec.pools}
    problems = []
    for item in spec.items:
        if item.kind is ItemKind.STORE and item.pool is None:
            continue
        if pools and item.pool is None:
            problems.append(
                f"element '{item.id}' needs a 'zone': when there are zones, each element "
                "sits in one"
            )
            continue
        pool = pools.get(item.pool or "")
        if pool is None:
            continue
        if pool.is_black_box:
            problems.append(
                f"element '{item.id}' is in the black-box pool '{pool.label}', which shows "
                "no elements"
            )
        elif pool.lanes and item.lane is None:
            problems.append(
                f"element '{item.id}' is in pool '{pool.label}': name one of its lanes as the zone"
            )
    return problems


def _check_boundaries(spec: BpmnSpec) -> list[str]:
    """Report a boundary event that is not an event or not on a task."""
    by_id = {item.id: item for item in spec.items}
    problems = []
    for item in spec.items:
        if item.attached_to is None:
            continue
        host = by_id.get(item.attached_to)
        if host is None or host.kind not in TASK_KINDS:
            problems.append(f"element '{item.id}': 'attached_to' must name a task")
        if item.kind not in EVENT_KINDS or item.kind in (ItemKind.START, ItemKind.END):
            problems.append(
                f"element '{item.id}': only an intermediate event can sit on a task edge"
            )
    return problems


def _pool_of(name: str, by_id: dict[str, Item]) -> str | None:
    """Return the pool of an element, or the id of a black-box pool that is named directly."""
    item = by_id.get(name)
    return item.pool if item is not None else name


def _check_flows(spec: BpmnSpec) -> list[str]:
    """Report a sequence flow across pools, a message flow inside one, and a misused data flow."""
    by_id = {item.id: item for item in spec.items}
    problems = []
    for link in spec.links:
        where = f"flow {link.source} to {link.target}"
        source_pool, target_pool = (
            _pool_of(link.source, by_id),
            _pool_of(link.target, by_id),
        )
        ends = [by_id.get(link.source), by_id.get(link.target)]
        if (
            link.style is LinkStyle.MESSAGE
            and source_pool == target_pool
            and source_pool is not None
        ):
            problems.append(
                f"{where} is a message flow inside one pool: messages go between pools, "
                "use a sequence flow"
            )
        elif (
            link.style in (LinkStyle.SEQUENCE, LinkStyle.RETURN)
            and source_pool != target_pool
            and spec.pools
        ):
            problems.append(f"{where} is a sequence flow between two pools: use a message flow")
        if link.style is LinkStyle.DATA and not _is_data_link(ends):
            problems.append(f"{where}: a data flow joins a data store and a task")
        elif link.style is not LinkStyle.DATA and any(
            e is not None and e.kind is ItemKind.STORE for e in ends
        ):
            problems.append(f"{where}: a data store is joined with style 'data'")
    return problems


def _is_data_link(ends: list[Item | None]) -> bool:
    """Tell whether a flow joins a data store and a task."""
    first, second = ends
    if first is None or second is None:
        return False
    kinds = {first.kind is ItemKind.STORE, second.kind is ItemKind.STORE}
    return kinds == {True, False} and (first.kind in TASK_KINDS or second.kind in TASK_KINDS)


def _check_events(spec: BpmnSpec) -> list[str]:
    """Report a start event with a flow into it and an end event with a flow out of it."""
    problems = []
    sequence = [link for link in spec.links if link.style is not LinkStyle.MESSAGE]
    for item in spec.items:
        if item.kind is ItemKind.START and any(link.target == item.id for link in sequence):
            problems.append(
                f"start event '{item.id}' has a flow into it: a start event begins a flow"
            )
        if item.kind is ItemKind.END and any(link.source == item.id for link in sequence):
            problems.append(
                f"end event '{item.id}' has a flow out of it: an end event finishes a flow"
            )
    return problems
