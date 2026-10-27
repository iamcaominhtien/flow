"""Turn the items of a screen flow into nodes, and give each one a cell of the grid.

The author names a row and a column (``at``); an item without one is placed by ``screen_arrange``:
zone by zone, in reading order, wrapping in whole rows. Entries, which sit in a column of their
own at the left, take the row of the screen they open.
"""

from ..model import (
    DEFAULT_FONT_SIZE_PX,
    EdgeLabel,
    LabelKind,
    Node,
    Shape,
    Tone,
)
from ..reader import SpecError
from ..screen_parts import screen_size
from ..sizing import wrap_text
from ..theme import Theme
from .screen_arrange import arrange
from .screen_spec import FlowSpec, Item, ItemKind

ENTRY_COLUMN = -1  # entries sit in a column of their own, left of column 0
DECISION_TEXT_FRACTION = 0.64  # of its width, the part of a diamond that can hold text
DECISION_CHIP_RISE_PX = 14  # the system chip of a decision hangs this far above its top
Cell = tuple[int, int]


def build_nodes(spec: FlowSpec, theme: Theme) -> dict[str, Node]:
    """Build one unplaced node per item; positions are set later by the layout.

    Args:
        spec: The parsed spec.
        theme: The design tokens, which hold the sizes.

    Returns:
        Item id to node.
    """
    tones = {zone.id: zone.tone for zone in spec.zones}
    return {
        item.id: _node(item, item.tone or tones.get(item.zone or ""), theme) for item in spec.items
    }


def _node(item: Item, zone_tone: Tone | None, theme: Theme) -> Node:
    """Build the node of one item."""
    if item.kind is ItemKind.SCREEN:
        return _screen_node(item, zone_tone, theme)
    if item.kind is ItemKind.DECISION:
        return _decision_node(item, zone_tone, theme)
    if item.kind in (ItemKind.START, ItemKind.END):
        return _mark_node(item, theme)
    size = _size_of(item, theme)
    shape = {
        ItemKind.ENTRY: Shape.TERMINATOR,
        ItemKind.FLAG: Shape.FLAG,
        ItemKind.TAB: Shape.SCREEN,
    }[item.kind]
    return _plain_node(item, shape, size)


def _size_of(item: Item, theme: Theme) -> tuple[float, float]:
    """Return the size of an entry, a flag or a tab."""
    rules = theme.screen
    return {ItemKind.ENTRY: rules.entry, ItemKind.FLAG: rules.flag, ItemKind.TAB: rules.tab}[
        item.kind
    ]


def _plain_node(item: Item, shape: Shape, size: tuple[float, float]) -> Node:
    """Build a node that is a box with a name and an optional second line."""
    return Node(
        id=item.id,
        shape=shape,
        x=0,
        y=0,
        width=size[0],
        height=size[1],
        text=(item.name,),
        icon=item.icon,
        tone=None,
        number=None,
        font_size=DEFAULT_FONT_SIZE_PX,
        detail=(item.detail,) if item.detail else (),
    )


def _screen_node(item: Item, zone_tone: Tone | None, theme: Theme) -> Node:
    """Build a screen: a device frame, or a card, in the colour of its zone."""
    view = item.view
    assert view is not None
    width, height = screen_size(view, theme)
    return Node(
        id=item.id,
        shape=Shape.SCREEN,
        x=0,
        y=0,
        width=width,
        height=height,
        text=(item.name,),
        icon=None,
        tone=zone_tone,
        number=None,
        font_size=DEFAULT_FONT_SIZE_PX,
        screen=view,
    )


def _decision_node(item: Item, zone_tone: Tone | None, theme: Theme) -> Node:
    """Build a decision: a diamond with no id, and a system chip when an event decides it."""
    width, height = theme.screen.decision
    room = width * DECISION_TEXT_FRACTION
    lines = wrap_text(item.name, theme.layout, room, DEFAULT_FONT_SIZE_PX)
    has_zone_color = zone_tone is not None and zone_tone is not Tone.GRAY
    chip = None
    if item.trigger is not None:
        kind = LabelKind.SYSTEM if item.trigger.system_icon else LabelKind.USER
        at = (width / 2, -DECISION_CHIP_RISE_PX)
        chip = EdgeLabel(item.trigger.text, at, kind, icon=item.trigger.system_icon)
    return Node(
        id=item.id,
        shape=Shape.DECISION,
        x=0,
        y=0,
        width=width,
        height=height,
        text=tuple(lines),
        icon=None,
        tone=zone_tone if has_zone_color else None,
        number=None,
        font_size=DEFAULT_FONT_SIZE_PX,
        chip=chip,
    )


def _mark_node(item: Item, theme: Theme) -> Node:
    """Build the start or the end of the flow: a small circle with its name under it."""
    width, height = theme.layout.min_sizes[Shape.START]
    shape = Shape.START if item.kind is ItemKind.START else Shape.END
    return Node(
        id=item.id,
        shape=shape,
        x=0,
        y=0,
        width=width,
        height=height,
        text=(),
        icon=None,
        tone=None,
        number=None,
        font_size=DEFAULT_FONT_SIZE_PX,
        caption=item.name or None,
    )


def assign_cells(spec: FlowSpec) -> dict[str, Cell]:
    """Give every item a ``(row, column)``: the author's ``at``, else one found by rank.

    Args:
        spec: The parsed spec.

    Returns:
        Item id to cell. Entries are in column ``ENTRY_COLUMN``.

    Raises:
        SpecError: When two items are in the same cell.
    """
    cells = {
        item.id: (item.at[0], ENTRY_COLUMN if item.kind is ItemKind.ENTRY else item.at[-1])
        for item in spec.items
        if item.at is not None
    }
    _check_free(spec, cells)
    loose = [i for i in spec.items if i.id not in cells and i.kind is not ItemKind.ENTRY]
    first_row = max((row for row, _ in cells.values()), default=-1) + 1
    cells.update(arrange(spec, loose, first_row))
    for item in spec.items:
        if item.kind is ItemKind.ENTRY and item.id not in cells:
            cells[item.id] = (_entry_row(item, spec, cells), ENTRY_COLUMN)
    return cells


def _check_free(spec: FlowSpec, cells: dict[str, Cell]) -> None:
    """Raise when two items that are not entries name the same cell."""
    owners: dict[Cell, str] = {}
    kinds = {item.id: item.kind for item in spec.items}
    problems = []
    for item_id, cell in cells.items():
        if kinds[item_id] is ItemKind.ENTRY:
            continue
        if cell in owners:
            problems.append(f"'{owners[cell]}' and '{item_id}' are both at {list(cell)}")
        owners[cell] = item_id
    if problems:
        raise SpecError(problems)


def _entry_row(item: Item, spec: FlowSpec, cells: dict[str, Cell]) -> int:
    """Return the row of an entry: the row of the first screen it opens, or 0."""
    for transition in spec.transitions:
        if transition.source == item.id and transition.target in cells:
            return cells[transition.target][0]
    return 0


def densify(cells: dict[str, Cell]) -> tuple[dict[str, Cell], int, int]:
    """Renumber rows and columns so that there are no empty ones.

    Args:
        cells: Item id to cell, with any non-negative rows and columns (entries at column -1).

    Returns:
        The renumbered cells, the number of rows and the number of columns.
    """
    rows = {row: index for index, row in enumerate(sorted({c[0] for c in cells.values()}))}
    columns = {col: index for index, col in enumerate(sorted({c[1] for c in cells.values()}))}
    dense = {key: (rows[row], columns[col]) for key, (row, col) in cells.items()}
    return dense, len(rows), len(columns)
