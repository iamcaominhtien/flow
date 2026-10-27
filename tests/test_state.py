"""Tests for the state diagram: marks, transitions and errors."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
ORDER = ROOT / "examples" / "order-state.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.model import Role, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


def order_raw() -> dict:
    """Load the order example as a fresh dictionary.

    Returns:
        The parsed spec, safe to modify.
    """
    return copy.deepcopy(json.loads(ORDER.read_text()))


def test_example_has_no_errors() -> None:
    """The order example passes the checks with no error."""
    scene = diagrams.layout(order_raw())
    assert [f for f in check_scene(scene) if f.severity is Severity.ERROR] == []


def test_kind_decides_the_shape() -> None:
    """Start and end marks and the failure state get their own outlines."""
    shapes = {node.id: node.shape for node in diagrams.layout(order_raw()).nodes}
    assert shapes["begin"] is Shape.INITIAL
    assert shapes["done"] is Shape.FINAL
    assert shapes["cancelled"] is Shape.PROCESS
    assert shapes["paid"] is Shape.PROCESS


def test_main_transitions_have_the_main_role() -> None:
    """The transitions flagged main follow the main role."""
    edges = [edge for edge in diagrams.layout(order_raw()).edges if edge.role is Role.MAIN]
    assert len(edges) == 3


def test_unknown_state_is_rejected_with_a_suggestion() -> None:
    """A transition to a misspelt state fails and names the likely one."""
    raw = order_raw()
    raw["transitions"][1]["to"] = "pad"
    with pytest.raises(SpecError, match="paid"):
        diagrams.layout(raw)


def test_start_and_end_marks_keep_their_own_size() -> None:
    """A mark is not widened to its column; a stretched circle would be an ellipse in draw.io."""
    nodes = {node.id: node for node in diagrams.layout(order_raw()).nodes}
    for name in ("begin", "done"):
        assert nodes[name].width == nodes[name].height
