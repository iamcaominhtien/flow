"""A concept diagram: one central idea with its parts around it, joined by spokes.

The JSON format::

    {"type": "concept", "style": "plain|illustrated", "title": "...", "desc": "...",
     "center": {"label", "detail", "icon", "tone"},
     "items": [{"label", "detail", "icon", "tone"}]}

The items are placed clockwise from the top, on a circle large enough that none touch.
"""

import math
from dataclasses import dataclass
from typing import Any

from ..canvas import fit_canvas
from ..geometry import border_point, center_of
from ..model import DEFAULT_FONT_SIZE_PX, Edge, Head, Node, Role, Scene, Shape, Tone
from ..reader import Reader, SpecError
from ..sizing import FittedNode, NodeContent, fit_card, fit_node
from ..theme import LayoutRules, icon_names, load_theme

CONCEPT = "concept"
MAX_ITEMS = 10
RING_GAP_PX = 50.0
ITEM_GAP_PX = 30.0
SPEC_KEYS = {"type", "title", "desc", "style", "center", "items"}
ITEM_KEYS = {"label", "detail", "icon", "tone"}


@dataclass
class _Part:
    """One box of the diagram as written."""

    label: str
    detail: str
    icon: str | None
    tone: Tone | None
    is_card: bool


def _part(raw: object, where: str, read: Reader, illustrated: bool) -> _Part | None:
    """Read one part, reporting what is wrong with it."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ITEM_KEYS, where)
    icon = raw.get("icon")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    label = read.text(raw, "label", where)
    if not label:
        read.report(where, "'label' is required")
    return _Part(
        label or "",
        read.text(raw, "detail", where) or "",
        icon,
        read.enum(Tone, raw, "tone", where),
        illustrated and icon is not None,
    )


def _fit(part: _Part, shape: Shape, rules: LayoutRules) -> FittedNode:
    """Size a part: a card when illustrated, else a box of the given shape."""
    content = NodeContent(part.label, part.detail, part.icon is not None)
    return fit_card(content, rules) if part.is_card else fit_node(shape, content, rules)


def _node(name: str, part: _Part, shape: Shape, fit: tuple[FittedNode, Any]) -> Node:
    """Build the scene node of a part, centred on a point."""
    size, (center_x, center_y) = fit
    return Node(
        id=name,
        shape=shape,
        x=center_x - size.width / 2,
        y=center_y - size.height / 2,
        width=size.width,
        height=size.height,
        text=size.lines,
        icon=part.icon,
        tone=part.tone,
        number=None,
        font_size=DEFAULT_FONT_SIZE_PX,
        detail=size.detail,
        card=part.is_card,
    )


def _radius(center: FittedNode, items: list[FittedNode]) -> float:
    """Return the radius of the ring: far enough from the centre and from each neighbour."""
    item_reach = max(math.hypot(size.width, size.height) for size in items)
    from_center = (math.hypot(center.width, center.height) + item_reach) / 2 + RING_GAP_PX
    around = len(items) * (item_reach + ITEM_GAP_PX) / (2 * math.pi)
    return max(from_center, around)


def _spoke(center: Node, item: Node) -> Edge:
    """Build the plain line from the centre box to one item."""
    start = border_point(center, center_of(item))
    end = border_point(item, center_of(center))
    return Edge(f"spoke-{item.id}", Role.NEXT, (start, end), None, center.id, item.id, Head.NONE)


def layout_raw(raw: object) -> Scene:
    """Lay out a concept diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a concept spec.

    Returns:
        The scene.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    illustrated = read.illustrated(raw, "spec")
    center = _part(raw.get("center"), "center", read, illustrated)
    listed = raw.get("items", [])
    listed = listed if isinstance(listed, list) else []
    items = [_part(each, f"items[{i}]", read, illustrated) for i, each in enumerate(listed)]
    if not 1 <= len(listed) <= MAX_ITEMS:
        read.report("spec", f"'items' must list between 1 and {MAX_ITEMS} items")
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    if read.problems or center is None:
        raise SpecError(read.problems or ["'center' is required"])
    rules = load_theme().layout
    parts = [part for part in items if part is not None]
    center_size = _fit(center, Shape.ELLIPSE, rules)
    sizes = [_fit(part, Shape.PROCESS, rules) for part in parts]
    ring = _radius(center_size, sizes)
    top = rules.margin + (rules.title_block_height if title else 0)
    middle = (
        rules.margin + ring + max(s.width for s in sizes) / 2,
        top + ring + max(s.height for s in sizes) / 2,
    )
    hub = _node("center", center, Shape.ELLIPSE, (center_size, middle))
    nodes = [hub]
    for index, (part, size) in enumerate(zip(parts, sizes, strict=True)):
        angle = 2 * math.pi * index / len(parts) - math.pi / 2
        point = (middle[0] + ring * math.cos(angle), middle[1] + ring * math.sin(angle))
        nodes.append(_node(f"item-{index}", part, Shape.PROCESS, (size, point)))
    edges = tuple(_spoke(hub, node) for node in nodes[1:])
    return fit_canvas(Scene(0, 0, title, description, (), tuple(nodes), edges))
