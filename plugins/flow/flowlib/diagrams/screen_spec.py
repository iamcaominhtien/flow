"""Read the spec of a screen flow: its screens, decisions, entries and transitions.

The JSON format (design 02)::

    {"type": "screen", "title": "...", "desc": "...", "conditions": "inline|coded", "tab_count": 4,
     "zones": [{"id", "label", "tone"}],
     "screens": [{"id", "label", "kind": "screen|decision|start|end|entry|flag|tab",
                  "code", "state", "overlay", "overlay_title", "device", "orientation", "size",
                  "fidelity": "L0|L1|L2|L3", "content", "hatch", "elements", "tab", "undecided",
                  "trigger", "system", "detail", "icon", "zone", "at": [row, column]}],
     "taps": [{"from", "to", "trigger", "system", "guard", "effect", "kind", "code", "route",
               "main": true}],
     "buses": [{"trigger", "system", "to": ["tab id", ...]}]}

A spec that uses none of the new keys is drawn as plain boxes by the older graph layout.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..model import (
    Content,
    Device,
    ElementStyle,
    Fidelity,
    Layer,
    Orientation,
    Overlay,
    Placement,
    ScreenElement,
    ScreenView,
    Tone,
)
from ..reader import Reader, SpecError, suggestion
from ..spec import SpecZone
from ..theme import icon_names

SCREEN_FLOW = "screen"
AT_LENGTH = 2
ENTRY_AT_LENGTH = 1
DEFAULT_TAB_COUNT = 4
DEFAULT_ZONE_TONE = Tone.GRAY
DEFAULT_HATCH_LABEL = "other content"
MINI_SIZE = "mini"
STATE_SEPARATOR = " · "
OVERLAY_SEPARATOR = " + "
TOP_KEYS = {"type", "title", "desc", "direction", "style", "screens", "taps", "zones", "buses"}
TOP_KEYS |= {"conditions", "tab_count"}
NEW_TOP_KEYS = {"zones", "buses", "conditions", "tab_count"}
ITEM_KEYS = {"id", "label", "kind", "detail", "icon", "tone", "zone", "at"}
NEW_ITEM_KEYS = {"code", "state", "overlay", "overlay_title", "device", "orientation", "size"}
NEW_ITEM_KEYS |= {"fidelity", "content", "hatch", "elements", "tab", "undecided", "trigger"}
NEW_ITEM_KEYS |= {"system"}
LINK_KEYS = {"from", "to", "label", "style", "main", "from_label", "to_label"}
NEW_LINK_KEYS = {"trigger", "system", "guard", "effect", "kind", "code", "route"}
ELEMENT_KEYS = {"text", "style", "at", "on", "hotspot"}
BUS_KEYS = {"trigger", "system", "to"}
ZONE_KEYS = {"id", "label", "tone"}


class ItemKind(StrEnum):
    """What an item of the flow is."""

    SCREEN = "screen"
    DECISION = "decision"
    START = "start"
    END = "end"
    ENTRY = "entry"
    FLAG = "flag"
    TAB = "tab"


class TransitionKind(StrEnum):
    """The role of a transition; it decides the line (design 02 section 7)."""

    FORWARD = "forward"
    BACK = "back"
    RETRY = "retry"
    FAILURE = "failure"
    MAIN = "main"


class Route(StrEnum):
    """Where an arrow runs: in the strip above a row, straight between frames, or as an elbow.

    An elbow leaves the top or bottom of its source and turns once into the side of its target.
    """

    STRIP = "strip"
    DIRECT = "direct"
    ELBOW = "elbow"


class Conditions(StrEnum):
    """Whether guards are written on the arrows or as codes with a table."""

    INLINE = "inline"
    CODED = "coded"


@dataclass(frozen=True)
class Trigger:
    """What starts a transition: a user action, or a system event with an icon."""

    text: str
    system_icon: str | None = None


@dataclass(frozen=True)
class Item:
    """One thing placed on the grid: a screen, a decision, a mark, an entry, a flag or a tab."""

    id: str
    kind: ItemKind
    name: str
    detail: str = ""
    icon: str | None = None
    view: ScreenView | None = None
    zone: str | None = None
    tone: Tone | None = None  # the colour of its id chip, when it differs from its zone
    at: tuple[int, ...] | None = None
    trigger: Trigger | None = None  # on a decision: the system event that decides it


@dataclass(frozen=True)
class Transition:
    """An arrow: ``trigger [guard] / effect`` from one item to another."""

    source: str
    target: str
    trigger: Trigger | None
    guard: str | None
    effect: str | None
    kind: TransitionKind
    code: str | None
    route: Route | None


@dataclass(frozen=True)
class Bus:
    """One line into many tabs, drawn once instead of a pair of arrows per tab."""

    trigger: Trigger
    targets: tuple[str, ...]


@dataclass(frozen=True)
class FlowSpec:
    """A whole screen flow, as the author describes it."""

    title: str | None
    description: str | None
    zones: tuple[SpecZone, ...]
    items: tuple[Item, ...]
    transitions: tuple[Transition, ...]
    buses: tuple[Bus, ...]
    conditions: Conditions


def uses_screen_features(raw: object) -> bool:
    """Tell whether a spec uses a key that only the screen flow of design 02 knows.

    Args:
        raw: The parsed JSON spec.

    Returns:
        False for a spec that older versions drew as plain boxes.
    """
    if not isinstance(raw, dict):
        return False
    if NEW_TOP_KEYS & set(raw):
        return True
    for item in _dicts(raw.get("screens")):
        if NEW_ITEM_KEYS & set(item) or item.get("kind") in NEW_ITEM_KINDS:
            return True
    return any(NEW_LINK_KEYS & set(link) for link in _dicts(raw.get("taps")))


NEW_ITEM_KINDS = {ItemKind.ENTRY.value, ItemKind.FLAG.value, ItemKind.TAB.value}


def parse_flow(raw: object) -> FlowSpec:
    """Check a screen flow spec and turn it into the description the layout works on.

    Args:
        raw: The result of ``json.loads`` on the spec.

    Returns:
        The items, the transitions and the zones.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, TOP_KEYS, "spec")
    zones = _zones(raw, read)
    tab_count = _tab_count(raw, read)
    built = [
        _item(entry, f"screens[{index}]", read, (set(zones), tab_count))
        for index, entry in enumerate(_listed(raw, "screens", read))
    ]
    items = {item.id: item for item in built if item is not None}
    if not items:
        read.report("spec", "'screens' must list at least one item")
    transitions = [
        _transition(entry, f"taps[{index}]", read, set(items))
        for index, entry in enumerate(_listed(raw, "taps", read))
    ]
    buses = [
        _bus(entry, f"buses[{index}]", read, set(items))
        for index, entry in enumerate(_listed(raw, "buses", read))
    ]
    conditions = read.enum(Conditions, raw, "conditions", "spec") or Conditions.INLINE
    if read.problems:
        raise SpecError(read.problems)
    return FlowSpec(
        title=read.text(raw, "title", "spec"),
        description=read.text(raw, "desc", "spec"),
        zones=tuple(zones.values()),
        items=tuple(items.values()),
        transitions=tuple(found for found in transitions if found is not None),
        buses=tuple(found for found in buses if found is not None),
        conditions=conditions,
    )


def _dicts(value: object) -> list[dict[str, Any]]:
    """Return the objects of a field that should be a list of objects."""
    return [entry for entry in value if isinstance(entry, dict)] if isinstance(value, list) else []


def _listed(raw: dict[str, Any], key: str, read: Reader) -> list[object]:
    """Return a field that should be a list, reporting a problem when it is something else."""
    value = raw.get(key, [])
    if isinstance(value, list):
        return value
    read.report("spec", f"'{key}' must be a list")
    return []


def _tab_count(raw: dict[str, Any], read: Reader) -> int:
    """Read how many tabs a tab bar has."""
    count = raw.get("tab_count", DEFAULT_TAB_COUNT)
    if isinstance(count, int) and not isinstance(count, bool) and count > 0:
        return count
    read.report("spec", "'tab_count' must be a positive whole number")
    return DEFAULT_TAB_COUNT


def _zones(raw: dict[str, Any], read: Reader) -> dict[str, SpecZone]:
    """Read the zones: a dashed tinted frame each, with a pill label and one colour."""
    zones: dict[str, SpecZone] = {}
    for index, entry in enumerate(_listed(raw, "zones", read)):
        where = f"zones[{index}]"
        if not isinstance(entry, dict):
            read.report(where, "must be an object")
            continue
        read.check_keys(entry, ZONE_KEYS, where)
        identifier = read.identifier(entry, where)
        tone = read.enum(Tone, entry, "tone", where) or DEFAULT_ZONE_TONE
        label = read.text(entry, "label", where) or identifier
        zones[identifier] = SpecZone(id=identifier, label=label, tone=tone)
    return zones


def _icon(raw: dict[str, Any], key: str, where: str, read: Reader) -> str | None:
    """Read an icon name, which must be in the icon library."""
    name = raw.get(key)
    if name is not None and name not in icon_names():
        read.report(where, f"unknown icon '{name}'; see the icon list in the skill")
    return name if isinstance(name, str) else None


def _trigger(raw: dict[str, Any], key: str, where: str, read: Reader) -> Trigger | None:
    """Read a trigger text and its ``system`` icon: no icon means the user does it."""
    text = read.text(raw, key, where)
    icon = _icon(raw, "system", where, read)
    if text is None:
        if icon is not None:
            read.report(where, "'system' needs a 'trigger' text")
        return None
    return Trigger(text, icon)


def _at(raw: dict[str, Any], kind: ItemKind, where: str, read: Reader) -> tuple[int, ...] | None:
    """Read ``at``: ``[row, column]``, or ``[row]`` for an entry, which has no column."""
    at = raw.get("at")
    if at is None:
        return None
    length = ENTRY_AT_LENGTH if kind is ItemKind.ENTRY else AT_LENGTH
    valid = isinstance(at, list) and all(isinstance(n, int) and n >= 0 for n in at)
    if not valid or len(at) not in {length, AT_LENGTH}:
        read.report(where, "'at' must be [row, column] with whole numbers from 0")
        return None
    return tuple(at)


def _item(raw: object, where: str, read: Reader, known: tuple[set[str], int]) -> Item | None:
    """Build one item, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ITEM_KEYS | NEW_ITEM_KEYS, where)
    kind = read.enum(ItemKind, raw, "kind", where) or ItemKind.SCREEN
    identifier = read.identifier(raw, where)
    zone = raw.get("zone")
    if zone is not None and zone not in known[0]:
        read.report(
            where, f"'zone' names '{zone}', which is not a zone{suggestion(zone, known[0])}"
        )
    name = read.text(raw, "label", where) or ("" if kind in UNNAMED_KINDS else identifier)
    return Item(
        id=identifier,
        kind=kind,
        name=name,
        detail=read.text(raw, "detail", where) or "",
        icon=_icon(raw, "icon", where, read),
        view=_view(raw, identifier, where, (read, known[1], name))
        if kind is ItemKind.SCREEN
        else None,
        zone=zone,
        tone=read.enum(Tone, raw, "tone", where),
        at=_at(raw, kind, where, read),
        trigger=_trigger(raw, "trigger", where, read) if kind is ItemKind.DECISION else None,
    )


UNNAMED_KINDS = {ItemKind.START, ItemKind.END}


def _element(raw: object, where: str, read: Reader) -> ScreenElement | None:
    """Build one named element of a screen from a string or an object."""
    if isinstance(raw, str):
        return ScreenElement(raw)
    if not isinstance(raw, dict):
        read.report(where, "must be a string or an object with a 'text'")
        return None
    read.check_keys(raw, ELEMENT_KEYS, where)
    text = read.text(raw, "text", where)
    if not text:
        read.report(where, "needs a 'text'")
        return None
    return ScreenElement(
        text=text,
        style=read.enum(ElementStyle, raw, "style", where) or ElementStyle.PRIMARY,
        placement=read.enum(Placement, raw, "at", where) or Placement.BOTTOM,
        layer=Layer.OVERLAY if raw.get("on") == Layer.OVERLAY.value else Layer.BASE,
        is_hotspot=raw.get("hotspot", True) is not False,
    )


def _elements(raw: dict[str, Any], where: str, read: Reader) -> tuple[ScreenElement, ...]:
    """Read the named elements of a screen."""
    listed = raw.get("elements", [])
    if not isinstance(listed, list):
        read.report(where, "'elements' must be a list")
        return ()
    found = [_element(entry, f"{where}.elements[{i}]", read) for i, entry in enumerate(listed)]
    return tuple(element for element in found if element is not None)


def _fidelity(raw: dict[str, Any], where: str, read: Reader) -> Fidelity:
    """Read the fidelity level; no level means L0, because nothing is decided until it is said."""
    text = raw.get("fidelity")
    if text is None:
        return Fidelity.L0
    return read.enum(Fidelity, {"fidelity": str(text).upper()}, "fidelity", where) or Fidelity.L0


def _chip_text(raw: dict[str, Any], identifier: str, where: str, read: Reader) -> str:
    """Build the id chip: the code, then ``· state`` and ``+ overlay`` when there are any."""
    text = read.text(raw, "code", where) or identifier
    state = read.text(raw, "state", where)
    overlay = read.enum(Overlay, raw, "overlay", where)
    if state:
        text += STATE_SEPARATOR + state
    if overlay:
        text += OVERLAY_SEPARATOR + overlay.value
    return text


def _view(
    raw: dict[str, Any], identifier: str, where: str, context: tuple[Reader, int, str]
) -> ScreenView:
    """Build what a screen node shows from the keys of its item."""
    read, tab_count, name = context
    tab = raw.get("tab")
    if tab is not None and not (isinstance(tab, int) and 0 <= tab < tab_count):
        read.report(where, f"'tab' must be a whole number below tab_count ({tab_count})")
        tab = None
    size = raw.get("size")
    if size is not None and size != MINI_SIZE:
        read.report(where, f"unknown size '{size}'; use '{MINI_SIZE}' or leave it out")
    return ScreenView(
        code=_chip_text(raw, identifier, where, read),
        title=name,
        device=read.enum(Device, raw, "device", where) or Device.PHONE,
        orientation=read.enum(Orientation, raw, "orientation", where) or Orientation.PORTRAIT,
        is_mini=size == MINI_SIZE,
        fidelity=_fidelity(raw, where, read),
        content=read.enum(Content, raw, "content", where) or Content.HATCH,
        hatch_label=read.text(raw, "hatch", where) or DEFAULT_HATCH_LABEL,
        elements=_elements(raw, where, read),
        overlay=read.enum(Overlay, raw, "overlay", where),
        overlay_title=read.text(raw, "overlay_title", where) or "",
        tab_active=tab if isinstance(tab, int) else None,
        tab_count=tab_count if isinstance(tab, int) else 0,
        is_undecided=raw.get("undecided") is True,
    )


def _kind_of(raw: dict[str, Any], where: str, read: Reader) -> TransitionKind:
    """Read the kind of a transition: ``kind``, else ``main: true``, else the old ``style``."""
    if raw.get("main") is True:
        return TransitionKind.MAIN
    kind = read.enum(TransitionKind, raw, "kind", where)
    if kind is not None:
        return kind
    return TransitionKind.BACK if raw.get("style") == "back" else TransitionKind.FORWARD


def _transition(raw: object, where: str, read: Reader, ids: set[str]) -> Transition | None:
    """Build one transition, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, LINK_KEYS | NEW_LINK_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in ids:
            read.report(
                where, f"'{key}' names '{name}', which is not an item{suggestion(name, ids)}"
            )
        ends.append(name if name in ids else "")
    legacy = {"trigger": raw.get("trigger", raw.get("label")), "system": raw.get("system")}
    return Transition(
        source=ends[0],
        target=ends[1],
        trigger=_trigger(legacy, "trigger", where, read),
        guard=read.text(raw, "guard", where),
        effect=read.text(raw, "effect", where),
        kind=_kind_of(raw, where, read),
        code=read.text(raw, "code", where),
        route=read.enum(Route, raw, "route", where),
    )


def _bus(raw: object, where: str, read: Reader, ids: set[str]) -> Bus | None:
    """Build one bus: a trigger and the tabs it reaches."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, BUS_KEYS, where)
    trigger = _trigger(raw, "trigger", where, read)
    targets = raw.get("to")
    if trigger is None or not isinstance(targets, list) or len(targets) < AT_LENGTH:
        read.report(where, "needs a 'trigger' and a list 'to' of at least two items")
        return None
    for name in targets:
        if name not in ids:
            read.report(where, f"'to' names '{name}', which is not an item{suggestion(name, ids)}")
    return Bus(trigger, tuple(str(name) for name in targets))
