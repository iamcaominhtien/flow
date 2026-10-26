"""Choose the grid cell of every box of a data flow diagram.

A cell is ``(column, row)``; columns are 640 px apart and rows 400 px (design 14 section 5).
Outside parties go on the outside edge, processes in the middle and stores between the
processes that share them. An element with ``at`` keeps the cell the author gave it.
"""

from collections import Counter

from ..reader import SpecError
from .dfd_spec import CONTEXT_LEVEL, OPENED_LEVEL, DfdSpec, Element, Kind

Cell = tuple[float, float]

CONTEXT_PROCESS_CELL: Cell = (1, 1)
CONTEXT_PARTY_CELLS: tuple[Cell, ...] = (
    (0, 1),
    (1, 0),
    (2, 1),
    (1, 2),
    (0, 0),
    (2, 0),
    (2, 2),
    (0, 2),
)  # west, north, east, south, then the four corners
PROCESS_COLUMNS = 2  # level 1 puts its processes in two columns, in reading order
FIRST_PROCESS_COLUMN = 1
ROW_STEP = 2  # a row of processes, then a row for the stores between them
NEIGHBOUR_STEPS: tuple[Cell, ...] = (
    (0, 0),
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
    (2, 0),
    (-2, 0),
    (0, 2),
    (0, -2),
)


def assign_cells(spec: DfdSpec) -> dict[str, Cell]:
    """Return the cell of every element: chosen by its links, or as the author wrote with ``at``.

    Args:
        spec: The checked spec.

    Returns:
        Element id to ``(column, row)``.

    Raises:
        SpecError: If level 0 has more outside parties than it has places for.
    """
    if spec.level == CONTEXT_LEVEL:
        cells = _context_cells(spec)
    elif spec.level == OPENED_LEVEL:
        cells = _opened_cells(spec)
    else:
        cells = _top_cells(spec)
    cells.update({e.id: (e.at[1], e.at[0]) for e in spec.elements if e.at is not None})
    return cells


def _links(spec: DfdSpec) -> dict[str, Counter[str]]:
    """Count the flows between each element and each of its neighbours."""
    links: dict[str, Counter[str]] = {element.id: Counter() for element in spec.elements}
    for flow in spec.flows:
        links[flow.source][flow.target] += 1
        links[flow.target][flow.source] += 1
    return links


def _free_cell(taken: set[Cell], wanted: Cell) -> Cell:
    """Return the cell nearest to ``wanted`` that no box holds yet."""
    for step_x, step_y in NEIGHBOUR_STEPS:
        cell = (wanted[0] + step_x, wanted[1] + step_y)
        if cell not in taken:
            return cell
    return wanted


def _main_neighbour(element: Element, links: dict[str, Counter[str]], among: list[str]) -> str:
    """Return the process an element has the most flows with, the first one on a tie."""
    counts = links[element.id]
    return max(among, key=lambda process: (counts[process], -among.index(process)))


def _context_cells(spec: DfdSpec) -> dict[str, Cell]:
    """Place the one process in the middle and the outside parties around it."""
    parties = [e for e in spec.elements if e.kind is not Kind.PROCESS]
    if len(parties) > len(CONTEXT_PARTY_CELLS):
        raise SpecError(
            [f"level 0 has room for {len(CONTEXT_PARTY_CELLS)} outside parties; set 'at' on them"]
        )
    cells = {e.id: CONTEXT_PROCESS_CELL for e in spec.elements if e.kind is Kind.PROCESS}
    cells.update({party.id: CONTEXT_PARTY_CELLS[i] for i, party in enumerate(parties)})
    return cells


def _top_cells(spec: DfdSpec) -> dict[str, Cell]:
    """Place level 1: processes in two columns, parties beside their process, stores between."""
    links = _links(spec)
    processes = [e for e in spec.elements if e.kind is Kind.PROCESS]
    cells: dict[str, Cell] = {}
    for index, process in enumerate(processes):
        column = FIRST_PROCESS_COLUMN + index % PROCESS_COLUMNS
        cells[process.id] = (column, ROW_STEP * (index // PROCESS_COLUMNS))
    taken = set(cells.values())
    for party in (e for e in spec.elements if e.kind is Kind.EXTERNAL):
        owner = cells[_main_neighbour(party, links, [p.id for p in processes])]
        side = 0 if owner[0] == FIRST_PROCESS_COLUMN else FIRST_PROCESS_COLUMN + PROCESS_COLUMNS
        cells[party.id] = _free_cell(taken, (side, owner[1]))
        taken.add(cells[party.id])
    for store in (e for e in spec.elements if e.kind is Kind.STORE):
        cells[store.id] = _free_cell(taken, _between(store, links, cells))
        taken.add(cells[store.id])
    return cells


def _between(store: Element, links: dict[str, Counter[str]], cells: dict[str, Cell]) -> Cell:
    """Return the cell in the middle of the processes a store is linked to."""
    near = [cells[other] for other in links[store.id] if other in cells]
    if not near:
        return (FIRST_PROCESS_COLUMN + 0.5, 1)
    column = sum(cell[0] for cell in near) / len(near)
    row = sum(cell[1] for cell in near) / len(near)
    return (column, row + 1 if row % ROW_STEP == 0 else row)


def _opened_cells(spec: DfdSpec) -> dict[str, Cell]:
    """Place level 2: the parts in a row, parties above, outside stores aside, new stores below."""
    links = _links(spec)
    inner = [e for e in spec.elements if e.kind is Kind.PROCESS and not e.is_outside]
    cells = {process.id: (FIRST_PROCESS_COLUMN + i, 0) for i, process in enumerate(inner)}
    taken = set(cells.values())
    names = [process.id for process in inner]
    for element in spec.elements:
        if element.id in cells:
            continue
        wanted = _opened_wanted(element, links, cells, names)
        cells[element.id] = _free_cell(taken, wanted)
        taken.add(cells[element.id])
    return cells


def _opened_wanted(
    element: Element, links: dict[str, Counter[str]], cells: dict[str, Cell], names: list[str]
) -> Cell:
    """Return the cell an element of level 2 would like: above, aside or below its process."""
    owner = cells[_main_neighbour(element, links, names)]
    if element.kind is Kind.EXTERNAL:
        return (owner[0], -1)
    if element.is_outside:
        first = element.id in links and names[0] in links[element.id]
        return (0, 0) if first else (FIRST_PROCESS_COLUMN + len(names), 0)
    touched = [cells[other][0] for other in links[element.id] if other in cells]
    return (round(sum(touched) / len(touched)) if touched else owner[0], 1)
