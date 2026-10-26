"""Choose the column and the row of every element of a BPMN diagram.

Time runs left to right, so a column is a moment. An element is one column after the one that
leads to it. Elements that happen at the same moment in different pools share a column when
they are tied by a message flow, so that the message runs straight up or down. A row is a line
inside a lane: the happy path stays on row 0 and an alternative branch goes to the row below.
"""

from dataclasses import dataclass

from .bpmn_spec import BpmnSpec, Item, ItemKind, Link, LinkStyle

ROUND_LIMIT_FACTOR = 4  # a ranking that needs more rounds than this per element does not settle
ROUND_LIMIT_BASE = 10
Edge = tuple[str, str, int]  # from, to, how many columns later the target is
LaneKey = tuple[str | None, str | None]


@dataclass(frozen=True)
class Grid:
    """The column and the row of every element, by id."""

    columns: dict[str, int]
    rows: dict[str, int]


def build_grid(spec: BpmnSpec) -> Grid:
    """Place every element on a grid of columns and rows.

    Args:
        spec: The checked spec.

    Returns:
        The grid. A data store gets the column of its task and the row below it.
    """
    items = {item.id: item for item in spec.items if item.kind is not ItemKind.STORE}
    columns = _columns(spec, items)
    rows = _rows(spec, items, columns)
    for store in (item for item in spec.items if item.kind is ItemKind.STORE):
        host = _host_of_store(spec, store)
        columns[store.id] = columns.get(host.id, 0) if host else 0
        rows[store.id] = (rows.get(host.id, 0) if host else 0) + 1
    return Grid(columns, _free_store_rows(spec, columns, rows))


def _host_of_store(spec: BpmnSpec, store: Item) -> Item | None:
    """Return the task a data store is joined to by a data flow."""
    by_id = {item.id: item for item in spec.items}
    for link in spec.links:
        other = link.target if link.source == store.id else link.source
        if store.id in (link.source, link.target) and other in by_id:
            return by_id[other]
    return None


def _free_store_rows(
    spec: BpmnSpec, columns: dict[str, int], rows: dict[str, int]
) -> dict[str, int]:
    """Move a data store down until no other element holds its cell."""
    taken = {
        (columns[item.id], item.pool, item.lane, rows[item.id])
        for item in spec.items
        if item.kind is not ItemKind.STORE
    }
    result = dict(rows)
    for store in (item for item in spec.items if item.kind is ItemKind.STORE):
        host = _host_of_store(spec, store)
        pool, lane = (host.pool, host.lane) if host else (store.pool, store.lane)
        while (columns[store.id], pool, lane, result[store.id]) in taken:
            result[store.id] += 1
        taken.add((columns[store.id], pool, lane, result[store.id]))
    return result


def _forward(spec: BpmnSpec, items: dict[str, Item]) -> list[Link]:
    """Return the sequence flows that lead forward, leaving out the ones that loop back."""
    links = [
        link
        for link in spec.links
        if link.style is LinkStyle.SEQUENCE and link.source in items and link.target in items
    ]
    returning = _returning(links, items)
    return [link for link in links if link not in returning]


def _returning(links: list[Link], items: dict[str, Item]) -> list[Link]:
    """Find the flows that close a loop: those that lead to an element still being visited."""
    out: dict[str, list[Link]] = {}
    for link in links:
        out.setdefault(link.source, []).append(link)
    found: list[Link] = []
    done: set[str] = set()
    on_path: set[str] = set()

    def visit(name: str) -> None:
        """Walk the flows from one element, noting those that go back to one on the path."""
        on_path.add(name)
        for link in out.get(name, []):
            if link.target in on_path:
                found.append(link)
            elif link.target not in done:
                visit(link.target)
        on_path.discard(name)
        done.add(name)

    for name in items:
        if name not in done:
            visit(name)
    return found


def _edges(spec: BpmnSpec, items: dict[str, Item]) -> list[Edge]:
    """Return the ordering the columns must keep: each flow, and each boundary event on its task."""
    boundaries: dict[str, list[Item]] = {}
    for item in items.values():
        if item.attached_to in items:
            boundaries.setdefault(item.attached_to or "", []).append(item)
    edges = [(host, event.id, 0) for host, events in boundaries.items() for event in events]
    messaged = {
        end
        for link in spec.links
        if link.style is LinkStyle.MESSAGE
        for end in (link.source, link.target)
    }
    for link in _forward(spec, items):
        edges.append((link.source, link.target, _gap(items[link.source], (boundaries, messaged))))
    return edges


def _gap(source: Item, where: tuple[dict[str, list[Item]], set[str]]) -> int:
    """Return how many columns after its source a flow's target is.

    The handler of the first boundary event of a task is under the task, in its column; the
    handler of the next one is one column later; any other target is one column later. When a
    message flow runs straight up or down at the column of the task, its handlers move one
    column on so that the message does not run through them.
    """
    boundaries, messaged = where
    if source.attached_to not in boundaries:
        return 1
    host = source.attached_to or ""
    return boundaries[host].index(source) + (host in messaged)


def _columns(spec: BpmnSpec, items: dict[str, Item]) -> dict[str, int]:
    """Give every element a column, then tie the two ends of each message flow together."""
    edges = _edges(spec, items)
    floors = {name: item.column or 0 for name, item in items.items()}
    fixed = {name for name, item in items.items() if item.column is not None}
    equal: list[tuple[str, str]] = []
    messages = [
        (link.source, link.target)
        for link in spec.links
        if link.style is LinkStyle.MESSAGE and link.source in items and link.target in items
    ]
    for pair in messages:
        if _solve(floors, edges, ([*equal, pair], fixed)) is not None:
            equal.append(pair)
    return _solve(floors, edges, (equal, fixed)) or dict(floors)


def _solve(
    floors: dict[str, int], edges: list[Edge], rules: tuple[list[tuple[str, str]], set[str]]
) -> dict[str, int] | None:
    """Push elements to later columns until every rule holds; None when they never settle.

    Args:
        floors: The first column of every element.
        edges: The ordering the columns must keep.
        rules: The pairs of elements that must share a column, and the elements whose column
            the author fixed, which are never moved.

    Returns:
        The column of every element, or None when the rules cannot all hold.
    """
    equal, fixed = rules
    ranks = dict(floors)
    for _ in range(ROUND_LIMIT_FACTOR * len(ranks) + ROUND_LIMIT_BASE):
        changed = False
        for source, target, gap in edges:
            if target not in fixed and ranks[target] < ranks[source] + gap:
                ranks[target] = ranks[source] + gap
                changed = True
        for first, second in equal:
            changed |= _tie(ranks, first, second, fixed)
        if not changed:
            return ranks
    return None


def _tie(ranks: dict[str, int], first: str, second: str, fixed: set[str]) -> bool:
    """Bring two elements that must share a column to the same one; tell whether one moved."""
    if first in fixed and second in fixed:
        return False
    if first in fixed or second in fixed:
        anchor, mover = (first, second) if first in fixed else (second, first)
        moved = ranks[mover] != ranks[anchor]
        ranks[mover] = ranks[anchor]
        return moved
    highest = max(ranks[first], ranks[second])
    moved = ranks[first] != highest or ranks[second] != highest
    ranks[first] = ranks[second] = highest
    return moved


@dataclass(frozen=True)
class _Flows:
    """The sequence flows that lead forward, and which way each element talks to other pools."""

    forward: list[Link]
    leans: dict[str, int]  # -1: sends or receives a message to a pool above, 1: below


def _leans(spec: BpmnSpec) -> dict[str, int]:
    """Say, for each element, whether its message partners are in pools above or below it."""
    order = {pool.id: index for index, pool in enumerate(spec.pools)}
    pool_of = {item.id: item.pool for item in spec.items}
    leans: dict[str, int] = {}
    for link in spec.links:
        if link.style is not LinkStyle.MESSAGE:
            continue
        for mine, other in ((link.source, link.target), (link.target, link.source)):
            first, second = pool_of.get(mine), pool_of.get(other, other)
            if mine in pool_of and first in order and second in order:
                leans[mine] = 1 if order[second] > order[first] else -1
    return leans


def _rows(spec: BpmnSpec, items: dict[str, Item], columns: dict[str, int]) -> dict[str, int]:
    """Give every element a row in its lane: its predecessor's, or the one below for a branch."""
    flows = _Flows(_forward(spec, items), _leans(spec))
    rows: dict[str, int] = {}
    taken: set[tuple[LaneKey, int, int]] = set()
    depth = _solve(dict.fromkeys(items, 0), _edges(spec, items), ([], set())) or columns
    order = sorted(items.values(), key=lambda item: (depth[item.id], _position(spec, item)))
    for item in order:
        wanted = item.row if item.row is not None else _wanted_row(item, items, flows, rows)
        key = ((item.pool, item.lane), columns[item.id])
        row = wanted
        while (*key, row) in taken and item.attached_to is None:
            row += 1
        rows[item.id] = row
        if item.attached_to is None:
            taken.add((*key, row))
    return rows


def _position(spec: BpmnSpec, item: Item) -> int:
    """Return where an element is written in the spec, to break ties in the order."""
    return [candidate.id for candidate in spec.items].index(item.id)


def _wanted_row(item: Item, items: dict[str, Item], flows: _Flows, rows: dict[str, int]) -> int:
    """Return the row an element would like: its host's, its predecessor's, or the one below."""
    if item.attached_to in rows:
        return rows[item.attached_to or ""]
    for link in flows.forward:
        if link.target != item.id or link.source not in rows:
            continue
        source = items[link.source]
        if source.attached_to is not None:
            return rows[source.attached_to] + 1
        if (source.pool, source.lane) == (item.pool, item.lane):
            return rows[link.source] + _branch_index(link, flows, items)
    return 0


def _branch_index(link: Link, flows: _Flows, items: dict[str, Item]) -> int:
    """Return which branch of its source a flow is in its lane: 0 for the main one.

    The main flow comes first. Among the others, a branch whose element sends a message to a
    pool below goes lower, so that the message does not run through its sibling.
    """
    source = items[link.source]
    same_lane = [
        other
        for other in flows.forward
        if other.source == link.source
        and (items[other.target].pool, items[other.target].lane) == (source.pool, source.lane)
    ]

    def rank(other: Link) -> tuple[bool, int, int]:
        """Rank a branch: main first, then upward messages, then none, then downward ones."""
        return (not other.is_main, flows.leans.get(other.target, 0), flows.forward.index(other))

    return sorted(same_lane, key=rank).index(link)
