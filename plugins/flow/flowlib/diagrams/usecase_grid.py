"""Choose the grid cell and the owner of every use case of a use case diagram.

A use case belongs to the actor that takes part in it; one that only another use case includes
or extends belongs to the owner of that use case. Column 0 holds the use cases of the actors on
the left, one actor after the other and all of one actor together. A use case that another one
includes or extends goes to column 1, in the row of the use case it relates to (or the nearest
free row). The use cases of an actor outside the system on the right go to column 1.
"""

from .usecase_spec import Actor, LinkStyle, UseCaseSpec

Cell = tuple[int, int]  # (column, row)
BASE_COLUMN = 0
RELATED_COLUMN = 1


def related_partner(spec: UseCaseSpec) -> dict[str, str]:
    """Return, for each use case that is included or extends another, the use case it relates to.

    Args:
        spec: The checked spec.

    Returns:
        Dependent use case id to its base use case id.
    """
    partners: dict[str, str] = {}
    for link in spec.links:
        if link.style is LinkStyle.INCLUDE:
            partners.setdefault(link.target, link.source)
        elif link.style is LinkStyle.EXTEND:
            partners.setdefault(link.source, link.target)
    return partners


def owners(spec: UseCaseSpec) -> dict[str, str | None]:
    """Return the actor id each use case belongs to, or None when no actor can be found.

    Args:
        spec: The checked spec.

    Returns:
        Use case id to actor id.
    """
    actors = {actor.id for actor in spec.actors}
    found: dict[str, str | None] = {case.id: None for case in spec.use_cases}
    for link in spec.links:
        if link.style is not LinkStyle.ASSOCIATION:
            continue
        for actor_id, case_id in ((link.source, link.target), (link.target, link.source)):
            if actor_id in actors and case_id in found and found[case_id] is None:
                found[case_id] = actor_id
    partners = related_partner(spec)
    for case in spec.use_cases:
        found[case.id] = found[case.id] or _inherited(case.id, found, partners)
    return found


def _inherited(case_id: str, found: dict[str, str | None], partners: dict[str, str]) -> str | None:
    """Return the owner of the use case this one relates to, following the chain of partners."""
    seen = {case_id}
    current = partners.get(case_id)
    while current is not None and current not in seen:
        if found.get(current):
            return found[current]
        seen.add(current)
        current = partners.get(current)
    return None


def assign_cells(spec: UseCaseSpec) -> dict[str, Cell]:
    """Return the ``(column, row)`` of every use case.

    Args:
        spec: The checked spec.

    Returns:
        Use case id to cell.
    """
    owner, partners = owners(spec), related_partner(spec)
    cells: dict[str, Cell] = {}
    taken: set[Cell] = set()
    next_row = 0
    for actor in _in_order(spec):
        column = RELATED_COLUMN if actor and actor.is_external else BASE_COLUMN
        for case in spec.use_cases:
            if owner[case.id] != (actor.id if actor else None) or case.id in partners:
                continue
            row = _free_row(taken, column, next_row)
            cells[case.id] = (column, row)
            taken.add((column, row))
            next_row = row + 1
            _place_related(case.id, spec, (cells, taken), partners)
    for case in spec.use_cases:  # a dependent whose base was never placed
        if case.id not in cells:
            row = _free_row(taken, BASE_COLUMN, next_row)
            cells[case.id] = (BASE_COLUMN, row)
            taken.add((BASE_COLUMN, row))
    return cells


def _in_order(spec: UseCaseSpec) -> list[Actor | None]:
    """Return the actors on the left, then those on the right, then None for use cases of none."""
    left = [actor for actor in spec.actors if not actor.is_external]
    right = [actor for actor in spec.actors if actor.is_external]
    return [*left, *right, None]


def _free_row(taken: set[Cell], column: int, start: int) -> int:
    """Return the first row from ``start`` where a column is still free."""
    row = start
    while (column, row) in taken:
        row += 1
    return row


def _nearest_free_row(taken: set[Cell], column: int, wanted: int) -> int:
    """Return the free row of a column nearest to ``wanted``, trying the row above first.

    A line to a use case in the same or the next row above or below crosses no use case of the
    column it leaves; a farther row would send it across the ones in between.
    """
    distance = 0
    while True:
        for row in (wanted - distance, wanted + distance):
            if row >= 0 and (column, row) not in taken:
                return row
        distance += 1


def _place_related(
    base: str,
    spec: UseCaseSpec,
    placed: tuple[dict[str, Cell], set[Cell]],
    partners: dict[str, str],
) -> None:
    """Place the use cases that relate to a placed one in column 1, from the row of that one."""
    cells, taken = placed
    for case in spec.use_cases:
        if partners.get(case.id) != base or case.id in cells:
            continue
        row = _nearest_free_row(taken, RELATED_COLUMN, cells[base][1])
        cells[case.id] = (RELATED_COLUMN, row)
        taken.add((RELATED_COLUMN, row))
        _place_related(case.id, spec, placed, partners)
