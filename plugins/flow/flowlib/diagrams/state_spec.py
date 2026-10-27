"""Read and check the spec of a UML state diagram.

The JSON format::

    {"type": "state", "title": "...", "desc": "...",
     "states": [{"id", "label", "kind": "state|start|end|fail", "tone", "icon", "detail",
                 "entry", "do", "exit", "group", "states": [nested states]}],
     "transitions": [{"from", "to", "event", "guard", "action", "main": true, "fail": true}]}

A transition is written ``event [guard] / action``; any part may be left out. ``label`` is
accepted for ``event``. A state with a ``group``, or inside a state with nested ``states``, is
drawn in a frame named after the group.
"""

from dataclasses import dataclass
from enum import StrEnum

from ..model import Tone
from ..reader import Reader, SpecError, suggestion
from ..theme import icon_names

SPEC_KEYS = {"type", "title", "desc", "theme", "states", "transitions"}
STATE_KEYS = {
    "id", "label", "kind", "tone", "icon", "detail", "entry", "do", "exit", "group", "states",
}  # fmt: skip
TRANSITION_KEYS = {"from", "to", "event", "guard", "action", "label", "main", "fail"}
ACTIVITY_KEYS = ("entry", "do", "exit")  # the order the lines are drawn in


class StateKind(StrEnum):
    """What a state is: a box, the start dot, an end dot, or a box on a failure path."""

    STATE = "state"
    START = "start"
    END = "end"
    FAIL = "fail"


@dataclass(frozen=True)
class State:
    """One state, a start dot or an end dot."""

    id: str
    name: str
    kind: StateKind
    tone: Tone | None
    icon: str | None
    detail: str
    activities: tuple[str, ...]
    group: str | None

    @property
    def is_mark(self) -> bool:
        """Tell whether this is the start dot or an end dot."""
        return self.kind in (StateKind.START, StateKind.END)


@dataclass(frozen=True)
class Transition:
    """One transition: where it goes and the three parts of its label."""

    source: str
    target: str
    event: str
    guard: str
    action: str
    is_main: bool
    is_failure: bool

    @property
    def text(self) -> str:
        """Return the label as ``event [guard] / action``, leaving out the parts not given."""
        parts = [self.event, f"[{self.guard}]" if self.guard else ""]
        if self.action:
            parts.append(f"/ {self.action}")
        return " ".join(part for part in parts if part)


@dataclass(frozen=True)
class StateSpec:
    """A checked state diagram."""

    title: str | None
    description: str | None
    states: tuple[State, ...]
    transitions: tuple[Transition, ...]


def read_spec(raw: object) -> StateSpec:
    """Check a state spec.

    Args:
        raw: The result of ``json.loads`` on a ``state`` spec.

    Returns:
        The checked spec, with nested states flattened into states that have a group.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    items = raw.get("states", [])
    states = _states(items if isinstance(items, list) else [], "states", None, read)
    known = {state.id: state for state in states}
    if not known:
        read.report("spec", "'states' must list at least one state")
    rows = raw.get("transitions", [])
    transitions = [
        _transition(item, f"transitions[{index}]", read, known)
        for index, item in enumerate(rows if isinstance(rows, list) else [])
    ]
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    if read.problems:
        raise SpecError(read.problems)
    return StateSpec(title, description, tuple(states), tuple(t for t in transitions if t))


def _states(items: list, where: str, group: str | None, read: Reader) -> list[State]:
    """Read a list of states; a state with nested states becomes the group of its children."""
    found: list[State] = []
    for index, raw in enumerate(items):
        place = f"{where}[{index}]"
        state = _state(raw, place, group, read)
        if state is None:
            continue
        nested = raw.get("states")
        if nested is None:
            found.append(state)
            continue
        if not isinstance(nested, list):
            read.report(place, "'states' must be a list of states")
            continue
        found.extend(_states(nested, f"{place}.states", state.name, read))
    return found


def _state(raw: object, where: str, group: str | None, read: Reader) -> State | None:
    """Build one state, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, STATE_KEYS, where)
    icon = raw.get("icon")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'; use one of: {', '.join(sorted(icon_names()))}")
    identifier = read.identifier(raw, where)
    kind = read.enum(StateKind, raw, "kind", where) or StateKind.STATE
    is_mark = kind in (StateKind.START, StateKind.END)
    name = read.text(raw, "label", where) or ("" if is_mark else identifier)
    activities = tuple(
        f"{key} / {text}" for key in ACTIVITY_KEYS if (text := read.text(raw, key, where))
    )
    return State(
        id=identifier,
        name=name,
        kind=kind,
        tone=read.enum(Tone, raw, "tone", where),
        icon=icon,
        detail=read.text(raw, "detail", where) or "",
        activities=activities,
        group=read.text(raw, "group", where) or group,
    )


def _transition(
    raw: object, where: str, read: Reader, states: dict[str, State]
) -> Transition | None:
    """Build one transition, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, TRANSITION_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in states:
            read.report(
                where,
                f"'{key}' names '{name}', which is not a state{suggestion(name, states)}",
            )
        ends.append(name if name in states else "")
    event = read.text(raw, "event", where) or read.text(raw, "label", where) or ""
    return Transition(
        source=ends[0],
        target=ends[1],
        event=event,
        guard=read.text(raw, "guard", where) or "",
        action=read.text(raw, "action", where) or "",
        is_main=raw.get("main") is True,
        is_failure=raw.get("fail") is True,
    )
