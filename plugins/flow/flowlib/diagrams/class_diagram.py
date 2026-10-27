"""The UML class diagram: boxes with name, attributes and operations on a grid.

See ``class_spec`` for the spec format. The boxes are placed on a grid (``class_grid``), the
relations are routed with at most two bends (``grid_routes``), and the numbers at the ends of a
relation are drawn next to the boxes.
"""

import math
from dataclasses import replace

from ..model import Edge, EdgeLabel, LabelKind, Node, Point, Role, Row, Scene, Shape, Tone
from ..sizing import fit_table
from ..theme import Theme, load_theme
from .class_grid import Cell, assign_cells
from .class_spec import (
    LINE_ENDS,
    ClassBox,
    ClassKind,
    ClassSpec,
    Relation,
    read_spec,
)
from .grid_routes import Extras, GridSpacing, route_flows
from .grid_scene import Heading, Line, build_edges, finish_scene

ROW_GAP_PX = 130  # least free space between two rows of boxes: room for a line and its label
COUNT_ALONG_PX = 22.0  # a number sits this far from the box along its line
COUNT_ACROSS_PX = 12.0  # and this far to the side of it
SELF_LOOP_PX = 48  # how far a relation of a class to itself sticks out of its right side
INTERFACE_TONE = Tone.GRAY


def layout_raw(raw: object) -> Scene:
    """Lay out a class diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``class`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(read_spec(raw))


def layout(spec: ClassSpec) -> Scene:
    """Place the classes of a checked spec, route and mark its relations.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    rules = theme.uml
    nodes = _place(spec, assign_cells(spec), theme)
    straight = [r for r in spec.relations if r.source != r.target]
    spacing = GridSpacing(
        rules.class_row_pitch,
        rules.class_column_pitch,
        rules.pair_gap,
        rules.channel_step,
        rules.channel_clearance,
    )
    routes = route_flows(nodes, tuple(_line(r) for r in straight), spacing, Extras())
    lines = tuple(_line(relation) for relation in straight)
    edges = [
        _marked(edge, relation)
        for edge, relation in zip(build_edges(lines, routes, set(nodes)), straight, strict=True)
    ]
    loops = [
        _self_loop(relation, nodes[relation.source], len(straight) + index + 1)
        for index, relation in enumerate(r for r in spec.relations if r.source == r.target)
    ]
    return finish_scene(
        Heading(spec.title, spec.description),
        ((), tuple(nodes.values()), (*edges, *loops)),
    )


def _line(relation: Relation) -> Line:
    """Build the plain line of a relation: ink, with the name of the relation as its label."""
    return Line(relation.source, relation.target, relation.label, Role.NEXT)


def _marked(edge: Edge, relation: Relation) -> Edge:
    """Give an edge the ends of its relation style and the numbers at its two ends."""
    ends = LINE_ENDS[relation.style]
    return replace(
        edge,
        head=ends.head,
        tail=ends.tail,
        dashed=ends.is_dashed,
        extras=_counts(edge.points, relation),
    )


def _counts(points: tuple[Point, ...], relation: Relation) -> tuple[EdgeLabel, ...]:
    """Build the labels with the numbers at the two ends of a line, such as ``1`` and ``0..*``."""
    found = []
    for text, near, toward in (
        (relation.source_count, points[0], points[1]),
        (relation.target_count, points[-1], points[-2]),
    ):
        if text:
            found.append(EdgeLabel(text, _beside(near, toward), LabelKind.TEXT))
    return tuple(found)


def _beside(near: Point, toward: Point) -> Point:
    """Return a point just along a line from its end and a little to the side."""
    length = max(math.dist(near, toward), 1.0)
    along = ((toward[0] - near[0]) / length, (toward[1] - near[1]) / length)
    return (
        near[0] + along[0] * COUNT_ALONG_PX - along[1] * COUNT_ACROSS_PX,
        near[1] + along[1] * COUNT_ALONG_PX + along[0] * COUNT_ACROSS_PX,
    )


def _self_loop(relation: Relation, node: Node, number: int) -> Edge:
    """Draw a relation of a class to itself as a loop at the right side of its box."""
    right = node.x + node.width
    first = node.y + node.height / 3
    second = node.y + 2 * node.height / 3
    out = right + SELF_LOOP_PX
    points = ((right, first), (out, first), (out, second), (right, second))
    ends = LINE_ENDS[relation.style]
    label = EdgeLabel(relation.label, (out, (first + second) / 2), LabelKind.PLAIN)
    return Edge(
        id=f"e{number}",
        role=Role.NEXT,
        points=points,
        label=label if relation.label else None,
        source=relation.source,
        target=relation.target,
        head=ends.head,
        tail=ends.tail,
        dashed=ends.is_dashed,
        extras=_counts(points, relation),
    )


def _place(spec: ClassSpec, cells: dict[str, Cell], theme: Theme) -> dict[str, Node]:
    """Build the node of every class at its pixel position.

    A row starts below the tallest box of the row above, with room for lines between.
    """
    rules, margin = theme.uml, theme.layout.margin
    boxes = {box.id: _node(box, theme) for box in spec.classes}
    row_numbers = sorted({cell[0] for cell in cells.values()})
    tops: dict[float, float] = {}
    top = margin + theme.layout.title_block_height
    for number in row_numbers:
        tops[number] = top
        tallest = max(boxes[name].height for name, cell in cells.items() if cell[0] == number)
        top += max(tallest + ROW_GAP_PX, rules.class_row_pitch)
    left = min(cell[1] for cell in cells.values())
    return {
        name: replace(
            node,
            x=margin + (cells[name][1] - left) * rules.class_column_pitch,
            y=tops[cells[name][0]],
        )
        for name, node in boxes.items()
    }


def _node(box: ClassBox, theme: Theme) -> Node:
    """Build the node of a class: a table with a header and its non-empty compartments."""
    rules = theme.uml
    sections = tuple(
        tuple(Row(member, is_mono=True) for member in compartment)
        for compartment in (box.attributes, box.operations)
        if compartment
    )
    fitted = fit_table(box.name, sections, False, theme.layout)
    stereotype_room = theme.layout.table_stereotype_height if box.stereotype else 0
    return Node(
        id=box.id,
        shape=Shape.TABLE,
        x=0,
        y=0,
        width=max(rules.class_width, fitted.width),
        height=fitted.height + stereotype_room,
        text=(box.name,),
        icon=None,
        tone=box.tone or (INTERFACE_TONE if box.kind is ClassKind.INTERFACE else Tone.BLUE),
        number=None,
        font_size=theme.type_scale.node.size,
        sections=sections,
        stereotype=box.stereotype,
        is_italic=box.kind is ClassKind.ABSTRACT,
        is_centered=True,
    )
