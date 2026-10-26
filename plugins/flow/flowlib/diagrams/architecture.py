"""The architecture diagram: components grouped in zones, joined by calls and data flows.

The JSON format::

    {"type": "architecture", "title": "...", "desc": "...", "direction": "down|right",
     "zones": [{"id", "label", "tone", "parent"}],
     "components": [{"id", "label", "kind": "service|client|external|database|store|queue",
                     "detail", "icon", "tone", "zone", "at": [row, column]}],
     "links": [{"from": "component", "to": "component", "label",
                "style": "call|async", "main": true}]}

A ``call`` is a solid line; an ``async`` link (a queue, an event) is dashed. A component in a
zone is drawn inside that zone's frame; a zone with a ``parent`` is drawn inside the parent.
"""

from enum import StrEnum
from typing import Any

from ..model import Direction, Head, Role, Scene, Shape, Tone
from ..reader import Reader, SpecError, suggestion
from ..spec import Spec, SpecEdge, SpecNode, SpecZone, check_explicit_cells
from ..theme import icon_names
from . import flowchart

SPEC_KEYS = {"type", "title", "desc", "direction", "zones", "components", "links", "style"}
ZONE_KEYS = {"id", "label", "tone", "parent"}
COMPONENT_KEYS = {"id", "label", "kind", "detail", "icon", "tone", "zone", "at"}
LINK_KEYS = {"from", "to", "label", "style", "main"}
AT_LENGTH = 2
DEFAULT_ZONE_TONE = Tone.GRAY


class ComponentKind(StrEnum):
    """What a component is; decides its outline."""

    SERVICE = "service"
    CLIENT = "client"
    EXTERNAL = "external"
    DATABASE = "database"
    STORE = "store"
    QUEUE = "queue"


class LinkStyle(StrEnum):
    """A call waits for an answer; an async link does not."""

    CALL = "call"
    ASYNC = "async"


SHAPE_OF_KIND = {
    ComponentKind.SERVICE: Shape.PROCESS,
    ComponentKind.CLIENT: Shape.TERMINATOR,
    ComponentKind.EXTERNAL: Shape.SUBPROCESS,
    ComponentKind.DATABASE: Shape.CYLINDER,
    ComponentKind.STORE: Shape.STORE,
    ComponentKind.QUEUE: Shape.PREPARATION,
}


def _zone(raw: object, where: str, read: Reader) -> SpecZone | None:
    """Build one zone, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ZONE_KEYS, where)
    identifier = read.identifier(raw, where)
    return SpecZone(
        id=identifier,
        label=read.text(raw, "label", where) or identifier,
        tone=read.enum(Tone, raw, "tone", where) or DEFAULT_ZONE_TONE,
        parent=raw.get("parent"),
    )


def _check_zone_parents(zones: dict[str, SpecZone], read: Reader) -> None:
    """Report a zone whose parent is unknown or whose parents form a loop."""
    for zone in zones.values():
        where = f"zone '{zone.id}'"
        if zone.parent is not None and zone.parent not in zones:
            hint = suggestion(zone.parent, zones)
            read.report(where, f"'parent' names '{zone.parent}', which is not a zone{hint}")
            continue
        seen = {zone.id}
        current = zone
        while current.parent in zones:
            current = zones[current.parent]
            if current.id in seen:
                read.report(where, "'parent' makes a loop of zones")
                break
            seen.add(current.id)


def _component(
    raw: object, where: str, read: Reader, known: tuple[set[str], set[str]]
) -> SpecNode | None:
    """Build one component as a node, or report why it cannot be built."""
    icons, zones = known
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, COMPONENT_KEYS, where)
    icon, zone = raw.get("icon"), raw.get("zone")
    if icon is not None and icon not in icons:
        read.report(where, f"unknown icon '{icon}'; use one of: {', '.join(sorted(icons))}")
    if zone is not None and zone not in zones:
        read.report(where, f"'zone' names '{zone}', which is not a zone{suggestion(zone, zones)}")
    at = raw.get("at")
    if at is not None and not (isinstance(at, list) and len(at) == AT_LENGTH):
        read.report(where, "'at' must be [row, column]")
        at = None
    identifier = read.identifier(raw, where)
    kind = read.enum(ComponentKind, raw, "kind", where) or ComponentKind.SERVICE
    return SpecNode(
        id=identifier,
        kind=SHAPE_OF_KIND[kind],
        text=read.text(raw, "label", where) or identifier,
        icon=icon,
        tone=read.enum(Tone, raw, "tone", where),
        number=None,
        side=None,
        lane=None,
        detail=read.text(raw, "detail", where) or "",
        at=(int(at[0]), int(at[1])) if at else None,
        zone=zone,
    )


def _link(
    raw: object, where: str, read: Reader, components: dict[str, SpecNode]
) -> SpecEdge | None:
    """Build one link as an edge, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, LINK_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in components:
            read.report(
                where,
                f"'{key}' names '{name}', which is not a component{suggestion(name, components)}",
            )
        ends.append(name if name in components else "")
    style = read.enum(LinkStyle, raw, "style", where) or LinkStyle.CALL
    return SpecEdge(
        source=ends[0],
        target=ends[1],
        role=Role.MAIN if raw.get("main") is True else Role.DATA,
        label=read.text(raw, "label", where),
        head=Head.FILLED,
        dashed=style is LinkStyle.ASYNC,
    )


def _list(raw: dict[str, Any], key: str) -> list[object]:
    """Return a field that should be a list, or an empty list when it is not one."""
    value = raw.get(key, [])
    return value if isinstance(value, list) else []


def to_spec(raw: object) -> Spec:
    """Check an architecture spec and turn it into the description the layout works on.

    Args:
        raw: The result of ``json.loads`` on an architecture spec.

    Returns:
        The components as nodes, the links as edges and the zones.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    built_zones = [_zone(item, f"zones[{i}]", read) for i, item in enumerate(_list(raw, "zones"))]
    zones = {zone.id: zone for zone in built_zones if zone is not None}
    _check_zone_parents(zones, read)
    known = (icon_names(), set(zones))
    built = [
        _component(item, f"components[{i}]", read, known)
        for i, item in enumerate(_list(raw, "components"))
    ]
    components = {node.id: node for node in built if node is not None}
    check_explicit_cells(components.values(), read)
    if not components:
        read.report("spec", "'components' must list at least one component")
    links = [
        _link(item, f"links[{i}]", read, components) for i, item in enumerate(_list(raw, "links"))
    ]
    direction = read.enum(Direction, raw, "direction", "spec") or Direction.DOWN
    illustrated = read.illustrated(raw, "spec")
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    if read.problems:
        raise SpecError(read.problems)
    return Spec(
        title=title,
        description=description,
        direction=direction,
        lanes=(),
        nodes=tuple(components.values()),
        edges=tuple(edge for edge in links if edge is not None),
        zones=tuple(zones.values()),
        illustrated=illustrated,
    )


def layout_raw(raw: object) -> Scene:
    """Lay out an architecture diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on an architecture spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return flowchart.layout(to_spec(raw))
