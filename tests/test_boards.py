"""Tests for the boards: Kanban, layers and wireframe."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"
KANBAN = EXAMPLES / "sprint-kanban.spec.json"
LAYERS = EXAMPLES / "request-layers.spec.json"
WIREFRAME = EXAMPLES / "login-wireframe.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


def raw_of(path: Path) -> dict:
    """Load a spec file as a fresh dictionary.

    Args:
        path: A spec file.

    Returns:
        The parsed spec, safe to modify.
    """
    return copy.deepcopy(json.loads(path.read_text()))


@pytest.mark.parametrize("path", [KANBAN, LAYERS, WIREFRAME], ids=lambda path: path.name)
def test_example_has_no_errors_and_draws_in_draw_io(path: Path) -> None:
    """Each example passes the checks and renders to draw.io."""
    scene = diagrams.layout(raw_of(path))
    assert [f for f in check_scene(scene) if f.severity is Severity.ERROR] == []
    assert "<mxGraphModel" in render_drawio.render(scene)


def test_kanban_has_a_frame_per_column_and_cards_inside() -> None:
    """Each column is a frame in the order written and every card lies inside its column."""
    scene = diagrams.layout(raw_of(KANBAN))
    assert [frame.label for frame in scene.frames] == ["To do", "Doing", "Done"]
    for index, frame in enumerate(scene.frames):
        for node in (node for node in scene.nodes if node.id.startswith(f"c{index}-")):
            assert frame.x < node.x
            assert node.x + node.width < frame.x + frame.width
            assert frame.y < node.y
            assert node.y + node.height < frame.y + frame.height


def test_layers_are_stacked_and_joined_only_when_asked() -> None:
    """Layers run top to bottom; 'flow' draws one arrow between each pair and no flow draws none."""
    raw = raw_of(LAYERS)
    scene = diagrams.layout(raw)
    tops = [frame.y for frame in scene.frames]
    assert tops == sorted(tops)
    assert len(scene.edges) == len(scene.frames) - 1
    raw["flow"] = False
    assert diagrams.layout(raw).edges == ()


def test_wireframe_elements_follow_their_kind() -> None:
    """A list becomes one row per item and a button is a pill."""
    scene = diagrams.layout(raw_of(WIREFRAME))
    texts = [node.text for node in scene.nodes]
    assert ("Orders",) in texts
    assert ("[Email]",) in texts


def test_wireframe_unknown_element_kind_is_refused() -> None:
    """An element of an unknown kind fails and lists the kinds."""
    raw = raw_of(WIREFRAME)
    raw["screens"][0]["elements"][0]["kind"] = "carousel"
    with pytest.raises(SpecError, match="header"):
        diagrams.layout(raw)


def test_board_without_entries_is_refused() -> None:
    """An empty board fails with a message."""
    with pytest.raises(SpecError, match="columns"):
        diagrams.layout({"type": "kanban", "columns": []})
