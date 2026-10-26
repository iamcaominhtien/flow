"""Read and check an architecture diagram spec: zones, components and lines.

The JSON format::

    {"type": "architecture", "title": "...", "desc": "...", "style": "plain|illustrated",
     "zones": [{"id", "label", "tone", "parent", "beside"}],
     "components": [{"id", "label", "detail", "icon", "tone", "zone", "at": [row, column]}],
     "links": [{"from", "to", "label", "kind": "call|main|event|copy", "main": true}]}

A top-level zone is a layer: layers run top to bottom in the order of the spec. A zone with
``parent`` sits inside another zone, in its row. A zone with ``beside`` (the id of a layer)
shares the row of that layer, to the right of it: a third party. A component with no ``zone`` is
outside every layer and goes in a row above them. ``from`` and ``to`` may name a zone: the line
then starts or ends on the edge of the frame and means "any part inside".
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..model import Tone
from ..reader import Reader, SpecError, suggestion
from ..theme import icon_names

SPEC_KEYS = {"type", "title", "desc", "style", "zones", "components", "links", "theme"}
ZONE_KEYS = {"id", "label", "tone", "parent", "beside"}
COMPONENT_KEYS = {"id", "label", "detail", "icon", "tone", "zone", "at"}
LINK_KEYS = {"from", "to", "label", "kind", "main"}
AT_LENGTH = 2
DEFAULT_ZONE_TONE = Tone.GRAY


class LinkKind(StrEnum):
    """What a line is: a call, the main path, an event, or an optional line or a copy."""

    CALL = "call"
    MAIN = "main"
    EVENT = "event"
    COPY = "copy"


@dataclass(frozen=True)
class Zone:
    """A frame: a layer, a third party, or a group inside a layer."""

    id: str
    label: str
    tone: Tone
    parent: str | None = None
    beside: str | None = None


@dataclass(frozen=True)
class Component:
    """One part of the system."""

    id: str
    label: str
    detail: str = ""
    icon: str | None = None
    tone: Tone | None = None
    zone: str | None = None
    at: tuple[float, float] | None = None


@dataclass(frozen=True)
class Link:
    """A line from the part that starts the call to the one that receives it."""

    source: str
    target: str
    label: str
    kind: LinkKind = LinkKind.CALL


@dataclass(frozen=True)
class ArchitectureSpec:
    """A checked architecture diagram."""

    title: str | None
    description: str | None
    illustrated: bool
    zones: tuple[Zone, ...]
    components: tuple[Component, ...]
    links: tuple[Link, ...]

    def top_zone(self, zone_id: str | None) -> Zone | None:
        """Return the outermost zone around a zone id, or None for no zone."""
        by_id = {zone.id: zone for zone in self.zones}
        zone = by_id.get(zone_id or "")
        while zone is not None and zone.parent in by_id:
            zone = by_id[zone.parent]
        return zone


def read_spec(raw: object) -> ArchitectureSpec:
    """Check an architecture spec and turn it into the description the layout uses.

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
    zones = _read_zones(raw.get("zones", []), read)
    by_zone = {zone.id: zone for zone in zones}
    components = _read_components(raw.get("components", []), by_zone, read)
    ends = {*(c.id for c in components), *by_zone}
    links = _read_links(raw.get("links", []), ends, read)
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    illustrated = read.illustrated(raw, "spec")
    if read.problems:
        raise SpecError(read.problems)
    return ArchitectureSpec(
        title=title,
        description=description,
        illustrated=illustrated,
        zones=tuple(zones),
        components=tuple(components),
        links=tuple(links),
    )


def _items(raw: dict[str, Any] | list[Any] | object) -> list[object]:
    """Return a field that should be a list, or an empty list when it is not one."""
    return raw if isinstance(raw, list) else []


def _read_zones(raw: object, read: Reader) -> list[Zone]:
    """Read the zones; an item that is not valid is reported and left out."""
    built = [_zone(item, f"zones[{i}]", read) for i, item in enumerate(_items(raw))]
    zones = [zone for zone in built if zone is not None]
    known = {zone.id: zone for zone in zones}
    for zone in zones:
        _check_zone(zone, known, read)
    return zones


def _zone(raw: object, where: str, read: Reader) -> Zone | None:
    """Build one zone, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ZONE_KEYS, where)
    identifier = read.identifier(raw, where)
    return Zone(
        id=identifier,
        label=read.text(raw, "label", where) or identifier,
        tone=read.enum(Tone, raw, "tone", where) or DEFAULT_ZONE_TONE,
        parent=raw.get("parent"),
        beside=raw.get("beside"),
    )


def _check_zone(zone: Zone, known: dict[str, Zone], read: Reader) -> None:
    """Report a zone whose parent or ``beside`` is unknown, or whose parents make a loop."""
    where = f"zone '{zone.id}'"
    for key, name in (("parent", zone.parent), ("beside", zone.beside)):
        if name is not None and name not in known:
            read.report(
                where, f"'{key}' names '{name}', which is not a zone{suggestion(name, known)}"
            )
    if zone.beside is not None and zone.parent is not None:
        read.report(where, "'beside' belongs to a layer: a zone cannot have a parent as well")
    if zone.beside in known and known[zone.beside].parent is not None:
        read.report(where, "'beside' must name a layer, a zone that has no parent")
    seen = {zone.id}
    current = zone
    while current.parent in known:
        current = known[current.parent]
        if current.id in seen:
            read.report(where, "'parent' makes a loop of zones")
            return
        seen.add(current.id)


def _read_components(raw: object, zones: dict[str, Zone], read: Reader) -> list[Component]:
    """Read the components; an item that is not valid is reported and left out."""
    items = _items(raw)
    if not items:
        read.report("spec", "'components' must list at least one component")
    built = [_component(item, f"components[{i}]", zones, read) for i, item in enumerate(items)]
    return [component for component in built if component is not None]


def _component(raw: object, where: str, zones: dict[str, Zone], read: Reader) -> Component | None:
    """Build one component, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, COMPONENT_KEYS, where)
    icon, zone = raw.get("icon"), raw.get("zone")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    if zone is not None and zone not in zones:
        read.report(where, f"'zone' names '{zone}', which is not a zone{suggestion(zone, zones)}")
    at = raw.get("at")
    if at is not None and not (isinstance(at, list) and len(at) == AT_LENGTH):
        read.report(where, "'at' must be [row, column]")
        at = None
    identifier = read.identifier(raw, where)
    return Component(
        id=identifier,
        label=read.text(raw, "label", where) or identifier,
        detail=read.text(raw, "detail", where) or "",
        icon=icon,
        tone=read.enum(Tone, raw, "tone", where),
        zone=zone,
        at=(at[0], at[1]) if at else None,
    )


def _read_links(raw: object, ends: set[str], read: Reader) -> list[Link]:
    """Read the links; each end names a component or a zone, and each link needs a label."""
    built = [_link(item, f"links[{i}]", ends, read) for i, item in enumerate(_items(raw))]
    return [link for link in built if link is not None]


def _link(raw: object, where: str, ends: set[str], read: Reader) -> Link | None:
    """Build one link, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, LINK_KEYS, where)
    names = [raw.get("from"), raw.get("to")]
    for key, name in zip(("from", "to"), names, strict=True):
        if name not in ends:
            read.report(
                where,
                f"'{key}' names '{name}', which is not a component or a zone"
                f"{suggestion(name, ends)}",
            )
    kind = LinkKind.MAIN if raw.get("main") is True else read.enum(LinkKind, raw, "kind", where)
    label = read.text(raw, "label", where)
    if not label:
        read.report(
            where, "needs a 'label': a protocol (HTTPS, SQL) or an action (charge, publish)"
        )
    if names[0] not in ends or names[1] not in ends or not label:
        return None
    return Link(names[0], names[1], label, kind or LinkKind.CALL)
