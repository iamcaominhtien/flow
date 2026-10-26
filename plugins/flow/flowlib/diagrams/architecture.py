"""The architecture diagram: components in layers, zones around them, lines between them.

See ``architecture_spec`` for the spec format. Every top-level zone is a layer and a row of the
grid; a third party sits in the row of the layer that calls it. Each zone becomes a frame drawn
around what it holds. A line may start or end on a frame. Plain parts are 196 x 68 and layers
260 px apart; illustrated cards are 232 x 96 and 240 px apart (design 06 section 7).
"""

from dataclasses import dataclass

from ..check import Rect, node_rect
from ..model import Frame, FrameVariant, Node, Role, Scene, Shape
from ..theme import ArchitectureRules, Theme, load_theme
from .architecture_spec import ArchitectureSpec, Component, Link, LinkKind, Zone, read_spec
from .grid_frames import frame_node, grown, pill_rect, shift_into_canvas, union
from .grid_routes import Extras, GridSpacing, route_flows
from .grid_scene import Heading, Line, build_edges, finish_scene

LINE_ROLES: dict[LinkKind, Role] = {
    LinkKind.CALL: Role.NEXT,
    LinkKind.MAIN: Role.MAIN,
    LinkKind.EVENT: Role.DATA,
    LinkKind.COPY: Role.BACK,
}
Cell = tuple[float, float]


@dataclass(frozen=True)
class Style:
    """The sizes of one style of the diagram: plain parts or illustrated cards."""

    part_size: tuple[float, float]
    layer_pitch: float
    column_pitch: float
    shape: Shape


def layout_raw(raw: object) -> Scene:
    """Lay out an architecture diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on an ``architecture`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(read_spec(raw))


def layout(spec: ArchitectureSpec) -> Scene:
    """Place the components of a checked spec, frame them in their zones and route the links.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    style = _style(spec, theme.architecture)
    nodes = _place(spec, style, theme)
    frames = _frames(spec, nodes, theme.architecture)
    nodes, frames = shift_into_canvas(nodes, frames, theme)
    spacing = GridSpacing(
        style.layer_pitch,
        style.column_pitch,
        theme.architecture.pair_gap,
        theme.architecture.channel_step,
        theme.architecture.channel_clearance,
    )
    lines = tuple(_line(link) for link in spec.links)
    extras = Extras(
        frames={f.id: frame_node(f) for f in frames if _is_end(f, spec)},
        blocked=[pill_rect(frame, theme) for frame in frames if frame.label],
    )
    routes = route_flows(nodes, lines, spacing, extras)
    heading = Heading(spec.title, spec.description)
    return finish_scene(
        heading, (tuple(frames), tuple(nodes.values()), build_edges(lines, routes, set(nodes)))
    )


def _style(spec: ArchitectureSpec, rules: ArchitectureRules) -> Style:
    """Return the sizes of the style the spec asks for."""
    if spec.illustrated:
        return Style(
            rules.card_size, rules.card_layer_pitch, rules.card_column_pitch, Shape.WIDE_CARD
        )
    return Style(rules.part_size, rules.layer_pitch, rules.column_pitch, Shape.PROCESS)


def _is_end(frame: Frame, spec: ArchitectureSpec) -> bool:
    """Tell whether a line starts or ends on a frame."""
    return any(frame.id in (link.source, link.target) for link in spec.links)


def _line(link: Link) -> Line:
    """Build the line of a link: blue for the main path, violet for events, slate for a copy."""
    return Line(link.source, link.target, link.label, LINE_ROLES[link.kind])


def _layers(spec: ArchitectureSpec) -> list[str | None]:
    """Return the layers top to bottom: the open row first when a component has no zone."""
    layers: list[str | None] = [
        zone.id for zone in spec.zones if zone.parent is None and zone.beside is None
    ]
    if any(component.zone is None for component in spec.components):
        layers.insert(0, None)
    return layers


def _row_of(spec: ArchitectureSpec, component: Component) -> str | None:
    """Return the layer a component is in; a third party is in the layer it sits beside."""
    top = spec.top_zone(component.zone)
    if top is None:
        return None
    return top.beside or top.id


def _cells(spec: ArchitectureSpec) -> dict[str, Cell]:
    """Return the cell of every component: its layer is the row, its order the column."""
    layers = _layers(spec)
    rows = {layer: [c for c in spec.components if _row_of(spec, c) == layer] for layer in layers}
    widest = max(len(members) for members in rows.values())
    cells: dict[str, Cell] = {}
    for row, layer in enumerate(layers):
        members = _in_order(spec, rows[layer])
        start = (widest - len(members)) / 2
        cells.update({c.id: (start + column, row) for column, c in enumerate(members)})
    cells.update({c.id: (c.at[1], c.at[0]) for c in spec.components if c.at is not None})
    return cells


def _in_order(spec: ArchitectureSpec, members: list[Component]) -> list[Component]:
    """Order a row: the layer's own components first, then each third party beside it."""

    def is_beside(component: Component) -> int:
        top = spec.top_zone(component.zone)
        return 1 if top is not None and top.beside else 0

    return sorted(members, key=is_beside)


def _place(spec: ArchitectureSpec, style: Style, theme: Theme) -> dict[str, Node]:
    """Build the node of every component at its pixel position."""
    cells = _cells(spec)
    return {c.id: _node(c, cells[c.id], style, theme) for c in spec.components}


def _node(component: Component, cell: Cell, style: Style, theme: Theme) -> Node:
    """Build the node of a component: a part or a card centred on its cell."""
    width, height = style.part_size
    return Node(
        id=component.id,
        shape=style.shape,
        x=cell[0] * style.column_pitch - width / 2,
        y=cell[1] * style.layer_pitch - height / 2,
        width=width,
        height=height,
        text=(component.label,),
        icon=component.icon,
        tone=component.tone,
        number=None,
        font_size=theme.type_scale.node.size,
        detail=(component.detail,) if component.detail else (),
    )


def _depth(spec: ArchitectureSpec, zone: Zone) -> int:
    """Return how many zones are around a zone."""
    by_id = {z.id: z for z in spec.zones}
    depth, current = 0, zone
    while current.parent in by_id:
        current = by_id[current.parent]
        depth += 1
    return depth


def _frames(
    spec: ArchitectureSpec, nodes: dict[str, Node], rules: ArchitectureRules
) -> list[Frame]:
    """Return the frames, outer ones first, each as large as what it holds plus 30 px."""
    rects: dict[str, Rect] = {}
    for zone in sorted(spec.zones, key=lambda z: -_depth(spec, z)):
        members = [
            grown(node_rect(nodes[c.id]), rules.frame_gap)
            for c in spec.components
            if c.zone == zone.id
        ]
        members += [grown(rects[z.id], rules.frame_gap) for z in spec.zones if z.parent == zone.id]
        rects[zone.id] = union(members)
    outer_first = sorted(spec.zones, key=lambda z: _depth(spec, z))
    return [_frame(zone, rects[zone.id]) for zone in outer_first]


def _frame(zone: Zone, rect: Rect) -> Frame:
    """Build the frame of a zone: dashed, tinted, with a dark pill."""
    return Frame(
        id=zone.id,
        x=rect.left,
        y=rect.top,
        width=rect.right - rect.left,
        height=rect.bottom - rect.top,
        label=zone.label,
        tone=zone.tone,
        variant=FrameVariant.LAYER,
    )
