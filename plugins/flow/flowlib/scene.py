"""Read a scene from JSON, check it, and turn it into the dataclasses of ``model``.

The JSON format::

    {"size": [width, height], "title": "...", "desc": "...",
     "frames": [{"id", "x", "y", "width", "height", "label", "tone", "variant", "guard",
                 "dividers": [{"y", "guard"}]}],
     "nodes":  [{"id", "shape", "x", "y", "width", "height", "text", "icon", "tone",
                 "number", "font_size", "detail": [...], "caption",
                 "sections": [[{"left", "right"}]]}],
     "edges":  [{"id", "from", "to", "role", "points": [[x, y], ...], "head", "tail", "dashed",
                 "label": {"text", "at": [x, y], "kind", "number"},
                 "extras": [{"text", "at": [x, y], "kind"}]}]}
"""

import json
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any, TypeVar

from .model import (
    DEFAULT_FONT_SIZE_PX,
    Divider,
    Edge,
    EdgeLabel,
    Frame,
    FrameVariant,
    Head,
    LabelKind,
    Node,
    Point,
    Role,
    Row,
    Scene,
    Shape,
    Tone,
)
from .reader import POINT_LENGTH, Reader, is_number
from .theme import icon_names

Built = TypeVar("Built")

SCENE_KEYS = {"size", "title", "desc", "frames", "nodes", "edges"}
FRAME_KEYS = {"id", "x", "y", "width", "height", "label", "tone", "variant", "guard", "dividers"}
DIVIDER_KEYS = {"y", "guard"}
NODE_KEYS = {"id", "shape", "x", "y", "width", "height", "text", "icon", "tone"}
NODE_KEYS |= {"number", "font_size", "detail", "caption", "sections", "card"}
ROW_KEYS = {"left", "right"}
EDGE_KEYS = {"id", "from", "to", "role", "points", "head", "tail", "dashed", "label", "extras"}
LABEL_KEYS = {"text", "at", "kind", "number"}
MIN_ROUTE_POINTS = 2


class SceneError(ValueError):
    """The scene is not valid. The message lists every problem found, one per line."""

    def __init__(self, problems: list[str]) -> None:
        """Keep the problems and join them into the message.

        Args:
            problems: One sentence per problem, each starting with where it was found.
        """
        self.problems = problems
        super().__init__("\n".join(problems))


def load(path: str | Path) -> Scene:
    """Read a scene file.

    Args:
        path: A JSON file in the scene format.

    Returns:
        The scene.

    Raises:
        SceneError: If the file is not a valid scene.
    """
    return parse(json.loads(Path(path).read_text(encoding="utf-8")))


def parse(raw: object) -> Scene:
    """Check a parsed JSON value and build the scene from it.

    Args:
        raw: The result of ``json.loads`` on a scene document.

    Returns:
        The scene.

    Raises:
        SceneError: With every problem found, not only the first.
    """
    return _SceneParser().scene(raw)


def dump(scene: Scene) -> dict[str, Any]:
    """Turn a scene back into the JSON format, so that it can be saved and read again.

    Args:
        scene: The scene to write.

    Returns:
        A JSON-style dict that ``parse`` accepts.
    """
    return {
        "size": [scene.width, scene.height],
        "title": scene.title,
        "desc": scene.description,
        "frames": [_dump_frame(frame) for frame in scene.frames],
        "nodes": [_dump_node(node) for node in scene.nodes],
        "edges": [_dump_edge(edge) for edge in scene.edges],
    }


def dumps(scene: Scene, indent: int | None = None) -> str:
    """Write a scene as JSON text.

    Args:
        scene: The scene to write.
        indent: Spaces per level, or None for a single line.

    Returns:
        The JSON text.
    """
    return json.dumps(dump(scene), indent=indent)


def _dump_frame(frame: Frame) -> dict[str, Any]:
    """Write one frame in the JSON format."""
    written: dict[str, Any] = {
        "id": frame.id,
        "x": frame.x,
        "y": frame.y,
        "width": frame.width,
        "height": frame.height,
        "label": frame.label,
        "tone": frame.tone.value,
        "variant": frame.variant.value,
    }
    if frame.guard:
        written["guard"] = frame.guard
    if frame.dividers:
        written["dividers"] = [
            {"y": divider.y, "guard": divider.guard} for divider in frame.dividers
        ]
    return written


def _dump_node(node: Node) -> dict[str, Any]:
    """Write one node in the JSON format, leaving out the fields it does not use."""
    written: dict[str, Any] = {
        "id": node.id,
        "shape": node.shape.value,
        "x": node.x,
        "y": node.y,
        "width": node.width,
        "height": node.height,
        "text": list(node.text),
        "font_size": node.font_size,
    }
    if node.icon:
        written["icon"] = node.icon
    if node.tone:
        written["tone"] = node.tone.value
    if node.number:
        written["number"] = node.number
    if node.detail:
        written["detail"] = list(node.detail)
    if node.caption:
        written["caption"] = node.caption
    if node.card:
        written["card"] = True
    if node.sections:
        written["sections"] = [
            [{"left": row.left, "right": row.right} for row in section] for section in node.sections
        ]
    return written


def _dump_edge(edge: Edge) -> dict[str, Any]:
    """Write one edge in the JSON format, leaving out the fields it does not use."""
    written: dict[str, Any] = {
        "id": edge.id,
        "role": edge.role.value,
        "points": [list(point) for point in edge.points],
        "head": edge.head.value,
        "tail": edge.tail.value,
        "dashed": edge.dashed,
    }
    if edge.source:
        written["from"] = edge.source
    if edge.target:
        written["to"] = edge.target
    if edge.label:
        written["label"] = {
            "text": edge.label.text,
            "at": list(edge.label.at),
            "kind": edge.label.kind.value,
        }
        if edge.label.number:
            written["label"]["number"] = edge.label.number
    if edge.extras:
        written["extras"] = [
            {"text": extra.text, "at": list(extra.at), "kind": extra.kind.value}
            for extra in edge.extras
        ]
    return written


class _SceneParser:
    """Turns raw JSON into a scene while collecting every problem instead of stopping at one."""

    def __init__(self) -> None:
        """Start with an empty reader."""
        self._read = Reader()
        self._icon_names = icon_names()

    def scene(self, raw: object) -> Scene:
        """Build the scene, or raise if anything was wrong.

        Args:
            raw: The parsed JSON document.

        Returns:
            The scene.

        Raises:
            SceneError: If any problem was found.
        """
        if not isinstance(raw, dict):
            raise SceneError(["the scene must be a JSON object"])
        self._read.check_keys(raw, SCENE_KEYS, "scene")
        width, height = self._size(raw.get("size"))
        frames = tuple(self._each(raw, "frames", self._frame))
        nodes = tuple(self._each(raw, "nodes", self._node))
        node_ids = {node.id for node in nodes}
        edges = tuple(self._each(raw, "edges", partial(self._edge, node_ids=node_ids)))
        if self._read.problems:
            raise SceneError(self._read.problems)
        return Scene(
            width=width,
            height=height,
            title=raw.get("title"),
            description=raw.get("desc"),
            frames=frames,
            nodes=nodes,
            edges=edges,
        )

    def _each(
        self,
        raw: dict[str, Any],
        key: str,
        build: Callable[[dict[str, Any], str], Built | None],
    ) -> list[Built]:
        """Build every item of a list field, skipping the ones that are invalid.

        Args:
            raw: The parent object.
            key: The name of the list field (``frames``, ``nodes`` or ``edges``).
            build: A function taking ``(item, where)`` and returning the built item or None.

        Returns:
            The items that were built.
        """
        built = []
        for index, item in enumerate(raw.get(key, [])):
            where = f"{key}[{index}]"
            if not isinstance(item, dict):
                self._read.report(where, "must be an object")
                continue
            result = build(item, where)
            if result is not None:
                built.append(result)
        return built

    def _size(self, raw: object) -> tuple[float, float]:
        """Read ``[width, height]``, reporting a problem when it is malformed."""
        if isinstance(raw, list) and len(raw) == POINT_LENGTH and all(map(is_number, raw)):
            return raw[0], raw[1]
        self._read.report("scene", "'size' must be [width, height]")
        return 0, 0

    def _frame(self, raw: dict[str, Any], where: str) -> Frame:
        """Build one frame."""
        read = self._read
        read.check_keys(raw, FRAME_KEYS, where)
        return Frame(
            id=read.identifier(raw, where),
            x=read.number(raw, "x", where),
            y=read.number(raw, "y", where),
            width=read.extent(raw, "width", where),
            height=read.extent(raw, "height", where),
            label=read.text(raw, "label", where),
            tone=read.enum(Tone, raw, "tone", where) or Tone.GRAY,
            variant=read.enum(FrameVariant, raw, "variant", where) or FrameVariant.AREA,
            guard=read.text(raw, "guard", where),
            dividers=self._dividers(raw.get("dividers", []), where),
        )

    def _dividers(self, raw: object, where: str) -> tuple[Divider, ...]:
        """Read the dividers of a fragment frame."""
        if not isinstance(raw, list):
            self._read.report(where, "'dividers' must be a list")
            return ()
        found = []
        for index, item in enumerate(raw):
            place = f"{where}.dividers[{index}]"
            if not isinstance(item, dict):
                self._read.report(place, "must be an object")
                continue
            self._read.check_keys(item, DIVIDER_KEYS, place)
            found.append(
                Divider(
                    y=self._read.number(item, "y", place),
                    guard=self._read.text(item, "guard", place) or "",
                )
            )
        return tuple(found)

    def _node(self, raw: dict[str, Any], where: str) -> Node:
        """Build one node."""
        read = self._read
        read.check_keys(raw, NODE_KEYS, where)
        shape = read.enum(Shape, raw, "shape", where)
        if "shape" not in raw:
            read.report(where, "'shape' is required")
        return Node(
            id=read.identifier(raw, where),
            shape=shape or Shape.PROCESS,
            x=read.number(raw, "x", where),
            y=read.number(raw, "y", where),
            width=read.extent(raw, "width", where),
            height=read.extent(raw, "height", where),
            text=self._lines(raw.get("text", ""), where),
            icon=self._icon(raw, where),
            tone=read.enum(Tone, raw, "tone", where),
            number=read.text(raw, "number", where),
            font_size=raw.get("font_size", DEFAULT_FONT_SIZE_PX),
            detail=self._lines(raw.get("detail", []), where),
            caption=read.text(raw, "caption", where),
            sections=self._sections(raw.get("sections", []), where),
            card=raw.get("card") is True,
        )

    def _sections(self, raw: object, where: str) -> tuple[tuple[Row, ...], ...]:
        """Read the row groups of a table node."""
        if not isinstance(raw, list):
            self._read.report(where, "'sections' must be a list of lists of rows")
            return ()
        sections = []
        for index, group in enumerate(raw):
            rows = []
            for row_index, item in enumerate(group if isinstance(group, list) else []):
                place = f"{where}.sections[{index}][{row_index}]"
                if not isinstance(item, dict):
                    self._read.report(place, "must be an object")
                    continue
                self._read.check_keys(item, ROW_KEYS, place)
                rows.append(
                    Row(
                        left=self._read.text(item, "left", place) or "",
                        right=self._read.text(item, "right", place) or "",
                    )
                )
            sections.append(tuple(rows))
        return tuple(sections)

    def _lines(self, raw: object, where: str) -> tuple[str, ...]:
        """Read node text, given as one string or as a list of lines."""
        if isinstance(raw, str):
            return (raw,) if raw else ()
        if isinstance(raw, list) and all(isinstance(line, str) for line in raw):
            return tuple(raw)
        self._read.report(where, "'text' must be a string or a list of lines")
        return ()

    def _icon(self, raw: dict[str, Any], where: str) -> str | None:
        """Read an icon name, which must be in the icon library."""
        name = raw.get("icon")
        if name is not None and name not in self._icon_names:
            self._read.report(where, f"unknown icon '{name}'")
        return name

    def _edge(self, raw: dict[str, Any], where: str, node_ids: set[str]) -> Edge:
        """Build one edge.

        Args:
            raw: The edge object.
            where: Where the edge is, for messages.
            node_ids: The ids of all nodes, which ``from`` and ``to`` must name.

        Returns:
            The edge.
        """
        read = self._read
        read.check_keys(raw, EDGE_KEYS, where)
        for end in ("from", "to"):
            if end in raw and raw[end] not in node_ids:
                read.report(where, f"'{end}' names '{raw[end]}', which is not a node")
        return Edge(
            id=read.identifier(raw, where),
            role=read.enum(Role, raw, "role", where) or Role.NEXT,
            points=self._route(raw.get("points"), where),
            label=self._label(raw.get("label"), where),
            source=raw.get("from"),
            target=raw.get("to"),
            head=read.enum(Head, raw, "head", where) or Head.FILLED,
            tail=read.enum(Head, raw, "tail", where) or Head.NONE,
            dashed=raw.get("dashed", False) is True,
            extras=self._extras(raw.get("extras", []), where),
        )

    def _extras(self, raw: object, where: str) -> tuple[EdgeLabel, ...]:
        """Read the small labels at the ends of an edge."""
        if not isinstance(raw, list):
            self._read.report(where, "'extras' must be a list")
            return ()
        found = [self._label(item, f"{where}.extras[{index}]") for index, item in enumerate(raw)]
        return tuple(label for label in found if label is not None)

    def _route(self, raw: object, where: str) -> tuple[Point, ...]:
        """Read the routed points of an edge, at least two of them."""
        if not isinstance(raw, list) or len(raw) < MIN_ROUTE_POINTS:
            self._read.report(where, "'points' must be a list of at least two [x, y] pairs")
            return ()
        points = [self._read.point(item, f"{where}.points") for item in raw]
        return tuple(point for point in points if point is not None)

    def _label(self, raw: object, where: str) -> EdgeLabel | None:
        """Read the label of an edge, or None when there is none."""
        if raw is None:
            return None
        where = f"{where}.label"
        if not isinstance(raw, dict) or not isinstance(raw.get("text"), str):
            self._read.report(where, "needs a 'text'")
            return None
        self._read.check_keys(raw, LABEL_KEYS, where)
        at = self._read.point(raw.get("at"), f"{where}.at")
        kind = self._read.enum(LabelKind, raw, "kind", where) or LabelKind.PLAIN
        number = self._read.text(raw, "number", where)
        return EdgeLabel(text=raw["text"], at=at, kind=kind, number=number) if at else None
