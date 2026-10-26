"""The C4 diagram: people, systems, containers and components on a grid, at three levels.

See ``c4_spec`` for the spec format. The layout puts every box on a grid (``c4_grid``), routes
the relations (``grid_routes``) and, for level 2 and 3, draws a dashed frame around the box
that was opened, with its name on the bottom edge.
"""

from pathlib import Path

from ..model import Frame, FrameVariant, Node, Role, Scene, Shape
from ..theme import C4Rules, load_theme
from .c4_grid import Cell, assign_cells
from .c4_spec import (
    CONTEXT_LEVEL,
    C4Spec,
    Element,
    Kind,
    LineKind,
    Relation,
    read_spec,
)
from .grid_routes import Extras, route_flows
from .grid_scene import Heading, Line, build_edges, finish_scene

FRAME_ID = "opened"
LINE_ROLES: dict[LineKind, Role] = {
    LineKind.CALL: Role.NEXT,
    LineKind.MAIN: Role.MAIN,
    LineKind.EVENT: Role.DATA,
}
SHAPES: dict[Kind, Shape] = {
    Kind.PERSON: Shape.C4_PERSON,
    Kind.SYSTEM: Shape.C4_BOX,
    Kind.EXTERNAL: Shape.C4_BOX,
    Kind.CONTAINER: Shape.C4_BOX,
    Kind.DATABASE: Shape.C4_BOX,
    Kind.COMPONENT: Shape.C4_BOX,
}


def layout_raw(raw: object, source_dir: Path | None = None) -> Scene:
    """Lay out a C4 diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``c4`` spec.
        source_dir: The folder of the spec file, where ``opens`` looks for the level above.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid, or breaks a rule of C4 diagrams.
    """
    return layout(read_spec(raw, source_dir))


def layout(spec: C4Spec) -> Scene:
    """Place the boxes of a checked spec, route its relations and frame the opened box.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    nodes = _place(spec, theme.c4)
    flows = tuple(_line(relation) for relation in spec.relations)
    routes = route_flows(nodes, flows, theme.c4, Extras())
    edges = build_edges(flows, routes, set(nodes))
    frames = _frames(spec, nodes, theme.c4)
    return finish_scene(
        Heading(spec.title, spec.description), (frames, tuple(nodes.values()), edges)
    )


def _line(relation: Relation) -> Line:
    """Build the line of a relation: blue for the main route, violet for events."""
    return Line(relation.source, relation.target, relation.text, LINE_ROLES[relation.kind])


def _size(element: Element, spec: C4Spec, rules: C4Rules) -> tuple[float, float]:
    """Return the size of a box: larger for the one system of level 1."""
    if element.kind is Kind.SYSTEM and spec.level == CONTEXT_LEVEL:
        return rules.system_size
    return rules.box_size


def _place(spec: C4Spec, rules: C4Rules) -> dict[str, Node]:
    """Build the node of every element at its pixel position."""
    layout_rules = load_theme().layout
    cells = assign_cells(spec)
    shift = (
        layout_rules.margin
        + rules.frame_pad
        - min(col for col, _ in cells.values()) * rules.column_pitch,
        layout_rules.title_block_height
        + layout_rules.margin
        - min(row for _, row in cells.values()) * rules.row_pitch,
    )
    return {
        element.id: _node(
            element, _box(cells[element.id], _size(element, spec, rules), (rules, shift))
        )
        for element in spec.elements
    }


def _box(
    cell: Cell, size: tuple[float, float], setting: tuple[C4Rules, tuple[float, float]]
) -> tuple[float, float, float, float]:
    """Return the left, top, width and height of a box whose cell centre is on the grid."""
    rules, shift = setting
    width, height = size
    centre_x = cell[0] * rules.column_pitch + rules.box_size[0] / 2 + shift[0]
    centre_y = cell[1] * rules.row_pitch + rules.box_size[1] / 2 + shift[1]
    return (centre_x - width / 2, centre_y - height / 2, width, height)


def _node(element: Element, box: tuple[float, float, float, float]) -> Node:
    """Build the node of an element: a rounded box, dashed when it is outside our control."""
    rules = load_theme().c4
    x, y, width, height = box
    return Node(
        id=element.id,
        shape=SHAPES[element.kind],
        x=x,
        y=y,
        width=width,
        height=height,
        text=(element.label,),
        icon=element.icon,
        tone=element.tone,
        number=None,
        font_size=rules.name_font_size,
        detail=(element.description,) if element.description else (),
        technology=element.type_line,
        dashed=element.kind is Kind.EXTERNAL,
    )


def _frames(spec: C4Spec, nodes: dict[str, Node], rules: C4Rules) -> tuple[Frame, ...]:
    """Return the dashed frame around the parts of the opened box, or nothing on level 1."""
    if spec.opened is None:
        return ()
    inner = [nodes[e.id] for e in spec.elements if spec.is_inside(e)]
    left = min(node.x for node in inner) - rules.frame_pad
    top = min(node.y for node in inner) - rules.frame_pad
    right = max(node.x + node.width for node in inner) + rules.frame_pad
    bottom = max(node.y + node.height for node in inner) + rules.frame_pad_bottom
    frame = Frame(
        id=FRAME_ID,
        x=left,
        y=top,
        width=right - left,
        height=bottom - top,
        label=spec.opened.label,
        tone=spec.opened.tone,
        variant=FrameVariant.OPENED,
    )
    return (frame,)
