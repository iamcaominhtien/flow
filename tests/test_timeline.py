"""Tests for the timeline diagrams: Gantt chart and roadmap."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
GANTT = ROOT / "examples" / "website-gantt.spec.json"
ROADMAP = ROOT / "examples" / "product-roadmap.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams  # noqa: E402
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


@pytest.mark.parametrize("path", [GANTT, ROADMAP], ids=lambda path: path.name)
def test_example_has_no_errors(path: Path) -> None:
    """Both examples pass the checks with no error."""
    errors = [f for f in check_scene(diagrams.layout(raw_of(path))) if f.severity is Severity.ERROR]
    assert errors == []


def test_bar_position_and_width_follow_start_and_length() -> None:
    """A bar starts at its period and spans as many periods as its length."""
    scene = diagrams.layout(raw_of(GANTT))
    nodes = {node.id: node for node in scene.nodes}
    period = nodes["period-1"].x - nodes["period-0"].x
    assert nodes["design"].x - nodes["brief"].x == pytest.approx(period)
    assert nodes["build"].width > nodes["design"].width > nodes["brief"].width


def test_gantt_dependencies_are_lines_from_the_end_to_the_start() -> None:
    """A task that follows another gets a line from the right of the first to the left of itself."""
    scene = diagrams.layout(raw_of(GANTT))
    nodes = {node.id: node for node in scene.nodes}
    line = next(edge for edge in scene.edges if edge.target == "design")
    assert line.points[0] == (nodes["brief"].x + nodes["brief"].width, line.points[0][1])
    assert line.points[-1][0] == nodes["design"].x


def test_overlapping_roadmap_items_go_to_separate_rows() -> None:
    """Items in one lane that overlap in time are stacked; others share a row."""
    nodes = {node.id: node for node in diagrams.layout(raw_of(ROADMAP)).nodes}
    assert nodes["l0i0"].y == nodes["l0i1"].y
    assert nodes["l0i2"].y > nodes["l0i1"].y


def test_task_past_the_last_period_is_refused() -> None:
    """A bar that runs out of the periods fails with a message."""
    raw = raw_of(GANTT)
    raw["tasks"][-1]["length"] = 3
    with pytest.raises(SpecError, match="only 8"):
        diagrams.layout(raw)


def test_task_that_starts_before_its_dependency_ends_is_refused() -> None:
    """An 'after' that starts too early fails; a misspelt one gets a suggestion."""
    raw = raw_of(GANTT)
    raw["tasks"][2]["start"] = 2
    with pytest.raises(SpecError, match="starts before"):
        diagrams.layout(raw)
    raw = raw_of(GANTT)
    raw["tasks"][1]["after"] = "brif"
    with pytest.raises(SpecError, match="brief"):
        diagrams.layout(raw)
