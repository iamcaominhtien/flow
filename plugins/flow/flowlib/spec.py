"""Read a diagram spec: what Claude writes, with meaning but no coordinates.

The JSON format of a flowchart::

    {"type": "flowchart", "title": "...", "desc": "...", "direction": "down",
     "nodes": [{"id", "kind", "text", "icon", "tone", "number", "side"}],
     "edges": [{"from", "to", "role", "label"}]}

``kind`` is a shape name; ``side`` (``left`` or ``right``) asks for a branch on that side.
"""

import json
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from .model import Role, Shape, Side, Tone
from .reader import Reader
from .theme import load_icons

SPEC_KEYS = {"type", "title", "desc", "direction", "nodes", "edges"}
NODE_KEYS = {"id", "kind", "text", "icon", "tone", "number", "side"}
EDGE_KEYS = {"from", "to", "role", "label"}
FLOWCHART = "flowchart"
DIRECTION_DOWN = "down"
MAX_SUGGESTIONS = 1


class SpecError(ValueError):
    """The spec is not valid. The message lists every problem found, one per line."""

    def __init__(self, problems: list[str]) -> None:
        """Keep the problems and join them into the message.

        Args:
            problems: One sentence per problem, each starting with where it was found.
        """
        self.problems = problems
        super().__init__("\n".join(problems))


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


@dataclass(frozen=True)
class SpecEdge:
    """A connection between two steps."""

    source: str
    target: str
    role: Role
    label: str | None


@dataclass(frozen=True)
class Spec:
    """A whole flowchart description."""

    title: str | None
    description: str | None
    nodes: tuple[SpecNode, ...]
    edges: tuple[SpecEdge, ...]


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
        self._check_type(raw)
        nodes = [self._node(item, f"nodes[{i}]") for i, item in enumerate(raw.get("nodes", []))]
        node_ids = [node.id for node in nodes if node is not None]
        if not node_ids:
            read.report("spec", "'nodes' must list at least one node")
        edges = [
            self._edge(item, f"edges[{i}]", node_ids) for i, item in enumerate(raw.get("edges", []))
        ]
        if read.problems:
            raise SpecError(read.problems)
        return Spec(
            title=read.text(raw, "title", "spec"),
            description=read.text(raw, "desc", "spec"),
            nodes=tuple(node for node in nodes if node is not None),
            edges=tuple(edge for edge in edges if edge is not None),
        )

    def _check_type(self, raw: dict[str, Any]) -> None:
        """Report a spec that is not a top-to-bottom flowchart, the only kind built so far."""
        if raw.get("type") != FLOWCHART:
            self._read.report("spec", f"'type' must be '{FLOWCHART}' (the only type so far)")
        direction = raw.get("direction", DIRECTION_DOWN)
        if direction != DIRECTION_DOWN:
            self._read.report("spec", f"'direction' must be '{DIRECTION_DOWN}' (only one so far)")

    def _node(self, raw: object, where: str) -> SpecNode | None:
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
        )

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
        hint = ""
        if isinstance(name, str):
            close = get_close_matches(name, node_ids, n=MAX_SUGGESTIONS)
            hint = f"; did you mean '{close[0]}'?" if close else ""
        self._read.report(where, f"'{end}' names '{name}', which is not a node{hint}")
        return ""
