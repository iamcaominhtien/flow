"""Build a diagram from a spec: place and route it, check it, and write the files."""

from dataclasses import dataclass, replace
from pathlib import Path

from . import overrides as overrides_io
from . import scene as scene_io
from . import spec as spec_io
from . import transpose
from .check import Finding, check_scene
from .layered import build_grid
from .model import Direction, Scene
from .placement import place_nodes
from .render_drawio import render as render_drawio
from .render_html import render as render_html
from .routing import route_edges
from .spec import Spec
from .theme import load_theme

SPEC_SUFFIX = ".spec.json"
OVERRIDES_SUFFIX = ".overrides.json"
SCENE_SUFFIX = ".scene.json"
HTML_SUFFIX = ".html"
DRAWIO_SUFFIX = ".drawio"
JSON_INDENT = 1


@dataclass(frozen=True)
class BuildResult:
    """What a build wrote and what the checks found."""

    scene_path: Path
    html_path: Path
    drawio_path: Path
    findings: list[Finding]


def fit_canvas(scene: Scene) -> Scene:
    """Size the canvas to hold everything in a scene, with a margin and a minimum width.

    Args:
        scene: A scene whose nodes, frames, lines and labels have their final positions.

    Returns:
        The same scene with ``width`` and ``height`` set.
    """
    rules = load_theme().layout
    xs = [node.x + node.width for node in scene.nodes] + [f.x + f.width for f in scene.frames]
    ys = [node.y + node.height for node in scene.nodes] + [f.y + f.height for f in scene.frames]
    for edge in scene.edges:
        xs += [x for x, _ in edge.points]
        ys += [y for _, y in edge.points]
        if edge.label:
            xs.append(edge.label.at[0] + rules.margin)
            ys.append(edge.label.at[1] + rules.margin)
    return replace(
        scene,
        width=max(rules.min_canvas_width, max(xs)) + rules.margin,
        height=max(ys) + rules.margin,
    )


def layout(spec: Spec) -> Scene:
    """Place and route a flowchart, giving a scene ready to draw.

    Args:
        spec: The flowchart description.

    Returns:
        The scene: sized nodes at pixel positions, routed lines, swimlane frames, and a canvas
        that holds them.
    """
    rules = load_theme().layout
    grid = build_grid(spec)
    placement = place_nodes(spec, grid, rules)
    nodes = tuple(placement.nodes.values())
    frames = placement.frames
    edges = tuple(route_edges(spec, grid, placement, rules))
    if spec.direction is Direction.RIGHT:
        nodes = tuple(transpose.node(node) for node in nodes)
        frames = tuple(transpose.frame(frame) for frame in frames)
        edges = tuple(transpose.edge(edge) for edge in edges)
    scene = Scene(
        width=0,
        height=0,
        title=spec.title,
        description=spec.description,
        frames=frames,
        nodes=nodes,
        edges=edges,
    )
    return fit_canvas(scene)


def output_stem(spec_path: Path) -> str:
    """Return the file name without the ``.spec.json`` ending, to name the outputs after.

    Args:
        spec_path: The spec file.

    Returns:
        The name without suffix, for example ``order`` for ``order.spec.json``.
    """
    name = spec_path.name
    return name.removesuffix(SPEC_SUFFIX) if name.endswith(SPEC_SUFFIX) else spec_path.stem


def build(spec_path: Path, out_dir: Path) -> BuildResult:
    """Build the scene, the HTML page and the draw.io file of a spec, and check the result.

    Args:
        spec_path: A spec file.
        out_dir: Where to write ``<name>.scene.json``, ``<name>.html`` and ``<name>.drawio``.

    Returns:
        The paths written and the findings of the checks.

    Raises:
        SpecError: If the spec is not valid.
        OverridesError: If a ``<name>.overrides.json`` file beside the spec is not valid.
    """
    stem = output_stem(spec_path)
    scene = layout(spec_io.load(spec_path))
    overrides_path = spec_path.with_name(f"{stem}{OVERRIDES_SUFFIX}")
    if overrides_path.is_file():
        scene = fit_canvas(overrides_io.apply(scene, overrides_io.load(overrides_path)))
    out_dir.mkdir(parents=True, exist_ok=True)
    scene_path = out_dir / f"{stem}{SCENE_SUFFIX}"
    html_path = out_dir / f"{stem}{HTML_SUFFIX}"
    drawio_path = out_dir / f"{stem}{DRAWIO_SUFFIX}"
    scene_path.write_text(scene_io.dumps(scene, JSON_INDENT) + "\n", encoding="utf-8")
    html_path.write_text(render_html(scene), encoding="utf-8")
    drawio_path.write_text(render_drawio(scene), encoding="utf-8")
    return BuildResult(scene_path, html_path, drawio_path, check_scene(scene))
