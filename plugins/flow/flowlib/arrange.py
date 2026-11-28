"""Arrangements for a hand-laid diagram: a chain that wraps like text, a list, a fitted zone.

The author kit (``author.Canvas``) leaves every position to the author. For a large diagram that
means a great deal of arithmetic, and three shapes of content keep coming back: a sequence of
steps, a set of names that are not steps, and a group drawn around what it holds. These functions
place them by one rule each, so a script says what the content is and the reading order stays
the same everywhere:

- ``chain``: steps in order, left to right; a row that is full continues at the left of the next
  row, as text does. A row never runs right to left.
- ``listing``: names in a set (loaders, filters, flags) as one table node with a title, split
  into columns when long, instead of one box per name.
- ``fit_zone``: a zone drawn around the nodes it holds, with room for its name.
- ``block``: a part with branches (decisions, loops, joins) laid out by Flow's own flowchart
  engine, so the author arranges blocks and the engine arranges what is inside each.
- ``connect``: a line between parts, routed around every node and off the lines already drawn.
"""

from dataclasses import dataclass, replace
from itertools import pairwise
from typing import Any

from . import diagrams
from .author import Box, Canvas, NodeOptions, Route, Side
from .model import Edge, EdgeLabel, Node, Point, Role, Row, Shape, Tone
from .pathfind import SearchSpace, find_route
from .sizing import estimate_text_width
from .theme import load_theme

CHAIN_GAP_PX = 70  # between two steps of a row, room for an arrowhead and a short label
ROW_GAP_PX = 70  # between two rows of a chain, room for the line that wraps
CELL_WIDTH_PX = 200  # the width of a step in a chain, so the columns line up
ZONE_PAD_PX = 24  # between a zone's border and what it holds
ZONE_HEADER_PX = 40  # above the content of a zone, for its name pill
LIST_GAP_PX = 24  # between two columns of a list
MIN_ROWS_PER_COLUMN = 4  # a list shorter than this stays in one column
GRID_PX = 10  # positions snap to this grid
ROUTE_MARGIN_PX = 12.0  # how far a connecting line keeps from every box
STUB_PX = 16.0  # a connecting line leaves a box straight for this far before it turns
SIDE_COST_PX = 400.0  # a route that does not use the facing sides costs this much more
PILL_ROOM_PX = 60  # beside the name pill of a zone: its own padding and the zone's inset


@dataclass(frozen=True)
class Step:
    """One step of a chain: its id, its words and how it looks."""

    name: str
    text: str
    detail: str | None = None
    shape: Shape = Shape.PROCESS
    tone: Tone | None = None
    icon: str | None = None
    number: str | None = None


@dataclass(frozen=True)
class Bounds:
    """A rectangle on the page: left, top, right and bottom, in pixels."""

    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        """The width of the rectangle."""
        return self.right - self.left

    @property
    def height(self) -> float:
        """The height of the rectangle."""
        return self.bottom - self.top


@dataclass(frozen=True)
class Listing:
    """A set of names to draw as a list: its id, its title and its entries."""

    name: str
    title: str
    entries: tuple[str | tuple[str, str], ...]
    is_ordered: bool = False  # number the entries: a sequence with no branch, read top down


@dataclass(frozen=True)
class ChainSpace:
    """Where a chain goes and how wide its rows may be."""

    left: float
    top: float
    width: float
    cell_width: float = CELL_WIDTH_PX
    role: Role = Role.NEXT  # the role of the lines between the steps; ``Role.MAIN`` for the path


def chain(canvas: Canvas, steps: list[Step], space: ChainSpace) -> Bounds:
    """Place steps in reading order, left to right, wrapping to the left of the next row.

    Every step has the same width, so the columns line up; a row is as tall as its tallest step.
    Each step is joined to the next: across within a row, and at a wrap from the bottom of the
    last step of a row, along the gap between the rows, into the top of the first step of the
    next. Join the chain to the rest of the diagram with ``canvas.edge`` on the first and last
    ids.

    Args:
        canvas: The diagram.
        steps: The steps, in order; at least one.
        space: The left and top of the first row, the width the rows may use, the width of a
            step and the role of the joining lines.

    Returns:
        The rectangle the chain covers.

    Raises:
        ValueError: If there is no step.
    """
    if not steps:
        raise ValueError("a chain needs at least one step")
    per_row = max(1, int((space.width + CHAIN_GAP_PX) // (space.cell_width + CHAIN_GAP_PX)))
    rows = [steps[i : i + per_row] for i in range(0, len(steps), per_row)]
    top, right = space.top, space.left
    for row in rows:
        boxes = [_place_step(canvas, step, space.cell_width) for step in row]
        height = max(box.node.height for box in boxes)
        for column, box in enumerate(boxes):
            left = space.left + column * (space.cell_width + CHAIN_GAP_PX)
            _move(canvas, box.node.id, (left + space.cell_width / 2, top + height / 2))
        right = max(right, space.left + len(row) * (space.cell_width + CHAIN_GAP_PX) - CHAIN_GAP_PX)
        top += height + ROW_GAP_PX
    _join_chain(canvas, rows, space.role)
    return Bounds(space.left, space.top, right, top - ROW_GAP_PX)


def listing(canvas: Canvas, items: "Listing", corner: tuple[float, float]) -> list[Box]:
    """Draw a set of names as one titled table, in columns side by side when it is long.

    Use it for members of a set that are not steps of a flow: loaders that run at once, the
    terms of a sum, flags, side effects. One table holds a name per row (and a short note on the
    right when an entry is a pair). A list of more than about twelve entries is split into
    columns of equal length, each a table; the first carries the title and the others
    ``title (2/3)`` and so on, so a reader knows they belong together.

    Args:
        canvas: The diagram.
        items: The id of the first table (the others get ``-2``, ``-3`` and so on), the name of
            the set (with its count if it helps), and the names or (name, note) pairs in order.
        corner: The left and top of the first table.

    Returns:
        The placed tables, left to right; join lines to the first, or to the zone around them.
    """
    name, title, entries = items.name, items.title, items.entries
    columns = _list_columns(len(entries))
    per_column = -(-len(entries) // columns)
    chunks = [entries[i : i + per_column] for i in range(0, len(entries), per_column)]
    boxes: list[Box] = []
    left = corner[0]
    for index, chunk in enumerate(chunks):
        heading = title if index == 0 else f"{title} ({index + 1}/{len(chunks)})"
        node_id = name if index == 0 else f"{name}-{index + 1}"
        first = index * per_column + 1
        rows = tuple(
            _row(entry, first + offset if items.is_ordered else None)
            for offset, entry in enumerate(chunk)
        )
        box = canvas.node(node_id, Shape.TABLE, heading, NodeOptions((0, 0), rows=rows))
        box = _move(canvas, node_id, (left + box.node.width / 2, corner[1] + box.node.height / 2))
        boxes.append(box)
        left += box.node.width + LIST_GAP_PX
    _align_heights(canvas, boxes)
    return [canvas.boxes[box.node.id] for box in boxes]


def fit_zone(canvas: Canvas, name: str, label: tuple[str, Tone], members: list[str]) -> Bounds:
    """Draw a zone tightly around the nodes it holds, with room above them for its name.

    Args:
        canvas: The diagram.
        name: The id of the zone.
        label: The name shown on the pill, and the zone's tone.
        members: The ids of the nodes inside it; at least one.

    Returns:
        The rectangle of the zone, to place the next thing below or beside it.
    """
    inner = cover(canvas, members)
    theme = load_theme()
    pill = estimate_text_width(label[0], theme.layout, theme.type_scale.pill.size) + PILL_ROOM_PX
    right = max(inner.right + ZONE_PAD_PX, inner.left - ZONE_PAD_PX + pill)
    bounds = Bounds(
        inner.left - ZONE_PAD_PX, inner.top - ZONE_HEADER_PX, right, inner.bottom + ZONE_PAD_PX
    )
    canvas.zone(name, label[0], label[1], (bounds.left, bounds.top, bounds.width, bounds.height))
    return bounds


def block(
    canvas: Canvas, content: dict[str, Any], corner: Point, direction: str = "down"
) -> Bounds:
    """Lay out a part with branches using Flow's flowchart engine, and add it to the canvas.

    ``content`` holds ``nodes`` and ``edges`` in the flowchart spec format (``id``, ``kind``,
    ``text``, ``detail``, ``tone``, ``icon``; ``from``, ``to``, ``role``, ``label``), as the
    flowchart skill describes. The engine keeps the main continuation of every step in one
    column (``"role": "main"`` on the edges of the path that matters, including a ``no`` exit
    the flow continues through), puts short branches beside it, routes the lines and places
    their labels. Lines that leave the part are added afterwards with ``connect``.

    Args:
        canvas: The diagram; the ids of the part must be new to it.
        content: ``nodes`` and ``edges`` of the part.
        corner: Where the top left of the part goes.
        direction: ``down`` (the flow runs top to bottom) or ``right``; choose the one that
            makes the part's exit face the next part.

    Returns:
        The rectangle the part covers, to draw a zone around it or place the next part.

    Raises:
        ValueError: If an id of the part is already on the canvas.
    """
    spec = {"type": "flowchart", "title": "part", "direction": direction, **content}
    laid = diagrams.layout(spec)
    clash = [node.id for node in laid.nodes if node.id in canvas.boxes]
    if clash:
        raise ValueError(f"ids already on the canvas: {', '.join(clash)}")
    left = min(node.x for node in laid.nodes)
    top = min(node.y for node in laid.nodes)
    shift = (_snap(corner[0]) - left, _snap(corner[1]) - top)
    for node in laid.nodes:
        canvas.boxes[node.id] = Box(_shift_node(node, shift))
    for edge in laid.edges:
        canvas.edges.append(_shift_edge(edge, shift, f"e{len(canvas.edges) + 1}"))
    return cover(canvas, [node.id for node in laid.nodes])


def connect(canvas: Canvas, source: str, target: str, route: Route | None = None) -> Edge:
    """Join two placed nodes, usually in different parts, by a line that finds its own way.

    The line leaves and enters on the sides that face each other when it can, keeps clear of
    every node, and avoids running along lines already drawn. Use it for every line between
    parts instead of giving corner points by hand. Draw the parts first.

    Args:
        canvas: The diagram.
        source: The id of the node the line leaves.
        target: The id of the node it enters.
        route: The role, label and style of the line; its sides and points are chosen here.

    Returns:
        The line that was added.
    """
    route = route or Route()
    first, second = canvas.boxes[source], canvas.boxes[target]
    space = SearchSpace(_obstacles(canvas), _drawn_segments(canvas))
    best: tuple[float, str, str, list[Point]] | None = None
    for leave in Side:
        for arrive in Side:
            found = _search(space, (first, leave), (second, arrive))
            if found is None:
                continue
            cost = found[0] + _side_cost(first, second, leave, arrive)
            if best is None or cost < best[0]:
                best = (cost, leave, arrive, found[1])
    if best is None:
        return canvas.edge(source, target, route)
    _, leave, arrive, points = best
    chosen = replace(route, leave=leave, arrive=arrive, via=tuple(points))
    return canvas.edge(source, target, chosen)


def cover(canvas: Canvas, members: list[str]) -> Bounds:
    """Return the rectangle that covers some placed nodes.

    Args:
        canvas: The diagram.
        members: The ids of the nodes; at least one.

    Returns:
        The smallest rectangle around them.

    Raises:
        ValueError: If no id is given.
    """
    if not members:
        raise ValueError("give at least one node")
    nodes = [canvas.boxes[member].node for member in members]
    return Bounds(
        min(node.x for node in nodes),
        min(node.y for node in nodes),
        max(node.x + node.width for node in nodes),
        max(node.y + node.height for node in nodes),
    )


def _place_step(canvas: Canvas, step: Step, width: float) -> Box:
    """Add a step at the origin with the chain's width; it is moved into its row afterwards."""
    options = NodeOptions(
        (0, 0), icon=step.icon, tone=step.tone, number=step.number, detail=step.detail, width=width
    )
    return canvas.node(step.name, step.shape, step.text, options)


def _move(canvas: Canvas, name: str, centre: tuple[float, float]) -> Box:
    """Move a placed node so its middle is at a grid point; no line may attach to it yet."""
    if any(name in (edge.source, edge.target) for edge in canvas.edges):
        raise ValueError(f"'{name}' already has a line; place parts before joining them")
    node = canvas.boxes[name].node
    x = _snap(centre[0] - node.width / 2)
    y = _snap(centre[1] - node.height / 2)
    moved = Box(replace(node, x=x, y=y))
    canvas.boxes[name] = moved
    return moved


def _join_chain(canvas: Canvas, rows: list[list[Step]], role: Role) -> None:
    """Join each step of a chain to the next, in reading order: across a row, down at a wrap."""
    for index, row in enumerate(rows):
        for first, second in pairwise(row):
            canvas.edge(first.name, second.name, Route(Side.RIGHT, Side.LEFT, role=role))
        if index + 1 < len(rows):
            _wrap(canvas, row, rows[index + 1][0], role)


def _wrap(canvas: Canvas, row: list[Step], first: Step, role: Role) -> None:
    """Join the last step of a row to the first of the next, along the gap between the rows."""
    last, start = canvas.boxes[row[-1].name], canvas.boxes[first.name]
    bottom = cover(canvas, [step.name for step in row]).bottom
    gap = bottom + (start.node.y - bottom) / 2
    via = ((last.centre[0], gap), (start.centre[0], gap))
    canvas.edge(row[-1].name, first.name, Route(Side.BOTTOM, Side.TOP, via=via, role=role))


def _list_columns(count: int) -> int:
    """Return how many columns a list of this many entries takes: about twelve rows each."""
    if count < MIN_ROWS_PER_COLUMN * 3:
        return 1
    return min(4, -(-count // 12))


def _row(entry: str | tuple[str, str], number: int | None) -> Row:
    """Turn an entry of a list into a table row: a name, a note when it is a pair, its number."""
    flags = (str(number),) if number is not None else ()
    if isinstance(entry, tuple):
        return Row(entry[0], entry[1], flags)
    return Row(entry, flags=flags)


def _align_heights(canvas: Canvas, boxes: list[Box]) -> None:
    """Make the columns of a list the same height, so they read as one block."""
    tallest = max(box.node.height for box in boxes)
    for box in boxes:
        canvas.boxes[box.node.id] = Box(replace(box.node, height=tallest))


def _shift_node(node: Node, shift: Point) -> Node:
    """Return a node moved by an offset."""
    return replace(node, x=node.x + shift[0], y=node.y + shift[1])


def _shift_point(point: Point, shift: Point) -> Point:
    """Return a point moved by an offset."""
    return point[0] + shift[0], point[1] + shift[1]


def _shift_label(label: EdgeLabel, shift: Point) -> EdgeLabel:
    """Return a line's chip moved by an offset."""
    return replace(label, at=_shift_point(label.at, shift))


def _shift_edge(edge: Edge, shift: Point, name: str) -> Edge:
    """Return a line moved by an offset, under a new id."""
    return replace(
        edge,
        id=name,
        points=tuple(_shift_point(point, shift) for point in edge.points),
        label=_shift_label(edge.label, shift) if edge.label else None,
        extras=tuple(_shift_label(extra, shift) for extra in edge.extras),
    )


def _obstacles(canvas: Canvas) -> tuple[tuple[float, float, float, float], ...]:
    """Return every node as a box grown by the routing margin."""
    margin = ROUTE_MARGIN_PX
    return tuple(
        (n.x - margin, n.y - margin, n.x + n.width + margin, n.y + n.height + margin)
        for n in (box.node for box in canvas.boxes.values())
    )


def _drawn_segments(canvas: Canvas) -> tuple[tuple[Point, Point], ...]:
    """Return every straight stretch of the lines already drawn."""
    return tuple(segment for edge in canvas.edges for segment in pairwise(edge.points))


def _search(
    space: SearchSpace, start: tuple[Box, str], end: tuple[Box, str]
) -> tuple[float, list[Point]] | None:
    """Search a route from one side of a box to one side of another, outside both."""
    found = find_route(space, _outside(*start), _outside(*end))
    if found is None:
        return None
    return found.cost, found.points


def _outside(box: Box, side: str) -> Point:
    """Return the point just outside the middle of one side of a box, past the margin."""
    x, y = box.port(side)
    reach = ROUTE_MARGIN_PX + STUB_PX
    step = {Side.TOP: (0, -reach), Side.BOTTOM: (0, reach), Side.LEFT: (-reach, 0)}
    dx, dy = step.get(Side(side), (reach, 0))
    return x + dx, y + dy


def _side_cost(first: Box, second: Box, leave: str, arrive: str) -> float:
    """Return the extra cost of not using the sides that face each other."""
    facing = _facing(first, second), _facing(second, first)
    return SIDE_COST_PX * ((leave != facing[0]) + (arrive != facing[1]))


def _facing(box: Box, other: Box) -> str:
    """Return the side of a box that looks towards another box."""
    delta_x = other.centre[0] - box.centre[0]
    delta_y = other.centre[1] - box.centre[1]
    if abs(delta_x) >= abs(delta_y):
        return Side.RIGHT if delta_x > 0 else Side.LEFT
    return Side.BOTTOM if delta_y > 0 else Side.TOP


def _snap(value: float) -> float:
    """Round a position to the grid."""
    return round(value / GRID_PX) * GRID_PX
