"""A tidy tree layout: leaves in a row, each parent centred over its children.

Used by the org chart (top down) and the mind map (left to right). The layered engine of the
flowchart would merge the lines of neighbouring parents into one bus; here every parent has
its own.
"""

from dataclasses import dataclass, replace

from .canvas import fit_canvas
from .model import Direction, Edge, Head, Node, Role, Scene
from .placement import fit_content, make_node, page_origin
from .sizing import FittedNode
from .spec import Spec
from .theme import LayoutRules, load_theme

STEM_FRACTION = 0.5  # where the bus of a parent runs, as a fraction of the gap below it


@dataclass
class _Slot:
    """The place of one item along the two axes of the tree."""

    size: FittedNode
    breadth: float = 0.0  # centre across the siblings
    depth: float = 0.0  # start along the flow


def _children_of(spec: Spec) -> dict[str, list[str]]:
    """Return each item's children, in the order the spec lists them."""
    children: dict[str, list[str]] = {node.id: [] for node in spec.nodes}
    for edge in spec.edges:
        children[edge.source].append(edge.target)
    return children


def _place_breadth(
    node_id: str, children: dict[str, list[str]], slots: dict[str, _Slot], cursor: list[float]
) -> None:
    """Set the breadth of an item: leaves take the next free place, parents centre on children."""
    below = children[node_id]
    for child in below:
        _place_breadth(child, children, slots, cursor)
    slot = slots[node_id]
    extent = slot.size.width
    if below:
        slot.breadth = (slots[below[0]].breadth + slots[below[-1]].breadth) / 2
    else:
        slot.breadth = cursor[0] + extent / 2
        cursor[0] += extent + cursor[1]


def layout_tree(spec: Spec) -> Scene:
    """Place a tree given as a ``Spec`` whose edges run from parent to child.

    Args:
        spec: The items and parent links; the direction is ``down`` or ``right``.

    Returns:
        The scene, with one elbow line per link.
    """
    rules = load_theme().layout
    is_down = spec.direction is Direction.DOWN
    children = _children_of(spec)
    root = next(node.id for node in spec.nodes if node.id not in {e.target for e in spec.edges})
    slots = {node.id: _Slot(_orient(fit_content(node, rules), is_down)) for node in spec.nodes}
    _place_breadth(root, children, slots, [0.0, rules.gap_horizontal / 2])
    _place_depth(root, children, slots, rules)
    return _scene(spec, slots, rules)


def _orient(size: FittedNode, is_down: bool) -> FittedNode:
    """Return a size where ``width`` runs across the siblings and ``height`` along the flow."""
    if is_down:
        return size
    return replace(size, width=size.height, height=size.width)


def _place_depth(
    root: str, children: dict[str, list[str]], slots: dict[str, _Slot], rules: LayoutRules
) -> None:
    """Set the depth of every item: each level starts after the deepest item of the one above."""
    levels: list[list[str]] = [[root]]
    while True:
        following = [child for node_id in levels[-1] for child in children[node_id]]
        if not following:
            break
        levels.append(following)
    start = 0.0
    for level in levels:
        for node_id in level:
            slots[node_id].depth = start
        start += max(slots[node_id].size.height for node_id in level) + rules.gap_vertical


def _scene(spec: Spec, slots: dict[str, _Slot], rules: LayoutRules) -> Scene:
    """Turn slots into pixel positions and elbow lines, in page space."""
    is_down = spec.direction is Direction.DOWN
    left, top = page_origin(spec, rules)
    if not is_down:
        left, top = rules.margin, rules.margin + (rules.title_block_height if spec.title else 0)
    shift_breadth = min(slot.breadth - slot.size.width / 2 for slot in slots.values())
    nodes = {}
    for node in spec.nodes:
        slot = slots[node.id]
        across = slot.breadth - shift_breadth
        along = slot.depth
        if is_down:
            center = (left + across, top + along + slot.size.height / 2)
            width, size = slot.size.width, slot.size
        else:
            center = (left + along + slot.size.height / 2, top + across)
            width, size = slot.size.height, replace(slot.size, height=slot.size.width)
        nodes[node.id] = make_node(node, size, center, width)
    edges = tuple(_edge(nodes[link.source], nodes[link.target], is_down) for link in spec.edges)
    scene = Scene(
        width=0,
        height=0,
        title=spec.title,
        description=spec.description,
        frames=(),
        nodes=tuple(nodes.values()),
        edges=edges,
    )
    return fit_canvas(scene)


def _edge(parent: Node, child: Node, is_down: bool) -> Edge:
    """Build the elbow line from a parent to one child, with its bus half way down the gap."""
    if is_down:
        start = (parent.x + parent.width / 2, parent.y + parent.height)
        end = (child.x + child.width / 2, child.y)
        bus = start[1] + (end[1] - start[1]) * STEM_FRACTION
        points = (start, (start[0], bus), (end[0], bus), end)
    else:
        start = (parent.x + parent.width, parent.y + parent.height / 2)
        end = (child.x, child.y + child.height / 2)
        bus = start[0] + (end[0] - start[0]) * STEM_FRACTION
        points = (start, (bus, start[1]), (bus, end[1]), end)
    return Edge(
        id=f"{parent.id}-{child.id}",
        role=Role.NEXT,
        points=points,
        label=None,
        source=parent.id,
        target=child.id,
        head=Head.NONE,
    )
