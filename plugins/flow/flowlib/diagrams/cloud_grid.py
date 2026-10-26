"""Choose the grid cell of every part of a cloud diagram.

A cell is ``(column, row)``. The row follows the trust level: users above, then the edge, then
the public, private and data subnets (design 13 sections 3 and 8). Parts of one subnet kind
share a row in every zone, and a zone takes as many columns as its fullest subnet. A managed
service that sits in the region, outside the VPC, goes to the right of the VPC; an on-premises
site goes to the left. A part with ``at`` keeps the cell the author gave it.
"""

from ..theme import CloudRules
from .cloud_spec import SUBNET_KINDS, CloudSpec, Frame, FrameKind, Part

Cell = tuple[float, float]

MAX_PASSES = 6  # how often a row is passed on from part to part along the links
ABOVE = -1
SAME_ROW = 0
BELOW = 1


def assign_cells(spec: CloudSpec, rules: CloudRules) -> dict[str, Cell]:
    """Return the cell of every part: chosen by its frame and its links, or as written in ``at``.

    Args:
        spec: The checked spec.
        rules: The sizes and rows of a cloud diagram.

    Returns:
        Part id to ``(column, row)``.
    """
    rows = _subnet_and_edge_rows(spec, rules)
    columns = _network_columns(spec)
    _edge_columns(spec, columns)
    rows = _pass_rows(spec, rows)
    _outside_columns(spec, (rows, columns), rules)
    cells = {part.id: (columns[part.id], rows[part.id]) for part in spec.parts}
    cells = _apart(spec, cells)
    cells.update({part.id: (part.at[1], part.at[0]) for part in spec.parts if part.at is not None})
    return cells


def _subnet_and_edge_rows(spec: CloudSpec, rules: CloudRules) -> dict[str, float]:
    """Return the rows that follow from the frame of a part: its subnet, or the edge."""
    by_kind = {
        FrameKind.PUBLIC: rules.public_row,
        FrameKind.DMZ: rules.public_row,
        FrameKind.PRIVATE: rules.private_row,
        FrameKind.DATA: rules.data_row,
        FrameKind.EDGE: rules.edge_row,
    }
    rows: dict[str, float] = {}
    for part in spec.parts:
        for frame in spec.chain(part.frame):
            if frame.kind in by_kind:
                rows[part.id] = by_kind[frame.kind]
                break
    return rows


def _children(spec: CloudSpec, parent: str | None) -> list[Frame]:
    """Return the frames inside a frame, in the order of the spec."""
    return [frame for frame in spec.frames if frame.parent == parent]


def _network_columns(spec: CloudSpec) -> dict[str, float]:
    """Return the column of every part that sits in a network frame, left to right."""
    columns: dict[str, float] = {}
    next_column = 0.0
    for frame in _children(spec, None):
        if frame.kind in (FrameKind.EDGE, FrameKind.ONPREM):
            continue
        next_column = _visit(spec, frame, next_column, columns)
    return columns


def _visit(spec: CloudSpec, frame: Frame, start: float, columns: dict[str, float]) -> float:
    """Give columns to the parts inside a frame from ``start`` on; return the next free column."""
    subnets = [f for f in _children(spec, frame.id) if f.kind in SUBNET_KINDS]
    next_column = start
    for child in _children(spec, frame.id):
        if child.kind not in SUBNET_KINDS:
            next_column = _visit(spec, child, next_column, columns)
    if subnets:
        next_column = _stack_subnets(spec, subnets, next_column, columns)
    direct = [part for part in spec.parts if part.frame == frame.id]
    for part in direct if frame.kind not in SUBNET_KINDS else []:
        columns[part.id] = next_column
        next_column += 1
    return next_column


def _stack_subnets(
    spec: CloudSpec, subnets: list[Frame], start: float, columns: dict[str, float]
) -> float:
    """Put the subnets of one zone over each other, sharing columns; return the next column."""
    members = {subnet.id: [p for p in spec.parts if p.frame == subnet.id] for subnet in subnets}
    width = max([len(parts) for parts in members.values()] + [1])
    for parts in members.values():
        for index, part in enumerate(parts):
            columns[part.id] = start + (width - 1) / 2 + index - (len(parts) - 1) / 2
    return start + width


def _edge_columns(spec: CloudSpec, columns: dict[str, float]) -> None:
    """Centre the parts of the edge over the columns of the parts that sit in subnets."""
    inside = [columns[p.id] for p in spec.parts if _is_in_subnet(spec, p) and p.id in columns]
    spread = inside or list(columns.values())
    centre = (min(spread, default=0) + max(spread, default=0)) / 2
    edge = [p for p in spec.parts if _kind_of(spec, p) is FrameKind.EDGE]
    for index, part in enumerate(edge):
        columns[part.id] = centre + index - (len(edge) - 1) / 2


def _is_in_subnet(spec: CloudSpec, part: Part) -> bool:
    """Tell whether a part sits in a subnet."""
    return _kind_of(spec, part) in SUBNET_KINDS


def _kind_of(spec: CloudSpec, part: Part) -> FrameKind | None:
    """Return the kind of the frame a part sits in, or None for a part outside the cloud."""
    frame = spec.frame_of(part)
    return frame.kind if frame else None


def _pass_rows(spec: CloudSpec, rows: dict[str, float]) -> dict[str, float]:
    """Give a row to every part that has none, from the part it is linked to."""
    rows = dict(rows)
    for _ in range(MAX_PASSES):
        for link in spec.links:
            _pass_row(spec, link.source, link.target, rows)
    return rows


def _pass_row(spec: CloudSpec, source: str, target: str, rows: dict[str, float]) -> None:
    """Set the row of the end of a link that has none from the end that has one."""
    by_id = {part.id: part for part in spec.parts}
    if source not in rows and target in rows:
        rows[source] = rows[target] + _step(spec, by_id[source], by_id[target], is_source=True)
    elif target not in rows and source in rows:
        rows[target] = rows[source] + _step(spec, by_id[target], by_id[source], is_source=False)


def _step(spec: CloudSpec, part: Part, other: Part, is_source: bool) -> int:
    """Return how many rows a part sits from the part it is linked to."""
    if part.frame is None:
        return ABOVE if is_source else BELOW
    same_site = part.frame == other.frame
    if _kind_of(spec, part) is FrameKind.ONPREM and same_site:
        return ABOVE if is_source else BELOW
    return SAME_ROW


def _outside_columns(
    spec: CloudSpec, cell_maps: tuple[dict[str, float], dict[str, float]], rules: CloudRules
) -> None:
    """Give columns to the parts outside the network: users over their target, sites to the left."""
    rows, columns = cell_maps
    left = min(columns.values(), default=0) - rules.site_offset
    for part in spec.parts:
        if part.id in columns:
            continue
        rows.setdefault(part.id, 0)
        columns[part.id] = (
            left if _kind_of(spec, part) is FrameKind.ONPREM else _over(spec, part, columns)
        )


def _over(spec: CloudSpec, part: Part, columns: dict[str, float]) -> float:
    """Return the column of a user, centred with its sisters over the part they all reach."""
    partners = [
        link.target if link.source == part.id else link.source
        for link in spec.links
        if part.id in (link.source, link.target)
    ]
    anchor = next((columns[p] for p in partners if p in columns), 0.0)
    sisters = [
        p
        for p in spec.parts
        if p.frame is None and p.id not in columns and _first_partner(spec, p, columns) == anchor
    ]
    ranked = [part, *[s for s in sisters if s.id != part.id]]
    return anchor + ranked.index(part) - (len(ranked) - 1) / 2


def _first_partner(spec: CloudSpec, part: Part, columns: dict[str, float]) -> float | None:
    """Return the column of the first part that a part is linked to, when it has one."""
    for link in spec.links:
        other = link.target if link.source == part.id else link.source
        if part.id in (link.source, link.target) and other in columns:
            return columns[other]
    return None


def _apart(spec: CloudSpec, cells: dict[str, Cell]) -> dict[str, Cell]:
    """Move a part that shares its cell with another one down a row, until each has its own."""
    taken: set[Cell] = set()
    moved: dict[str, Cell] = {}
    for part in spec.parts:
        column, row = cells[part.id]
        while (column, row) in taken:
            row += 1
        taken.add((column, row))
        moved[part.id] = (column, row)
    return moved
