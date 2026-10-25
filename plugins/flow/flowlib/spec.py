"""Read a diagram spec: what Claude writes, with meaning but no coordinates.

The JSON format of a flowchart::

    {"type": "flowchart", "title": "...", "desc": "...", "direction": "down",
     "lanes": [{"id", "label", "tone"}],
     "nodes": [{"id", "kind", "text", "icon", "tone", "number", "side", "lane"}],
     "edges": [{"from", "to", "role", "label"}]}

``kind`` is a shape name; ``side`` (``left`` or ``right``) asks for a branch on that side;
``direction`` is ``down`` (default) or ``right``; with ``lanes``, every node names its lane.
"""

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .model import Direction, Head, Role, Row, Shape, Side, Tone
from .reader import Reader, SpecError, suggestion
from .theme import load_icons

SPEC_KEYS = {"type", "title", "desc", "direction", "lanes", "nodes", "edges", "style"}
NODE_KEYS = {"id", "kind", "text", "icon", "tone", "number", "side", "lane", "detail"}
LANE_KEYS = {"id", "label", "tone"}
EDGE_KEYS = {"from", "to", "role", "label"}
FLOWCHART = "flowchart"


@dataclass(frozen=True)
class SpecLane:
    """A swimlane: a band that holds the steps of one actor."""

    id: str
    label: str
    tone: Tone


@dataclass(frozen=True)
class SpecNode:
    """One step of the diagram, as the author describes it."""

    id: str
    kind: Shape
    text: str
    icon: str | None
    tone: Tone | None
    number: str | None
    side: Side | None
    lane: str | None
    detail: str = ""
    caption: str | None = None
    sections: tuple[tuple[Row, ...], ...] = ()
    at: tuple[int, int] | None = None  # (row, column) on an explicit grid
    zone: str | None = None
    card: bool = False


@dataclass(frozen=True)
class SpecZone:
    """A frame that groups nodes, and may sit inside another zone."""

    id: str
    label: str
    tone: Tone
    parent: str | None = None


@dataclass(frozen=True)
class SpecEdge:
    """A connection between two steps."""

    source: str
    target: str
    role: Role
    label: str | None
    head: Head = Head.FILLED
    tail: Head = Head.NONE
    dashed: bool = False
    start_label: str | None = None
    end_label: str | None = None


@dataclass(frozen=True)
class Spec:
    """A whole flowchart description."""

    title: str | None
    description: str | None
    direction: Direction
    lanes: tuple[SpecLane, ...]
    nodes: tuple[SpecNode, ...]
    edges: tuple[SpecEdge, ...]
    zones: tuple[SpecZone, ...] = ()
    illustrated: bool = False


def load(path: str | Path) -> Spec:
    """Read a spec file.

    Args:
        path: A JSON file in the spec format.

    Returns:
        The spec.

    Raises:
        SpecError: If the file is not a valid spec.
    """
    return parse(json.loads(Path(path).read_text(encoding="utf-8")))


def parse(raw: object) -> Spec:
    """Check a parsed JSON value and build the spec from it.

    Args:
        raw: The result of ``json.loads`` on a spec document.

    Returns:
        The spec.

    Raises:
        SpecError: With every problem found, not only the first.
    """
    return _SpecParser().spec(raw)


class _SpecParser:
    """Turns raw JSON into a spec while collecting every problem."""

    def __init__(self) -> None:
        """Start with an empty reader."""
        self._read = Reader()
        self._icon_names = load_icons().keys()

    def spec(self, raw: object) -> Spec:
        """Build the spec, or raise if anything was wrong.

        Args:
            raw: The parsed JSON document.

        Returns:
            The spec.

        Raises:
            SpecError: If any problem was found.
        """
        if not isinstance(raw, dict):
            raise SpecError(["the spec must be a JSON object"])
        read = self._read
        read.check_keys(raw, SPEC_KEYS, "spec")
        if raw.get("type") != FLOWCHART:
            read.report("spec", f"'type' must be '{FLOWCHART}' (the only type so far)")
        lanes = [self._lane(item, f"lanes[{i}]") for i, item in enumerate(raw.get("lanes", []))]
        lane_ids = [lane.id for lane in lanes if lane is not None]
        nodes = [
            self._node(item, f"nodes[{i}]", lane_ids) for i, item in enumerate(raw.get("nodes", []))
        ]
        node_ids = [node.id for node in nodes if node is not None]
        if not node_ids:
            read.report("spec", "'nodes' must list at least one node")
        edges = [
            self._edge(item, f"edges[{i}]", node_ids) for i, item in enumerate(raw.get("edges", []))
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
            lanes=tuple(lane for lane in lanes if lane is not None),
            nodes=tuple(node for node in nodes if node is not None),
            edges=tuple(edge for edge in edges if edge is not None),
            illustrated=illustrated,
        )

    def _lane(self, raw: object, where: str) -> SpecLane | None:
        """Build one swimlane, or report why it cannot be built."""
        read = self._read
        if not isinstance(raw, dict):
            read.report(where, "must be an object")
            return None
        read.check_keys(raw, LANE_KEYS, where)
        return SpecLane(
            id=read.identifier(raw, where),
            label=read.text(raw, "label", where) or "",
            tone=read.enum(Tone, raw, "tone", where) or Tone.GRAY,
        )

    def _node(self, raw: object, where: str, lane_ids: list[str]) -> SpecNode | None:
        """Build one node, or report why it cannot be built."""
        read = self._read
        if not isinstance(raw, dict):
            read.report(where, "must be an object")
            return None
        read.check_keys(raw, NODE_KEYS, where)
        if "kind" not in raw:
            read.report(where, "'kind' is required")
        icon = raw.get("icon")
        if icon is not None and icon not in self._icon_names:
            read.report(where, f"unknown icon '{icon}'; use one of: {', '.join(self._icon_names)}")
        return SpecNode(
            id=read.identifier(raw, where),
            kind=read.enum(Shape, raw, "kind", where) or Shape.PROCESS,
            text=read.text(raw, "text", where) or "",
            icon=icon,
            tone=read.enum(Tone, raw, "tone", where),
            number=read.text(raw, "number", where),
            side=read.enum(Side, raw, "side", where),
            lane=self._lane_of(raw, where, lane_ids),
            detail=read.text(raw, "detail", where) or "",
        )

    def _lane_of(self, raw: dict[str, Any], where: str, lane_ids: list[str]) -> str | None:
        """Read the lane of a node: required when lanes exist, forbidden when none do."""
        lane = raw.get("lane")
        if lane_ids and lane not in lane_ids:
            self._read.report(where, f"'lane' must be one of: {', '.join(lane_ids)}")
        elif not lane_ids and lane is not None:
            self._read.report(where, "'lane' needs a 'lanes' list at the top of the spec")
        return lane

    def _edge(self, raw: object, where: str, node_ids: list[str]) -> SpecEdge | None:
        """Build one edge, checking that both ends name a node."""
        read = self._read
        if not isinstance(raw, dict):
            read.report(where, "must be an object")
            return None
        read.check_keys(raw, EDGE_KEYS, where)
        ends = [self._end(raw, end, where, node_ids) for end in ("from", "to")]
        return SpecEdge(
            source=ends[0],
            target=ends[1],
            role=read.enum(Role, raw, "role", where) or Role.NEXT,
            label=read.text(raw, "label", where),
        )

    def _end(self, raw: dict[str, Any], end: str, where: str, node_ids: list[str]) -> str:
        """Read the node id at one end of an edge, suggesting a close match for a typo."""
        name = raw.get(end)
        if name in node_ids:
            return name
        hint = suggestion(name, node_ids)
        self._read.report(where, f"'{end}' names '{name}', which is not a node{hint}")
        return ""


CARD_KINDS = (Shape.PROCESS, Shape.SUBPROCESS)  # outlines that become cards when they have an icon


def with_cards(spec: Spec) -> Spec:
    """Mark the nodes that an illustrated spec draws as cards: boxes that have an icon.

    Args:
        spec: A description that asked for the illustrated style.

    Returns:
        A copy in which each box with an icon has ``card`` set; the other nodes are unchanged.
    """
    nodes = tuple(
        replace(node, card=True) if node.kind in CARD_KINDS and node.icon else node
        for node in spec.nodes
    )
    return replace(spec, nodes=nodes)
