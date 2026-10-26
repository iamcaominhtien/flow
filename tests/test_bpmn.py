"""Tests for BPMN: event and task markers, boundary events, pools, message flows and layout."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, import_drawio, render_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.check import Code, Severity, check_scene  # noqa: E402
from flowlib.model import FrameVariant, Head, Marker, Role, Scene, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402

EXAMPLE_NAMES = ("delivery-bpmn", "order-bpmn", "refund-advanced-bpmn")
EVENT_RADIUS_PX = 20
TASK_SIZE_PX = (130, 64)
GATEWAY_WIDTH_PX = 52
BAND_PX = 38
POOL_LEFT_PX = 64
LANE_MIN_PX = 200
POOL_GAP_PX = 40
LABELLED_GAP_PX = 100


def raw_example(name: str) -> dict:
    """Load an example spec as a fresh dictionary."""
    return copy.deepcopy(json.loads((EXAMPLES / f"{name}.spec.json").read_text()))


def draw(raw: dict) -> Scene:
    """Lay out a spec."""
    return diagrams.layout(raw)


def pools(**extra: object) -> dict:
    """Return a small valid spec of two pools, with the given changes."""
    raw = {
        "type": "bpmn",
        "zones": [{"id": "a", "label": "A", "tone": "blue"}, {"id": "b", "label": "B"}],
        "elements": [
            {"id": "s", "kind": "start", "label": "Go", "zone": "a"},
            {"id": "t", "label": "Do it", "zone": "a"},
            {"id": "e", "kind": "end", "zone": "a"},
            {"id": "r", "kind": "start", "trigger": "message", "zone": "b"},
            {"id": "u", "label": "Answer", "zone": "b"},
        ],
        "flows": [
            {"from": "s", "to": "t"},
            {"from": "t", "to": "e"},
            {"from": "r", "to": "u"},
            {"from": "t", "to": "r", "style": "message", "label": "ask"},
        ],
    }
    raw.update(extra)
    return raw


def centre(node) -> float:  # noqa: ANN001
    """Return the x of the middle of a node."""
    return node.x + node.width / 2


def node_of(scene: Scene, name: str):  # noqa: ANN201
    """Return the node of an element."""
    return next(node for node in scene.nodes if node.id == name)


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_examples_have_no_errors_and_draw_in_both_formats(name: str) -> None:
    """Each example passes the checks and renders to HTML and draw.io."""
    scene = draw(raw_example(name))
    assert [f for f in check_scene(scene) if f.severity is Severity.ERROR] == []
    assert "<mxGraphModel" in render_drawio.render(scene)
    assert "<svg" in render_html.render(scene)


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_examples_survive_the_scene_round_trip(name: str) -> None:
    """A scene written as JSON and read back is the same scene."""
    scene = draw(raw_example(name))
    assert scene_io.parse(scene_io.dump(scene)) == scene


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_every_route_has_at_most_two_bends(name: str) -> None:
    """Routes are orthogonal with at most two bends."""
    scene = draw(raw_example(name))
    assert all(len(edge.points) - 2 <= 2 for edge in scene.edges)
    assert Code.BPMN_ROUTE_BENDS not in [f.code for f in check_scene(scene)]


def test_sizes_follow_the_design() -> None:
    """An event has radius 20, a task is 130 by 64 and a gateway diamond is 52 wide."""
    scene = draw(raw_example("delivery-bpmn"))
    assert (node_of(scene, "hungry").width, node_of(scene, "hungry").height) == (40, 40)
    assert node_of(scene, "hungry").width / 2 == EVENT_RADIUS_PX
    task = node_of(scene, "cook")
    assert (task.width, task.height) == TASK_SIZE_PX
    assert node_of(scene, "stock").width == GATEWAY_WIDTH_PX


def test_event_kinds_and_markers() -> None:
    """Start, message start, timer, message, end and error end are the right ring and mark."""
    scene = draw(raw_example("delivery-bpmn"))
    assert node_of(scene, "hungry").shape is Shape.START and not node_of(scene, "hungry").markers
    assert node_of(scene, "received").markers == (Marker.MESSAGE,)
    assert node_of(scene, "received").shape is Shape.START
    assert node_of(scene, "confirmed").shape is Shape.INTERMEDIATE
    assert node_of(scene, "confirmed").markers == (Marker.MESSAGE,)
    assert node_of(scene, "done").shape is Shape.END
    assert node_of(scene, "notserved").markers == (Marker.ERROR,)
    raw = pools()
    raw["elements"][0]["trigger"] = "signal"
    assert node_of(draw(raw), "s").markers == (Marker.SIGNAL,)


def test_task_types_repeats_and_sub_process_markers() -> None:
    """A task type puts a mark in the corner; repeat and sub-process marks go at the bottom."""
    raw = pools()
    kinds = ("user", "service", "send", "receive", "manual", "subprocess")
    raw["elements"][1:1] = [
        {"id": f"k_{kind}", "kind": kind, "label": kind, "zone": "a"} for kind in kinds
    ]
    raw["elements"][1]["repeat"] = "multi"
    raw["elements"][2]["repeat"] = "loop"
    scene = draw(raw)
    assert node_of(scene, "k_user").markers == (Marker.USER, Marker.MULTI_INSTANCE)
    assert node_of(scene, "k_service").markers == (Marker.SERVICE, Marker.LOOP)
    assert node_of(scene, "k_send").markers == (Marker.MESSAGE_FILLED,)
    assert node_of(scene, "k_receive").markers == (Marker.MESSAGE,)
    assert node_of(scene, "k_manual").markers == (Marker.MANUAL,)
    assert node_of(scene, "k_subprocess").markers == (Marker.SUBPROCESS,)


def test_gateway_kinds_have_their_marks() -> None:
    """Exclusive is a cross, parallel a plus, inclusive a circle, event-based a ringed pentagon."""
    raw = pools()
    raw["elements"][1:1] = [
        {"id": f"g_{kind}", "kind": kind, "zone": "a"}
        for kind in ("exclusive", "parallel", "inclusive", "event_based", "gateway")
    ]
    scene = draw(raw)
    marks = {name: node_of(scene, f"g_{name}").markers for name in ("exclusive", "parallel")}
    assert marks == {"exclusive": (Marker.CROSS,), "parallel": (Marker.PLUS,)}
    assert node_of(scene, "g_inclusive").markers == (Marker.CIRCLE,)
    assert node_of(scene, "g_event_based").markers == (Marker.EVENT_BASED,)
    assert node_of(scene, "g_gateway").markers == ()


def test_boundary_events_sit_on_the_task_edge_and_the_ring_says_if_it_interrupts() -> None:
    """A dashed ring does not interrupt; a solid one does; both sit on the task's bottom edge."""
    scene = draw(raw_example("refund-advanced-bpmn"))
    host = node_of(scene, "approve")
    nudge, escalate = node_of(scene, "nudge"), node_of(scene, "escalate")
    assert nudge.dashed and not escalate.dashed
    assert nudge.host == escalate.host == "approve"
    for event in (nudge, escalate):
        assert event.y + event.height / 2 == host.y + host.height
    assert nudge.x < escalate.x


def test_a_data_store_is_a_can_joined_by_a_dotted_line() -> None:
    """The data store is a cylinder; the flow to it is a dotted association with an open head."""
    scene = draw(raw_example("refund-advanced-bpmn"))
    assert node_of(scene, "db").shape is Shape.CYLINDER
    line = next(edge for edge in scene.edges if edge.target == "db")
    assert line.role is Role.ASSOCIATION and line.head is Head.OPEN


def test_flow_styles() -> None:
    """Main is blue, failure red, return slate; a message has a ring and a hollow head."""
    scene = draw(raw_example("order-bpmn"))
    message = next(edge for edge in scene.edges if edge.label and edge.label.text == "order")
    assert message.dashed and message.tail is Head.CIRCLE and message.head is Head.TRIANGLE
    assert message.role is Role.NEXT
    roles = {edge.role for edge in scene.edges}
    assert {Role.MAIN, Role.NO, Role.BACK} <= roles
    assert sum(1 for edge in scene.edges if edge.role is Role.MAIN) > 1


def test_pools_lanes_and_black_box() -> None:
    """Pools start 64 px from the left with a 38 px band, 40 px apart; lanes are 200 px or more."""
    scene = draw(raw_example("order-bpmn"))
    frames = {frame.id: frame for frame in scene.frames}
    assert frames["customer"].variant is FrameVariant.BLACK_BOX
    assert all(frame.x >= POOL_LEFT_PX for frame in scene.frames)
    assert frames["customer"].x == POOL_LEFT_PX
    for lane in ("orders", "warehouse", "finance"):
        assert frames[lane].variant is FrameVariant.POOL
        assert frames[lane].height >= LANE_MIN_PX
    assert frames["provider"].height >= LANE_MIN_PX
    assert frames["provider"].y - (frames["finance"].y + frames["finance"].height) == POOL_GAP_PX
    assert frames["courier"].y - (frames["provider"].y + frames["provider"].height) == POOL_GAP_PX
    assert frames["orders"].x == POOL_LEFT_PX


def test_pool_band_is_38_px_in_both_outputs() -> None:
    """The band that carries the pool name is 38 px wide in the HTML and in draw.io."""
    scene = draw(raw_example("delivery-bpmn"))
    assert f"width:{BAND_PX}px" in render_html.render(scene)
    assert f'width="{BAND_PX}"' in render_drawio.render(scene)


def test_elements_of_one_moment_share_an_x_and_messages_run_straight() -> None:
    """The two ends of a message flow share an x, so the line has no bend."""
    scene = draw(raw_example("delivery-bpmn"))
    for edge in scene.edges:
        if edge.dashed:
            assert len(edge.points) == 2
            assert edge.points[0][0] == edge.points[1][0]
    first = node_of(scene, "place")
    second = node_of(scene, "received")
    assert first.x + first.width / 2 == second.x + second.width / 2


def test_a_labelled_flow_has_a_gap_of_100_px_or_more() -> None:
    """Between an element and the one a labelled flow leads to there are 100 px or more."""
    scene = draw(raw_example("delivery-bpmn"))
    stock, confirm = node_of(scene, "stock"), node_of(scene, "confirm")
    assert confirm.x - (stock.x + stock.width) >= LABELLED_GAP_PX


def test_a_pinned_column_keeps_a_message_straight_and_apart_from_its_neighbour() -> None:
    """``column`` fixes the column of an element: here it keeps a message clear of a sibling."""
    scene = draw(raw_example("delivery-bpmn"))
    confirm, confirmed = node_of(scene, "confirm"), node_of(scene, "confirmed")
    assert centre(confirm) == centre(confirmed)
    assert centre(node_of(scene, "rejected")) < centre(confirmed)
    assert centre(node_of(scene, "reject")) == centre(node_of(scene, "rejected"))


def test_a_message_line_keeps_out_of_the_elements_between_two_pools() -> None:
    """A message flow may cross a pool but never an element."""
    scene = draw(raw_example("order-bpmn"))
    assert Code.LINE_THROUGH_NODE not in [f.code for f in check_scene(scene)]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            lambda r: r["flows"].append({"from": "s", "to": "t", "style": "message"}),
            "inside one pool",
        ),
        (lambda r: r["flows"].append({"from": "u", "to": "e"}), "between two pools"),
        (lambda r: r["flows"].append({"from": "t", "to": "s"}), "flow into it"),
        (lambda r: r["flows"].append({"from": "e", "to": "t"}), "flow out of it"),
        (lambda r: r["elements"][1].pop("zone"), "needs a 'zone'"),
        (lambda r: r["elements"][1].update(trigger="timer"), "'trigger' belongs"),
        (lambda r: r["elements"][1].update(repeat="loop", kind="start"), "'repeat' belongs"),
        (lambda r: r["elements"][2].update(attached_to="s"), "must name a task"),
        (lambda r: r.update(style="illustrated"), "one style"),
        (lambda r: r["elements"][1].update(kind="robot"), "unknown kind 'robot'"),
    ],
)
def test_rules_are_refused_with_a_reason(change, message: str) -> None:  # noqa: ANN001
    """Each rule of BPMN that the spec breaks is an error that says why."""
    raw = pools()
    change(raw)
    with pytest.raises(SpecError, match=message):
        draw(raw)


def test_a_laned_pool_needs_a_lane_and_a_black_box_shows_no_element() -> None:
    """With lanes an element names a lane; a black-box pool holds no element."""
    raw = pools()
    raw["zones"] += [{"id": "lane", "parent": "a"}]
    with pytest.raises(SpecError, match="name one of its lanes"):
        draw(raw)
    raw = pools()
    raw["zones"][1]["black_box"] = True
    with pytest.raises(SpecError, match="black-box pool"):
        draw(raw)


def test_a_message_flow_may_end_on_a_black_box_pool() -> None:
    """A black-box pool is named by its id; the line meets its bar straight above the element."""
    scene = draw(raw_example("refund-advanced-bpmn"))
    bar = next(frame for frame in scene.frames if frame.id == "customer")
    line = next(e for e in scene.edges if e.label and e.label.text == "refund confirmed")
    assert line.target is None
    assert line.points[-1][1] == bar.y + bar.height


def test_too_many_elements_and_two_main_paths_are_warnings() -> None:
    """More than 25 elements, or a main path in two pools, is reported but not refused."""
    raw = pools()
    raw["elements"] += [{"id": f"x{i}", "label": "Step", "zone": "a"} for i in range(26)]
    codes = [f.code for f in check_scene(draw(raw))]
    assert Code.BPMN_TOO_MANY_ELEMENTS in codes
    raw = pools()
    raw["flows"][0]["main"] = True
    raw["flows"][2]["main"] = True
    assert Code.BPMN_MAIN_PATH in [f.code for f in check_scene(draw(raw))]


def test_a_flat_diagram_has_no_pool_frames() -> None:
    """A diagram without zones draws its elements and flows only."""
    scene = draw(raw_example("refund-bpmn"))
    assert scene.frames == ()
    assert all(len(edge.points) >= 2 for edge in scene.edges)


def test_captions_hang_above_an_element_when_a_line_leaves_below() -> None:
    """The name of an event sits under it, or above it when a message line leaves downward."""
    scene = draw(raw_example("delivery-bpmn"))
    assert not node_of(scene, "hungry").caption_above
    assert node_of(scene, "confirmed").caption_above


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_drawio_file_reads_back_with_its_shapes(name: str, tmp_path: Path) -> None:
    """Importing the draw.io file brings back each shape, mark, number and frame variant."""
    scene = draw(raw_example(name))
    path = tmp_path / "diagram.drawio"
    path.write_text(render_drawio.render(scene), encoding="utf-8")
    back = {node.id.removeprefix("node-"): node for node in import_drawio.convert(path).scene.nodes}
    for node in scene.nodes:
        read = back[node.id]
        assert (read.shape, read.markers, read.number) == (node.shape, node.markers, node.number)
        assert read.host == node.host
    frames = import_drawio.convert(path).scene.frames
    assert [frame.variant for frame in frames] == [frame.variant for frame in scene.frames]
