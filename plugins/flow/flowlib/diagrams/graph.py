"""A diagram type of the graph family, described by data: its words, its kinds and its lines.

Flowchart-like types (DFD, C4, cloud, BPMN, use case, class, screen flow) differ only in what
the nodes and lines are called, which outline a kind gets, and how a line style is drawn. Each
is a ``GraphType`` value; this module reads any of them into a ``Spec`` and lays it out.

The JSON format, with the words of the type in place of ``nodes`` and ``links``::

    {"type": "...", "title": "...", "desc": "...", "direction": "down|right",
     "zones": [{"id", "label", "tone", "parent"}],
     "<nodes>": [{"id", "label", "kind", "detail", "icon", "tone", "zone", "at": [row, column]}],
     "<links>": [{"from", "to", "label", "style", "main": true, "from_label", "to_label"}]}
"""

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from ..model import Direction, Head, Role, Row, Scene, Shape, Tone
from ..reader import Reader, SpecError, suggestion
from ..spec import Spec, SpecEdge, SpecLane, SpecNode, SpecZone, check_explicit_cells
from ..theme import icon_names
from . import flowchart

AT_LENGTH = 2
CAPTIONED_SHAPES = {
    Shape.ACTOR,
    Shape.INTERMEDIATE,
    Shape.START,
    Shape.END,
}  # a figure or a ring: the label goes under it
DEFAULT_ZONE_TONE = Tone.GRAY
NODE_KEYS = {"id", "label", "kind", "detail", "icon", "tone", "zone", "at"}
LINK_KEYS = {"from", "to", "label", "style", "main", "from_label", "to_label"}
ZONE_KEYS = {"id", "label", "tone", "parent"}
Extra = Callable[[dict[str, Any], str, Reader], dict[str, Any]]


@dataclass(frozen=True)
class LineKind:
    """How a line style is drawn: dashed or solid, and what is at each end."""

    dashed: bool = False
    head: Head = Head.FILLED
    tail: Head = Head.NONE
    role: Role | None = None  # the line role this style implies, when it is not the type's default


@dataclass(frozen=True)
class GraphType:
    """Everything that makes one graph-family type different from another."""

    name: str
    nodes_key: str
    links_key: str
    kinds: dict[str, Shape]
    default_kind: str
    line_kinds: dict[str, LineKind]
    default_line: str
    default_role: Role = Role.NEXT
    unlabelled_kinds: frozenset[str] = frozenset()
    has_zones: bool = False
    side_by_side: bool = False  # branches inside one lane share a rank instead of stacking
    zones_are_lanes: bool = False  # zones become swimlanes: every item sits in exactly one
    extra_node_keys: frozenset[str] = frozenset()
    kind_icons: dict[str, str] = field(default_factory=dict, compare=False)
    extra: Extra | None = field(default=None, compare=False)

    @property
    def spec_keys(self) -> set[str]:
        """Return the keys the top level of a spec may have."""
        keys = {"type", "title", "desc", "direction", "style", self.nodes_key, self.links_key}
        return keys | ({"zones"} if self.has_zones else set())


@dataclass
class _Context:
    """What reading one spec needs: the problem collector, the type and what is known so far."""

    read: Reader
    graph: GraphType
    zones: set[str] = field(default_factory=set)
    nodes: dict[str, SpecNode] = field(default_factory=dict)


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
        seen, current = {zone.id}, zone
        while current.parent in zones:
            current = zones[current.parent]
            if current.id in seen:
                read.report(where, "'parent' makes a loop of zones")
                break
            seen.add(current.id)


def _node(raw: object, where: str, context: _Context) -> SpecNode | None:
    """Build one node of the type, or report why it cannot be built."""
    read, graph, zones = context.read, context.graph, context.zones
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, NODE_KEYS | graph.extra_node_keys, where)
    icon, zone = raw.get("icon"), raw.get("zone")
    icon = icon if icon is not None else graph.kind_icons.get(raw.get("kind", ""))
    if icon is not None and icon not in icon_names():
        known = ", ".join(sorted(icon_names()))
        read.report(where, f"unknown icon '{icon}'; use one of: {known}")
    if zone is not None and zone not in zones:
        read.report(where, f"'zone' names '{zone}', which is not a zone{suggestion(zone, zones)}")
    at = raw.get("at")
    if at is not None and not (isinstance(at, list) and len(at) == AT_LENGTH):
        read.report(where, "'at' must be [row, column]")
        at = None
    identifier = read.identifier(raw, where)
    kind = raw.get("kind", graph.default_kind)
    if kind not in graph.kinds:
        read.report(where, f"unknown kind '{kind}'; use one of: {', '.join(graph.kinds)}")
        kind = graph.default_kind
    fallback = "" if kind in graph.unlabelled_kinds else identifier
    label = read.text(raw, "label", where) or fallback
    captioned = graph.kinds[kind] in CAPTIONED_SHAPES
    fields = {"detail": read.text(raw, "detail", where) or ""}
    fields.update({"caption": label} if captioned else {})
    if graph.extra is not None:
        fields.update(graph.extra(raw, where, read))
    return SpecNode(
        id=identifier,
        kind=graph.kinds[kind],
        text="" if captioned else label,
        icon=icon,
        tone=read.enum(Tone, raw, "tone", where),
        number=None,
        side=None,
        lane=None,
        at=(int(at[0]), int(at[1])) if at else None,
        zone=zone,
        **fields,
    )


def _link(raw: object, where: str, context: _Context) -> SpecEdge | None:
    """Build one link of the type, or report why it cannot be built."""
    read, graph, nodes = context.read, context.graph, context.nodes
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, LINK_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in nodes:
            hint = suggestion(name, nodes)
            read.report(where, f"'{key}' names '{name}', which is not a {graph.name} item{hint}")
        ends.append(name if name in nodes else "")
    style = raw.get("style", graph.default_line)
    if style not in graph.line_kinds:
        read.report(where, f"unknown style '{style}'; use one of: {', '.join(graph.line_kinds)}")
        style = graph.default_line
    line = graph.line_kinds[style]
    return SpecEdge(
        source=ends[0],
        target=ends[1],
        role=Role.MAIN if raw.get("main") is True else line.role or graph.default_role,
        label=read.text(raw, "label", where),
        head=line.head,
        tail=line.tail,
        dashed=line.dashed,
        start_label=read.text(raw, "from_label", where),
        end_label=read.text(raw, "to_label", where),
    )


def _require_lane(nodes: dict[str, SpecNode], read: Reader) -> None:
    """Report an item with no zone, for a type whose zones are swimlanes."""
    for node in nodes.values():
        if node.zone is None:
            read.report(
                f"item '{node.id}'", "needs a 'zone': when there are zones, each item sits in one"
            )


def _as_lanes(spec: Spec) -> Spec:
    """Turn the zones of a spec into swimlanes, and each item's zone into its lane."""
    lanes = tuple(SpecLane(zone.id, zone.label, zone.tone) for zone in spec.zones)
    nodes = tuple(replace(node, lane=node.zone, zone=None) for node in spec.nodes)
    return replace(spec, lanes=lanes, nodes=nodes, zones=())


def _list(raw: dict[str, Any], key: str) -> list[object]:
    """Return a field that should be a list, or an empty list when it is not one."""
    value = raw.get(key, [])
    return value if isinstance(value, list) else []


def to_spec(graph: GraphType, raw: object) -> Spec:
    """Check a spec of a graph-family type and turn it into the description the layout uses.

    Args:
        graph: The type the spec is for.
        raw: The result of ``json.loads`` on the spec.

    Returns:
        The nodes, the edges and the zones.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, graph.spec_keys, "spec")
    built = [_zone(item, f"zones[{i}]", read) for i, item in enumerate(_list(raw, "zones"))]
    zones = {zone.id: zone for zone in built if zone is not None}
    _check_zone_parents(zones, read)
    context = _Context(read, graph, set(zones))
    items = [
        _node(item, f"{graph.nodes_key}[{i}]", context)
        for i, item in enumerate(_list(raw, graph.nodes_key))
    ]
    nodes = context.nodes = {node.id: node for node in items if node is not None}
    if not nodes:
        read.report("spec", f"'{graph.nodes_key}' must list at least one item")
    links = [
        _link(item, f"{graph.links_key}[{i}]", context)
        for i, item in enumerate(_list(raw, graph.links_key))
    ]
    direction = read.enum(Direction, raw, "direction", "spec") or Direction.DOWN
    illustrated = read.illustrated(raw, "spec")
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    check_explicit_cells(nodes.values(), read)
    if graph.zones_are_lanes and zones:
        _require_lane(nodes, read)
    if read.problems:
        raise SpecError(read.problems)
    spec = Spec(
        title=title,
        description=description,
        direction=direction,
        lanes=(),
        nodes=tuple(nodes.values()),
        edges=tuple(link for link in links if link is not None),
        zones=tuple(zones.values()),
        illustrated=illustrated,
        side_by_side=graph.side_by_side,
    )
    return _as_lanes(spec) if graph.zones_are_lanes else spec


def layout_with(graph: GraphType) -> Callable[[object], Scene]:
    """Return the layout function of a type, as the registry wants it.

    Args:
        graph: The type.

    Returns:
        A function from a parsed JSON spec to a scene; it raises ``SpecError`` for a bad spec.
    """
    return lambda raw: flowchart.layout(to_spec(graph, raw))


def rows_from(raw: dict[str, Any], key: str, where: str, read: Reader) -> tuple[Row, ...]:
    """Read a list of strings as table rows.

    Args:
        raw: The object that holds the list.
        key: The field name.
        where: Where the object is, for messages.
        read: The reader that collects problems.

    Returns:
        One row per string; empty when the field is absent.
    """
    items = raw.get(key, [])
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        read.report(where, f"'{key}' must be a list of strings")
        return ()
    return tuple(Row(item) for item in items)
