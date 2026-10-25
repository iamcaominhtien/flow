"""Build a diagram from a spec: place and route it, check it, and write the files."""

from dataclasses import dataclass
from pathlib import Path

from . import scene as scene_io
from . import spec as spec_io
from .check import Finding, check_scene
from .layered import build_grid
from .model import Scene
from .placement import place_nodes
from .render_html import render
from .routing import route_edges
from .spec import Spec
from .theme import load_theme

SPEC_SUFFIX = ".spec.json"
SCENE_SUFFIX = ".scene.json"
HTML_SUFFIX = ".html"
JSON_INDENT = 1


@dataclass(frozen=True)
class BuildResult:
    """What a build wrote and what the checks found."""

    scene_path: Path
    html_path: Path
    findings: list[Finding]


def layout(spec: Spec) -> Scene:
    """Place and route a flowchart, giving a scene ready to draw.

    Args:
        spec: The flowchart description.

    Returns:
        The scene: sized nodes at pixel positions, routed lines, and a canvas that holds them.
    """
    rules = load_theme().layout
    grid = build_grid(spec)
    placement = place_nodes(spec, grid, rules)
    edges = route_edges(spec, grid, placement, rules)
    farthest_x = max(x for edge in edges for x, _ in edge.points)
    label_right = max((edge.label.at[0] + rules.margin for edge in edges if edge.label), default=0)
    width = max(rules.min_canvas_width, placement.right, farthest_x, label_right)
    return Scene(
        width=width + rules.margin,
        height=placement.bottom + rules.margin,
        title=spec.title,
        description=spec.description,
        frames=(),
        nodes=tuple(placement.nodes.values()),
        edges=tuple(edges),
    )


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
    """Build the scene and the HTML of a spec file and check the result.

    Args:
        spec_path: A spec file.
        out_dir: Where to write ``<name>.scene.json`` and ``<name>.html``.

    Returns:
        The paths written and the findings of the checks.

    Raises:
        SpecError: If the spec is not valid.
    """
    scene = layout(spec_io.load(spec_path))
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem(spec_path)
    scene_path = out_dir / f"{stem}{SCENE_SUFFIX}"
    html_path = out_dir / f"{stem}{HTML_SUFFIX}"
    scene_path.write_text(scene_io.dumps(scene, JSON_INDENT) + "\n", encoding="utf-8")
    html_path.write_text(render(scene), encoding="utf-8")
    return BuildResult(scene_path, html_path, check_scene(scene))
