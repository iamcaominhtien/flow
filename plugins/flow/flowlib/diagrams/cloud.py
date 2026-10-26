"""The cloud diagram: parts inside nested frames (region, VPC, zone, subnet), joined by links.

See ``cloud_spec`` for the spec format. The layout puts every part on a grid (``cloud_grid``),
draws each frame around what it holds, routes the links (``grid_routes``) and keeps the lines
away from the pill that names a frame.
"""

from dataclasses import dataclass

from ..check import Rect, node_rect
from ..model import Frame as SceneFrame
from ..model import FrameVariant, Node, Role, Scene, Shape
from ..theme import CloudRules, Theme, load_theme
from .cloud_grid import Cell, assign_cells
from .cloud_spec import SUBNET_KINDS, CloudSpec, Link, LinkKind, Part, read_spec
from .cloud_spec import Frame as SpecFrame
from .grid_frames import grown, pill_rect, shift_into_canvas, union
from .grid_routes import Extras, route_flows
from .grid_scene import Heading, Line, build_edges, finish_scene

LINE_ROLES: dict[LinkKind, Role] = {
    LinkKind.CALL: Role.NEXT,
    LinkKind.MAIN: Role.MAIN,
    LinkKind.EVENT: Role.DATA,
    LinkKind.COPY: Role.DATA,
}


@dataclass(frozen=True)
class Plan:
    """What the frame rectangles are worked out from."""

    spec: CloudSpec
    nodes: dict[str, Node]
    rules: CloudRules


def layout_raw(raw: object) -> Scene:
    """Lay out a cloud diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``cloud`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid, or breaks a rule of cloud diagrams.
    """
    return layout(read_spec(raw))


def layout(spec: CloudSpec) -> Scene:
    """Place the parts of a checked spec, frame them, and route its links.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    rules = theme.cloud
    nodes = _place(spec, theme)
    frames = _frames(Plan(spec, nodes, rules))
    nodes, frames = shift_into_canvas(nodes, frames, theme)
    lines = tuple(_line(link) for link in spec.links)
    blocked = [pill_rect(frame, theme) for frame in frames if frame.label]
    routes = route_flows(nodes, lines, rules, Extras(blocked=blocked))
    heading = Heading(spec.title, spec.description)
    return finish_scene(
        heading, (tuple(frames), tuple(nodes.values()), build_edges(lines, routes, set(nodes)))
    )


def _line(link: Link) -> Line:
    """Build the line of a link: blue for the main route, violet for events and copies."""
    return Line(link.source, link.target, link.label, LINE_ROLES[link.kind])


def _place(spec: CloudSpec, theme: Theme) -> dict[str, Node]:
    """Build the node of every part at its pixel position, the origin at the first cell."""
    rules = theme.cloud
    cells = assign_cells(spec, rules)
    return {part.id: _node(part, cells[part.id], theme) for part in spec.parts}


def _node(part: Part, cell: Cell, theme: Theme) -> Node:
    """Build the node of a part: a box of the part size, centred on its cell."""
    rules = theme.cloud
    width, height = rules.part_size
    return Node(
        id=part.id,
        shape=Shape.PROCESS,
        x=cell[0] * rules.column_pitch - width / 2,
        y=cell[1] * rules.row_pitch - height / 2,
        width=width,
        height=height,
        text=(part.label,),
        icon=part.icon,
        tone=part.tone,
        number=None,
        font_size=theme.type_scale.node.size,
        detail=(part.detail,) if part.detail else (),
    )


def _depth(spec: CloudSpec, frame: SpecFrame) -> int:
    """Return how many frames are around a frame."""
    return len(spec.chain(frame.id)) - 1


def _frames(plan: Plan) -> list[SceneFrame]:
    """Return the frames, the outer ones first, each as large as what it holds."""
    rects: dict[str, Rect] = {}
    ordered = sorted(plan.spec.frames, key=lambda frame: -_depth(plan.spec, frame))
    for frame in ordered:
        rects[frame.id] = _rect(frame, plan, rects)
    outer_first = sorted(plan.spec.frames, key=lambda frame: _depth(plan.spec, frame))
    return [_scene_frame(frame, rects[frame.id]) for frame in outer_first]


def _scene_frame(frame: SpecFrame, rect: Rect) -> SceneFrame:
    """Build the scene frame of a spec frame."""
    return SceneFrame(
        id=frame.id,
        x=rect.left,
        y=rect.top,
        width=rect.right - rect.left,
        height=rect.bottom - rect.top,
        label=frame.label,
        tone=frame.look.tone,
        variant=FrameVariant.NETWORK,
        is_solid=frame.look.is_solid,
    )


def _rect(frame: SpecFrame, plan: Plan, done: dict[str, Rect]) -> Rect:
    """Return the rectangle of a frame: its parts and inner frames, each with its padding."""
    rules = plan.rules
    boxes = [grown(_slot(plan, part), rules.part_pad) for part in _members(plan, frame)]
    boxes += [grown(done[child.id], rules.frame_gap) for child in _inside(plan.spec, frame)]
    return union(boxes)


def _members(plan: Plan, frame: SpecFrame) -> list[Part]:
    """Return the parts that sit directly in a frame."""
    return [part for part in plan.spec.parts if part.frame == frame.id]


def _inside(spec: CloudSpec, frame: SpecFrame) -> list[SpecFrame]:
    """Return the frames that sit directly in a frame."""
    return [child for child in spec.frames if child.parent == frame.id]


def _slot(plan: Plan, part: Part) -> Rect:
    """Return the room of a part: its box, and for a part in a subnet the columns of the zone."""
    node = plan.nodes[part.id]
    frame = plan.spec.frame_of(part)
    if frame is None or frame.kind not in SUBNET_KINDS:
        return node_rect(node)
    siblings = [
        plan.nodes[other.id]
        for other in plan.spec.parts
        if _sibling_subnet(plan.spec, other, frame)
    ]
    return Rect(
        min(sibling.x for sibling in siblings),
        node.y,
        max(sibling.x + sibling.width for sibling in siblings),
        node.y + node.height,
    )


def _sibling_subnet(spec: CloudSpec, part: Part, frame: SpecFrame) -> bool:
    """Tell whether a part sits in a subnet of the same zone as ``frame``."""
    other = spec.frame_of(part)
    return other is not None and other.kind in SUBNET_KINDS and other.parent == frame.parent
