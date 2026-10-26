"""Build a diagram from a spec: place and route it, check it, and write the files."""

import json
from dataclasses import dataclass
from pathlib import Path

from . import diagrams
from . import overrides as overrides_io
from . import scene as scene_io
from .canvas import fit_canvas
from .check import Finding, check_scene
from .render_drawio import render as render_drawio
from .render_html import render as render_html

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
    scene = diagrams.layout(json.loads(spec_path.read_text(encoding="utf-8")), spec_path.parent)
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
