"""Tests for the flowchart rules of design 03: bars, fans, notes, lanes and the lint."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
DELIVERY = ROOT / "examples" / "delivery-flowchart.spec.json"
PAYMENT = ROOT / "examples" / "payment-flowchart.spec.json"
LANE_PLAIN_PX = 210
LANE_CARD_PX = 240
BAR_THICKNESS_PX = 8

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio, render_html, scene as scene_io  # noqa: E402,I001
from flowlib.check import Code, check_scene  # noqa: E402
from flowlib.import_drawio import convert  # noqa: E402
from flowlib.model import FrameVariant, LabelKind, Role, Scene, Shape  # noqa: E402


def chart(nodes: list[dict], edges: list[dict], **extra: object) -> Scene:
    """Lay out a small flowchart written in the spec format."""
    raw = {"type": "flowchart", "nodes": nodes, "edges": edges, **extra}
    return diagrams.layout(raw)


def delivery() -> Scene:
    """Lay out the food delivery example."""
    return diagrams.layout(json.loads(DELIVERY.read_text()))


def codes(scene: Scene) -> set[str]:
    """Return the codes of the findings of a scene."""
    return {finding.code.value for finding in check_scene(scene)}


def test_bar_spans_its_branches_and_lines_drop_from_it() -> None:
    """A split bar reaches both branches, and each line leaves it straight at its target."""
    nodes = [
        {"id": "a", "kind": "process", "text": "Start work"},
        {"id": "bar", "kind": "fork"},
        {"id": "b", "kind": "process", "text": "Task A"},
        {"id": "c", "kind": "process", "text": "Task B"},
    ]
    edges = [{"from": "a", "to": "bar"}, {"from": "bar", "to": "b"}, {"from": "bar", "to": "c"}]
    laid = chart(nodes, edges)
    by_id = {node.id: node for node in laid.nodes}
    bar = by_id["bar"]
    assert bar.shape is Shape.FORK and bar.height == BAR_THICKNESS_PX
    for name in ("b", "c"):
        centre = by_id[name].x + by_id[name].width / 2
        assert bar.x < centre < bar.x + bar.width
        edge = next(each for each in laid.edges if each.target == name)
        assert len({point[0] for point in edge.points}) == 1
    assert Code.NODES_OVERLAP.value not in codes(laid)


def test_join_is_another_name_for_the_bar() -> None:
    """The kind ``join`` is read as the same bar."""
    laid = chart(
        [{"id": "a", "kind": "process", "text": "A"}, {"id": "j", "kind": "join"}],
        [{"from": "a", "to": "j"}],
    )
    assert {node.id: node.shape for node in laid.nodes}["j"] is Shape.FORK


def test_bar_survives_scene_round_trip_and_draws_in_both_formats() -> None:
    """The bar is kept by the scene file, drawn in HTML and in draw.io, and read back."""
    laid = delivery()
    assert scene_io.parse(scene_io.dump(laid)) == laid
    assert 'data-id="split"' in render_html.render(laid)
    assert "flowFork=1" in render_drawio.render(laid)


def test_bar_comes_back_from_drawio(tmp_path: Path) -> None:
    """A bar written to draw.io is imported as a bar."""
    path = tmp_path / "delivery.drawio"
    path.write_text(render_drawio.render(delivery()), encoding="utf-8")
    shapes = {node.shape for node in convert(path).scene.nodes}
    assert Shape.FORK in shapes


def test_multiway_decision_fans_out_by_three_sides() -> None:
    """Three exits go to three columns, the middle one straight down, with no shared stretch."""
    nodes = [{"id": "plan", "kind": "decision", "text": "Plan?"}] + [
        {"id": name, "kind": "process", "text": name} for name in ("free", "pro", "other")
    ]
    edges = [
        {"from": "plan", "to": "free", "label": "Free"},
        {"from": "plan", "to": "pro", "label": "Pro"},
        {"from": "plan", "to": "other", "label": "else"},
    ]
    laid = chart(nodes, edges)
    by_id = {node.id: node for node in laid.nodes}
    plan_centre = by_id["plan"].x + by_id["plan"].width / 2
    assert by_id["pro"].x + by_id["pro"].width / 2 == plan_centre
    assert by_id["free"].x < by_id["plan"].x < by_id["other"].x
    assert Code.LINES_OVERLAP.value not in codes(laid)
    assert Code.DECISION_NO_ELSE.value not in codes(laid)


def test_connector_note_is_drawn_beside_the_circle() -> None:
    """The detail of a connector is a note beside it in HTML and its own cell in draw.io."""
    laid = delivery()
    link = next(node for node in laid.nodes if node.id == "link")
    assert link.detail == ("Continues in Support case flow",)
    assert "Continues in Support case flow" in render_html.render(laid)
    assert 'id="note-link"' in render_drawio.render(laid)


def test_data_role_is_violet_thin_and_slow() -> None:
    """A data line is in the scene, violet in HTML and has its own duration in draw.io."""
    laid = delivery()
    assert any(edge.role is Role.DATA for edge in laid.edges)
    assert "flowAnimationDuration=1500" in render_drawio.render(laid)


def test_yes_and_no_chips_keep_their_colour_on_the_main_path() -> None:
    """A Yes or No label on a main-path line is green or rose."""
    kinds = {
        edge.label.text: edge.label.kind
        for edge in delivery().edges
        if edge.label and edge.label.text in ("Yes", "No")
    }
    assert kinds["Yes"] is LabelKind.YES
    assert kinds["No"] is LabelKind.NO


def test_lane_floor_is_210_plain_and_240_with_cards() -> None:
    """A lane is at least 210 px across, 240 px when a card is drawn."""
    lanes = [{"id": "x", "label": "X", "tone": "blue"}]
    node = {"id": "a", "kind": "document", "text": "A", "lane": "x"}
    plain = chart([node], [], lanes=lanes)
    card = {**node, "kind": "process", "icon": "user"}
    cards = chart([card], [], lanes=lanes, style="illustrated")
    sizes = [
        frame.width
        for laid in (plain, cards)
        for frame in laid.frames
        if frame.variant is FrameVariant.LANE
    ]
    assert sizes[0] == LANE_PLAIN_PX
    assert sizes[1] >= LANE_CARD_PX


def test_lane_change_runs_straight_across() -> None:
    """Two steps that follow each other across lanes share one column."""
    laid = delivery()
    centre = {node.id: node.x + node.width / 2 for node in laid.nodes}
    assert centre["checkout"] == centre["create"] == centre["auth"]


def test_lint_flags_text_decisions_and_size() -> None:
    """Long text, a decision that is not a question, one exit, and a long chart are warned."""
    nodes = [
        {"id": "a", "kind": "process", "text": "Check the stock of every shop"},
        {"id": "d", "kind": "decision", "text": "Done"},
        {"id": "e", "kind": "process", "text": "End"},
    ]
    found = codes(chart(nodes, [{"from": "a", "to": "d"}, {"from": "d", "to": "e"}]))
    assert {"text-too-long", "decision-not-question", "decision-few-exits"} <= found
    many = [{"id": f"n{i}", "kind": "process", "text": "Step"} for i in range(16)]
    links = [{"from": f"n{i}", "to": f"n{i + 1}"} for i in range(15)]
    assert Code.CHART_TOO_BIG.value in codes(chart(many, links))


def test_lint_asks_for_else_last() -> None:
    """A decision with three exits whose last is not else is warned."""
    nodes = [{"id": "d", "kind": "decision", "text": "Plan?"}] + [
        {"id": name, "kind": "process", "text": name} for name in ("a", "b", "c")
    ]
    edges = [{"from": "d", "to": name, "label": name} for name in ("a", "b", "c")]
    assert Code.DECISION_NO_ELSE.value in codes(chart(nodes, edges))


def test_lint_checks_start_and_end_placement() -> None:
    """A start that has a step above it is warned; the examples are fine."""
    assert Code.START_PLACEMENT.value not in codes(delivery())
    laid = chart(
        [
            {"id": "work", "kind": "process", "text": "Work"},
            {"id": "start", "kind": "terminator", "text": "Begin"},
        ],
        [{"from": "start", "to": "work"}],
    )
    assert Code.START_PLACEMENT.value not in codes(laid)


def test_payment_example_matches_the_design_parts() -> None:
    """The online payment chart has its subprocess, document, loop and lettered number chips."""
    laid = diagrams.layout(json.loads(PAYMENT.read_text()))
    shapes = {node.shape for node in laid.nodes}
    assert {Shape.SUBPROCESS, Shape.DOCUMENT, Shape.PREPARATION} <= shapes
    assert {"3a", "5a"} <= {node.number for node in laid.nodes}
    assert any(edge.role is Role.BACK for edge in laid.edges)
