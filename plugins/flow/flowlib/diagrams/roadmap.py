"""The roadmap: themes in rows, time in columns, drawn to design 08 section 6.

See ``roadmap_spec`` for the spec. A solid card is committed; a dashed card is an idea under
study. Each row has a card with a detailed icon. The one dependency that decides the order is a
blue animated arrow, and a note below the chart says what it means. There are no exact dates.
"""

from dataclasses import dataclass, field

from ..canvas import fit_canvas
from ..model import (
    Edge,
    Frame,
    FrameVariant,
    Head,
    Node,
    PlanView,
    Point,
    Role,
    Scene,
    Shape,
    Tone,
)
from ..sizing import estimate_text_width, wrap_text
from ..theme import RoadmapRules, Theme, load_theme
from .roadmap_spec import Dependency, Item, Lane, Period, RoadmapSpec, read_spec

COMMITTED_TAG = "Committed"
EXPLORING_TAG = "Exploring"
NOTE_SLACK_PX = 12
MIN_RUN_PX = 4  # a card must start at least this far right of another for a side-to-side route


@dataclass
class _Chart:
    """What is placed so far, and where the next row goes."""

    theme: Theme
    column: float  # the width of a column, with its gap
    left: float  # the left edge of the columns
    top: float
    frames: list[Frame] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)


def layout_raw(raw: object) -> Scene:
    """Lay out a roadmap from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``roadmap`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(read_spec(raw))


def layout(spec: RoadmapSpec) -> Scene:
    """Place the column headers, the rows with their cards, the arrow and the note.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    rules = theme.planning.roadmap
    margin = theme.layout.margin
    column = max(min(rules.column_budget / len(spec.periods), rules.column_max), rules.column_min)
    top = margin + (theme.layout.title_block_height if spec.title else 0)
    chart = _Chart(theme, column, margin + rules.lane_head[0] + rules.lane_head_gap, top)
    _headers(spec.periods, chart)
    chart.top += rules.period_height + rules.period_gap
    for index, lane in enumerate(spec.lanes):
        _lane(lane, index, chart)
    cards = {node.id: node for node in chart.nodes if node.shape is Shape.ROADMAP_CARD}
    edges = [_arrow(spec.dependency, cards, rules)] if spec.dependency else []
    bottom = chart.top - rules.lane_gap
    note = _note(spec, cards, (margin, bottom), theme)
    nodes = (*chart.nodes, *([note] if note else []))
    scene = Scene(0, 0, spec.title, spec.description, tuple(chart.frames), nodes, tuple(edges))
    return fit_canvas(scene)


def _headers(periods: tuple[Period, ...], chart: _Chart) -> None:
    """Add the header of each column: a tinted box with its name and its dates in words."""
    rules = chart.theme.planning.roadmap
    for index, period in enumerate(periods):
        chart.nodes.append(
            Node(
                f"period-{index}",
                Shape.PERIOD_HEAD,
                chart.left + index * chart.column,
                chart.top,
                chart.column - rules.column_gap,
                rules.period_height,
                (period.label,),
                None,
                period.tone,
                None,
                rules.period_font_size,
                detail=(period.detail,) if period.detail else (),
                plan=PlanView(),
            )
        )


def _lane(lane: Lane, index: int, chart: _Chart) -> None:
    """Add one row: its head card, its tinted area and its cards, stacked where they overlap."""
    rules = chart.theme.planning.roadmap
    rows = _pack(lane.items)
    needed = 2 * rules.lane_pad + len(rows) * rules.card_height + (len(rows) - 1) * rules.row_gap
    height = max(needed, rules.lane_head[1])
    margin = chart.theme.layout.margin
    chart.nodes.append(
        Node(
            f"lane-{index}", Shape.LANE_HEAD, margin, chart.top, rules.lane_head[0], height,
            (lane.label,), lane.icon, lane.tone, None, rules.lane_pill_font_size, plan=PlanView(),
        )
    )  # fmt: skip
    width = chart.column * _columns(chart) - rules.column_gap
    chart.frames.append(
        Frame(
            f"row-{index}",
            chart.left,
            chart.top,
            width,
            height,
            None,
            lane.tone,
            FrameVariant.COLUMN,
        )
    )
    for number, row in enumerate(rows):
        y = chart.top + rules.lane_pad + number * (rules.card_height + rules.row_gap)
        chart.nodes += [_card(item, lane, (chart, y)) for item in row]
    chart.top += height + rules.lane_gap


def _columns(chart: _Chart) -> int:
    """Return how many columns the roadmap has, from the headers placed."""
    return len([node for node in chart.nodes if node.shape is Shape.PERIOD_HEAD])


def _pack(items: list[Item]) -> list[list[Item]]:
    """Put cards that share a period in separate rows, as few rows as the order allows."""
    rows: list[list[Item]] = []
    for item in sorted(items, key=lambda each: each.first):
        for row in rows:
            if row[-1].first + row[-1].length <= item.first:
                row.append(item)
                break
        else:
            rows.append([item])
    return rows or [[]]


def _card(item: Item, lane: Lane, where: tuple[_Chart, float]) -> Node:
    """Build the card of an item: solid when committed, dashed when it is an idea."""
    chart, y = where
    rules = chart.theme.planning.roadmap
    width = item.length * chart.column - rules.column_gap - 2 * rules.card_inset
    room = width - 2 * rules.card_pad
    view = PlanView(
        initials=item.owner.initials if item.owner else "",
        person_tone=item.owner.tone if item.owner else None,
        tag=COMMITTED_TAG if item.is_committed else EXPLORING_TAG,
        tag_tone=Tone.GREEN if item.is_committed else Tone.GRAY,
    )
    return Node(
        item.id,
        Shape.ROADMAP_CARD,
        chart.left + item.first * chart.column + rules.card_inset,
        y,
        width,
        rules.card_height,
        tuple(wrap_text(item.label, chart.theme.layout, room, rules.title_font_size)),
        None,
        lane.tone,
        None,
        rules.title_font_size,
        detail=tuple(wrap_text(item.detail, chart.theme.layout, room, rules.detail_font_size)),
        dashed=not item.is_committed,
        plan=view,
    )


def _arrow(dependency: Dependency, cards: dict[str, Node], rules: RoadmapRules) -> Edge:
    """Draw the one dependency: a blue, animated arrow from the card that comes first."""
    before, after = cards[dependency.before], cards[dependency.after]
    return Edge(
        f"after-{before.id}-{after.id}",
        Role.MAIN,
        _route(before, after, rules),
        None,
        before.id,
        after.id,
        Head.FILLED,
    )


def _route(before: Node, after: Node, rules: RoadmapRules) -> tuple[Point, ...]:
    """Route the arrow: down the gap beside the first card and into the top of the next."""
    right = before.x + before.width
    if after.x < right + MIN_RUN_PX:
        return _vertical_route(before, after, rules)
    if abs(after.y - before.y) < 1:
        middle = before.y + before.height / 2
        return ((right, middle), (after.x, middle))
    gap_x = right + rules.exit_gap
    end_x = after.x + rules.entry_offset
    if after.y > before.y:
        start_y, bend_y, end_y = before.y + rules.exit_drop, after.y - rules.entry_run, after.y
    else:
        start_y = before.y + before.height - rules.exit_drop
        bend_y, end_y = after.y + after.height + rules.entry_run, after.y + after.height
    return ((right, start_y), (gap_x, start_y), (gap_x, bend_y), (end_x, bend_y), (end_x, end_y))


def _vertical_route(before: Node, after: Node, rules: RoadmapRules) -> tuple[Point, ...]:
    """Route a straight arrow between two cards that share a column."""
    x = max(before.x, after.x) + rules.entry_offset
    if after.y > before.y:
        return ((x, before.y + before.height), (x, after.y))
    return ((x, before.y), (x, after.y + after.height))


def _note(
    spec: RoadmapSpec, cards: dict[str, Node], origin: tuple[float, float], theme: Theme
) -> Node | None:
    """Build the note below the chart that says what the arrow and the dashed cards mean."""
    text = spec.note if spec.note is not None else _note_text(spec, cards)
    if not text:
        return None
    rules = theme.planning.roadmap
    x, bottom = origin
    height = 2 * rules.note_font_size
    width = estimate_text_width(text, theme.layout, rules.note_font_size) + NOTE_SLACK_PX
    return Node(
        "note", Shape.LABEL, x, bottom + rules.note_gap - height / 2, width, height, (text,),
        None, None, None, rules.note_font_size, plan=PlanView(),
    )  # fmt: skip


def _note_text(spec: RoadmapSpec, cards: dict[str, Node]) -> str:
    """Write the note: what the blue arrow means, and what solid and dashed cards are."""
    labels = {item.id: item.label for lane in spec.lanes for item in lane.items}
    parts = []
    if spec.dependency:
        before, after = labels[spec.dependency.before], labels[spec.dependency.after]
        parts.append(f"The blue arrow means {after} cannot start before {before} is done.")
    if any(card.dashed for card in cards.values()):
        parts.append("Solid cards are committed, dashed cards are still being studied.")
    return " ".join(parts)
