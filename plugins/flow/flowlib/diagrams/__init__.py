"""The diagram types. Each type turns a JSON spec into a scene; this module picks the type."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from ..model import DEFAULT_THEME, Scene
from ..reader import Reader, SpecError
from . import (
    architecture,
    boards,
    bpmn,
    c4,
    catalog,
    class_diagram,
    cloud,
    concept,
    dfd,
    er,
    flowchart,
    gantt,
    graph,
    mindmap,
    org,
    roadmap,
    screenflow,
    sequence,
    state,
    usecase,
)

THEME_KEY = "theme"
SOURCE_AWARE: dict[str, Callable[[object, Path | None], Scene]] = {
    "dfd": dfd.layout_raw,
    "c4": c4.layout_raw,
}  # the types whose layout needs the folder of the spec, to find the level above

Layout = Callable[[object], Scene]

LAYOUTS: dict[str, Layout] = {
    "architecture": architecture.layout_raw,
    "cloud": cloud.layout_raw,
    "flowchart": flowchart.layout_raw,
    "sequence": sequence.layout_raw,
    "state": state.layout_raw,
    "er": er.layout_raw,
    "class": class_diagram.layout_raw,
    "usecase": usecase.layout_raw,
    "org": org.layout_raw,
    "concept": concept.layout_raw,
    "kanban": boards.layout_kanban,
    "layers": boards.layout_layers,
    "wireframe": boards.layout_wireframe,
    "gantt": gantt.layout_raw,
    "roadmap": roadmap.layout_raw,
    "mindmap": mindmap.layout_raw,
    **{name: graph.layout_with(each) for name, each in catalog.TYPES.items()},
    "screen": screenflow.layout_raw,
    "bpmn": bpmn.layout_raw,
}


def layout(raw: object, source_dir: Path | None = None) -> Scene:
    """Lay out a diagram, choosing the type from the ``type`` field of the spec.

    Args:
        raw: The result of ``json.loads`` on a spec.
        source_dir: The folder of the spec file; a data flow diagram that opens a process of
            another spec looks for it here.

    Returns:
        The scene.

    Raises:
        SpecError: If the type is missing or unknown, or the spec for that type is not valid.
    """
    kind = raw.get("type") if isinstance(raw, dict) else None
    if kind not in LAYOUTS and kind not in SOURCE_AWARE:
        known = ", ".join(sorted({*LAYOUTS, *SOURCE_AWARE}))
        raise SpecError([f"spec: 'type' must be one of: {known}"])
    theme = _read_theme(raw)
    spec = {key: value for key, value in raw.items() if key != THEME_KEY}
    scene = SOURCE_AWARE[kind](spec, source_dir) if kind in SOURCE_AWARE else LAYOUTS[kind](spec)
    return replace(scene, theme=theme, diagram=kind)


def _read_theme(raw: dict[str, object]) -> str:
    """Read and check the ``theme`` field that every spec type accepts.

    Args:
        raw: The spec, a JSON object.

    Returns:
        The theme name, ``pastel`` when the spec has none.

    Raises:
        SpecError: If the theme is not one of the known themes.
    """
    reader = Reader()
    theme = reader.theme(raw) if THEME_KEY in raw else DEFAULT_THEME
    if reader.problems:
        raise SpecError(reader.problems)
    return theme
