"""Hand fixes applied to a laid-out scene: move a node, re-route a line, move a label.

The JSON format, kept beside the spec as ``<name>.overrides.json``::

    {"nodes": {"pay": {"x": 120, "y": 340}},
     "edges": {"e3": {"points": [[10, 10], [10, 90]], "label_at": [30, 50]}}}

An override replaces the value the layout chose. It is applied after the layout, before the
page and the draw.io file are written, so both outputs get the fix and the diagram can still
be rebuilt from its spec.
"""

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .model import Edge, EdgeLabel, Node, Point, Scene
from .reader import Reader

NODE_OVERRIDE_KEYS = {"x", "y"}
EDGE_OVERRIDE_KEYS = {"points", "label_at"}
ROOT_KEYS = {"nodes", "edges"}


class OverridesError(ValueError):
    """The overrides are not valid. The message lists every problem found, one per line."""

    def __init__(self, problems: list[str]) -> None:
        """Keep the problems and join them into the message.

        Args:
            problems: One sentence per problem, each starting with where it was found.
        """
        self.problems = problems
        super().__init__("\n".join(problems))


@dataclass(frozen=True)
class NodeOverride:
    """A new position for a node; a field left as None keeps the laid-out value."""

    x: float | None
    y: float | None


@dataclass(frozen=True)
class EdgeOverride:
    """A new route and/or label position for an edge; None keeps the laid-out value."""

    points: tuple[Point, ...] | None
    label_at: Point | None


@dataclass(frozen=True)
class Overrides:
    """All the hand fixes of one diagram."""

    nodes: dict[str, NodeOverride]
    edges: dict[str, EdgeOverride]


def load(path: str | Path) -> Overrides:
    """Read an overrides file.

    Args:
        path: A JSON file in the overrides format.

    Returns:
        The overrides.

    Raises:
        OverridesError: If the file is not valid.
    """
    return parse(json.loads(Path(path).read_text(encoding="utf-8")))


def parse(raw: object) -> Overrides:
    """Check a parsed JSON value and build the overrides from it.

    Args:
        raw: The result of ``json.loads`` on an overrides document.

    Returns:
        The overrides.

    Raises:
        OverridesError: With every problem found.
    """
    read = Reader()
    if not isinstance(raw, dict):
        raise OverridesError(["the overrides must be a JSON object"])
    read.check_keys(raw, ROOT_KEYS, "overrides")
    nodes = {
        name: _node_override(read, item, f"nodes.{name}")
        for name, item in _items(read, raw, "nodes")
    }
    edges = {
        name: _edge_override(read, item, f"edges.{name}")
        for name, item in _items(read, raw, "edges")
    }
    if read.problems:
        raise OverridesError(read.problems)
    return Overrides(nodes=nodes, edges=edges)


def _items(read: Reader, raw: dict[str, Any], key: str) -> list[tuple[str, dict[str, Any]]]:
    """Return the ``(id, object)`` pairs of one section, reporting entries that are not objects."""
    section = raw.get(key, {})
    if not isinstance(section, dict):
        read.report("overrides", f"'{key}' must be an object that maps ids to overrides")
        return []
    pairs = []
    for name, item in section.items():
        if isinstance(item, dict):
            pairs.append((name, item))
        else:
            read.report(f"{key}.{name}", "must be an object")
    return pairs


def _optional_number(read: Reader, raw: dict[str, Any], key: str, where: str) -> float | None:
    """Read a number field that may be absent."""
    return read.number(raw, key, where) if key in raw else None


def _node_override(read: Reader, raw: dict[str, Any], where: str) -> NodeOverride:
    """Build the override of one node."""
    read.check_keys(raw, NODE_OVERRIDE_KEYS, where)
    return NodeOverride(
        x=_optional_number(read, raw, "x", where), y=_optional_number(read, raw, "y", where)
    )


def _edge_override(read: Reader, raw: dict[str, Any], where: str) -> EdgeOverride:
    """Build the override of one edge."""
    read.check_keys(raw, EDGE_OVERRIDE_KEYS, where)
    points = None
    if "points" in raw:
        listed = raw["points"] if isinstance(raw["points"], list) else []
        found = [read.point(item, f"{where}.points") for item in listed]
        if len(found) < 2 or None in found:  # noqa: PLR2004 - a route needs two points
            read.report(where, "'points' must be a list of at least two [x, y] pairs")
        points = tuple(point for point in found if point is not None)
    label_at = read.point(raw["label_at"], f"{where}.label_at") if "label_at" in raw else None
    return EdgeOverride(points=points, label_at=label_at)


def apply(scene: Scene, overrides: Overrides) -> Scene:
    """Apply the overrides to a scene.

    Args:
        scene: The laid-out scene.
        overrides: The hand fixes.

    Returns:
        A new scene. The canvas size is not changed; ``build.fit_canvas`` does that.

    Raises:
        OverridesError: If an override names a node or an edge that the scene does not have.
    """
    node_ids = {node.id for node in scene.nodes}
    edge_ids = {edge.id for edge in scene.edges}
    problems = [f"nodes.{name}: no such node" for name in overrides.nodes if name not in node_ids]
    problems += [f"edges.{name}: no such edge" for name in overrides.edges if name not in edge_ids]
    if problems:
        raise OverridesError(problems)
    nodes = tuple(_moved(node, overrides.nodes.get(node.id)) for node in scene.nodes)
    edges = tuple(_rerouted(edge, overrides.edges.get(edge.id)) for edge in scene.edges)
    return replace(scene, nodes=nodes, edges=edges)


def _moved(node: Node, override: NodeOverride | None) -> Node:
    """Return the node at its overridden position, or the node itself without an override."""
    if override is None:
        return node
    return replace(
        node,
        x=node.x if override.x is None else override.x,
        y=node.y if override.y is None else override.y,
    )


def _rerouted(edge: Edge, override: EdgeOverride | None) -> Edge:
    """Return the edge with its overridden route and label position, or the edge itself."""
    if override is None:
        return edge
    label = edge.label
    if label is not None and override.label_at is not None:
        label = EdgeLabel(text=label.text, at=override.label_at, kind=label.kind)
    points = edge.points if override.points is None else override.points
    return replace(edge, points=points, label=label)
