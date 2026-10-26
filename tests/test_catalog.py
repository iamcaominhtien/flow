"""Tests for the data-driven graph types: C4, cloud, use case, BPMN, class and screen flow."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"
CASES = {
    "delivery-c4.spec.json": "c4",
    "web-cloud.spec.json": "cloud",
    "shop-usecase.spec.json": "usecase",
    "refund-bpmn.spec.json": "bpmn",
    "shapes-class.spec.json": "class",
    "signup-screen.spec.json": "screen",
    "order-pools-bpmn.spec.json": "bpmn",
    "order-fulfilment-bpmn.spec.json": "bpmn",
}

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio, render_html  # noqa: E402
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
    raw = raw_example("refund-bpmn.spec.json")
    raw["elements"][0]["kind"] = "robot"
    raw["flows"][0]["style"] = "zigzag"
    with pytest.raises(SpecError) as caught:
        diagrams.layout(raw)
    message = str(caught.value)
    assert "unknown kind 'robot'" in message
    assert "unknown style 'zigzag'" in message


def test_a_link_to_a_missing_item_gets_a_suggestion() -> None:
    """A misspelt end of a link names the likely item."""
    raw = raw_example("refund-bpmn.spec.json")
    raw["flows"][0]["to"] = "chek"
    with pytest.raises(SpecError, match="check"):
        diagrams.layout(raw)


def test_multiplicity_label_is_drawn_in_html() -> None:
    """The end label of a class relation appears as a chip in the HTML page."""
    scene = diagrams.layout(raw_example("shapes-class.spec.json"))
    assert [extra.text for edge in scene.edges for extra in edge.extras] == ["*"]
    assert ">*<" in render_html.render(scene).replace(" ", "")


def test_a_line_leaves_an_actor_below_its_name() -> None:
    """The line from an actor starts under the caption, not through the name."""
    scene = diagrams.layout(raw_example("shop-usecase.spec.json"))
    shopper = next(node for node in scene.nodes if node.id == "shopper")
    line = next(edge for edge in scene.edges if edge.source == "shopper")
    assert line.points[0][1] > shopper.y + shopper.height


def test_bpmn_event_and_gateway_markers_and_pools() -> None:
    """Timer, message and parallel kinds get a marker icon; zones become swimlanes."""
    scene = diagrams.layout(raw_example("order-pools-bpmn.spec.json"))
    nodes = {node.id: node for node in scene.nodes}
    assert nodes["wait"].icon == "clock"
    assert nodes["split"].icon == "plus"
    assert nodes["ok"].icon == "x"
    assert nodes["wait"].shape is Shape.INTERMEDIATE
    assert [frame.label for frame in scene.frames] == ["Shop", "Bank"]
    assert nodes["charge"].x > nodes["pay"].x
    message = next(edge for edge in scene.edges if edge.source == "pay" and edge.target == "charge")
    assert message.dashed
    assert message.tail is Head.DOT


def test_an_item_without_a_zone_is_refused_when_zones_are_pools() -> None:
    """In a BPMN diagram with pools, an element outside every pool fails."""
    raw = raw_example("order-pools-bpmn.spec.json")
    del raw["elements"][0]["zone"]
    with pytest.raises(SpecError, match="needs a 'zone'"):
        diagrams.layout(raw)


def test_branches_of_one_gateway_in_a_pool_sit_side_by_side() -> None:
    """The two tasks after a parallel split share a rank and are stacked across the flow."""
    scene = diagrams.layout(raw_example("order-pools-bpmn.spec.json"))
    nodes = {node.id: node for node in scene.nodes}
    assert nodes["pay"].x == nodes["pack"].x
    assert nodes["pay"].y != nodes["pack"].y
    assert nodes["pay"].y + nodes["pay"].height < nodes["pack"].y


def test_start_and_end_events_keep_their_label_as_a_caption() -> None:
    """A label on a start or end event goes under the circle, not inside it."""
    raw = raw_example("refund-bpmn.spec.json")
    raw["elements"][0]["label"] = "Request arrives"
    start = next(node for node in diagrams.layout(raw).nodes if node.id == "begin")
    assert start.caption == "Request arrives"
    assert start.text == ()


def test_findings_name_the_items_they_mention() -> None:
    """A check message says which labels the quoted ids stand for."""
    raw = raw_example("order-pools-bpmn.spec.json")
    scene = diagrams.layout(raw)
    node = scene.nodes[1]
    crowded = scene.__class__(
        scene.width,
        scene.height,
        scene.title,
        scene.description,
        scene.frames,
        (node, node.__class__(**{**node.__dict__, "id": "twin"})),
        (),
    )
    messages = [finding.message for finding in check_scene(crowded)]
    assert any(f"'{node.id}' (Take the order)" in message for message in messages)


def test_at_on_some_items_only_is_refused_not_a_crash() -> None:
    """Setting 'at' on one element but not the others fails with a message naming the rest."""
    raw = raw_example("refund-bpmn.spec.json")
    raw["elements"][0]["at"] = [0, 0]
    with pytest.raises(SpecError, match="set it on all or none"):
        diagrams.layout(raw)
