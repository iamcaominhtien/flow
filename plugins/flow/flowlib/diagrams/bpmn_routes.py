"""Route the flows of a BPMN diagram.

A sequence flow stays inside its pool and is straight or has at most two bends. A message flow
runs between two pools: straight up or down when its two ends share an x, else along a channel
in the gap between two pools. A message flow may cross a pool but never an element. The one
blue main path is drawn like any sequence flow.
"""

from dataclasses import dataclass
from itertools import pairwise, product

from ..check import Rect, caption_rect, node_rect
from ..model import Edge, EdgeLabel, Head, LabelKind, Node, Point, Role, Shape
from ..orthogonal import Anchor, Facing, anchor_on, simplify
from ..route_search import Plan, Search, best_route, score_route
from ..theme import BpmnRules, Theme
from .bpmn_place import Placed
from .bpmn_spec import BpmnSpec, Item, Link, LinkStyle

SAME_LINE_PX = 4.0  # two centres this close are on one line
CHANNEL_STEPS = (0, 1, -1, 2, -2)  # in units of ``channel_step``
CAPTION_OWNER = "caption:"  # a caption blocks every line, even those of its own node
WIDE_BOX_PX = 100  # a box this wide lets a message attach away from the middle of its side
SIDE_SHIFT_PX = 54
SHIFT_COST = 3.0  # moving away from the middle of a side is allowed, not liked
KEEP_CLEAR_PX = 10  # a line passes this far from a box it does not join
END_MARGIN_PX = 10  # a line attaches this far from the corners of a box
LINE_HEADS: dict[LinkStyle, tuple[Head, Head]] = {
    LinkStyle.SEQUENCE: (Head.FILLED, Head.NONE),
    LinkStyle.RETURN: (Head.FILLED, Head.NONE),
    LinkStyle.MESSAGE: (Head.TRIANGLE, Head.CIRCLE),
    LinkStyle.DATA: (Head.OPEN, Head.NONE),
}


@dataclass(frozen=True)
class _Context:
    """What the routing of a diagram needs: the elements, their places and what is in the way."""

    items: dict[str, Item]
    placed: Placed
    obstacles: list[tuple[str, Rect]]
    rules: BpmnRules


def route_links(spec: BpmnSpec, placed: Placed, theme: Theme) -> list[Edge]:
    """Route every flow of a diagram and build its line.

    Args:
        spec: The checked spec.
        placed: The nodes and the pool rectangles.
        theme: The design tokens.

    Returns:
        One edge per flow, in the order of the spec.
    """
    obstacles = [(node.id, _inflate(node_rect(node))) for node in placed.nodes.values()]
    obstacles += [
        (CAPTION_OWNER + node.id, rect)
        for node in placed.nodes.values()
        if (rect := caption_rect(node, theme.layout)) is not None
    ]
    context = _Context({item.id: item for item in spec.items}, placed, obstacles, theme.bpmn)
    routes: dict[int, list[Point]] = {}
    for index in _order(spec):
        link = spec.links[index]
        others = [r for i, r in routes.items() if not _shares_end(spec.links[i], link)]
        routes[index] = _route(link, context, others)
    return [_edge(i, spec.links[i], routes[i], placed) for i in range(len(spec.links))]


def _inflate(rect: Rect) -> Rect:
    """Grow a rectangle on every side, so that a line keeps clear of the box, not only out of it."""
    pad = KEEP_CLEAR_PX
    return Rect(rect.left - pad, rect.top - pad, rect.right + pad, rect.bottom + pad)


def _shares_end(first: Link, second: Link) -> bool:
    """Tell whether two flows leave the same element or arrive at the same one.

    Such flows may run on one trunk, like the exits of a split, so they do not count against
    each other.
    """
    return first.source == second.source or first.target == second.target


def _order(spec: BpmnSpec) -> list[int]:
    """Return the order to route flows in: the main path first, then the rest, messages last."""
    indexes = range(len(spec.links))
    return sorted(
        indexes,
        key=lambda i: (
            spec.links[i].style is LinkStyle.MESSAGE,
            not spec.links[i].is_main,
            i,
        ),
    )


def _search(link: Link, context: _Context, taken: list[list[Point]]) -> Search:
    """Describe what a route is scored against: the boxes and captions in its way, the lines."""
    ends = {link.source, link.target}
    blocking = [rect for owner, rect in context.obstacles if owner not in ends]
    pools = list(context.placed.pools.values())
    bounds = _bounds_of(context.placed)
    if pools:
        bounds = Rect(
            min(p.left for p in pools),
            min(p.top for p in pools),
            max(p.right for p in pools),
            max(p.bottom for p in pools),
        )
    rules = context.rules
    limit = _limit(link, context)
    return Search(blocking, taken, bounds, rules.channel_step, rules.channel_clearance, limit)


def _bounds_of(placed: Placed) -> Rect:
    """Return the rectangle that holds every node, for a diagram that has no pools."""
    rects = [node_rect(node) for node in placed.nodes.values()]
    return Rect(
        min(r.left for r in rects),
        min(r.top for r in rects),
        max(r.right for r in rects),
        max(r.bottom for r in rects),
    )


def _limit(link: Link, context: _Context) -> Rect | None:
    """Return the pool a sequence flow must stay in, or None for a message flow."""
    if link.style is LinkStyle.MESSAGE:
        return None
    source = context.items.get(link.source)
    return context.placed.pools.get(source.pool or "") if source is not None else None


def _route(link: Link, context: _Context, taken: list[list[Point]]) -> list[Point]:
    """Return the points of one flow."""
    search = _search(link, context, taken)
    if link.style is LinkStyle.MESSAGE:
        return _message_route(link, context, search)
    source, target = context.placed.nodes[link.source], context.placed.nodes[link.target]
    is_boundary = context.items[link.source].attached_to is not None
    sides, end_offset = _sides(source, target, is_boundary)
    return best_route(Plan(source, target, sides, 0.0, end_offset), search)


def _sides(source: Node, target: Node, is_boundary: bool) -> tuple[tuple[Facing, Facing], float]:
    """Choose the sides a sequence flow is first tried on, and where it attaches to the target."""
    delta_x = (target.x + target.width / 2) - (source.x + source.width / 2)
    delta_y = (target.y + target.height / 2) - (source.y + source.height / 2)
    vertical = (Facing.SOUTH, Facing.NORTH) if delta_y > 0 else (Facing.NORTH, Facing.SOUTH)
    if abs(delta_y) < SAME_LINE_PX:
        return ((Facing.EAST, Facing.WEST) if delta_x > 0 else (Facing.WEST, Facing.EAST)), 0.0
    if is_boundary and delta_y > 0:
        return _below_boundary(source, target)
    if abs(delta_x) < SAME_LINE_PX or delta_x < 0:
        return vertical, 0.0
    return _forward(source, target, vertical), 0.0


def _forward(source: Node, target: Node, vertical: tuple[Facing, Facing]) -> tuple[Facing, Facing]:
    """Choose the sides of a flow that goes right and to another row.

    A gateway leaves through the top or bottom corner and a join is entered through it; any
    other box leaves on its right and is entered on its left.
    """
    if source.shape is Shape.DECISION:
        return (vertical[0], Facing.WEST)
    if target.shape is Shape.DECISION:
        return (Facing.EAST, vertical[1])
    return (Facing.EAST, Facing.WEST)


def _below_boundary(source: Node, target: Node) -> tuple[tuple[Facing, Facing], float]:
    """Choose the sides for a flow that leaves a boundary event for a box below it.

    When the event sits over the width of the target the line goes straight down into its top.
    """
    reach = target.width / 2 - END_MARGIN_PX
    offset = (source.x + source.width / 2) - (target.x + target.width / 2)
    if abs(offset) <= reach:
        return (Facing.SOUTH, Facing.NORTH), offset
    side = Facing.WEST if offset < 0 else Facing.EAST
    return (Facing.SOUTH, side), 0.0


def _message_route(link: Link, context: _Context, search: Search) -> list[Point]:
    """Route a message flow: straight up or down, or along a channel between two pools.

    A message may leave or arrive at the side of the top or bottom of a wide box, so that it
    can pass beside an element that is in its way.
    """
    placed, rules = context.placed, context.rules
    first, second = _ends(link, placed)
    start, end = _anchors(first, second)
    levels = _channels(start[1], end[1], placed)
    scored: list[tuple[float, list[Point]]] = []
    for start_shift, end_shift in product(_shifts(first), _shifts(second)):
        begin, finish = (start[0] + start_shift, start[1]), (end[0] + end_shift, end[1])
        candidates = [
            _z(begin, finish, level + step * rules.channel_step)
            for level in levels
            for step in CHANNEL_STEPS
        ]
        if abs(begin[0] - finish[0]) < SAME_LINE_PX:
            candidates.append([begin, finish])
        shifted = (start_shift != 0) + (end_shift != 0)
        scored.extend((SHIFT_COST * shifted + score_route(c, search), c) for c in candidates)
    return min(scored, key=lambda pair: pair[0])[1]


def _shifts(thing: Node | Rect) -> tuple[float, ...]:
    """Return how far from the middle of its side a message may attach: wide boxes allow some."""
    if isinstance(thing, Rect) or thing.width < WIDE_BOX_PX:
        return (0.0,)
    return (0.0, SIDE_SHIFT_PX, -SIDE_SHIFT_PX)


def _z(start: Point, end: Point, level: float) -> list[Point]:
    """Return the route that goes down or up to ``level``, across, and on to the end."""
    return simplify([start, (start[0], level), (end[0], level), end])


def _ends(link: Link, placed: Placed) -> tuple[Node | Rect, Node | Rect]:
    """Return what each end of a message flow is: an element, or the bar of a black-box pool."""
    first = placed.nodes.get(link.source) or placed.pools[link.source]
    second = placed.nodes.get(link.target) or placed.pools[link.target]
    return first, second


def _centre(thing: Node | Rect) -> Point:
    """Return the middle of an element or of a pool."""
    if isinstance(thing, Rect):
        return ((thing.left + thing.right) / 2, (thing.top + thing.bottom) / 2)
    return (thing.x + thing.width / 2, thing.y + thing.height / 2)


def _anchors(first: Node | Rect, second: Node | Rect) -> tuple[Point, Point]:
    """Return where a message flow leaves and arrives: on the sides that face each other.

    A black-box pool has no fixed place: the line meets its bar straight above or below the
    element at the other end.
    """
    down = _centre(second)[1] > _centre(first)[1]
    leave, arrive = (Facing.SOUTH, Facing.NORTH) if down else (Facing.NORTH, Facing.SOUTH)
    start = _anchor(first, leave, _centre(second)[0])
    end = _anchor(second, arrive, start[0] if isinstance(second, Rect) else _centre(second)[0])
    if isinstance(first, Rect):
        start = (end[0], start[1])
    return start, end


def _anchor(thing: Node | Rect, facing: Facing, x: float) -> Point:
    """Return the point of a side of an element, or of a pool bar at the given x."""
    if isinstance(thing, Rect):
        return (x, thing.bottom if facing is Facing.SOUTH else thing.top)
    anchor: Anchor = anchor_on(thing, facing)
    return anchor.point


def _channels(start_y: float, end_y: float, placed: Placed) -> list[float]:
    """Return the y of the middle of each gap between pools that lies between two heights."""
    rects = sorted(placed.pools.values(), key=lambda rect: rect.top)
    gaps = [(upper.bottom + lower.top) / 2 for upper, lower in pairwise(rects)]
    low, high = sorted((start_y, end_y))
    between = [level for level in gaps if low < level < high]
    return between or [(start_y + end_y) / 2]


def _edge(index: int, link: Link, route: list[Point], placed: Placed) -> Edge:
    """Build the line of a flow."""
    head, tail = LINE_HEADS[link.style]
    return Edge(
        id=f"e{index + 1}",
        role=_role(link),
        points=tuple(route),
        label=_label(link, route),
        source=link.source if link.source in placed.nodes else None,
        target=link.target if link.target in placed.nodes else None,
        head=head,
        tail=tail,
        dashed=link.style is LinkStyle.MESSAGE,
    )


def _role(link: Link) -> Role:
    """Return the colour role of a line: blue main path, red failure, slate return or data."""
    if link.is_main:
        return Role.MAIN
    if link.is_failure:
        return Role.NO
    if link.style is LinkStyle.RETURN:
        return Role.BACK
    if link.style is LinkStyle.DATA:
        return Role.ASSOCIATION
    return Role.NEXT


def _label(link: Link, route: list[Point]) -> EdgeLabel | None:
    """Return the label chip of a flow, in the middle of its longest segment."""
    if not link.label:
        return None
    start, end = max(pairwise(route), key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))
    kind = LabelKind.NO if link.is_failure else LabelKind.PLAIN
    return EdgeLabel(link.label, ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2), kind)
