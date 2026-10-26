"""Choose the grid cell of every box of a C4 diagram.

A cell is ``(column, row)``; columns are 520 px apart and rows 270 px (design 12 section 6).
People go on the top row, the boxes of the opened thing in rows by how far they are from a
person along the lines, and the outside systems to the right of the row of the box that calls
them. An element with ``at`` keeps the cell the author gave it.
"""

from .c4_spec import CONTEXT_LEVEL, C4Spec, Element, Kind

Cell = tuple[float, float]

PEOPLE_ROW = 0
CONTEXT_SYSTEM_ROW = 1
CONTEXT_OUTSIDE_ROW = 2


def assign_cells(spec: C4Spec) -> dict[str, Cell]:
    """Return the cell of every element: chosen by its lines, or as the author wrote with ``at``.

    Args:
        spec: The checked spec.

    Returns:
        Element id to ``(column, row)``.
    """
    cells = _context_cells(spec) if spec.level == CONTEXT_LEVEL else _zoom_cells(spec)
    cells.update({e.id: (e.at[1], e.at[0]) for e in spec.elements if e.at is not None})
    return cells


def _spread(count: int, centre: float) -> list[float]:
    """Return the columns of ``count`` boxes one column apart, centred on a column."""
    return [centre + index - (count - 1) / 2 for index in range(count)]


def _context_cells(spec: C4Spec) -> dict[str, Cell]:
    """Place level 1: people on top, the system in the middle, outside systems below."""
    people = [e for e in spec.elements if e.kind is Kind.PERSON]
    outside = [e for e in spec.elements if e.kind is Kind.EXTERNAL]
    systems = [e for e in spec.elements if e.kind is Kind.SYSTEM]
    centre = (max(len(people), len(outside), 1) - 1) / 2
    cells: dict[str, Cell] = {}
    for row, group in (
        (PEOPLE_ROW, people),
        (CONTEXT_SYSTEM_ROW, systems),
        (CONTEXT_OUTSIDE_ROW, outside),
    ):
        cells.update(
            {e.id: (col, row) for e, col in zip(group, _spread(len(group), centre), strict=True)}
        )
    return cells


def _zoom_cells(spec: C4Spec) -> dict[str, Cell]:
    """Place level 2 or 3: rows by distance from the people, columns near the callers."""
    ranks = _ranks(spec)
    cells: dict[str, Cell] = {}
    taken: set[Cell] = set()
    ordered = sorted(spec.elements, key=lambda e: (ranks[e.id], _index(spec, e)))
    for element in ordered:
        if element.kind is Kind.EXTERNAL:
            continue
        cell = _free(taken, _wanted(element, spec, (ranks, cells)))
        cells[element.id] = cell
        taken.add(cell)
    right = max((col for col, _ in cells.values()), default=0) + 1
    for element in (e for e in spec.elements if e.kind is Kind.EXTERNAL):
        row = _caller_row(element, spec, cells)
        cell = _free_row(taken, (right, row))
        cells[element.id] = cell
        taken.add(cell)
    return cells


def _index(spec: C4Spec, element: Element) -> int:
    """Return the place of an element in the spec, to keep the order the author wrote."""
    return spec.elements.index(element)


def _callers(spec: C4Spec, element: Element) -> list[str]:
    """Return the ids of the boxes that start a relation to an element."""
    return [r.source for r in spec.relations if r.target == element.id and r.source != element.id]


def _ranks(spec: C4Spec) -> dict[str, int]:
    """Return the row of every element: people 0, then one more than the lowest caller."""
    ranks: dict[str, int] = {}
    for element in spec.elements:
        _rank_of(element.id, spec, ranks, set())
    return ranks


def _rank_of(identifier: str, spec: C4Spec, ranks: dict[str, int], visiting: set[str]) -> int:
    """Return the row of one element, going back along its callers; a loop is cut."""
    if identifier in ranks:
        return ranks[identifier]
    element = next(e for e in spec.elements if e.id == identifier)
    visiting.add(identifier)
    callers = [c for c in _callers(spec, element) if c not in visiting]
    above = [_rank_of(caller, spec, ranks, visiting) for caller in callers]
    visiting.discard(identifier)
    rank = PEOPLE_ROW if element.kind is Kind.PERSON or not above else max(above) + 1
    ranks[identifier] = rank
    return rank


def _wanted(element: Element, spec: C4Spec, placed: tuple[dict[str, int], dict[str, Cell]]) -> Cell:
    """Return the cell a box would like: in its rank, at the middle of its callers' columns."""
    ranks, cells = placed
    columns = [cells[c][0] for c in _callers(spec, element) if c in cells]
    column = round(sum(columns) / len(columns)) if columns else 0
    return (column, ranks[element.id])


def _free(taken: set[Cell], wanted: Cell) -> Cell:
    """Return the nearest cell to ``wanted`` on its row that no box holds, to the right first."""
    column, row = wanted
    step = 0
    while True:
        for candidate in (column + step, column - step):
            if (candidate, row) not in taken and candidate >= 0:
                return (candidate, row)
        step += 1


def _caller_row(element: Element, spec: C4Spec, cells: dict[str, Cell]) -> int:
    """Return the row of the box that calls an outside system, the row of its first line."""
    for relation in spec.relations:
        other = relation.source if relation.target == element.id else relation.target
        if element.id in (relation.source, relation.target) and other in cells:
            return int(cells[other][1])
    return CONTEXT_SYSTEM_ROW


def _free_row(taken: set[Cell], wanted: Cell) -> Cell:
    """Return the first cell at or below ``wanted`` that no box holds."""
    column, row = wanted
    while (column, row) in taken:
        row += 1
    return (column, row)
