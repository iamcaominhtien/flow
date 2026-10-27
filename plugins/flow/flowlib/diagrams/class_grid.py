"""Choose the grid cell of every class of a class diagram.

A cell is ``(row, column)``; a column may be a half, to centre two children under a parent.
Parents go above their children (inheritance and realisation); the class the story is about,
the first one written, goes top left. Classes with no cell of their own are ordered by how they
are joined and wrapped after four to a row. A class with ``at`` keeps its cell.
"""

from collections import deque

from .class_spec import HIERARCHY_STYLES, ClassSpec

Cell = tuple[float, float]
CLASSES_PER_ROW = 4  # about ten classes to a page: four across keeps a row readable


def assign_cells(spec: ClassSpec) -> dict[str, Cell]:
    """Return the ``(row, column)`` of every class.

    Args:
        spec: The checked spec.

    Returns:
        Class id to cell.
    """
    levels = _levels(spec)
    rows: list[list[str]] = []
    for level in sorted(set(levels.values())):
        members = [name for name in _joined_order(spec) if levels[name] == level]
        rows.extend(
            members[start : start + CLASSES_PER_ROW]
            for start in range(0, len(members), CLASSES_PER_ROW)
        )
    cells = {name: (float(row), float(column)) for row, names in enumerate(rows)
             for column, name in enumerate(names)}  # fmt: skip
    cells.update({box.id: box.at for box in spec.classes if box.at is not None})
    return cells


def _levels(spec: ClassSpec) -> dict[str, int]:
    """Return how many parents deep each class is: roots are level 0."""
    parents: dict[str, list[str]] = {box.id: [] for box in spec.classes}
    for relation in spec.relations:
        if relation.style in HIERARCHY_STYLES and relation.source != relation.target:
            parents[relation.source].append(relation.target)
    levels: dict[str, int] = {}

    def depth(name: str, path: tuple[str, ...]) -> int:
        """Return the depth of a class; a loop of parents counts as a root."""
        if name in levels:
            return levels[name]
        if name in path:
            return 0
        found = max((depth(parent, (*path, name)) + 1 for parent in parents[name]), default=0)
        levels[name] = found
        return found

    for box in spec.classes:
        depth(box.id, ())
    return levels


def _joined_order(spec: ClassSpec) -> list[str]:
    """Return the classes in the order a walk along the relations from the first one meets them."""
    neighbours: dict[str, list[str]] = {box.id: [] for box in spec.classes}
    for relation in spec.relations:
        neighbours[relation.source].append(relation.target)
        neighbours[relation.target].append(relation.source)
    order: list[str] = []
    for box in spec.classes:
        if box.id in order:
            continue
        queue = deque([box.id])
        order.append(box.id)
        while queue:
            for name in neighbours[queue.popleft()]:
                if name not in order:
                    order.append(name)
                    queue.append(name)
    return order
