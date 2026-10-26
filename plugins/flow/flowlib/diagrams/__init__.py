"""The diagram types. Each type turns a JSON spec into a scene; this module picks the type."""

from collections.abc import Callable

from ..model import Scene
from ..reader import SpecError
from . import (
    architecture,
    boards,
    catalog,
    concept,
    er,
    flowchart,
    graph,
    sequence,
    state,
    timeline,
    tree,
)

Layout = Callable[[object], Scene]

LAYOUTS: dict[str, Layout] = {
    "architecture": architecture.layout_raw,
    "flowchart": flowchart.layout_raw,
    "sequence": sequence.layout_raw,
    "state": state.layout_raw,
    "er": er.layout_raw,
    "org": tree.layout_org,
    "concept": concept.layout_raw,
    "kanban": boards.layout_kanban,
    "layers": boards.layout_layers,
    "wireframe": boards.layout_wireframe,
    "gantt": timeline.layout_gantt,
    "roadmap": timeline.layout_roadmap,
    "mindmap": tree.layout_mind_map,
    **{name: graph.layout_with(each) for name, each in catalog.TYPES.items()},
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
