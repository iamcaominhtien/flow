"""The mind map: one topic in the middle, branches on both sides, drawn to design 08 section 4.

See ``mindmap_spec`` for the spec and ``mindmap_grid`` for where the items go. A branch is a
solid colour pill with a round icon (or a tinted pill, in the plain style); its leaves are white
cards with a colour bar and a small icon (or underlined phrases). Lines are curves, 8 px at the
centre and 4 px beyond, in the colour of the branch. A larger map has four levels, marks for
priority, done, owner and hidden ideas, and a few dashed violet arcs between ideas. Nothing
animates, and no order is implied.
"""

from ..canvas import fit_canvas
from ..model import (
    Edge,
    EdgeLabel,
    Head,
    LabelKind,
    MindLevel,
    Node,
    PlanView,
    Point,
    Role,
    Scene,
    Shape,
    Side,
    Status,
)
from ..theme import MindScale, Theme, load_theme
from .mindmap_grid import Box, level_of, place_ideas
from .mindmap_key import KEY_HEIGHT_PX, has_key, key_parts
from .mindmap_spec import BRANCH_ICONS, Idea, Link, MindSpec, read_spec

BRANCH_DEPTH = 1
LARGE_FROM_DEPTH = 2  # a map deeper than two levels is drawn at the large scale
HEADER_GAP_PX = 26  # between the title block and the top of the map
UNDERLINE_PX = 3  # the line under a plain leaf; the curve meets the text above it
LINK_STAGGER_PX = 14  # each arc on a side bulges this much further out than the one before
ARC_PEAK = 0.75  # how far a cubic curve with both controls at X reaches towards X
LINK_HEAD = Head.OPEN
LEVEL_SHAPES = {
    MindLevel.CENTRE: Shape.BRANCH,
    MindLevel.BRANCH: Shape.BRANCH,
    MindLevel.GROUP: Shape.BRANCH,
    MindLevel.LEAF: Shape.LEAF,
    MindLevel.IDEA: Shape.LEAF,
    MindLevel.DETAIL: Shape.LEAF,
}


def layout_raw(raw: object) -> Scene:
    """Lay out a mind map from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``mindmap`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(read_spec(raw))


def layout(spec: MindSpec) -> Scene:
    """Place the items, the curves and the links of a checked spec.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    scale = scale_of(spec, theme)
    rules = theme.layout
    title_bottom = rules.margin + (rules.title_block_height if spec.title else 0)
    key_room = KEY_HEIGHT_PX if has_key(spec) else 0
    top = title_bottom + HEADER_GAP_PX + key_room
    boxes = place_ideas(spec, scale, (rules.margin, top))
    icons = _branch_icons(spec)
    nodes = {idea.id: _node(idea, spec, (boxes[idea.id], scale), icons) for idea in spec.ideas}
    edges = _curves(spec, nodes) + _arcs(spec, nodes, theme)
    key_nodes, key_edges = key_parts(spec, (rules.margin, title_bottom + KEY_HEIGHT_PX / 2), theme)
    scene = Scene(
        width=0,
        height=0,
        title=spec.title,
        description=spec.description,
        frames=(),
        nodes=tuple(list(nodes.values()) + key_nodes),
        edges=tuple(edges + key_edges),
    )
    return fit_canvas(scene)


def scale_of(spec: MindSpec, theme: Theme) -> MindScale:
    """Return the sizes to use: the large ones for a map of three or more levels."""
    rules = theme.planning.mind
    if spec.depth > LARGE_FROM_DEPTH:
        return rules.large
    return rules.illustrated if spec.is_illustrated else rules.plain


def _node(idea: Idea, spec: MindSpec, drawn: tuple[Box, MindScale], icons: dict[str, str]) -> Node:
    """Build the node of one item."""
    box, scale = drawn
    level = level_of(idea, spec)
    view = PlanView(
        status=Status.DONE if idea.is_done else None,
        initials=idea.owner.initials if idea.owner else "",
        person_tone=idea.owner.tone if idea.owner else None,
        level=level,
        side=idea.side,
        priority=idea.priority,
        hidden=idea.hidden,
    )
    return Node(
        id=idea.id,
        shape=LEVEL_SHAPES[level],
        x=box.x,
        y=box.y,
        width=box.width,
        height=box.height,
        text=(idea.label,),
        icon=_icon_of(idea, level, icons.get(idea.id, "")),
        tone=idea.tone,
        number=None,
        font_size=_font_of(level, scale),
        detail=(f"Goal: {idea.detail}",) if idea.detail else (),
        card=spec.is_illustrated,
        plan=view,
    )


def _font_of(level: MindLevel, scale: MindScale) -> float:
    """Return the font size of an item of a level."""
    sizes = {
        MindLevel.CENTRE: scale.branch_font + 3,
        MindLevel.BRANCH: scale.branch_font,
        MindLevel.GROUP: scale.group_font,
        MindLevel.LEAF: scale.idea_font,
        MindLevel.IDEA: scale.idea_font,
        MindLevel.DETAIL: scale.detail_font,
    }
    return sizes[level]


def _branch_icons(spec: MindSpec) -> dict[str, str]:
    """Return, for every item below the topic, the icon of the branch it hangs on."""
    by_id = {idea.id: idea for idea in spec.ideas}
    branches = [idea for idea in spec.ideas if idea.depth == BRANCH_DEPTH]
    own = {
        branch.id: branch.icon or BRANCH_ICONS[index % len(BRANCH_ICONS)]
        for index, branch in enumerate(branches)
    }
    icons = {}
    for idea in spec.ideas[1:]:
        top = idea
        while top.depth > BRANCH_DEPTH:
            top = by_id[top.parent or ""]
        icons[idea.id] = own[top.id]
    return icons


def _icon_of(idea: Idea, level: MindLevel, branch_icon: str) -> str | None:
    """Return the icon of an item: its own, else its branch's for a branch or a leaf."""
    if idea.icon or level not in (MindLevel.BRANCH, MindLevel.LEAF):
        return idea.icon
    return branch_icon


def _anchor(node: Node, side: Side, is_outer: bool) -> Point:
    """Return where a curve meets a node: the middle of its outer or its inner edge."""
    faces_right = (side is Side.RIGHT) is is_outer
    x = node.x + node.width if faces_right else node.x
    is_plain_leaf = (
        node.shape is Shape.LEAF
        and not node.card
        and node.plan
        and node.plan.level is MindLevel.LEAF
    )
    height = node.height - UNDERLINE_PX if is_plain_leaf else node.height
    return (x, node.y + height / 2)


def _curve(start: Point, end: Point) -> tuple[Point, Point, Point, Point]:
    """Return the four points of a curve that leaves and enters level, like an S."""
    middle = (start[0] + end[0]) / 2
    return (start, (middle, start[1]), (middle, end[1]), end)


def _curves(spec: MindSpec, nodes: dict[str, Node]) -> list[Edge]:
    """Draw a curve from every item to what hangs on it, in the colour of its branch."""
    edges = []
    for idea in spec.ideas[1:]:
        side = idea.side or Side.RIGHT
        parent, child = nodes[idea.parent or ""], nodes[idea.id]
        points = _curve(_anchor(parent, side, True), _anchor(child, side, False))
        role = Role.BRANCH if idea.depth == 1 else Role.TWIG
        edges.append(
            Edge(
                f"line-{idea.id}",
                role,
                points,
                None,
                parent.id,
                child.id,
                Head.NONE,
                tone=idea.tone,
                is_curved=True,
            )
        )
    return edges


def _arcs(spec: MindSpec, nodes: dict[str, Node], theme: Theme) -> list[Edge]:
    """Draw a dashed violet arc, with a pill, between each pair of linked ideas."""
    outer = {side: _outer_edge(side, nodes) for side in Side}
    count = dict.fromkeys(Side, 0)
    edges = []
    for index, link in enumerate(spec.links):
        first, second = nodes[link.source], nodes[link.target]
        side = (first.plan.side if first.plan else None) or Side.RIGHT
        bulge = theme.planning.mind.link_bulge + count[side] * LINK_STAGGER_PX
        count[side] += 1
        edges.append(_arc(link, index, (first, second), (side, outer[side], bulge)))
    return edges


def _outer_edge(side: Side, nodes: dict[str, Node]) -> float:
    """Return the x of the outermost edge of the items on a side."""
    members = [node for node in nodes.values() if node.plan and node.plan.side is side]
    if side is Side.RIGHT:
        return max((node.x + node.width for node in members), default=0.0)
    return min((node.x for node in members), default=0.0)


def _arc(link: Link, index: int, ends: tuple[Node, Node], bend: tuple[Side, float, float]) -> Edge:
    """Build the arc between two ideas: out to the side, round and back in."""
    first, second = ends
    side, outer, bulge = bend
    start, end = _anchor(first, side, True), _anchor(second, side, True)
    direction = 1 if side is Side.RIGHT else -1
    control_x = outer + direction * bulge / ARC_PEAK
    points = (start, (control_x, start[1]), (control_x, end[1]), end)
    label = None
    if link.label:
        peak = (start[0] + 3 * control_x + 3 * control_x + end[0]) / 8
        label = EdgeLabel(link.label, (peak, (start[1] + end[1]) / 2), LabelKind.LINK)
    return Edge(
        f"link-{index + 1}",
        Role.LINK,
        points,
        label,
        first.id,
        second.id,
        LINK_HEAD,
        is_curved=True,
    )
