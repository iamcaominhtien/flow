"""The data flow diagram in the Gane-Sarson style: outside parties, processes and stores.

See ``dfd_spec`` for the spec format. The layout puts every box on a grid (``dfd_grid``),
routes the flows (``grid_routes``) and, for a level 2 diagram, draws a dashed frame around the
process that was opened.
"""

from itertools import pairwise
from pathlib import Path

from ..canvas import fit_canvas
from ..labels import place_labels
from ..model import (
    Edge,
    EdgeLabel,
    Frame,
    FrameVariant,
    Head,
    LabelKind,
    Node,
    Point,
    Role,
    Scene,
    Shape,
)
from ..theme import DfdRules, Theme, load_theme
from .dfd_grid import Cell, assign_cells
from .dfd_spec import CONTEXT_LEVEL, DfdSpec, Element, Flow, Kind, read_spec
from .grid_routes import route_flows

NAME_FONT_SIZE_PX = 13
FRAME_ID = "opened"
SHAPES: dict[Kind, Shape] = {
    Kind.EXTERNAL: Shape.ENTITY,
    Kind.PROCESS: Shape.DFD_PROCESS,
    Kind.STORE: Shape.DFD_STORE,
}


def layout_raw(raw: object, source_dir: Path | None = None) -> Scene:
    """Lay out a data flow diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``dfd`` spec.
        source_dir: The folder of the spec file, where ``opens`` looks for the level above.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid, or breaks a rule of data flow diagrams.
    """
    return layout(read_spec(raw, source_dir))


def layout(spec: DfdSpec) -> Scene:
    """Place the boxes of a checked spec, route its flows and frame the opened process.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    nodes = _place(spec, theme)
    routes = route_flows(nodes, spec.flows, theme.dfd)
    edges = tuple(
        _edge(index, flow, route) for index, (flow, route) in enumerate(_pairs(spec, routes))
    )
    frames = _frames(spec, nodes, theme.dfd)
    scene = Scene(
        width=0,
        height=0,
        title=spec.title,
        description=spec.description,
        frames=frames,
        nodes=tuple(nodes.values()),
        edges=edges,
    )
    return fit_canvas(place_labels(scene))


def _pairs(spec: DfdSpec, routes: list[list[Point]]) -> list[tuple[Flow, list[Point]]]:
    """Pair each flow with its route."""
    return list(zip(spec.flows, routes, strict=True))


def _size(element: Element, spec: DfdSpec, rules: DfdRules) -> tuple[float, float]:
    """Return the size of an element: plain or card, and larger for the one process of level 0."""
    if spec.illustrated:
        sizes = {
            Kind.EXTERNAL: rules.card_entity_size,
            Kind.PROCESS: rules.card_process_size,
            Kind.STORE: rules.card_store_size,
        }
        return sizes[element.kind]
    if element.kind is Kind.PROCESS and spec.level == CONTEXT_LEVEL:
        return rules.context_process_size
    plain = {
        Kind.EXTERNAL: rules.entity_size,
        Kind.PROCESS: rules.process_size,
        Kind.STORE: rules.store_size,
    }
    return plain[element.kind]


def _place(spec: DfdSpec, theme: Theme) -> dict[str, Node]:
    """Build the node of every element at its pixel position."""
    rules = theme.dfd
    cells = assign_cells(spec)
    pitch_x = rules.card_column_pitch if spec.illustrated else rules.column_pitch
    pitch_y = rules.card_row_pitch if spec.illustrated else rules.row_pitch
    boxes = {
        e.id: _box(cells[e.id], (pitch_x, pitch_y), _size(e, spec, rules)) for e in spec.elements
    }
    shift_x = theme.layout.margin - min(x for x, _, _, _ in boxes.values())
    shift_y = (
        theme.layout.title_block_height
        + theme.layout.margin
        - min(y for _, y, _, _ in boxes.values())
    )
    return {
        element.id: _node(element, boxes[element.id], (shift_x, shift_y), spec.illustrated)
        for element in spec.elements
    }


def _box(
    cell: Cell, pitch: tuple[float, float], size: tuple[float, float]
) -> tuple[float, float, float, float]:
    """Return the left, top, width and height of an element whose cell centre is on the grid."""
    width, height = size
    return (cell[0] * pitch[0] - width / 2, cell[1] * pitch[1] - height / 2, width, height)


def _node(
    element: Element,
    box: tuple[float, float, float, float],
    shift: tuple[float, float],
    is_card: bool,
) -> Node:
    """Build the node of an element."""
    x, y, width, height = box
    return Node(
        id=element.id,
        shape=SHAPES[element.kind],
        x=x + shift[0],
        y=y + shift[1],
        width=width,
        height=height,
        text=(element.label,),
        icon=element.icon,
        tone=element.tone,
        number=element.number,
        font_size=NAME_FONT_SIZE_PX,
        detail=(element.detail,) if element.detail else (),
        card=is_card,
        dashed=element.is_outside and element.kind is Kind.STORE,
    )


def _edge(index: int, flow: Flow, route: list[Point]) -> Edge:
    """Build the line of a flow: blue and thick for the main journey, violet for a status."""
    role = Role.MAIN if flow.is_main else Role.DATA if flow.is_status else Role.NEXT
    return Edge(
        id=f"e{index + 1}",
        role=role,
        points=tuple(route),
        label=EdgeLabel(flow.label, _middle_of_longest(route), LabelKind.PLAIN),
        source=flow.source,
        target=flow.target,
        head=Head.FILLED,
    )


def _middle_of_longest(route: list[Point]) -> Point:
    """Return the middle of the longest segment of a route, where its label goes."""
    start, end = max(pairwise(route), key=lambda segment: _length(*segment))
    return ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)


def _length(start: Point, end: Point) -> float:
    """Return the length of a horizontal or vertical segment."""
    return abs(end[0] - start[0]) + abs(end[1] - start[1])


def _frames(spec: DfdSpec, nodes: dict[str, Node], rules: DfdRules) -> tuple[Frame, ...]:
    """Return the dashed frame around the parts of an opened process, or nothing."""
    if spec.opened is None:
        return ()
    inner = [nodes[e.id] for e in spec.elements if not e.is_outside]
    left = min(node.x for node in inner) - rules.frame_pad_x
    top = min(node.y for node in inner) - rules.frame_pad_top
    right = max(node.x + node.width for node in inner) + rules.frame_pad_x
    bottom = max(node.y + node.height for node in inner) + rules.frame_pad_bottom
    frame = Frame(
        id=FRAME_ID,
        x=left,
        y=top,
        width=right - left,
        height=bottom - top,
        label=f"{spec.opened.number} {spec.opened.label}",
        tone=spec.opened.tone,
        variant=FrameVariant.OPENED,
    )
    return (frame,)
