"""Tests for the helpers a hand-laid diagram script uses."""

import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib.author import Canvas, NodeOptions, Route, Side, sentence_case  # noqa: E402
from flowlib.check import Severity  # noqa: E402
from flowlib.model import Role, Row, Shape, Tone  # noqa: E402


def _small_canvas() -> Canvas:
    """Return a canvas with a lane, a terminator, a decision and a process."""
    canvas = Canvas("A test", "Three steps")
    canvas.lane("ops", "Operations", Tone.BLUE, (40, 100, 900, 260))
    canvas.node("start", Shape.TERMINATOR, "Start", NodeOptions((200, 230)))
    canvas.node("ok", Shape.DECISION, "All good?", NodeOptions((420, 230)))
    canvas.node("done", Shape.PROCESS, "Ship it", NodeOptions((680, 230)))
    return canvas


def test_a_node_is_sized_by_its_shape_and_centred_on_the_point() -> None:
    """The terminator keeps its minimum size and sits where it was put."""
    box = _small_canvas().boxes["start"]
    assert box.centre == (200, 230)
    assert (box.node.width, box.node.height) == (150, 48)


def test_a_line_leaves_the_sides_that_face_each_other() -> None:
    """Left to right: the right of one node to the left of the next, in a straight line."""
    canvas = _small_canvas()
    line = canvas.edge("start", "ok")
    assert line.points[0] == canvas.boxes["start"].port(Side.RIGHT)
    assert line.points[-1] == canvas.boxes["ok"].port(Side.LEFT)


def test_a_line_through_waypoints_has_only_right_angles() -> None:
    """Every segment of a routed line is horizontal or vertical."""
    canvas = _small_canvas()
    route = Route(
        leave=Side.BOTTOM, arrive=Side.BOTTOM, via=((420, 330), (680, 330)), role=Role.BACK
    )
    line = canvas.edge("ok", "done", route)
    for start, end in zip(line.points, line.points[1:], strict=False):
        assert start[0] == end[0] or start[1] == end[1]


def test_the_same_id_twice_is_refused() -> None:
    """A second node with the same id is an error."""
    canvas = _small_canvas()
    with pytest.raises(ValueError, match="used twice"):
        canvas.node("start", Shape.PROCESS, "Again", NodeOptions((10, 10)))


def test_write_gives_all_three_files_and_no_error(tmp_path: Path) -> None:
    """The scene, the HTML and the draw.io file are written and the checks find no error."""
    canvas = _small_canvas()
    canvas.edge("start", "ok")
    canvas.edge("ok", "done", Route(label="Yes", role=Role.YES))
    findings = canvas.write(tmp_path, "demo")
    assert {path.name for path in tmp_path.iterdir()} == {
        "demo.scene.json",
        "demo.html",
        "demo.drawio",
    }
    assert not [finding for finding in findings if finding.severity is Severity.ERROR]


def test_sentence_case_keeps_acronyms() -> None:
    """Only the first word is capitalised; an acronym keeps its capitals."""
    assert sentence_case("Soft Reconfig Store") == "Soft reconfig store"
    assert sentence_case("install RIB table") == "Install RIB table"


def test_a_port_can_be_anywhere_along_a_side_except_on_a_diamond() -> None:
    """A wide node takes several lines at different points; a diamond only has its tips."""
    canvas = Canvas()
    wide = canvas.node("bar", Shape.PROCESS, "Hub", NodeOptions((300, 100), width=400, height=40))
    diamond = canvas.node("q", Shape.DECISION, "Ok?", NodeOptions((300, 300)))
    left, right = wide.port(Side.TOP, 0.0), wide.port(Side.TOP, 1.0)
    assert right[0] - left[0] == 400
    with pytest.raises(ValueError, match="tips"):
        diamond.port(Side.LEFT, 0.25)
    with pytest.raises(ValueError, match="between 0 and 1"):
        wide.port(Side.TOP, 1.5)


def test_sentence_case_keeps_names_with_capitals_inside() -> None:
    """Names such as Adj-RIB-In stay as written."""
    assert sentence_case("Store Adj-RIB-In") == "Store Adj-RIB-In"


def test_a_legend_adds_a_heading_and_one_line_per_role(tmp_path: Path) -> None:
    """The legend is a heading plus a sample line and words for each role, and checks clean."""
    canvas = _small_canvas()
    canvas.legend((60, 420), (Role.MAIN, Role.NO, Role.BACK))
    assert {"legend-title", "legend-text-0", "legend-text-2"} <= set(canvas.boxes)
    assert len([edge for edge in canvas.edges if edge.id.startswith("legend-line")]) == 3
    findings = canvas.write(tmp_path, "legend")
    assert not [finding for finding in findings if finding.severity is Severity.ERROR]


def test_a_card_is_tall_enough_for_its_icon_pill_and_detail() -> None:
    """A card is sized as a card, so its name and detail sit inside its box."""
    canvas = Canvas()
    plain = canvas.node("a", Shape.PROCESS, "Update FIB", NodeOptions((100, 100)))
    options = NodeOptions((300, 100), icon="database", detail="Forwarding table updated", card=True)
    card = canvas.node("b", Shape.PROCESS, "Update FIB", options)
    assert card.node.height > plain.node.height + 60
    assert card.node.width >= 180


def test_a_gateway_with_a_mark_shows_its_name_as_a_caption() -> None:
    """A BPMN gateway keeps its mark inside and its question under it."""
    canvas = Canvas()
    gate = canvas.node(
        "g", Shape.DECISION, "Verified?", NodeOptions((100, 100), icon="x", width=64, height=64)
    )
    assert gate.node.caption == "Verified?"
    assert gate.node.text == ()


def test_an_event_is_a_circle_whatever_its_caption() -> None:
    """Start, end and timer events keep their fixed round size whatever the caption."""
    canvas = Canvas()
    for index, shape in enumerate((Shape.START, Shape.END, Shape.INTERMEDIATE)):
        box = canvas.node(
            f"event{index}",
            shape,
            "A very long caption for an event",
            NodeOptions((100, 100 + index * 80)),
        )
        assert box.node.width == box.node.height == 38


def test_a_node_may_not_take_an_id_the_canvas_gives_to_lines() -> None:
    """An id such as e1 would clash with the first line when the scene is read back."""
    canvas = Canvas("A test", "One step")
    with pytest.raises(ValueError, match="kept for lines"):
        canvas.node("e1", Shape.PROCESS, "Check", NodeOptions((200, 230)))


def test_a_table_is_sized_by_its_rows_and_has_a_taller_header_when_illustrated() -> None:
    """The illustrated table has the same rows under a header of the card height."""
    rows = (Row("id", "uuid", ("PK",)), Row("customer_id", "uuid", ("FK",)))
    canvas = Canvas("Schema", "Two tables")
    plain = canvas.node("plain", Shape.TABLE, "orders", NodeOptions((300, 300), rows=rows))
    card = canvas.node(
        "card", Shape.TABLE, "orders", NodeOptions((700, 300), rows=rows, card=True, icon="cart")
    )
    assert card.node.height - plain.node.height == 24
    assert plain.node.sections == (rows,)
