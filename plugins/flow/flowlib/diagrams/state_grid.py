"""Choose where every state of a state diagram goes: the happy path left to right, the rest below.

The first row holds the start dot and the states reached by the main transitions (or, when no
transition is marked, by the first transition of each state). A state that is not on that path
sits one row below the state that leads to it, centred under all the states that lead to it. An
end dot that is not on the path goes to the right of the state that leads to it.
"""

from dataclasses import dataclass

from ..sizing import estimate_text_width
from ..theme import LayoutRules, UmlRules
from .state_spec import State, StateKind, StateSpec, Transition

MIN_SPACING_PX = 40  # the least free space between two states of one row
LABEL_CLEARANCE_PX = 24  # free line kept on each side of the chip of a transition


@dataclass(frozen=True)
class Slot:
    """Where a state sits: the x of its centre and its row (0 is the happy path)."""

    centre_x: float
    row: int


@dataclass
class _Grid:
    """What placing the states that are off the happy path needs: the spec and what is placed."""

    spec: StateSpec
    slots: dict[str, Slot]
    sizes: dict[str, tuple[float, float]]


def place_states(
    spec: StateSpec, sizes: dict[str, tuple[float, float]], rules: tuple[UmlRules, LayoutRules]
) -> dict[str, Slot]:
    """Return the slot of every state.

    Args:
        spec: The checked spec.
        sizes: The width and height of each state by id.
        rules: The UML spacing and the layout rules, which size the chips of labels.

    Returns:
        State id to slot.
    """
    uml, layout = rules
    by_id = {state.id: state for state in spec.states}
    chain = _chain(spec, by_id)
    slots = _place_chain(chain, spec, (sizes, uml, layout))
    ends = [s for s in spec.states if s.id not in slots and s.kind is StateKind.END]
    others = [s for s in spec.states if s.id not in slots and s not in ends]
    grid = _Grid(spec, slots, sizes)
    _place_rest(others, grid)
    _place_rest(ends, grid, uml.state_gap_mark)
    return slots


def _chain(spec: StateSpec, by_id: dict[str, State]) -> list[str]:
    """Follow the main transitions from the start; fall back to the first plain transition."""
    start = next((s for s in spec.states if s.kind is StateKind.START), spec.states[0])
    chain = [start.id]
    while True:
        options = [
            t
            for t in spec.transitions
            if t.source == chain[-1] and t.target not in chain and t.target != t.source
        ]
        picked = next((t for t in options if t.is_main), None) or next(
            (t for t in options if _is_plain(t, by_id)), None
        )
        if picked is None:
            return chain
        chain.append(picked.target)


def _is_plain(transition: Transition, by_id: dict[str, State]) -> bool:
    """Tell whether a transition is on no failure path: it may carry the main row on."""
    return not transition.is_failure and by_id[transition.target].kind is not StateKind.FAIL


def _chip_width(text: str, layout: LayoutRules) -> float:
    """Estimate the width of the chip that carries a label."""
    return estimate_text_width(text, layout, layout.chip_font_size) + layout.chip_padding_x


def _place_chain(
    chain: list[str], spec: StateSpec, setting: tuple[dict, UmlRules, LayoutRules]
) -> dict[str, Slot]:
    """Put the states of the happy path in row 0, each far enough from the last for its label."""
    sizes, uml, layout = setting
    slots: dict[str, Slot] = {}
    by_id = {state.id: state for state in spec.states}
    right_edge = 0.0
    for index, name in enumerate(chain):
        width = sizes[name][0]
        gap = 0.0
        if index:
            gap = _gap(by_id[chain[index - 1]], by_id[name], spec, (uml, layout))
        slots[name] = Slot(right_edge + gap + width / 2, 0)
        right_edge += gap + width
    return slots


def _gap(
    before: State, after: State, spec: StateSpec, rules: tuple[UmlRules, LayoutRules]
) -> float:
    """Return the free space between two neighbours: more when a label has to fit on the line."""
    uml, layout = rules
    base = uml.state_gap_mark if before.is_mark or after.is_mark else uml.state_gap_labelled
    labels = [
        _chip_width(t.text, layout) + 2 * LABEL_CLEARANCE_PX
        for t in spec.transitions
        if t.text and {t.source, t.target} == {before.id, after.id}
    ]
    leaving = uml.state_frame_pad_x * (bool(before.group) + bool(after.group))
    return max([base, *labels]) + (leaving if before.group != after.group else 0.0)


def _place_rest(states: list[State], grid: _Grid, beside_gap: float | None = None) -> None:
    """Place the states that are not on the happy path, as soon as one that leads to them is.

    With ``beside_gap`` a state goes to the right of the rightmost state that leads to it, in
    that state's row; otherwise one row below, centred under the states that lead to it.
    """
    waiting = list(states)
    while waiting:
        ready = next((s for s in waiting if _anchors(s, grid)), None)
        target = ready or waiting[0]
        grid.slots[target.id] = _slot_near(target, _anchors(target, grid), grid, beside_gap)
        waiting.remove(target)


def _anchors(state: State, grid: _Grid) -> list[str]:
    """Return the placed states that lead to a state, or else the placed ones it leads to."""
    slots, transitions = grid.slots, grid.spec.transitions
    leading = [t.source for t in transitions if t.target == state.id and t.source in slots]
    if leading:
        return leading
    return [t.target for t in transitions if t.source == state.id and t.target in slots]


def _slot_near(state: State, anchors: list[str], grid: _Grid, beside_gap: float | None) -> Slot:
    """Choose the slot of a state from its anchors, then move it clear of its row neighbours."""
    width = grid.sizes[state.id][0]
    if not anchors:
        return _clear(Slot(0.0, 1), width, grid)
    if beside_gap is not None:
        right = max(anchors, key=lambda name: grid.slots[name].centre_x)
        slot = grid.slots[right]
        centre = slot.centre_x + grid.sizes[right][0] / 2 + beside_gap + width / 2
        return _clear(Slot(centre, slot.row), width, grid)
    placed = [grid.slots[name] for name in anchors]
    centre = sum(slot.centre_x for slot in placed) / len(placed)
    return _clear(Slot(centre, max(slot.row for slot in placed) + 1), width, grid)


def _clear(slot: Slot, width: float, grid: _Grid) -> Slot:
    """Move a slot to the right until it no longer touches a state of its row."""
    centre = slot.centre_x
    moved = True
    while moved:
        moved = False
        for name, other in grid.slots.items():
            room = (width + grid.sizes[name][0]) / 2 + MIN_SPACING_PX
            if other.row == slot.row and abs(other.centre_x - centre) < room:
                centre = other.centre_x + room
                moved = True
    return Slot(centre, slot.row)
