"""The UML state diagram: states joined by ``event [guard] / action`` transitions.

See ``state_spec`` for the spec format. The happy path runs left to right in the first row, the
other states sit below it (``state_grid``), a frame with a pill groups the states of one
composite state, and a transition from a state to itself is a loop above its box.
"""

from dataclasses import replace

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
    Tone,
)
from ..theme import Theme, load_theme
from .grid_frames import frame_node, pill_rect, shift_into_canvas
from .grid_routes import Extras, GridSpacing, route_flows
from .grid_scene import Heading, Line, build_edges, finish_scene
from .state_grid import Slot, place_states
from .state_spec import State, StateKind, StateSpec, Transition, read_spec

LOOP_LABEL_ROOM_PX = 36  # room above a self-transition loop for its label
LOOP_LABEL_GAP_PX = 14  # between the top of a loop and the middle of its label
FAILURE_KINDS = (StateKind.FAIL,)


def layout_raw(raw: object) -> Scene:
    """Lay out a state diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``state`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(read_spec(raw))


def layout(spec: StateSpec) -> Scene:
    """Place the states of a checked spec, group them in frames and route the transitions.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    rules = theme.uml
    sizes = {state.id: _size(state, theme) for state in spec.states}
    slots = place_states(spec, sizes, (rules, theme.layout))
    nodes = {state.id: _node(state, sizes[state.id], theme) for state in spec.states}
    nodes = _at_slots(nodes, slots, theme)
    frames = _frames(spec, nodes, theme)
    nodes, moved_frames = shift_into_canvas(nodes, frames, theme)
    nodes, moved_frames = _below_loops(spec, nodes, moved_frames, theme)
    return finish_scene(
        Heading(spec.title, spec.description),
        (tuple(moved_frames), tuple(nodes.values()), _edges(spec, nodes, moved_frames, theme)),
    )


def _size(state: State, theme: Theme) -> tuple[float, float]:
    """Return the size of a state: the box grows by a line for each activity after the first."""
    rules = theme.uml
    if state.is_mark:
        return (rules.state_dot, rules.state_dot)
    width, height = rules.state_size
    extra = max(len(state.activities) - 1, 0) + (1 if state.detail and state.activities else 0)
    return (width, height + extra * rules.state_activity_line_height)


def _node(state: State, size: tuple[float, float], theme: Theme) -> Node:
    """Build the node of a state: a dot, or a rounded box tinted by its phase."""
    shape = {StateKind.START: Shape.INITIAL, StateKind.END: Shape.FINAL}.get(
        state.kind, Shape.PROCESS
    )
    tone = state.tone or (Tone.RED if state.kind is StateKind.FAIL else None)
    return Node(
        id=state.id,
        shape=shape,
        x=0,
        y=0,
        width=size[0],
        height=size[1],
        text=(state.name,) if state.name else (),
        icon=state.icon,
        tone=tone,
        number=None,
        font_size=theme.type_scale.node.size,
        detail=(state.detail,) if state.detail else (),
        activities=state.activities,
    )


def _at_slots(nodes: dict[str, Node], slots: dict[str, Slot], theme: Theme) -> dict[str, Node]:
    """Move every node to its slot: rows are one row pitch apart and centred on the row line."""
    rules = theme.uml
    return {
        name: replace(
            node,
            x=slots[name].centre_x - node.width / 2,
            y=slots[name].row * rules.state_row_pitch - node.height / 2,
        )
        for name, node in nodes.items()
    }


def _frames(spec: StateSpec, nodes: dict[str, Node], theme: Theme) -> list[Frame]:
    """Draw a dashed frame with a pill around the states of each group."""
    rules = theme.uml
    groups: dict[str, list[State]] = {}
    for state in spec.states:
        if state.group:
            groups.setdefault(state.group, []).append(state)
    frames = []
    for label, members in groups.items():
        boxes = [nodes[state.id] for state in members]
        left = min(box.x for box in boxes) - rules.state_frame_pad_x
        top = min(box.y for box in boxes) - rules.state_frame_pad_top
        right = max(box.x + box.width for box in boxes) + rules.state_frame_pad_x
        bottom = max(box.y + box.height for box in boxes) + rules.state_frame_pad_bottom
        tone = next((state.tone for state in members if state.tone), Tone.GRAY)
        frames.append(
            Frame(
                f"group-{label}", left, top, right - left, bottom - top, label, tone,
                FrameVariant.LAYER,
            )
        )  # fmt: skip
    return frames


def _below_loops(
    spec: StateSpec, nodes: dict[str, Node], frames: list[Frame], theme: Theme
) -> tuple[dict[str, Node], list[Frame]]:
    """Move everything down when a self-transition loop and its label would rise too high."""
    if not any(t.source == t.target for t in spec.transitions):
        return nodes, frames
    rules = theme.uml
    drop = rules.state_loop_height + LOOP_LABEL_ROOM_PX
    return (
        {name: replace(node, y=node.y + drop) for name, node in nodes.items()},
        [replace(frame, y=frame.y + drop) for frame in frames],
    )


def _edges(
    spec: StateSpec, nodes: dict[str, Node], frames: list[Frame], theme: Theme
) -> tuple[Edge, ...]:
    """Route the transitions between states and draw the loops of the self transitions."""
    rules = theme.uml
    by_id = {state.id: state for state in spec.states}
    straight = [t for t in spec.transitions if t.source != t.target]
    spacing = GridSpacing(
        rules.state_row_pitch,
        rules.state_column_pitch,
        rules.pair_gap,
        rules.channel_step,
        rules.channel_clearance,
    )
    extras = Extras({f.id: frame_node(f) for f in frames}, [pill_rect(f, theme) for f in frames])
    lines = tuple(_line(t, by_id) for t in straight)
    routes = route_flows(nodes, lines, spacing, extras)
    built = [
        _styled(edge, _is_rose(t, by_id))
        for edge, t in zip(build_edges(lines, routes, set(nodes)), straight, strict=True)
    ]
    loops = [t for t in spec.transitions if t.source == t.target]
    drawn = [
        _loop(t, nodes[t.source], (f"e{len(built) + index + 1}", _is_rose(t, by_id)), theme)
        for index, t in enumerate(loops)
    ]
    return (*built, *drawn)


def _is_rose(transition: Transition, by_id: dict[str, State]) -> bool:
    """Tell whether a transition is on a failure or cancel path, drawn in rose."""
    return not transition.is_main and (
        transition.is_failure
        or by_id[transition.source].kind in FAILURE_KINDS
        or by_id[transition.target].kind in FAILURE_KINDS
    )


def _role(transition: Transition, is_rose: bool) -> Role:
    """Pick the line role: blue and animated for the happy path, rose for a failure."""
    if transition.is_main:
        return Role.MAIN
    return Role.NO if is_rose else Role.NEXT


def _line(transition: Transition, by_id: dict[str, State]) -> Line:
    """Build the line of a transition, with its ``event [guard] / action`` label."""
    role = _role(transition, _is_rose(transition, by_id))
    return Line(transition.source, transition.target, transition.text, role)


def _styled(edge: Edge, is_rose: bool) -> Edge:
    """Give the chip of a rose transition the rose colours."""
    if edge.label is None or not is_rose:
        return edge
    return replace(edge, label=replace(edge.label, kind=LabelKind.NO))


def _loop(transition: Transition, node: Node, identity: tuple[str, bool], theme: Theme) -> Edge:
    """Draw a transition from a state to itself as a loop above its box, with its label above."""
    rules = theme.uml
    identifier, is_rose = identity
    middle = node.x + node.width / 2
    left, right = middle - rules.state_loop_span / 2, middle + rules.state_loop_span / 2
    top = node.y - rules.state_loop_height
    points: tuple[Point, ...] = ((left, node.y), (left, top), (right, top), (right, node.y))
    label = None
    if transition.text:
        kind = LabelKind.NO if is_rose else LabelKind.PLAIN
        label = EdgeLabel(transition.text, (middle, top - LOOP_LABEL_GAP_PX), kind)
    return Edge(
        id=identifier,
        role=_role(transition, is_rose),
        points=points,
        label=label,
        source=transition.source,
        target=transition.target,
        head=Head.FILLED,
    )
