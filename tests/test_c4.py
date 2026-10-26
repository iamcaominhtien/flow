"""Tests for the C4 diagram: kinds, levels, the opened box, spacing, lines and the round trip."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"
CONTEXT = EXAMPLES / "delivery-c4-context.spec.json"
CONTAINER = EXAMPLES / "delivery-c4-container.spec.json"
COMPONENT = EXAMPLES / "delivery-c4-component.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, import_drawio, render_drawio, render_html, scene  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.model import FrameVariant, Role, Scene, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402

COLUMN_PITCH_PX = 520
ROW_PITCH_PX = 270
MIN_LINE_PX = 240


def raw_of(path: Path) -> dict:
    """Load a spec as a fresh dictionary.

    Args:
        path: The spec file.

    Returns:
        The parsed spec, safe to modify.
    """
    return copy.deepcopy(json.loads(path.read_text()))


def drawn(path: Path) -> Scene:
    """Lay out an example, finding the level above in the examples folder.

    Args:
        path: The spec file.

    Returns:
        The scene.
    """
    return diagrams.layout(raw_of(path), EXAMPLES)


@pytest.mark.parametrize("path", [CONTEXT, CONTAINER, COMPONENT])
def test_examples_have_no_errors_and_draw_in_both_formats(path: Path) -> None:
    """Each level passes the checks and renders to HTML and draw.io."""
    found = check_scene(drawn(path))
    assert [f.message for f in found if f.severity is Severity.ERROR] == []
    assert "<mxGraphModel" in render_drawio.render(drawn(path))
    assert "[Person]" in render_html.render(drawn(path)) or path is COMPONENT


def test_every_box_has_the_standard_size_and_the_system_is_larger() -> None:
    """Boxes are 280 x 132; the system box of level 1 is 360 x 150."""
    nodes = {node.id: node for node in drawn(CONTEXT).nodes}
    assert (nodes["platform"].width, nodes["platform"].height) == (360, 150)
    others = [node for name, node in nodes.items() if name != "platform"]
    assert {(node.width, node.height) for node in others} == {(280, 132)}


def test_kinds_decide_the_shape_and_the_border() -> None:
    """A person has round corners, an external system a dashed border, a system a solid one."""
    nodes = {node.id: node for node in drawn(CONTEXT).nodes}
    assert nodes["customer"].shape is Shape.C4_PERSON
    assert nodes["psp"].dashed
    assert not nodes["platform"].dashed
    assert nodes["platform"].shape is Shape.C4_BOX


def test_a_box_has_a_type_line_and_a_sentence() -> None:
    """The mono line reads [Kind: technology]; the sentence is the detail."""
    nodes = {node.id: node for node in drawn(CONTAINER).nodes}
    assert nodes["order"].technology == "[Container: Kotlin, Spring]"
    assert nodes["order"].detail == ("Checkout, order status, events.",)
    assert nodes["customer"].technology == "[Person]"
    assert nodes["psp"].technology == "[External system]"
    assert nodes["db"].technology == "[Container: PostgreSQL]"


def test_a_box_without_icon_or_tone_gets_those_of_its_kind() -> None:
    """The colour convention: a person is blue, a system violet, an external system grey."""
    raw = raw_of(CONTEXT)
    for element in raw["elements"]:
        element.pop("icon", None)
        element.pop("tone", None)
    nodes = {node.id: node for node in diagrams.layout(raw).nodes}
    assert nodes["customer"].tone.value == "blue"
    assert nodes["platform"].tone.value == "violet"
    assert nodes["psp"].tone.value == "gray"
    assert nodes["psp"].icon == "cloud"


def test_level_one_has_no_frame_and_levels_two_and_three_open_one_box() -> None:
    """The opened box becomes a dashed frame whose name is its label and its kind."""
    assert drawn(CONTEXT).frames == ()
    (platform,) = drawn(CONTAINER).frames
    assert platform.variant is FrameVariant.OPENED
    assert platform.label == "Delivery platform [Software system]"
    (order,) = drawn(COMPONENT).frames
    assert order.label == "Order service [Container]"


def test_neighbours_stay_outside_the_frame_and_keep_what_level_one_said() -> None:
    """People and outside systems sit outside the frame and keep name, tone and icon."""
    result = drawn(CONTAINER)
    frame = result.frames[0]
    nodes = {node.id: node for node in result.nodes}
    for name in ("customer", "psp", "map", "sms"):
        node = nodes[name]
        assert (
            node.x + node.width <= frame.x
            or node.x >= frame.x + frame.width
            or node.y + node.height <= frame.y
        )
    above = {node.id: node for node in drawn(CONTEXT).nodes}
    assert nodes["customer"].text == above["customer"].text
    assert nodes["customer"].tone == above["customer"].tone
    assert nodes["psp"].icon == above["psp"].icon


def test_columns_are_520_and_rows_270_apart_with_240_between_boxes() -> None:
    """The grid of the design: 520 px between columns, 270 between rows, 240 px of line."""
    nodes = {node.id: node for node in drawn(CONTAINER).nodes}
    assert nodes["tablet"].x - nodes["custapp"].x == COLUMN_PITCH_PX
    assert nodes["custapp"].y - nodes["customer"].y == ROW_PITCH_PX
    assert nodes["tablet"].x - (nodes["custapp"].x + nodes["custapp"].width) >= MIN_LINE_PX


def test_main_route_is_blue_and_events_are_violet() -> None:
    """The order is the blue route; the event stream is violet."""
    edges = {(e.source, e.target): e for e in drawn(CONTAINER).edges}
    assert edges[("custapp", "gateway")].role is Role.MAIN
    assert edges[("bus", "notify")].role is Role.DATA
    assert edges[("tablet", "gateway")].role is Role.NEXT


def test_a_label_is_a_verb_phrase_and_the_protocol() -> None:
    """On level 2 the label carries the protocol after the verb phrase."""
    labels = {(e.source, e.target): e.label.text for e in drawn(CONTAINER).edges if e.label}
    assert labels[("courierapp", "map")] == "Shows routes using, SDK"
    assert labels[("custapp", "gateway")] == "HTTPS, JSON"
    assert drawn(CONTEXT).edges[0].label.text == "Orders food using"


def test_routes_have_at_most_two_bends() -> None:
    """Lines are orthogonal with at most two bends."""
    for path in (CONTEXT, CONTAINER, COMPONENT):
        for edge in drawn(path).edges:
            assert len(edge.points) <= 4


def test_mixing_levels_is_refused() -> None:
    """A component in a container diagram, stated as level 2, is refused."""
    raw = raw_of(CONTAINER)
    raw["level"] = 2
    raw["elements"].append({"id": "extra", "label": "Extra", "kind": "component", "at": [5, 5]})
    with pytest.raises(SpecError, match="never mix levels"):
        diagrams.layout(raw, EXAMPLES)


def test_level_two_lines_between_containers_need_a_protocol() -> None:
    """A relation between two containers without a protocol says how to fix it."""
    raw = raw_of(CONTAINER)
    del raw["relations"][8]["protocol"]
    with pytest.raises(SpecError, match="protocol"):
        diagrams.layout(raw, EXAMPLES)


def test_the_opened_element_must_exist_on_the_level_above() -> None:
    """Opening a box that is not in the level above fails and lists the choices."""
    raw = raw_of(CONTAINER)
    raw["opens"]["element"] = "nothing"
    with pytest.raises(SpecError, match="platform"):
        diagrams.layout(raw, EXAMPLES)


def test_c4_is_plain_only() -> None:
    """The illustrated style is refused."""
    raw = raw_of(CONTEXT)
    raw["style"] = "illustrated"
    with pytest.raises(SpecError, match="plain"):
        diagrams.layout(raw)


def test_a_context_diagram_needs_exactly_one_system() -> None:
    """Level 1 draws one software system."""
    raw = raw_of(CONTEXT)
    raw["elements"] = [e for e in raw["elements"] if e["kind"] != "system"]
    raw["relations"] = []
    with pytest.raises(SpecError, match="one software system"):
        diagrams.layout(raw)


def test_too_many_boxes_are_refused() -> None:
    """More than 15 boxes in the frame: zoom into a part instead."""
    raw = raw_of(CONTAINER)
    raw["elements"] += [
        {"id": f"extra{i}", "label": f"Extra {i}", "kind": "container", "at": [9, i]}
        for i in range(6)
    ]
    with pytest.raises(SpecError, match="too many"):
        diagrams.layout(raw, EXAMPLES)


def test_scene_file_round_trip_keeps_the_type_line() -> None:
    """Writing a scene and reading it back keeps the technology line and the sentence."""
    original = drawn(COMPONENT)
    again = scene.parse(scene.dump(original))
    assert [n.technology for n in again.nodes] == [n.technology for n in original.nodes]
    assert [n.detail for n in again.nodes] == [n.detail for n in original.nodes]


def test_drawio_round_trip_keeps_name_type_line_and_sentence(tmp_path: Path) -> None:
    """Importing the draw.io file gives each box back its three lines and its shape."""
    original = drawn(CONTAINER)
    path = tmp_path / "out.drawio"
    path.write_text(render_drawio.render(original))
    result = import_drawio.convert(path).scene
    nodes = {node.id: node for node in result.nodes}
    order = nodes["node-order"]
    assert order.shape is Shape.C4_BOX
    assert order.text == ("Order service",)
    assert order.technology == "[Container: Kotlin, Spring]"
    assert order.detail == ("Checkout, order status, events.",)
    assert nodes["node-customer"].shape is Shape.C4_PERSON
    assert [f.variant for f in result.frames] == [FrameVariant.OPENED]
