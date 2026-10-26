"""Tests for the data flow diagram: shapes, numbering, forbidden links, balancing, layout."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.model import FrameVariant, Role, Scene, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402

LEVELS = (
    "delivery-dfd-context",
    "delivery-dfd-level1",
    "delivery-dfd-level2",
    "delivery-dfd-context-illustrated",
    "delivery-dfd-level1-illustrated",
    "delivery-dfd-level2-illustrated",
)
PAIR_GAP_PX = 60
COLUMN_PITCH_PX = 640
ROW_PITCH_PX = 400


def raw_example(name: str) -> dict:
    """Load an example spec as a fresh dictionary."""
    return copy.deepcopy(json.loads((EXAMPLES / f"{name}.spec.json").read_text()))


def draw(raw: dict) -> Scene:
    """Lay out a spec; a level 2 spec finds the level above in the examples folder."""
    return diagrams.layout(raw, EXAMPLES)


def small(**changes: object) -> dict:
    """Return a small valid spec: a customer, a process and a store, with the given changes."""
    raw = {
        "type": "dfd",
        "elements": [
            {"id": "c", "label": "Customer", "kind": "external"},
            {"id": "p", "label": "Take order"},
            {"id": "s", "label": "Orders", "kind": "store"},
        ],
        "flows": [
            {"from": "c", "to": "p", "label": "Order"},
            {"from": "p", "to": "s", "label": "New order"},
            {"from": "s", "to": "p", "label": "Order status"},
            {"from": "p", "to": "c", "label": "Receipt"},
        ],
    }
    raw.update(changes)
    return raw


@pytest.mark.parametrize("name", LEVELS)
def test_examples_have_no_errors_and_draw_in_both_formats(name: str) -> None:
    """Each level, plain and illustrated, passes the checks and renders to HTML and draw.io."""
    scene = draw(raw_example(name))
    findings = check_scene(scene)
    assert [f for f in findings if f.severity is Severity.ERROR] == []
    assert "<mxGraphModel" in render_drawio.render(scene)
    assert "data-id=" in render_html.render(scene)


@pytest.mark.parametrize("name", LEVELS)
def test_examples_survive_the_scene_round_trip(name: str) -> None:
    """A scene written as JSON and read back is the same scene."""
    scene = draw(raw_example(name))
    assert scene_io.parse(scene_io.dump(scene)) == scene


def test_shapes_follow_gane_sarson() -> None:
    """A process has its number in a strip, a store is open at the right, a party has an id."""
    scene = draw(raw_example("delivery-dfd-level1"))
    shapes = {node.id: node for node in scene.nodes}
    assert shapes["take"].shape is Shape.DFD_PROCESS and shapes["take"].number == "1.0"
    assert shapes["orders"].shape is Shape.DFD_STORE and shapes["orders"].number == "D1"
    assert shapes["customer"].shape is Shape.ENTITY and shapes["customer"].number == "E1"
    assert (shapes["take"].width, shapes["take"].height) == (260, 124)
    assert (shapes["customer"].width, shapes["customer"].height) == (240, 80)
    assert (shapes["orders"].width, shapes["orders"].height) == (260, 64)


def test_illustrated_boxes_are_the_larger_cards() -> None:
    """The illustrated style draws cards of the sizes of design 14 section 5."""
    scene = draw(raw_example("delivery-dfd-level1-illustrated"))
    shapes = {node.id: node for node in scene.nodes}
    assert all(node.card for node in scene.nodes)
    assert (shapes["take"].width, shapes["take"].height) == (300, 170)
    assert (shapes["customer"].width, shapes["customer"].height) == (280, 120)
    assert (shapes["orders"].width, shapes["orders"].height) == (340, 96)


def test_numbers_are_made_up_in_order_and_never_reused() -> None:
    """A number the author sets is skipped by the ones that are made up."""
    raw = small()
    raw["elements"][2]["number"] = "D1"
    raw["elements"].append({"id": "s2", "label": "Menu", "kind": "store"})
    raw["flows"] += [{"from": "p", "to": "s2", "label": "Menu item"}]
    raw["flows"] += [{"from": "s2", "to": "p", "label": "Menu entry"}]
    numbers = {node.id: node.number for node in draw(raw).nodes}
    assert numbers == {"c": "E1", "p": "1.0", "s": "D1", "s2": "D2"}


def test_a_level_0_process_is_numbered_zero_and_has_no_stores() -> None:
    """The context diagram is one process, numbered 0, with the parties around it."""
    scene = draw(raw_example("delivery-dfd-context"))
    system = next(node for node in scene.nodes if node.shape is Shape.DFD_PROCESS)
    assert system.number == "0"
    assert not [node for node in scene.nodes if node.shape is Shape.DFD_STORE]


def test_a_store_on_level_0_is_refused() -> None:
    """Level 0 shows the border only, so a store is an error."""
    raw = small(level=0)
    with pytest.raises(SpecError, match="belongs on level 1"):
        draw(raw)


@pytest.mark.parametrize(
    ("ends", "message"),
    [
        (("c", "c2"), "two external entities"),
        (("s", "s2"), "two data stores"),
        (("c", "s"), "external entity and a data store"),
        (("s", "c"), "external entity and a data store"),
    ],
)
def test_forbidden_links_are_refused_with_a_reason(ends: tuple[str, str], message: str) -> None:
    """Entity to entity, store to store and entity to store are errors that say why."""
    raw = small()
    raw["elements"] += [
        {"id": "c2", "label": "Courier", "kind": "external"},
        {"id": "s2", "label": "Menu", "kind": "store"},
    ]
    raw["flows"].append({"from": ends[0], "to": ends[1], "label": "Data"})
    with pytest.raises(SpecError, match=message):
        draw(raw)


def test_a_process_without_output_or_input_is_refused() -> None:
    """A black hole has no output; a process with no input is refused too."""
    raw = small()
    raw["elements"].append({"id": "q", "label": "Log visit"})
    raw["flows"].append({"from": "c", "to": "q", "label": "Visit"})
    with pytest.raises(SpecError, match=r"no output \(a black hole\)"):
        draw(raw)
    raw["flows"][-1] = {"from": "q", "to": "c", "label": "Visit"}
    with pytest.raises(SpecError, match="no input"):
        draw(raw)


def test_a_flow_needs_a_label() -> None:
    """Every flow carries data, so it needs a label."""
    raw = small()
    del raw["flows"][0]["label"]
    with pytest.raises(SpecError, match="needs a 'label'"):
        draw(raw)


def test_every_problem_is_listed_at_once() -> None:
    """The error message lists each rule broken, not only the first."""
    raw = small()
    raw["elements"].append({"id": "c2", "label": "Courier", "kind": "external"})
    raw["flows"].append({"from": "c", "to": "c2", "label": "Data"})
    raw["flows"].append({"from": "c", "to": "s", "label": "Data"})
    with pytest.raises(SpecError) as caught:
        draw(raw)
    assert len(caught.value.problems) == 2


def test_the_opened_process_gets_a_dashed_frame_and_numbered_children() -> None:
    """Level 2 numbers its parts 4.1, 4.2, 4.3 and frames them with the name of 4.0."""
    scene = draw(raw_example("delivery-dfd-level2"))
    frame = scene.frames[0]
    assert frame.variant is FrameVariant.OPENED and frame.label == "4.0 Deliver order"
    numbers = {node.id: node.number for node in scene.nodes}
    assert (numbers["match"], numbers["offer"], numbers["confirm"]) == ("4.1", "4.2", "4.3")
    assert numbers["courier"] == "E3" and numbers["orders"] == "D1"


def test_a_store_of_the_level_above_is_drawn_dashed() -> None:
    """The store of level 1 is shown for reference, with a dashed outline."""
    scene = draw(raw_example("delivery-dfd-level2"))
    shapes = {node.id: node for node in scene.nodes}
    assert shapes["orders"].dashed and not shapes["positions"].dashed


def test_balancing_refuses_a_flow_that_vanished() -> None:
    """Dropping a flow of the opened process is an error that names the flow."""
    raw = raw_example("delivery-dfd-level2")
    raw["flows"] = [flow for flow in raw["flows"] if flow["label"] != "Ready order"]
    with pytest.raises(SpecError, match="the flow 'Ready order' from 'Orders' into"):
        draw(raw)


def test_balancing_refuses_a_flow_that_appeared() -> None:
    """A flow to the neighbour that level 1 did not have is an error."""
    raw = raw_example("delivery-dfd-level2")
    raw["elements"].append({"id": "customer"})
    raw["flows"].append({"from": "confirm", "to": "customer", "label": "Delivery receipt"})
    with pytest.raises(SpecError, match="Delivery receipt"):
        draw(raw)


def test_balancing_accepts_a_split_flow() -> None:
    """One flow of level 1 may arrive as two parts that name it with ``of``."""
    raw = raw_example("delivery-dfd-level2")
    parts = [flow for flow in raw["flows"] if flow.get("of")]
    assert len(parts) == 2
    draw(raw)
    del parts[0]["of"]
    with pytest.raises(SpecError, match="balancing"):
        draw(raw)


def test_level_3_is_refused() -> None:
    """A level 2 spec may not open a level 2 spec."""
    raw = raw_example("delivery-dfd-level2")
    raw["opens"]["spec"] = "delivery-dfd-level2.spec.json"
    with pytest.raises(SpecError, match="do not go past level 2"):
        draw(raw)


def test_two_way_exchange_is_two_arrows_60_px_apart() -> None:
    """The flows both ways between a party and a process run side by side, 60 px apart."""
    scene = draw(raw_example("delivery-dfd-level1"))
    pair = [e for e in scene.edges if {e.source, e.target} == {"customer", "take"}]
    assert len(pair) == 2
    assert abs(pair[0].points[0][1] - pair[1].points[0][1]) == PAIR_GAP_PX
    assert all(len(edge.points) == 2 for edge in pair)


def test_boxes_sit_on_a_grid_of_640_by_400() -> None:
    """Columns are 640 px apart and rows 400 px apart, measured between box centres."""
    scene = draw(raw_example("delivery-dfd-level1"))
    centre = {n.id: (n.x + n.width / 2, n.y + n.height / 2) for n in scene.nodes}
    assert centre["pay"][0] - centre["take"][0] == COLUMN_PITCH_PX
    assert centre["cook"][1] - centre["take"][1] == 2 * ROW_PITCH_PX
    assert centre["customer"][0] - centre["take"][0] == -COLUMN_PITCH_PX


def test_routes_have_at_most_two_bends_and_cross_no_box() -> None:
    """Every flow is straight or orthogonal with at most two bends."""
    for name in LEVELS:
        scene = draw(raw_example(name))
        assert all(len(edge.points) <= 4 for edge in scene.edges), name
        assert not [f for f in check_scene(scene) if f.code.value == "line-through-node"], name


def test_main_flows_are_blue_and_status_flows_violet() -> None:
    """The main journey uses the main role, a status flow the data role, the rest the ink."""
    scene = draw(raw_example("delivery-dfd-level1"))
    roles = {edge.source + ">" + edge.target: edge.role for edge in scene.edges}
    assert roles["take>pay"] is Role.MAIN
    assert roles["orders>take"] is Role.DATA
    assert roles["take>customer"] is Role.NEXT


def test_a_store_that_is_only_written_is_a_warning() -> None:
    """Data that is stored but never used is reported, not refused."""
    raw = small()
    raw["flows"] = [flow for flow in raw["flows"] if flow["label"] != "Order status"]
    codes = [finding.code.value for finding in check_scene(draw(raw))]
    assert "dfd-store-one-way" in codes


def test_a_level_with_too_few_processes_is_a_warning() -> None:
    """Level 1 asks for four to seven processes; one process is allowed but reported."""
    codes = [finding.code.value for finding in check_scene(draw(small()))]
    assert "dfd-process-count" in codes
