"""The org chart: who reports to whom, drawn to design 08 section 3.

See ``org_spec`` for the spec. A card per person, 210 x 78 (plain) or 232 x 110 (illustrated),
250 px apart in a row and one level every 240 to 270 px. A solid bus line runs from a manager
down to a bar and on to each report; a dashed line with a pill joins two people who work
together without a reporting line; an open role is a dashed, faded card.
"""

from dataclasses import dataclass, replace

from ..canvas import fit_canvas
from ..model import (
    DEFAULT_FONT_SIZE_PX,
    Edge,
    EdgeLabel,
    Head,
    LabelKind,
    Node,
    PlanView,
    Point,
    Role,
    Scene,
    Shape,
)
from ..sizing import estimate_text_width
from ..theme import OrgRules, Theme, load_theme
from .org_spec import Link, Member, OrgSpec, read_spec

HEADER_GAP_PX = 26  # between the title block and the first card
LEGEND_FONT_PX = 11
LEGEND_TEXT_GAP_PX = 10
LEGEND_ITEM_GAP_PX = 36
TEXT_SLACK_PX = 6
LEGEND_SWATCH_PX = (34, 22)


@dataclass(frozen=True)
class _Plan:
    """What decides where a card goes: the size of a card and the rules of the chart."""

    rules: OrgRules
    size: tuple[float, float]
    top: float


@dataclass
class _Row:
    """The x of the next leaf, and the manager of the leaf before it."""

    next_x: float
    manager: str | None = None


def layout_raw(raw: object) -> Scene:
    """Lay out an org chart from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on an ``org`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(read_spec(raw))


def layout(spec: OrgSpec) -> Scene:
    """Place the cards, the bus lines, the working links and the legend of a checked spec.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    rules = theme.planning.org
    size = rules.card_illustrated if spec.is_illustrated else rules.card
    margin = theme.layout.margin
    top = margin + (theme.layout.title_block_height if spec.title else 0) + HEADER_GAP_PX
    plan = _Plan(rules, size, top)
    centres = _centres(spec.members, rules, margin + size[0] / 2)
    nodes = {member.id: _card(member, spec, centres[member.id], plan) for member in spec.members}
    edges = _bus_lines(spec.members, nodes, rules) + _work_links(spec.links, nodes)
    bottom = max(node.y + node.height for node in nodes.values())
    legend_nodes, legend_edges = _legend(spec, (margin, bottom + rules.legend_gap), theme)
    scene = Scene(
        width=0,
        height=0,
        title=spec.title,
        description=spec.description,
        frames=(),
        nodes=tuple(list(nodes.values()) + legend_nodes),
        edges=tuple(edges + legend_edges),
    )
    return fit_canvas(scene)


def _centres(members: tuple[Member, ...], rules: OrgRules, first: float) -> dict[str, float]:
    """Return the x of the centre of every card: leaves in a row, a manager over its reports.

    Args:
        members: The cards, the top one first.
        rules: The sizes of the chart.
        first: The x of the centre of the first leaf.

    Returns:
        Member id to the x of the centre of its card.
    """
    children: dict[str, list[Member]] = {}
    for member in members:
        if member.parent is not None:
            children.setdefault(member.parent, []).append(member)
    centres: dict[str, float] = {}
    row = _Row(first)
    _place(members[0], (children, centres), (row, rules))
    return centres


def _place(
    member: Member,
    tree: tuple[dict[str, list[Member]], dict[str, float]],
    context: tuple[_Row, OrgRules],
) -> None:
    """Give a member its centre, placing the members below it first."""
    children, centres = tree
    row, rules = context
    below = children.get(member.id, [])
    if not below:
        is_new_manager = row.manager is not None and row.manager != member.parent
        centres[member.id] = row.next_x + (rules.subtree_gap if is_new_manager else 0.0)
        row.next_x = centres[member.id] + rules.card_pitch
        row.manager = member.parent
        return
    for child in below:
        _place(child, tree, context)
    middle = len(below) // 2
    if len(below) % 2:
        centres[member.id] = centres[below[middle].id]
    else:
        centres[member.id] = (centres[below[middle - 1].id] + centres[below[middle].id]) / 2


def _card(member: Member, spec: OrgSpec, centre: float, plan: _Plan) -> Node:
    """Build the card of one person."""
    width, height = plan.size
    rules = plan.rules
    view = PlanView(
        initials=member.person.initials, person_tone=member.person.tone, is_open=member.is_open
    )
    return Node(
        id=member.id,
        shape=Shape.PERSON_CARD,
        x=centre - width / 2,
        y=plan.top + member.depth * _pitch(spec, rules),
        width=width,
        height=height,
        text=(member.name,),
        icon=member.icon,
        tone=member.person.tone,
        number=None,
        font_size=rules.name_font_size,
        detail=(member.role,),
        card=spec.is_illustrated,
        plan=view,
    )


def _pitch(spec: OrgSpec, rules: OrgRules) -> float:
    """Return the distance between two levels: 240 px for plain cards, 270 px for illustrated."""
    return rules.level_pitch_illustrated if spec.is_illustrated else rules.level_pitch


def _bus_lines(members: tuple[Member, ...], nodes: dict[str, Node], rules: OrgRules) -> list[Edge]:
    """Draw a line from each manager down to a bar, along it, and down to each report."""
    edges = []
    for member in members:
        if member.parent is None:
            continue
        above, below = nodes[member.parent], nodes[member.id]
        start = (above.x + above.width / 2, above.y + above.height)
        end = (below.x + below.width / 2, below.y)
        bar = start[1] + rules.bus_drop
        points: tuple[Point, ...] = (start, end)
        if abs(start[0] - end[0]) > 1:
            points = (start, (start[0], bar), (end[0], bar), end)
        edges.append(
            Edge(f"reports-{member.id}", Role.REPORTS, points, None, above.id, below.id, Head.NONE)
        )
    return edges


def _work_links(links: tuple[Link, ...], nodes: dict[str, Node]) -> list[Edge]:
    """Draw a dashed line, with a pill, between the facing sides of two cards of a level."""
    edges = []
    for index, link in enumerate(links):
        left, right = sorted((nodes[link.source], nodes[link.target]), key=lambda each: each.x)
        y = left.y + left.height / 2
        start, end = (left.x + left.width, y), (right.x, y)
        middle = ((start[0] + end[0]) / 2, y)
        label = EdgeLabel(link.label, middle, LabelKind.PLAIN)
        edges.append(
            Edge(
                f"works-{index + 1}",
                Role.WORKS_WITH,
                (start, end),
                label,
                left.id,
                right.id,
                Head.NONE,
            )
        )
    return edges


def _legend(spec: OrgSpec, origin: Point, theme: Theme) -> tuple[list[Node], list[Edge]]:
    """Draw the legend: what a solid line, a dashed line and a dashed card mean."""
    rules = theme.planning.org
    x, middle = origin
    entries = [("Reports to", Role.REPORTS)]
    if spec.links:
        entries.append(("Works with, no reporting line", Role.WORKS_WITH))
    if any(member.is_open for member in spec.members):
        entries.append(("Open role", None))
    nodes: list[Node] = []
    edges: list[Edge] = []
    for index, (text, role) in enumerate(entries):
        if role is None:
            nodes.append(_open_swatch((x, middle)))
            sample = LEGEND_SWATCH_PX[0]
        else:
            ends = ((x, middle), (x + rules.legend_line, middle))
            edges.append(Edge(f"legend-line-{index}", role, ends, None, None, None, Head.NONE))
            sample = rules.legend_line
        text_x = x + sample + LEGEND_TEXT_GAP_PX
        width = estimate_text_width(text, theme.layout, LEGEND_FONT_PX) + TEXT_SLACK_PX
        nodes.append(_legend_text(f"legend-text-{index}", text, (text_x, middle), width))
        x = text_x + width + LEGEND_ITEM_GAP_PX
    return nodes, edges


def _open_swatch(origin: Point) -> Node:
    """Build the small dashed card that stands for an open role in the legend."""
    width, height = LEGEND_SWATCH_PX
    view = PlanView(is_open=True)
    return Node(
        "legend-open", Shape.PERSON_CARD, origin[0], origin[1] - height / 2, width, height, (),
        None, None, None, DEFAULT_FONT_SIZE_PX, plan=view,
    )  # fmt: skip


def _legend_text(identifier: str, text: str, origin: Point, width: float) -> Node:
    """Build the words of a legend entry."""
    height = 2 * LEGEND_SWATCH_PX[1]
    node = Node(
        identifier, Shape.LABEL, origin[0], origin[1] - height / 2, width, height, (text,),
        None, None, None, LEGEND_FONT_PX, plan=PlanView(),
    )  # fmt: skip
    return replace(node, font_size=LEGEND_FONT_PX)
