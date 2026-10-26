"""Tests for the concept diagram: a centre with items on a ring."""

import copy
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLE = ROOT / "examples" / "payments-concept.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


def raw_example() -> dict:
    """Load the example as a fresh dictionary.

    Returns:
        The parsed spec, safe to modify.
    """
    return copy.deepcopy(json.loads(EXAMPLE.read_text()))


def test_example_has_no_errors_and_draws_in_draw_io() -> None:
    """The example passes the checks and renders to draw.io."""
    scene = diagrams.layout(raw_example())
    assert [f for f in check_scene(scene) if f.severity is Severity.ERROR] == []
    assert "<mxGraphModel" in render_drawio.render(scene)


def test_items_sit_on_a_ring_clockwise_from_the_top() -> None:
    """All items are at one distance from the centre; the first is straight above it."""
    scene = diagrams.layout(raw_example())
    nodes = {node.id: node for node in scene.nodes}
    hub = nodes["center"]
    hub_centre = (hub.x + hub.width / 2, hub.y + hub.height / 2)
    distances = []
    for index in range(5):
        item = nodes[f"item-{index}"]
        distances.append(math.dist(hub_centre, (item.x + item.width / 2, item.y + item.height / 2)))
    assert max(distances) - min(distances) < 1
    first = nodes["item-0"]
    assert first.x + first.width / 2 == pytest.approx(hub_centre[0])
    assert first.y < hub.y
    assert nodes["item-1"].x > hub.x


def test_each_item_has_a_spoke_without_a_head() -> None:
    """One line joins the centre to each item, with no arrowhead."""
    scene = diagrams.layout(raw_example())
    assert len(scene.edges) == 5
    assert {edge.head.value for edge in scene.edges} == {"none"}


def test_bad_specs_are_refused() -> None:
    """A missing centre, no items and too many items each fail with a message."""
    raw = raw_example()
    del raw["center"]
    with pytest.raises(SpecError, match="center"):
        diagrams.layout(raw)
    raw = raw_example()
    raw["items"] = []
    with pytest.raises(SpecError, match="between 1 and"):
        diagrams.layout(raw)
    raw = raw_example()
    raw["items"] = [{"label": f"n{i}"} for i in range(11)]
    with pytest.raises(SpecError, match="between 1 and"):
        diagrams.layout(raw)
