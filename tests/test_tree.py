"""Tests for the tree diagrams: org chart and mind map."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
ORG = ROOT / "examples" / "company-org.spec.json"
MIND_MAP = ROOT / "examples" / "launch-mindmap.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.model import Scene, Shape, Tone  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


def laid_out(path: Path) -> Scene:
    """Lay out a tree spec file.

    Args:
        path: A spec file.

    Returns:
        The scene.
    """
    return diagrams.layout(json.loads(path.read_text()))


@pytest.mark.parametrize("path", [ORG, MIND_MAP], ids=lambda path: path.name)
def test_example_has_no_errors(path: Path) -> None:
    """Both examples pass the checks with no error."""
    errors = [f for f in check_scene(laid_out(path)) if f.severity is Severity.ERROR]
    assert errors == []


def test_parent_is_centred_over_its_children() -> None:
    """In the org chart a parent sits half way between its first and last child."""
    scene = laid_out(ORG)
    nodes = {node.id: node for node in scene.nodes}
    children = [nodes["n1"], nodes["n4"], nodes["n7"]]
    centres = [node.x + node.width / 2 for node in children]
    assert nodes["n0"].x + nodes["n0"].width / 2 == pytest.approx((centres[0] + centres[-1]) / 2)


def test_each_child_has_its_own_line() -> None:
    """There is one line per parent and child pair, none of them with an arrowhead."""
    scene = laid_out(ORG)
    assert len(scene.edges) == len(scene.nodes) - 1
    assert {edge.head.value for edge in scene.edges} == {"none"}


def test_mind_map_runs_left_to_right_and_branches_pass_their_tone_down() -> None:
    """A mind map's levels move right, and a branch gives its tone to what is below it."""
    scene = laid_out(MIND_MAP)
    nodes = {node.id: node for node in scene.nodes}
    assert nodes["n0"].shape is Shape.TERMINATOR
    assert nodes["n0"].x < nodes["n1"].x < nodes["n2"].x
    assert nodes["n1"].tone is Tone.BLUE
    assert nodes["n2"].tone is Tone.BLUE
    assert nodes["n4"].tone is Tone.VIOLET


def test_spec_without_a_root_is_refused() -> None:
    """A tree needs a root."""
    with pytest.raises(SpecError, match="root"):
        diagrams.layout({"type": "org"})
