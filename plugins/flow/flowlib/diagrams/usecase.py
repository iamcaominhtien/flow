"""The UML use case diagram: actors outside a system frame, use cases inside it.

See ``usecase_spec`` for the spec format and ``usecase_grid`` for where the use cases go. Actors
on the left are people, those outside the system on the right are external systems. Lines are
straight: a solid line without a head for an actor that takes part, a dashed arrow with an open
head for ``include`` and ``extend``. The plain style draws the actors as stick figures, the
illustrated style as cards with a large icon.
"""

import math
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
from .grid_frames import shift_into_canvas
from .grid_scene import Heading, finish_scene
from .usecase_grid import assign_cells, owners
from .usecase_spec import EXTERNAL_TAG, Actor, Link, LinkStyle, UseCaseSpec, read_spec

SYSTEM_FRAME_ID = "system"
ACTOR_TONES = (Tone.BLUE, Tone.GREEN, Tone.TEAL, Tone.AMBER, Tone.VIOLET, Tone.GRAY)
ACTOR_CAPTION_ROOM_PX = 44  # the name (and the external tag) under a stick figure
ACTOR_GAP_PX = 36  # least free space between two actors
ARM_FRACTION = 0.4  # where the arms of a stick figure are, as a fraction of its height
DEFAULT_LABELS = {LinkStyle.INCLUDE: "«include»", LinkStyle.EXTEND: "«extend»"}
LINE_ENDS = {
    LinkStyle.ASSOCIATION: (Head.NONE, False),
    LinkStyle.INCLUDE: (Head.OPEN, True),
    LinkStyle.EXTEND: (Head.OPEN, True),
    LinkStyle.GENERALIZES: (Head.TRIANGLE, False),
}  # head and whether the line is dashed


def layout_raw(raw: object) -> Scene:
    """Lay out a use case diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``usecase`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(read_spec(raw))


def layout(spec: UseCaseSpec) -> Scene:
    """Place the use cases in the system frame, the actors outside it, and draw the lines.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    tones = _actor_tones(spec)
    cases = _case_nodes(spec, tones, theme)
    frame = _frame(spec, cases, theme)
    actors = _actor_nodes(spec, (cases, frame), tones, theme)
    nodes, frames = shift_into_canvas({**cases, **actors}, [frame], theme)
    edges = tuple(_edge(link, index, nodes, spec) for index, link in enumerate(spec.links, 1))
    return finish_scene(
        Heading(spec.title, spec.description), (tuple(frames), tuple(nodes.values()), edges)
    )


def _actor_tones(spec: UseCaseSpec) -> dict[str, Tone]:
    """Give each actor a tone: the one asked for, or the next of the palette."""
    return {
        actor.id: actor.tone or ACTOR_TONES[index % len(ACTOR_TONES)]
        for index, actor in enumerate(spec.actors)
    }


def _case_nodes(spec: UseCaseSpec, tones: dict[str, Tone], theme: Theme) -> dict[str, Node]:
    """Build the oval of every use case at its cell, tinted by the actor it belongs to."""
    rules = theme.uml
    owner, cells = owners(spec), assign_cells(spec)
    width, height = rules.case_size
    nodes = {}
    for case in spec.use_cases:
        column, row = cells[case.id]
        owner_id = owner[case.id]
        tone = case.tone or (tones[owner_id] if owner_id else Tone.BLUE)
        nodes[case.id] = Node(
            id=case.id,
            shape=Shape.USE_CASE,
            x=column * rules.case_column_pitch,
            y=row * rules.case_row_pitch,
            width=width,
            height=height,
            text=(case.name,),
            icon=None,
            tone=tone,
            number=None,
            font_size=theme.type_scale.node.size,
        )
    return nodes


def _frame(spec: UseCaseSpec, cases: dict[str, Node], theme: Theme) -> Frame:
    """Draw the system: a white box round the use cases, with the system name at the top left."""
    rules = theme.uml
    boxes = list(cases.values())
    left = min(box.x for box in boxes) - rules.system_pad_x
    top = min(box.y for box in boxes) - rules.system_pad_top
    right = max(box.x + box.width for box in boxes) + rules.system_pad_x
    bottom = max(box.y + box.height for box in boxes) + rules.system_pad_bottom
    return Frame(
        SYSTEM_FRAME_ID, left, top, right - left, bottom - top, spec.system or None, Tone.GRAY,
        FrameVariant.SYSTEM,
    )  # fmt: skip


def _actor_nodes(
    spec: UseCaseSpec, inside: tuple[dict[str, Node], Frame], tones: dict[str, Tone], theme: Theme
) -> dict[str, Node]:
    """Build the actors: on the left of the frame, or on the right for an external system."""
    cases, frame = inside
    nodes = {}
    for is_external in (False, True):
        group = [actor for actor in spec.actors if actor.is_external is is_external]
        wanted = {actor.id: _wanted_y(actor, spec, cases) for actor in group}
        for actor in group:
            node = _actor_node(actor, tones[actor.id], spec.is_illustrated, theme)
            nodes[actor.id] = _beside(node, frame, is_external, theme)
        _spread(nodes, wanted)
    return nodes


def _wanted_y(actor: Actor, spec: UseCaseSpec, cases: dict[str, Node]) -> float:
    """Return the height an actor would like to be at: the middle of the use cases it joins."""
    joined = [
        cases[end].y + cases[end].height / 2
        for link in spec.links
        if link.style is LinkStyle.ASSOCIATION
        for actor_id, end in ((link.source, link.target), (link.target, link.source))
        if actor_id == actor.id and end in cases
    ]
    return sum(joined) / len(joined) if joined else 0.0


def _actor_node(actor: Actor, tone: Tone, is_illustrated: bool, theme: Theme) -> Node:
    """Build the node of an actor: a stick figure, or a card with a large icon."""
    rules = theme.uml
    caption = actor.name + (f"\n{EXTERNAL_TAG}" if actor.is_external else "")
    if not is_illustrated:
        width, height = rules.actor_size
        return Node(
            id=actor.id, shape=Shape.ACTOR, x=0, y=0, width=width, height=height,
            text=(), icon=None, tone=tone, number=None, font_size=theme.type_scale.node.size,
            caption=caption,
        )  # fmt: skip
    width, height = rules.actor_card_size
    tag_room = theme.layout.card_gap + theme.layout.detail_line_height
    return Node(
        id=actor.id, shape=Shape.PROCESS, x=0, y=0, width=width,
        height=height + (tag_room if actor.is_external else 0),
        text=(actor.name,), icon=actor.icon or "user", tone=tone, number=None,
        font_size=theme.type_scale.node.size, card=True,
        detail=(EXTERNAL_TAG,) if actor.is_external else (),
    )  # fmt: skip


def _beside(node: Node, frame: Frame, is_external: bool, theme: Theme) -> Node:
    """Put an actor beside the frame: its middle one actor distance from the frame's edge."""
    distance = theme.uml.actor_distance
    middle = frame.x + frame.width + distance if is_external else frame.x - distance
    return replace(node, x=middle - node.width / 2)


def _spread(nodes: dict[str, Node], wanted: dict[str, float]) -> None:
    """Set the height of each actor of one side: near its wish, with room for its caption."""
    previous_bottom = -math.inf
    for actor_id in sorted(wanted, key=lambda name: wanted[name]):
        node = nodes[actor_id]
        top = max(wanted[actor_id] - _anchor_offset(node), previous_bottom + ACTOR_GAP_PX)
        nodes[actor_id] = replace(node, y=top)
        previous_bottom = top + node.height + _caption_room(node)


def _anchor_offset(node: Node) -> float:
    """Return how far below the top of an actor its lines attach: at the arms, or the middle."""
    return node.height * (ARM_FRACTION if node.shape is Shape.ACTOR else 0.5)


def _caption_room(node: Node) -> float:
    """Return the room under an actor that its caption takes."""
    if node.shape is not Shape.ACTOR:
        return 0.0
    return ACTOR_CAPTION_ROOM_PX + (node.caption or "").count("\n") * ACTOR_CAPTION_ROOM_PX / 2


def _edge(link: Link, index: int, nodes: dict[str, Node], spec: UseCaseSpec) -> Edge:
    """Build the straight line of a link, with its head and its label."""
    source, target = nodes[link.source], nodes[link.target]
    actors = {actor.id for actor in spec.actors}
    if link.source in actors or link.target in actors:
        points = _actor_points(source, target, link.source in actors)
    else:
        points = (_on_oval(source, target), _on_oval(target, source))
    head, is_dashed = LINE_ENDS[link.style]
    text = link.label or DEFAULT_LABELS.get(link.style, "")
    middle = ((points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2)
    return Edge(
        id=f"e{index}",
        role=Role.NEXT,
        points=points,
        label=EdgeLabel(text, middle, LabelKind.PLAIN) if text else None,
        source=link.source,
        target=link.target,
        head=head,
        dashed=is_dashed,
    )


def _actor_points(source: Node, target: Node, is_actor_first: bool) -> tuple[Point, Point]:
    """Return the two ends of a line between an actor and a use case, in link order."""
    actor, case = (source, target) if is_actor_first else (target, source)
    case_middle_y = case.y + case.height / 2
    is_left = actor.x + actor.width / 2 < case.x
    actor_x = actor.x + actor.width if is_left else actor.x
    case_x = case.x if is_left else case.x + case.width
    ends = ((actor_x, actor.y + _anchor_offset(actor)), (case_x, case_middle_y))
    return ends if is_actor_first else (ends[1], ends[0])


def _on_oval(oval: Node, other: Node) -> Point:
    """Return where the line from the middle of an oval to another node leaves its outline."""
    middle_x, middle_y = oval.x + oval.width / 2, oval.y + oval.height / 2
    delta_x = other.x + other.width / 2 - middle_x
    delta_y = other.y + other.height / 2 - middle_y
    scale = math.hypot(delta_x / (oval.width / 2), delta_y / (oval.height / 2)) or 1.0
    return (middle_x + delta_x / scale, middle_y + delta_y / scale)
