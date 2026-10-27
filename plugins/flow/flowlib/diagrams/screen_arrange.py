"""Arrange the items of a screen flow that have no ``at`` on the grid of rows and columns.

The rules, which the skill states too:

- Each zone is a block. Its screens are read left to right in the order of the flow (their
  distance from the first screen of the zone) and wrap in whole rows: a row is filled before the
  next is begun, and the next row starts at the left.
- A zone wraps after at most ``MAX_ZONE_COLUMNS`` columns, and its rows are balanced.
- Blocks sit on shelves: a shelf is filled from the left with the next zones in the order of the
  flow until ``MAX_SHELF_COLUMNS`` columns are used, then the next shelf is begun below.
- A zone that holds desktop screens goes on shelves of its own at the bottom (a web flow is drawn
  below the app flow).
- The tabs of a tab bar stay together on a row of their own.
- An item with no zone joins the zone of the screen that leads to it, or that it leads to.
"""

from collections import defaultdict
from dataclasses import dataclass

from ..model import Device
from .screen_spec import FlowSpec, Item, ItemKind, Transition, TransitionKind

MAX_ZONE_COLUMNS = 5
MAX_SHELF_COLUMNS = 9
NO_ZONE = ""
Cell = tuple[int, int]


@dataclass(frozen=True)
class Block:
    """The items of one zone, in reading order, and the columns and rows they take."""

    zone: str
    items: list[Item]
    columns: int
    rows: int
    is_web: bool


def is_flow_edge(transition: Transition) -> bool:
    """Tell a transition that moves the flow on, as opposed to one that goes back."""
    return transition.kind not in (TransitionKind.BACK, TransitionKind.RETRY)


def rank_items(spec: FlowSpec) -> dict[str, int]:
    """Return each item's distance from the start of the flow, in forward arrows.

    Args:
        spec: The parsed spec.

    Returns:
        Item id to rank. The start is what the entries open, or the first item when there are
        none; an item that no path reaches comes after the others.
    """
    entries = {item.id for item in spec.items if item.kind is ItemKind.ENTRY}
    edges = [(t.source, t.target) for t in spec.transitions if is_flow_edge(t)]
    sources = [t.target for t in spec.transitions if t.source in entries]
    return _distances([item.id for item in spec.items], edges, sources)


def _distances(ids: list[str], edges: list[tuple[str, str]], sources: list[str]) -> dict[str, int]:
    """Return the shortest path from the sources to each id; an id no path reaches comes last."""
    following: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        following[source].append(target)
    depth: dict[str, int] = {}
    queue = list(dict.fromkeys(sources or ids[:1]))
    depth.update(dict.fromkeys(queue, 0))
    for current in queue:
        for target in following[current]:
            if target not in depth:
                depth[target] = depth[current] + 1
                queue.append(target)
    last = max(depth.values(), default=0) + 1
    return {item_id: depth.get(item_id, last) for item_id in ids}


def arrange(spec: FlowSpec, items: list[Item], first_row: int) -> dict[str, Cell]:
    """Give each of the items a cell, in blocks per zone on shelves, from a row on.

    Args:
        spec: The parsed spec.
        items: The items to place: not entries, and with no ``at``.
        first_row: The first row that is free.

    Returns:
        Item id to ``(row, column)``.
    """
    zones = _zones_of(spec, items)
    blocks = _blocks(spec, items, zones, rank_items(spec))
    return _place_blocks(blocks, first_row)


def _place_blocks(blocks: list[Block], first_row: int) -> dict[str, Cell]:
    """Put the blocks on shelves, in order, from a row on."""
    cells: dict[str, Cell] = {}
    row = first_row
    for shelf in _shelves(blocks):
        column = 0
        for block in shelf:
            cells.update(_place_block(block, row, column))
            column += block.columns
        row += max(block.rows for block in shelf)
    return cells


def _zones_of(spec: FlowSpec, items: list[Item]) -> dict[str, str]:
    """Return the zone each item is arranged in: its own, or that of a neighbour in the flow."""
    zones = {item.id: item.zone or NO_ZONE for item in spec.items}
    for item in items:
        if zones[item.id] != NO_ZONE:
            continue
        for transition in spec.transitions:
            other = None
            if transition.target == item.id:
                other = transition.source
            elif transition.source == item.id:
                other = transition.target
            if other is not None and zones[other] != NO_ZONE:
                zones[item.id] = zones[other]
                break
    return zones


def _blocks(
    spec: FlowSpec, items: list[Item], zones: dict[str, str], ranks: dict[str, int]
) -> list[Block]:
    """Group the items by zone, order the zones by the flow and the items inside each zone."""
    members: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        members[zones[item.id]].append(item)
    order = {item.id: number for number, item in enumerate(spec.items)}
    blocks = []
    for zone, group in members.items():
        ordered = _reading_order(spec, group, (order, ranks))
        columns, rows = _size_of(ordered)
        is_web = any(i.view is not None and i.view.device is Device.DESKTOP for i in group)
        blocks.append(Block(zone, ordered, columns, rows, is_web))
    start = {block.zone: min((ranks[i.id], order[i.id]) for i in block.items) for block in blocks}
    return sorted(blocks, key=lambda block: (block.is_web, start[block.zone]))


def _reading_order(
    spec: FlowSpec, group: list[Item], orders: tuple[dict[str, int], dict[str, int]]
) -> list[Item]:
    """Order the items of a zone by their distance from where the flow enters it.

    The flow enters a zone at the items that an arrow leads to from an entry or from an item that
    is nearer the start of the flow. The tabs of a bar stay together at the end.
    """
    order, ranks = orders
    entries = {item.id for item in spec.items if item.kind is ItemKind.ENTRY}
    ids = {item.id for item in group}
    flow = [t for t in spec.transitions if is_flow_edge(t)]
    inside = [(t.source, t.target) for t in flow if t.source in ids and t.target in ids]
    doors = [
        t.target
        for t in flow
        if t.target in ids
        and t.source not in ids
        and (t.source in entries or ranks[t.source] < ranks[t.target])
    ]
    depth = _distances([item.id for item in group], inside, doors)
    return sorted(
        group, key=lambda item: (item.kind is ItemKind.TAB, depth[item.id], order[item.id])
    )


def _size_of(items: list[Item]) -> tuple[int, int]:
    """Return the columns and rows of a block: as few columns as keep its rows balanced."""
    plain = [item for item in items if item.kind is not ItemKind.TAB]
    tabs = len(items) - len(plain)
    rows = max(1, -(-len(plain) // MAX_ZONE_COLUMNS)) if plain else 0
    columns = -(-len(plain) // rows) if rows else 0
    return max(columns, tabs), rows + (1 if tabs else 0)


def _shelves(blocks: list[Block]) -> list[list[Block]]:
    """Fill shelves from the left with the blocks in order; web blocks never share with app ones."""
    shelves: list[list[Block]] = []
    used = 0
    for block in blocks:
        fits = shelves and used + block.columns <= MAX_SHELF_COLUMNS
        if fits and shelves[-1][0].is_web == block.is_web:
            shelves[-1].append(block)
            used += block.columns
        else:
            shelves.append([block])
            used = block.columns
    return shelves


def _place_block(block: Block, row: int, column: int) -> dict[str, Cell]:
    """Put the items of a block in whole rows from the left, tabs on a row of their own."""
    plain = [item for item in block.items if item.kind is not ItemKind.TAB]
    tabs = [item for item in block.items if item.kind is ItemKind.TAB]
    cells = {
        item.id: (row + number // block.columns, column + number % block.columns)
        for number, item in enumerate(plain)
    }
    tab_row = row + block.rows - 1
    cells.update({item.id: (tab_row, column + number) for number, item in enumerate(tabs)})
    return cells
