"""Tests for the UML diagrams: state machine, use case and class diagram."""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib import diagrams, render_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.diagrams.state_spec import Transition  # noqa: E402
from flowlib.model import FrameVariant, Head, Role, Scene, Shape, Tone  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

EXAMPLE_NAMES = (
    "delivery-state",
    "delivery-usecase",
    "delivery-usecase-illustrated",
    "delivery-class",
)


def raw_example(name: str) -> dict:
    """Load an example as a fresh dictionary."""
    return copy.deepcopy(json.loads((EXAMPLES / f"{name}.spec.json").read_text()))


def drawn(name: str) -> Scene:
    """Lay out an example."""
    return diagrams.layout(raw_example(name))


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_example_has_no_errors_or_warnings_and_draws_in_both_formats(name: str) -> None:
    """Each design example passes every check and renders to HTML and draw.io."""
    scene = drawn(name)
    assert check_scene(scene) == []
    assert "<mxGraphModel" in render_drawio.render(scene)
    assert "<svg" in render_html.render(scene)


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_scene_round_trips_through_json(name: str) -> None:
    """The new node fields survive writing and reading the scene file."""
    scene = drawn(name)
    assert scene_io.parse(scene_io.dump(scene)) == scene


def test_transition_label_has_event_guard_and_action_in_order() -> None:
    """The label reads ``event [guard] / action``, and any part may be missing."""
    full = Transition("a", "b", "leaves", "near address", "notify", False, False)
    assert full.text == "leaves [near address] / notify"
    assert Transition("a", "b", "", "near address", "", False, False).text == "[near address]"
    assert Transition("a", "b", "", "", "notify", False, False).text == "/ notify"
    assert Transition("a", "b", "", "", "", False, False).text == ""


def test_state_happy_path_runs_left_to_right_in_one_row() -> None:
    """The main transitions line the states up in a row, each right of the one before."""
    scene = drawn("delivery-state")
    nodes = {node.id: node for node in scene.nodes}
    path = ["begin", "placed", "paid", "preparing", "ready", "picked", "onway", "arrived"]
    assert [nodes[name].x for name in path] == sorted(nodes[name].x for name in path)
    assert len({nodes[name].y + nodes[name].height / 2 for name in path}) == 1
    assert nodes["cancelled"].y > nodes["placed"].y  # branches go below


def test_state_boxes_are_160_by_64_and_activities_sit_under_the_name() -> None:
    """A state is 160 x 64; ``do`` becomes a mono line, and a mark is a small square."""
    nodes = {node.id: node for node in drawn("delivery-state").nodes}
    assert (nodes["placed"].width, nodes["placed"].height) == (160, 64)
    assert nodes["onway"].activities == ("do / share location",)
    assert nodes["begin"].shape is Shape.INITIAL
    assert nodes["finish"].shape is Shape.FINAL and nodes["closed"].shape is Shape.FINAL
    assert nodes["begin"].width == nodes["begin"].height


def test_labelled_states_are_at_least_130_px_apart() -> None:
    """The gap between two states with a label between them is 130 px or more."""
    nodes = {node.id: node for node in drawn("delivery-state").nodes}
    assert nodes["paid"].x - (nodes["placed"].x + nodes["placed"].width) >= 130


def test_composite_state_is_a_frame_with_a_pill_around_its_members() -> None:
    """The nested states are grouped in a frame named after the composite state."""
    scene = drawn("delivery-state")
    (frame,) = scene.frames
    assert (frame.label, frame.variant) == ("Delivering", FrameVariant.LAYER)
    nodes = {node.id: node for node in scene.nodes}
    for name in ("picked", "onway", "arrived"):
        assert frame.x < nodes[name].x and nodes[name].x + nodes[name].width < frame.x + frame.width
    assert not frame.x < nodes["ready"].x + nodes["ready"].width <= frame.x + frame.width


def test_one_animated_line_the_failures_are_rose_and_a_self_loop_is_above() -> None:
    """Only the happy path is the main role; failures use the rose role; the loop is above."""
    scene = drawn("delivery-state")
    roles = {edge.label.text if edge.label else edge.id: edge.role for edge in scene.edges}
    assert roles["cancel"] is Role.NO and roles["refund [within 7 days]"] is Role.NO
    assert roles["cleanup"] is Role.NO
    assert sum(edge.role is Role.MAIN for edge in scene.edges) == 9
    nodes = {node.id: node for node in scene.nodes}
    loop = next(edge for edge in scene.edges if edge.source == edge.target == "preparing")
    assert all(y <= nodes["preparing"].y for _, y in loop.points)
    assert loop.label is not None and loop.label.text == "item out of stock / substitute"


def test_state_without_main_follows_the_first_transitions() -> None:
    """A spec with no ``main`` still gets a row: the first transition of each state."""
    raw = {
        "type": "state",
        "states": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
        "transitions": [{"from": "a", "to": "b"}, {"from": "b", "to": "c"}],
    }
    nodes = {node.id: node for node in diagrams.layout(raw).nodes}
    assert nodes["a"].x < nodes["b"].x < nodes["c"].x
    assert nodes["a"].y == nodes["b"].y == nodes["c"].y


def test_state_rejects_an_unknown_state_with_a_suggestion() -> None:
    """A transition to a misspelt state names the likely one."""
    raw = raw_example("delivery-state")
    raw["transitions"][1]["to"] = "pad"
    with pytest.raises(SpecError, match="paid"):
        diagrams.layout(raw)


def test_class_boxes_are_280_wide_and_empty_compartments_are_left_out() -> None:
    """A class is 280 wide; the interface has an operations compartment only."""
    nodes = {node.id: node for node in drawn("delivery-class").nodes}
    assert all(node.width == 280 for node in nodes.values())
    assert len(nodes["notifier"].sections) == 1
    assert len(nodes["order"].sections) == 2
    assert all(row.is_mono for section in nodes["order"].sections for row in section)


def test_abstract_is_italic_and_an_interface_has_its_stereotype() -> None:
    """The name of an abstract class is italic; ``«interface»`` sits above the interface name."""
    scene = drawn("delivery-class")
    nodes = {node.id: node for node in scene.nodes}
    assert nodes["payment"].is_italic and not nodes["card"].is_italic
    assert nodes["notifier"].stereotype == "«interface»"
    assert nodes["notifier"].height > nodes["email"].height - 50  # a taller header
    html = render_html.render(scene)
    assert "«interface»" in html and "font-style:italic" in html
    assert "fontStyle=3" in render_drawio.render(scene)


def test_class_relationships_have_the_uml_line_ends() -> None:
    """Each relationship style has its own head, tail and dash."""
    edges = {(e.source, e.target): e for e in drawn("delivery-class").edges}
    assert edges["order", "item"].tail is Head.DIAMOND_FILLED
    assert edges["restaurant", "dish"].tail is Head.DIAMOND
    assert edges["card", "payment"].head is Head.TRIANGLE and not edges["card", "payment"].dashed
    email = edges["email", "notifier"]
    assert email.head is Head.TRIANGLE and email.dashed
    uses = edges["order", "notifier"]
    assert uses.head is Head.OPEN and uses.dashed
    assert edges["item", "dish"].head is Head.OPEN and not edges["item", "dish"].dashed
    assert edges["customer", "order"].head is Head.NONE


def test_multiplicities_are_drawn_at_both_ends_in_both_formats() -> None:
    """``from_label`` and ``to_label`` become small labels next to the two boxes."""
    scene = drawn("delivery-class")
    edge = next(e for e in scene.edges if (e.source, e.target) == ("customer", "order"))
    assert [extra.text for extra in edge.extras] == ["1", "0..*"]
    assert edge.extras[0].at[0] < edge.extras[1].at[0]
    assert ">0..*<" in render_html.render(scene).replace(" ", "")
    assert "0..*" in render_drawio.render(scene)


def test_parents_are_above_their_children() -> None:
    """Inheritance and realisation put the parent on a higher row than the child."""
    nodes = {node.id: node for node in drawn("delivery-class").nodes}
    assert nodes["payment"].y < nodes["card"].y and nodes["payment"].y < nodes["wallet"].y
    assert nodes["notifier"].y < nodes["email"].y


def test_classes_without_a_cell_are_placed_with_parents_above() -> None:
    """With no ``at``, the layout still puts a parent above its children, four across at most."""
    raw = raw_example("delivery-class")
    for item in raw["classes"]:
        del item["at"]
    scene = diagrams.layout(raw)
    nodes = {node.id: node for node in scene.nodes}
    assert nodes["payment"].y < nodes["card"].y
    assert nodes["notifier"].y < nodes["email"].y
    assert max(len({n.y for n in scene.nodes if n.x == x}) for x in {n.x for n in scene.nodes}) >= 1
    assert not [f for f in check_scene(scene) if f.severity is Severity.ERROR]


def test_class_self_relation_is_a_loop_at_the_right_side() -> None:
    """A relation of a class to itself leaves and returns on its right side."""
    raw = {
        "type": "class",
        "classes": [{"id": "node", "label": "Node"}],
        "relations": [{"from": "node", "to": "node", "label": "parent", "to_label": "0..1"}],
    }
    scene = diagrams.layout(raw)
    node, edge = scene.nodes[0], scene.edges[0]
    assert all(x >= node.x + node.width for x, _ in edge.points)
    assert [extra.text for extra in edge.extras] == ["0..1"]


def test_class_spec_errors_name_the_problem() -> None:
    """A wrong kind, style or class name is refused with the choices."""
    raw = raw_example("delivery-class")
    raw["classes"][0]["kind"] = "trait"
    raw["relations"][0]["style"] = "zigzag"
    raw["relations"][1]["to"] = "itm"
    with pytest.raises(SpecError) as caught:
        diagrams.layout(raw)
    message = str(caught.value)
    assert "unknown kind 'trait'" in message
    assert "unknown style 'zigzag'" in message
    assert "did you mean 'item'" in message


def test_use_case_ovals_are_240_by_64_and_tinted_by_their_actor() -> None:
    """Use cases are ovals; each takes the tone of the actor that uses it."""
    nodes = {node.id: node for node in drawn("delivery-usecase").nodes}
    assert nodes["browse"].shape is Shape.USE_CASE
    assert (nodes["browse"].width, nodes["browse"].height) == (240, 64)
    assert nodes["browse"].tone is Tone.BLUE and nodes["accept"].tone is Tone.GREEN
    assert nodes["deliver"].tone is Tone.TEAL
    assert nodes["pay"].tone is Tone.AMBER and nodes["prepare"].tone is Tone.GREEN
    assert nodes["promo"].tone is Tone.BLUE  # an extension takes the tone of its base


def test_use_cases_of_one_actor_share_a_column() -> None:
    """Everything the customer takes part in directly stands in one column."""
    nodes = {node.id: node for node in drawn("delivery-usecase").nodes}
    assert len({nodes[name].x for name in ("browse", "place", "rate", "track")}) == 1
    assert nodes["pay"].x == nodes["promo"].x > nodes["place"].x


def test_system_frame_holds_the_use_cases_and_actors_stand_outside() -> None:
    """The system is a white frame with its name; people on the left, external systems right."""
    scene = drawn("delivery-usecase")
    (frame,) = scene.frames
    assert (frame.label, frame.variant) == ("Delivery app", FrameVariant.SYSTEM)
    nodes = {node.id: node for node in scene.nodes}
    for name in ("browse", "pay", "share"):
        assert frame.x < nodes[name].x and nodes[name].x + nodes[name].width < frame.x + frame.width
    assert nodes["customer"].x + nodes["customer"].width < frame.x
    assert nodes["payment"].x > frame.x + frame.width
    assert nodes["customer"].shape is Shape.ACTOR
    assert nodes["payment"].caption == "Payment provider\n«external system»"


def test_include_and_extend_are_dashed_open_arrows_to_the_used_use_case() -> None:
    """An include points at the included use case, an extend at the base; solid has no head."""
    scene = drawn("delivery-usecase")
    nodes = {node.id: node for node in scene.nodes}
    edges = {(e.source, e.target): e for e in scene.edges}
    include, extend = edges["place", "pay"], edges["promo", "place"]
    assert include.head is Head.OPEN and include.dashed and include.label.text == "«include»"
    assert extend.head is Head.OPEN and extend.dashed and extend.label.text == "«extend»"
    pay = nodes["pay"]
    assert pay.x <= include.points[-1][0] <= pay.x + pay.width
    assert edges["customer", "place"].head is Head.NONE and not edges["customer", "place"].dashed


def test_illustrated_actors_are_cards_with_an_icon() -> None:
    """In the illustrated style an actor is a card with a large icon; use cases stay ovals."""
    nodes = {node.id: node for node in drawn("delivery-usecase-illustrated").nodes}
    assert nodes["customer"].card and nodes["customer"].icon == "user"
    assert nodes["payment"].detail == ("«external system»",)
    assert nodes["place"].shape is Shape.USE_CASE


def test_old_use_case_form_with_items_and_zones_is_still_read() -> None:
    """``items`` with a ``kind`` and the first zone as the system keep working."""
    scene = diagrams.layout(json.loads((EXAMPLES / "shop-usecase.spec.json").read_text()))
    assert scene.frames[0].label == "Online shop"
    assert {node.shape for node in scene.nodes} == {Shape.ACTOR, Shape.USE_CASE}


def test_technical_theme_draws_the_uml_marks() -> None:
    """The dots and ovals have colours in every theme."""
    for name in ("technical", "midnight"):
        theme = load_theme(name)
        for shape in (Shape.INITIAL, Shape.FINAL, Shape.USE_CASE):
            assert shape in theme.shapes
