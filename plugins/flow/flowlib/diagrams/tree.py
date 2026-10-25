"""Tree diagrams: an org chart (top down) and a mind map (left to right) from nested items.

The JSON format::

    {"type": "org|mindmap", "title": "...", "desc": "...",
     "root": {"label": "...", "detail": "...", "icon": "...", "tone": "...",
              "children": [{"label": "...", "children": [...]}]}}

Items get their ids from their position. In a mind map every branch from the root takes its
own tone and passes it on to everything below it.
"""

from typing import Any

from ..model import Direction, Head, Scene, Shape, Tone
from ..reader import Reader, SpecError
from ..spec import Spec
from ..theme import load_icons
from ..tidy import layout_tree
from .graph import GraphType, LineKind, to_spec

ORG = "org"
MIND_MAP = "mindmap"
ITEM_KEYS = {"label", "detail", "icon", "tone", "children"}
SPEC_KEYS = {"type", "title", "desc", "root"}
MAX_DEPTH = 8
BRANCH_TONES = (Tone.BLUE, Tone.VIOLET, Tone.AMBER, Tone.GREEN, Tone.TEAL)
DIRECTION_OF = {ORG: Direction.DOWN, MIND_MAP: Direction.RIGHT}
CHILD = LineKind(head=Head.NONE)
TREE = GraphType(
    name="tree",
    nodes_key="nodes",
    links_key="links",
    kinds={"item": Shape.PROCESS, "root": Shape.TERMINATOR},
    default_kind="item",
    line_kinds={"child": CHILD},
    default_line="child",
)


class _Flattener:
    """Walks a nested tree and writes it as the flat node and link lists the graph reader takes."""

    def __init__(self, read: Reader, kind: str) -> None:
        """Start with no items.

        Args:
            read: The reader that collects problems.
            kind: ``org`` or ``mindmap``.
        """
        self.read = read
        self.kind = kind
        self.nodes: list[dict[str, Any]] = []
        self.links: list[dict[str, Any]] = []

    def add(self, raw: object, where: str, parent: str | None, tone: str | None) -> None:
        """Add one item and everything below it.

        Args:
            raw: The item as parsed from JSON.
            where: Where the item is, for messages.
            parent: The id of the item above, or None for the root.
            tone: The tone passed down by a mind map branch, or None.
        """
        if not isinstance(raw, dict):
            self.read.report(where, "must be an object")
            return
        self.read.check_keys(raw, ITEM_KEYS, where)
        identifier = f"n{len(self.nodes)}"
        icon = raw.get("icon")
        if icon is not None and icon not in load_icons():
            self.read.report(where, f"unknown icon '{icon}'")
        node = {"id": identifier, "label": raw.get("label"), "detail": raw.get("detail")}
        node.update({"icon": icon, "tone": raw.get("tone", tone)})
        node = {key: value for key, value in node.items() if value is not None}
        if parent is None and self.kind == MIND_MAP:
            node["kind"] = "root"
        self.nodes.append(node)
        if parent is not None:
            self.links.append({"from": parent, "to": identifier})
        self._children(raw, where, identifier, tone)

    def _children(self, raw: dict[str, Any], where: str, identifier: str, tone: str | None) -> None:
        """Add the children of an item, giving each branch of a mind map root its own tone."""
        children = raw.get("children", [])
        if not isinstance(children, list):
            self.read.report(where, "'children' must be a list")
            return
        if where.count("children") >= MAX_DEPTH:
            self.read.report(where, f"is nested deeper than {MAX_DEPTH} levels")
            return
        for index, child in enumerate(children):
            branch = tone
            if self.kind == MIND_MAP and identifier == "n0":
                branch = BRANCH_TONES[index % len(BRANCH_TONES)].value
            self.add(child, f"{where}.children[{index}]", identifier, branch)


def tree_spec(raw: object, kind: str) -> Spec:
    """Check a tree spec and turn it into the description the layout works on.

    Args:
        raw: The result of ``json.loads`` on the spec.
        kind: ``org`` or ``mindmap``.

    Returns:
        The items as nodes and the parent links as edges.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    flat = _Flattener(read, kind)
    if "root" not in raw:
        read.report("spec", "'root' is required")
    else:
        flat.add(raw["root"], "root", None, None)
    if read.problems:
        raise SpecError(read.problems)
    graph_raw = {
        "title": raw.get("title"),
        "desc": raw.get("desc"),
        "direction": DIRECTION_OF[kind].value,
        "nodes": flat.nodes,
        "links": flat.links,
    }
    graph_raw = {key: value for key, value in graph_raw.items() if value is not None}
    return to_spec(TREE, graph_raw)


def layout_org(raw: object) -> Scene:
    """Lay out an org chart.

    Args:
        raw: The result of ``json.loads`` on an org chart spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout_tree(tree_spec(raw, ORG))


def layout_mind_map(raw: object) -> Scene:
    """Lay out a mind map.

    Args:
        raw: The result of ``json.loads`` on a mind map spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout_tree(tree_spec(raw, MIND_MAP))
