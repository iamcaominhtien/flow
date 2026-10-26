"""Tests for the helpers a hand-laid diagram script uses."""

import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib.author import Canvas, NodeOptions, Route, Side, sentence_case  # noqa: E402
from flowlib.check import Severity  # noqa: E402
from flowlib.model import Role, Shape, Tone  # noqa: E402


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
