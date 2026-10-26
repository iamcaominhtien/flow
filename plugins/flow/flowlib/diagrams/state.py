"""The state diagram: states joined by transitions, with a start and an end mark.

The JSON format::

    {"type": "state", "title": "...", "desc": "...", "direction": "down|right",
     "states": [{"id", "label", "kind": "state|start|end|fail", "detail", "icon", "tone"}],
     "transitions": [{"from": "state", "to": "state", "label", "main": true}]}

A ``start`` state is the small filled circle and an ``end`` state the ringed one; they need no
label. A transition that goes back to an earlier state is routed around the states between.
"""

from enum import StrEnum

from ..model import Direction, Head, Role, Scene, Shape, Tone
from ..reader import Reader, SpecError, suggestion
from ..spec import Spec, SpecEdge, SpecNode
from ..theme import icon_names
from . import flowchart

SPEC_KEYS = {"type", "title", "desc", "direction", "states", "transitions"}
STATE_KEYS = {"id", "label", "kind", "detail", "icon", "tone"}
TRANSITION_KEYS = {"from", "to", "label", "main"}


class StateKind(StrEnum):
    """What a state is; decides its outline."""

    STATE = "state"
    START = "start"
    END = "end"
    FAIL = "fail"


MARKS = {StateKind.START, StateKind.END}
SHAPE_OF_KIND = {
    StateKind.STATE: Shape.PROCESS,
    StateKind.START: Shape.START,
    StateKind.END: Shape.END,
    StateKind.FAIL: Shape.FAIL,
}


def _state(raw: object, where: str, read: Reader, icons: set[str]) -> SpecNode | None:
    """Build one state as a node, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, STATE_KEYS, where)
    icon = raw.get("icon")
    if icon is not None and icon not in icons:
        read.report(where, f"unknown icon '{icon}'; use one of: {', '.join(sorted(icons))}")
    identifier = read.identifier(raw, where)
    kind = read.enum(StateKind, raw, "kind", where) or StateKind.STATE
    return SpecNode(
        id=identifier,
        kind=SHAPE_OF_KIND[kind],
        text=read.text(raw, "label", where) or ("" if kind in MARKS else identifier),
        icon=icon,
        tone=read.enum(Tone, raw, "tone", where),
        number=None,
        side=None,
        lane=None,
        detail=read.text(raw, "detail", where) or "",
    )


def _transition(
    raw: object, where: str, read: Reader, states: dict[str, SpecNode]
) -> SpecEdge | None:
    """Build one transition as an edge, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, TRANSITION_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in states:
            hint = suggestion(name, states)
            read.report(where, f"'{key}' names '{name}', which is not a state{hint}")
        ends.append(name if name in states else "")
    return SpecEdge(
        source=ends[0],
        target=ends[1],
        role=Role.MAIN if raw.get("main") is True else Role.NEXT,
        label=read.text(raw, "label", where),
        head=Head.FILLED,
    )


def to_spec(raw: object) -> Spec:
    """Check a state spec and turn it into the description the layout works on.

    Args:
        raw: The result of ``json.loads`` on a state spec.

    Returns:
        The states as nodes and the transitions as edges.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    icons = icon_names()
    items = raw.get("states", [])
    built = [
        _state(item, f"states[{i}]", read, icons)
        for i, item in enumerate(items if isinstance(items, list) else [])
    ]
    states = {node.id: node for node in built if node is not None}
    if not states:
        read.report("spec", "'states' must list at least one state")
    rows = raw.get("transitions", [])
    transitions = [
        _transition(item, f"transitions[{i}]", read, states)
        for i, item in enumerate(rows if isinstance(rows, list) else [])
    ]
    direction = read.enum(Direction, raw, "direction", "spec") or Direction.DOWN
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    if read.problems:
        raise SpecError(read.problems)
    return Spec(
        title=title,
        description=description,
        direction=direction,
        lanes=(),
        nodes=tuple(states.values()),
        edges=tuple(edge for edge in transitions if edge is not None),
    )


def layout_raw(raw: object) -> Scene:
    """Lay out a state diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a state spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return flowchart.layout(to_spec(raw))
