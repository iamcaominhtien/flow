"""Tests for folding a layout that is too long into bands."""

import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

STEPS = 40


def _chain_spec(direction: str) -> dict:
    """Return a flowchart of one long chain of steps over two lanes."""
    nodes = [
        {
            "id": f"s{index}",
            "kind": "process",
            "text": f"Step {index}",
            "lane": "a" if index % 5 else "b",
        }
        for index in range(STEPS)
    ]
    edges = [{"from": f"s{index}", "to": f"s{index + 1}"} for index in range(STEPS - 1)]
    lanes = [{"id": "a", "label": "A", "tone": "blue"}, {"id": "b", "label": "B", "tone": "green"}]
    return {
        "type": "flowchart",
        "direction": direction,
        "lanes": lanes,
        "nodes": nodes,
        "edges": edges,
    }


def test_a_long_chain_going_right_is_folded_into_rows() -> None:
    """The page is far narrower than the chain would be in one row, and nothing is lost."""
    scene = diagrams.layout(_chain_spec("right"))
    one_row = STEPS * 200
    assert scene.width < one_row / 2
    assert len(scene.nodes) == STEPS
    assert len(scene.edges) == STEPS - 1
    assert not [f for f in check_scene(scene) if f.severity is Severity.ERROR]


def test_every_frame_id_is_unique_after_folding() -> None:
    """A lane cut into several pieces gives each piece its own id."""
    scene = diagrams.layout(_chain_spec("right"))
    ids = [frame.id for frame in scene.frames]
    assert len(ids) == len(set(ids))


def test_a_short_chain_is_not_folded() -> None:
    """A chart that fits in the allowed extent keeps one row."""
    spec = _chain_spec("right")
    spec["nodes"] = spec["nodes"][:6]
    spec["edges"] = spec["edges"][:5]
    scene = diagrams.layout(spec)
    assert scene.width < load_theme().layout.fold_extent
    assert len({frame.id for frame in scene.frames}) == len(scene.frames) == 2
