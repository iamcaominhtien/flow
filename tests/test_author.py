"""Tests for the helpers a hand-laid diagram script uses."""

import sys
from dataclasses import replace
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib.author import Canvas, EdgeWords, NodeOptions, Route, Side, sentence_case  # noqa: E402
from flowlib.check import Code, Severity, check_scene  # noqa: E402
from flowlib.glyph_widths import FontWeight, inter_width  # noqa: E402
from flowlib.labels import place_labels  # noqa: E402
from flowlib.model import (  # noqa: E402
    Device,
    Edge,
    Fidelity,
    LabelKind,
    Role,
    Row,
    ScreenView,
    Shape,
    Tone,
)
from flowlib.theme import load_theme  # noqa: E402


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


def _screen_canvas(gap: float = 600) -> Canvas:
    """Return a canvas with a phone screen and a desktop screen side by side."""
    canvas = Canvas("Screens", "Two screens")
    phone = ScreenView(code="S1", fidelity=Fidelity.L2)
    desktop = ScreenView(code="W1", device=Device.DESKTOP, fidelity=Fidelity.L2)
    canvas.node("home", Shape.SCREEN, "Home", NodeOptions((200, 300), screen=phone))
    canvas.node("web", Shape.SCREEN, "Web", NodeOptions((200 + gap, 300), screen=desktop))
    return canvas


def test_a_screen_node_is_sized_by_the_device_table() -> None:
    """A phone and a desktop screen take the size of their device frame, and keep their id."""
    canvas = _screen_canvas()
    sizes = load_theme().screen.sizes
    assert (canvas.boxes["home"].node.width, canvas.boxes["home"].node.height) == sizes["phone"]
    assert canvas.boxes["web"].node.width == sizes["desktop"][0]
    view = canvas.boxes["home"].node.screen
    assert view is not None and view.code == "S1" and view.title == "Home"


def test_a_screen_can_take_a_forced_size_and_is_refused_on_another_shape() -> None:
    """The size may be forced; a screen view on a process box is an error."""
    canvas = Canvas()
    view = ScreenView(code="S2", fidelity=Fidelity.L2, is_mini=True)
    box = canvas.node("a", Shape.SCREEN, "A", NodeOptions((100, 300), screen=view, width=150))
    assert box.node.width == 150
    with pytest.raises(ValueError, match="goes with"):
        canvas.node("b", Shape.PROCESS, "B", NodeOptions((400, 300), screen=view))


def test_a_trigger_chip_is_dark_for_a_person_and_slate_with_an_icon_for_the_system() -> None:
    """The two trigger kinds differ in chip kind and icon."""
    canvas = _screen_canvas()
    user = canvas.edge("home", "web", Route(words=EdgeWords(trigger="tap Open")))
    system = canvas.edge("web", "home", Route(words=EdgeWords("timer ends", system_icon="clock")))
    assert user.label is not None and user.label.kind is LabelKind.USER
    assert system.label is not None and system.label.kind is LabelKind.SYSTEM
    assert system.label.icon == "clock"


def test_a_guard_and_an_effect_follow_the_trigger_and_a_failure_is_rose() -> None:
    """Words are ``trigger [guard] / effect``: the chip is the label, the rest are extras."""
    canvas = _screen_canvas()
    words = EdgeWords("tap Pay", guard="card declined", effect="show error", is_failure=True)
    line = canvas.edge("home", "web", Route(words=words))
    assert line.label is not None and line.label.text == "tap Pay"
    assert [extra.text for extra in line.extras] == ["[card declined]", "/ show error"]
    assert [extra.kind for extra in line.extras] == [LabelKind.GUARD_FAIL, LabelKind.EFFECT]
    assert line.role is Role.NO
    guard_only = canvas.edge("web", "home", Route(words=EdgeWords(guard="ok")))
    assert guard_only.label is not None and guard_only.label.kind is LabelKind.GUARD_OK
    assert guard_only.extras == ()


def test_words_and_a_plain_label_cannot_be_given_together() -> None:
    """A route has either a short label or the words of a screen flow arrow."""
    canvas = _screen_canvas()
    with pytest.raises(ValueError, match="not both"):
        canvas.edge("home", "web", Route(label="x", words=EdgeWords("tap")))


def test_words_beside_a_vertical_line_sit_on_the_chosen_side() -> None:
    """On a vertical stretch the chip is beside the line, the text under the chip."""
    canvas = Canvas()
    view = ScreenView(code="S1", fidelity=Fidelity.L2)
    canvas.node("top", Shape.SCREEN, "Top", NodeOptions((200, 300), screen=view))
    canvas.node("low", Shape.SCREEN, "Low", NodeOptions((200, 800), screen=view))
    words = EdgeWords("tap Next", guard="valid")
    right = canvas.edge("top", "low", Route(words=words))
    left = canvas.edge(
        "top", "low", Route(words=EdgeWords("tap Next", guard="valid", is_left=True))
    )
    assert right.label is not None and left.label is not None
    assert right.label.at[0] > 200 > left.label.at[0]
    assert right.label.at[1] < right.extras[0].at[1]


def test_a_back_and_forth_pair_carries_its_words_outside_the_pair() -> None:
    """With no side given, each line of a vertical pair has its words on its outer side."""
    canvas = Canvas()
    view = ScreenView(code="S1", fidelity=Fidelity.L2)
    canvas.node("top", Shape.SCREEN, "Top", NodeOptions((200, 300), screen=view))
    canvas.node("low", Shape.SCREEN, "Low", NodeOptions((200, 800), screen=view))
    down = canvas.edge(
        "top", "low", Route(leave_along=0.3, arrive_along=0.3, words=EdgeWords("tap Next"))
    )
    up = canvas.edge(
        "low", "top", Route(leave_along=0.7, arrive_along=0.7, words=EdgeWords("tap Back"))
    )
    assert down.label is not None and up.label is not None
    assert down.label.at[0] < down.points[0][0] < up.points[0][0] < up.label.at[0]


def test_a_title_too_long_for_a_mini_phone_is_reported() -> None:
    """A mini phone cuts off a long title; the check says so, and a wider screen clears it."""
    canvas = Canvas()
    view = ScreenView(code="S1", fidelity=Fidelity.L1, is_mini=True)
    canvas.node(
        "cut", Shape.SCREEN, "Notification permission", NodeOptions((200, 300), screen=view)
    )
    canvas.node(
        "wide",
        Shape.SCREEN,
        "Notification permission",
        NodeOptions((500, 300), screen=view, width=160),
    )
    canvas.node("short", Shape.SCREEN, "Home map", NodeOptions((800, 300), screen=view))
    cut = [
        finding.items
        for finding in check_scene(canvas.scene())
        if finding.code is Code.TEXT_MAY_NOT_FIT
    ]
    assert cut == [("cut",)]


def test_a_name_too_long_for_an_l0_card_is_reported() -> None:
    """An L0 card draws its name in large bold type; a long one is cut and reported."""
    canvas = Canvas()
    card = ScreenView(code="S1")
    canvas.node("cut", Shape.SCREEN, "DeleteAccountConfirm", NodeOptions((200, 300), screen=card))
    canvas.node("fits", Shape.SCREEN, "Delete account", NodeOptions((500, 300), screen=card))
    cut = [
        finding.items
        for finding in check_scene(canvas.scene())
        if finding.code is Code.TEXT_MAY_NOT_FIT
    ]
    assert cut == [("cut",)]


def _blocked_canvas() -> tuple[Canvas, Edge]:
    """Return a canvas whose arrow has its chip over a small box beside the line."""
    canvas = _screen_canvas()
    canvas.node("note", Shape.PROCESS, "Note", NodeOptions((479, 270), width=100, height=20))
    line = canvas.edge("home", "web", Route(words=EdgeWords("tap Open", guard="valid")))
    return canvas, line


def test_extras_move_with_the_main_chip_and_stay_on_the_line() -> None:
    """A chip over a box slides along its line with its guard; both end clear."""
    canvas, line = _blocked_canvas()
    assert line.label is not None
    placed = place_labels(canvas.scene()).edges[0]
    assert placed.label is not None
    chip_shift = (placed.label.at[0] - line.label.at[0], placed.label.at[1] - line.label.at[1])
    extra_shift = (
        placed.extras[0].at[0] - line.extras[0].at[0],
        placed.extras[0].at[1] - line.extras[0].at[1],
    )
    assert chip_shift == extra_shift
    assert chip_shift[0] != 0 and chip_shift[1] == 0  # slid along the horizontal line only
    codes = [finding.code for finding in check_scene(canvas.scene())]
    assert Code.LABEL_COVERS not in codes


def test_a_chip_that_can_be_nudged_is_not_reported_but_one_that_cannot_is() -> None:
    """The check reports a chip over a box only when no place on its line is clear."""
    canvas, line = _blocked_canvas()
    unplaced = replace(canvas.scene(), edges=(line,))
    assert Code.LABEL_COVERS not in [finding.code for finding in check_scene(unplaced)]
    narrow = _screen_canvas(gap=240)
    narrow.edge("home", "web", Route(words=EdgeWords("tap a trigger far wider than the gap")))
    assert Code.LABEL_COVERS in [finding.code for finding in check_scene(narrow.scene())]


def test_a_screen_flow_scene_is_written_and_has_no_error(tmp_path: Path) -> None:
    """Screens and arrows with chips make the three files, and the check finds no error."""
    canvas = _screen_canvas()
    canvas.edge("home", "web", Route(words=EdgeWords("tap Open", guard="valid", effect="log")))
    findings = canvas.write(tmp_path, "screens")
    assert not [finding for finding in findings if finding.severity is Severity.ERROR]
    assert "S1" in (tmp_path / "screens.html").read_text(encoding="utf-8")


def test_inter_widths_match_what_a_browser_draws() -> None:
    """The measured widths give a bold name within 1% of Chromium (115 px at 13 px)."""
    width = inter_width("Payment methods", 13, FontWeight.BOLD)
    assert 114 <= width <= 116
