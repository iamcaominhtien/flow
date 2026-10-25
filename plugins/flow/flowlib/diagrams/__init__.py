"""The diagram types. Each type turns a JSON spec into a scene; this module picks the type."""

from collections.abc import Callable

from ..model import Scene
from ..reader import SpecError
from . import architecture, er, flowchart, sequence, state

Layout = Callable[[object], Scene]

LAYOUTS: dict[str, Layout] = {
    "architecture": architecture.layout_raw,
    "flowchart": flowchart.layout_raw,
    "sequence": sequence.layout_raw,
    "state": state.layout_raw,
    "er": er.layout_raw,
}


def layout(raw: object) -> Scene:
    """Lay out a diagram, choosing the type from the ``type`` field of the spec.

    Args:
        raw: The result of ``json.loads`` on a spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the type is missing or unknown, or the spec for that type is not valid.
    """
    kind = raw.get("type") if isinstance(raw, dict) else None
    if kind not in LAYOUTS:
        known = ", ".join(sorted(LAYOUTS))
        raise SpecError([f"spec: 'type' must be one of: {known}"])
    return LAYOUTS[kind](raw)
