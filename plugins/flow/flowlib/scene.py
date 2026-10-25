"""Read a scene from JSON, check it, and turn it into the dataclasses of ``model``.

The JSON format::

    {"size": [width, height], "title": "...", "desc": "...",
     "frames": [{"id", "x", "y", "width", "height", "label", "tone"}],
     "nodes":  [{"id", "shape", "x", "y", "width", "height", "text", "icon", "tone",
                 "number", "font_size"}],
     "edges":  [{"id", "from", "to", "role", "points": [[x, y], ...], "arrow",
                 "label": {"text", "at": [x, y], "kind"}}]}
"""

import json
from collections.abc import Callable, Collection
from enum import StrEnum
from functools import partial
from pathlib import Path
from typing import Any, TypeVar

from .model import (
    DEFAULT_FONT_SIZE_PX,
    ArrowEnd,
    Edge,
    EdgeLabel,
    Frame,
    LabelKind,
    Node,
    Point,
    Role,
    Scene,
    Shape,
    Tone,
)
from .theme import load_icons

Member = TypeVar("Member", bound=StrEnum)
Built = TypeVar("Built")

SCENE_KEYS = {"size", "title", "desc", "frames", "nodes", "edges"}
FRAME_KEYS = {"id", "x", "y", "width", "height", "label", "tone"}
NODE_KEYS = {"id", "shape", "x", "y", "width", "height", "text", "icon", "tone"}
NODE_KEYS |= {"number", "font_size"}
EDGE_KEYS = {"id", "from", "to", "role", "points", "arrow", "label"}
LABEL_KEYS = {"text", "at", "kind"}
MIN_ROUTE_POINTS = 2
POINT_LENGTH = 2


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
    return _Parser(load_icons().keys()).scene(raw)


class _Parser:
    """Turns raw JSON into a scene while collecting every problem instead of stopping at one."""

    def __init__(self, icon_names: Collection[str]) -> None:
        """Start with no problems and no ids seen.

        Args:
            icon_names: The icon names a node may use.
        """
        self._problems: list[str] = []
        self._seen_ids: set[str] = set()
        self._icon_names = icon_names

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
        self._check_keys(raw, SCENE_KEYS, "scene")
        width, height = self._size(raw.get("size"))
        frames = tuple(self._each(raw, "frames", self._frame))
        nodes = tuple(self._each(raw, "nodes", self._node))
        node_ids = {node.id for node in nodes}
        edges = tuple(self._each(raw, "edges", partial(self._edge, node_ids=node_ids)))
        if self._problems:
            raise SceneError(self._problems)
        return Scene(
            width=width,
            height=height,
            title=raw.get("title"),
            description=raw.get("desc"),
            frames=frames,
            nodes=nodes,
            edges=edges,
        )

    def _report(self, where: str, message: str) -> None:
        """Record one problem."""
        self._problems.append(f"{where}: {message}")

    def _check_keys(self, raw: dict[str, Any], allowed: set[str], where: str) -> None:
        """Report every key that is not in ``allowed``."""
        for key in sorted(set(raw) - allowed):
            self._report(where, f"unknown field '{key}'")

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
                self._report(where, "must be an object")
                continue
            result = build(item, where)
            if result is not None:
                built.append(result)
        return built

    def _size(self, raw: object) -> tuple[float, float]:
        """Read ``[width, height]``, reporting a problem when it is malformed."""
        if isinstance(raw, list) and len(raw) == POINT_LENGTH and all(map(_is_number, raw)):
            return raw[0], raw[1]
        self._report("scene", "'size' must be [width, height]")
        return 0, 0

    def _identifier(self, raw: dict[str, Any], where: str) -> str:
        """Read an id, which must be a non-empty string used only once."""
        ident = raw.get("id")
        if not isinstance(ident, str) or not ident:
            self._report(where, "'id' must be a non-empty string")
            return ""
        if ident in self._seen_ids:
            self._report(where, f"id '{ident}' is used twice")
        self._seen_ids.add(ident)
        return ident

    def _number(self, raw: dict[str, Any], key: str, where: str) -> float:
        """Read a number field, reporting a problem when it is missing or not a number."""
        value = raw.get(key)
        if _is_number(value):
            return value
        self._report(where, f"'{key}' must be a number")
        return 0

    def _extent(self, raw: dict[str, Any], key: str, where: str) -> float:
        """Read a width or a height, which must be a positive number."""
        value = self._number(raw, key, where)
        if _is_number(raw.get(key)) and value <= 0:
            self._report(where, f"'{key}' must be positive")
        return value

    def _enum(
        self, enum_type: type[Member], raw: dict[str, Any], key: str, where: str
    ) -> Member | None:
        """Read a field that must be a member of an enum, or None when it is absent.

        Args:
            enum_type: The enum that lists the allowed values.
            raw: The object that holds the field.
            key: The field name.
            where: Where the object is, for the message.

        Returns:
            The member, or None when the field is absent or not a member (a problem is
            reported for the second case).
        """
        if key not in raw:
            return None
        try:
            return enum_type(raw[key])
        except ValueError:
            allowed = ", ".join(member.value for member in enum_type)
            self._report(where, f"unknown {key} '{raw[key]}'; use one of: {allowed}")
            return None

    def _point(self, raw: object, where: str) -> Point | None:
        """Read an ``[x, y]`` pair, or report a problem."""
        if isinstance(raw, list) and len(raw) == POINT_LENGTH and all(map(_is_number, raw)):
            return raw[0], raw[1]
        self._report(where, "must be a pair [x, y] of numbers")
        return None

    def _frame(self, raw: dict[str, Any], where: str) -> Frame:
        """Build one frame."""
        self._check_keys(raw, FRAME_KEYS, where)
        return Frame(
            id=self._identifier(raw, where),
            x=self._number(raw, "x", where),
            y=self._number(raw, "y", where),
            width=self._extent(raw, "width", where),
            height=self._extent(raw, "height", where),
            label=raw.get("label"),
            tone=self._enum(Tone, raw, "tone", where) or Tone.GRAY,
        )

    def _node(self, raw: dict[str, Any], where: str) -> Node:
        """Build one node."""
        self._check_keys(raw, NODE_KEYS, where)
        shape = self._enum(Shape, raw, "shape", where)
        if shape is None and "shape" not in raw:
            self._report(where, "'shape' is required")
        return Node(
            id=self._identifier(raw, where),
            shape=shape or Shape.PROCESS,
            x=self._number(raw, "x", where),
            y=self._number(raw, "y", where),
            width=self._extent(raw, "width", where),
            height=self._extent(raw, "height", where),
            text=self._lines(raw.get("text", ""), where),
            icon=self._icon(raw, where),
            tone=self._enum(Tone, raw, "tone", where),
            number=raw.get("number"),
            font_size=raw.get("font_size", DEFAULT_FONT_SIZE_PX),
        )

    def _lines(self, raw: object, where: str) -> tuple[str, ...]:
        """Read node text, given as one string or as a list of lines."""
        if isinstance(raw, str):
            return (raw,) if raw else ()
        if isinstance(raw, list) and all(isinstance(line, str) for line in raw):
            return tuple(raw)
        self._report(where, "'text' must be a string or a list of lines")
        return ()

    def _icon(self, raw: dict[str, Any], where: str) -> str | None:
        """Read an icon name, which must be in the icon library."""
        name = raw.get("icon")
        if name is not None and name not in self._icon_names:
            self._report(where, f"unknown icon '{name}'")
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
        self._check_keys(raw, EDGE_KEYS, where)
        for end in ("from", "to"):
            if end in raw and raw[end] not in node_ids:
                self._report(where, f"'{end}' names '{raw[end]}', which is not a node")
        return Edge(
            id=self._identifier(raw, where),
            role=self._enum(Role, raw, "role", where) or Role.NEXT,
            points=self._route(raw.get("points"), where),
            arrow=self._enum(ArrowEnd, raw, "arrow", where) or ArrowEnd.END,
            label=self._label(raw.get("label"), where),
            source=raw.get("from"),
            target=raw.get("to"),
        )

    def _route(self, raw: object, where: str) -> tuple[Point, ...]:
        """Read the routed points of an edge, at least two of them."""
        if not isinstance(raw, list) or len(raw) < MIN_ROUTE_POINTS:
            self._report(where, "'points' must be a list of at least two [x, y] pairs")
            return ()
        points = [self._point(item, f"{where}.points") for item in raw]
        return tuple(point for point in points if point is not None)

    def _label(self, raw: object, where: str) -> EdgeLabel | None:
        """Read the label of an edge, or None when there is none."""
        if raw is None:
            return None
        where = f"{where}.label"
        if not isinstance(raw, dict) or not isinstance(raw.get("text"), str):
            self._report(where, "needs a 'text'")
            return None
        self._check_keys(raw, LABEL_KEYS, where)
        at = self._point(raw.get("at"), f"{where}.at")
        kind = self._enum(LabelKind, raw, "kind", where) or LabelKind.PLAIN
        return EdgeLabel(text=raw["text"], at=at, kind=kind) if at else None


def _is_number(value: object) -> bool:
    """Tell whether a JSON value is a number; ``True`` and ``False`` are not."""
    return isinstance(value, int | float) and not isinstance(value, bool)
