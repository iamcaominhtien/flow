"""Draw two arrows between the same two items as one, with both triggers on it.

A screen often has two ways to the same next screen (``click Sign up`` and ``click the heart``
both open Sign up). Drawn as two arrows they run side by side, and only their place tells them
apart. UML writes such a pair as one transition with a list of triggers, ``e1, e2 [guard] /
effect``; here arrows that agree on everything but the trigger are merged that way.
"""

from dataclasses import replace

from ..model import TRIGGER_JOIN
from .screen_spec import FlowSpec, Transition, Trigger


def merge_parallel(spec: FlowSpec) -> FlowSpec:
    """Merge the transitions that differ only in their trigger into one per pair of items.

    Two transitions merge when they have the same source, target, kind, guard, effect and
    route, neither has a code of its own, and their triggers are both the user's or both the
    same system event. The merged transition takes the place of the first one.

    Args:
        spec: The parsed spec.

    Returns:
        The spec with the merged transitions; the spec itself when nothing merges.
    """
    merged: list[Transition] = []
    places: dict[tuple[object, ...], int] = {}
    for transition in spec.transitions:
        key = _merge_key(transition)
        if key is None or key not in places:
            if key is not None:
                places[key] = len(merged)
            merged.append(transition)
            continue
        first = merged[places[key]]
        merged[places[key]] = replace(first, trigger=_joined(first.trigger, transition.trigger))
    if len(merged) == len(spec.transitions):
        return spec
    return replace(spec, transitions=tuple(merged))


def _merge_key(transition: Transition) -> tuple[object, ...] | None:
    """Return what two transitions must share to merge; None for one that never merges."""
    if transition.code:
        return None
    icon = transition.trigger.system_icon if transition.trigger else None
    return (
        transition.source,
        transition.target,
        transition.kind,
        transition.guard,
        transition.effect,
        transition.route,
        icon,
    )


def _joined(first: Trigger | None, second: Trigger | None) -> Trigger | None:
    """Join two triggers into one list; one that is missing or repeated adds nothing."""
    if first is None or second is None:
        return first or second
    if second.text in first.text.split(TRIGGER_JOIN):
        return first
    return replace(first, text=f"{first.text}{TRIGGER_JOIN}{second.text}")
