"""The Kanban board: columns of cards by state, drawn to design 08 section 5.

See ``kanban_spec`` for the spec. Columns are 360 px wide in the order work moves. A card is
100 px high: a title, a kind tag and an owner circle; a done card is struck through. A column with
a limit shows ``3 / 3``, red when the column is full. Cards are listed in priority order.
"""

from ..canvas import fit_canvas
from ..model import (
    Frame,
    FrameVariant,
    Node,
    PillKind,
    PlanView,
    Scene,
    Shape,
    Status,
)
from ..sizing import estimate_text_width, wrap_text
from ..theme import KanbanRules, Theme, load_theme
from .kanban_spec import Card, Column, KanbanSpec, read_spec

HEADER_GAP_PX = 6  # between the title block and the top of the columns


def layout_raw(raw: object) -> Scene:
    """Lay out a Kanban board from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``kanban`` spec drawn as a work board.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(read_spec(raw))


def layout(spec: KanbanSpec) -> Scene:
    """Place the columns, their header pills and their cards.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    rules = theme.planning.kanban
    top = theme.layout.margin + (theme.layout.title_block_height if spec.title else 0)
    top += HEADER_GAP_PX
    height = max(_content_height(column, rules) for column in spec.columns)
    frames, nodes = [], []
    for index, column in enumerate(spec.columns):
        left = theme.layout.margin + index * (rules.column_width + rules.column_gap)
        frames.append(_frame(column, index, (left, top, height), rules))
        nodes += _header(column, index, (left, top), theme)
        nodes += _cards(column, index, (left, top), theme)
    scene = Scene(0, 0, spec.title, spec.description, tuple(frames), tuple(nodes), ())
    return fit_canvas(scene)


def _content_height(column: Column, rules: KanbanRules) -> float:
    """Return the height a column needs for its header and its cards."""
    count = len(column.cards)
    stack = count * rules.card_height + max(count - 1, 0) * rules.card_gap
    return rules.cards_top + stack + rules.bottom_pad


def _frame(
    column: Column, index: int, box: tuple[float, float, float], rules: KanbanRules
) -> Frame:
    """Build the tinted area of a column."""
    left, top, height = box
    return Frame(
        f"column-{index}",
        left,
        top,
        rules.column_width,
        height,
        None,
        column.tone,
        FrameVariant.COLUMN,
    )


def _header(column: Column, index: int, origin: tuple[float, float], theme: Theme) -> list[Node]:
    """Build the pills of a column header: its name, and its count or its limit."""
    rules = theme.planning.kanban
    left, top = origin
    name_width = estimate_text_width(column.label, theme.layout, rules.pill_font_size)
    name_width += 2 * rules.pill_pad
    pills = [
        _pill(
            f"name-{index}",
            column.label,
            (left + rules.pad, top + rules.header_top, name_width, rules.pill_height),
            (PillKind.NAME, rules.pill_font_size, column),
        )
    ]
    text, kind = _count_text(column)
    width = estimate_text_width(text, theme.layout, rules.badge_font_size) + 2 * rules.badge_pad
    badge_top = top + rules.header_top + (rules.pill_height - rules.badge_height) / 2
    badge_left = left + rules.pad + name_width + rules.badge_gap
    box = (badge_left, badge_top, max(width, rules.badge_min_width), rules.badge_height)
    pills.append(_pill(f"count-{index}", text, box, (kind, rules.badge_font_size, column)))
    return pills


def _count_text(column: Column) -> tuple[str, PillKind]:
    """Return the text of the second pill of a header: the count, or ``3 / 3`` and its kind."""
    count = len(column.cards)
    if column.limit is None:
        return str(count), PillKind.COUNT
    kind = PillKind.FULL if count >= column.limit else PillKind.LIMIT
    return f"{count} / {column.limit}", kind


def _pill(
    identifier: str,
    text: str,
    box: tuple[float, float, float, float],
    look: tuple[PillKind, float, Column],
) -> Node:
    """Build one pill node at ``box`` (x, y, width, height)."""
    x, y, width, height = box
    kind, font_size, column = look
    return Node(
        identifier, Shape.BOARD_PILL, x, y, width, height, (text,), None, column.tone, None,
        font_size, plan=PlanView(pill=kind),
    )  # fmt: skip


def _cards(column: Column, index: int, origin: tuple[float, float], theme: Theme) -> list[Node]:
    """Build the cards of a column, the first at the top."""
    rules = theme.planning.kanban
    left, top = origin
    nodes = []
    for number, card in enumerate(column.cards):
        y = top + rules.cards_top + number * (rules.card_height + rules.card_gap)
        box = (left + rules.pad, y, rules.column_width - 2 * rules.pad, rules.card_height)
        nodes.append(_card(card, f"c{index}-{number}", box, (column, theme)))
    return nodes


def _card(
    card: Card,
    identifier: str,
    box: tuple[float, float, float, float],
    context: tuple[Column, Theme],
) -> Node:
    """Build the node of a card: its wrapped title, its tag and its owner circle."""
    column, theme = context
    rules = theme.planning.kanban
    x, y, width, height = box
    room = width - 2 * rules.card_pad
    view = PlanView(
        status=Status.DONE if card.is_done else None,
        initials=card.owner.initials if card.owner else "",
        person_tone=card.owner.tone if card.owner else None,
        tag=card.kind,
        tag_tone=card.tag_tone,
    )
    detail = wrap_text(card.detail, theme.layout, room, rules.detail_font_size)
    return Node(
        identifier,
        Shape.KANBAN_CARD,
        x,
        y,
        width,
        height,
        tuple(wrap_text(card.label, theme.layout, room, rules.title_font_size)),
        None,
        column.tone,
        None,
        rules.title_font_size,
        detail=tuple(detail),
        plan=view,
    )
