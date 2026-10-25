"""Tests for the data-driven graph types: DFD, C4, cloud, use case, BPMN, class and screen flow."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"
CASES = {
    "order-dfd.spec.json": "dfd",
    "delivery-c4.spec.json": "c4",
    "web-cloud.spec.json": "cloud",
    "shop-usecase.spec.json": "usecase",
    "refund-bpmn.spec.json": "bpmn",
    "shapes-class.spec.json": "class",
    "signup-screen.spec.json": "screen",
}

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.model import Head, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


def raw_example(name: str) -> dict:
    """Load an example as a fresh dictionary.

    Args:
        name: The example file name.

    Returns:
        The parsed spec, safe to modify.
    """
    return copy.deepcopy(json.loads((EXAMPLES / name).read_text()))


@pytest.mark.parametrize("name", CASES)
def test_example_has_no_errors_and_draws_in_both_formats(name: str) -> None:
    """Each example passes the checks and renders to draw.io."""
    assert raw_example(name)["type"] == CASES[name]
    scene = diagrams.layout(raw_example(name))
    assert [f for f in check_scene(scene) if f.severity is Severity.ERROR] == []
    assert "<mxGraphModel" in render_drawio.render(scene)


def test_class_sections_hold_attributes_then_methods() -> None:
    """A class is a table with an attribute section and a method section."""
    scene = diagrams.layout(raw_example("shapes-class.spec.json"))
    circle = next(node for node in scene.nodes if node.id == "circle")
    assert circle.shape is Shape.TABLE
    assert [row.left for row in circle.sections[1]] == ["+area(): float"]


def test_uml_styles_set_the_line_ends() -> None:
    """Inheritance has a triangle head; aggregation has a hollow diamond at the whole."""
    scene = diagrams.layout(raw_example("shapes-class.spec.json"))
    edges = {edge.source: edge for edge in scene.edges}
    assert edges["circle"].head is Head.TRIANGLE
    assert edges["canvas"].tail is Head.DIAMOND


def test_bpmn_gateway_is_a_diamond_without_label_text_by_default() -> None:
    """A BPMN gateway is a decision shape and a start mark carries no text."""
    scene = diagrams.layout(raw_example("refund-bpmn.spec.json"))
    shapes = {node.id: node for node in scene.nodes}
    assert shapes["ok"].shape is Shape.DECISION
    assert shapes["begin"].text == ()


def test_actor_label_goes_under_the_figure() -> None:
    """A person in C4 keeps its name as a caption, not as text over the figure."""
    scene = diagrams.layout(raw_example("delivery-c4.spec.json"))
    customer = next(node for node in scene.nodes if node.id == "customer")
    assert customer.caption == "Customer"
    assert customer.text == ()


def test_unknown_kind_and_style_are_refused() -> None:
    """A wrong kind or line style fails and lists the choices."""
    raw = raw_example("order-dfd.spec.json")
    raw["elements"][0]["kind"] = "robot"
    raw["flows"][0]["style"] = "zigzag"
    with pytest.raises(SpecError) as caught:
        diagrams.layout(raw)
    message = str(caught.value)
    assert "unknown kind 'robot'" in message
    assert "unknown style 'zigzag'" in message


def test_a_link_to_a_missing_item_gets_a_suggestion() -> None:
    """A misspelt end of a link names the likely item."""
    raw = raw_example("order-dfd.spec.json")
    raw["flows"][0]["to"] = "procs"
    with pytest.raises(SpecError, match="proc"):
        diagrams.layout(raw)
