"""Tests for the arrows of a screen flow: entry decisions, merged triggers, busy lines, top bars."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "flow"))

from flowlib.check import Code, check_busy_lines, check_scene  # noqa: E402
from flowlib.diagrams import layout  # noqa: E402
from flowlib.model import Edge, Role, Scene  # noqa: E402

FAR = 400.0  # the length of the lines of the busy line test


def _screen(item_id: str, at: list[int]) -> dict:
    """Return a screen at L0 in a cell."""
    return {"id": item_id, "label": item_id.title(), "fidelity": "L0", "at": at}


def test_two_entry_decisions_in_one_column_do_not_share_a_leg() -> None:
    """The guard of the lower entry must not run up the leg of the guard above it."""
    scene = layout(
        {
            "type": "screen",
            "screens": [
                _screen("list", [0, 1]),
                _screen("detail", [0, 2]),
                _screen("form", [1, 1]),
                _screen("done", [1, 2]),
                {"id": "e0", "kind": "entry", "label": "Open the app", "at": [0]},
                {"id": "d0", "kind": "decision", "label": "Signed in?", "at": [0, 0]},
                {"id": "e1", "kind": "entry", "label": "Open a link", "at": [1]},
                {"id": "d1", "kind": "decision", "label": "Signed in?", "at": [1, 0]},
            ],
            "taps": [
                {"from": "e0", "to": "d0", "trigger": "open"},
                {"from": "d0", "to": "done", "guard": "yes"},
                {"from": "d0", "to": "list", "guard": "no"},
                {"from": "e1", "to": "d1", "trigger": "open"},
                {"from": "d1", "to": "list", "guard": "yes"},
                {"from": "d1", "to": "detail", "guard": "no"},
            ],
        }
    )
    overlaps = [f for f in check_scene(scene) if f.code is Code.LINES_OVERLAP]
    between = [f for f in overlaps if "d0>" in f.message and "d1>" in f.message]
    assert not between


def test_two_taps_that_differ_only_in_their_trigger_are_one_arrow() -> None:
    """Both triggers go on one chip, as UML lists the triggers of one transition."""
    scene = layout(
        {
            "type": "screen",
            "screens": [_screen("home", [0, 0]), _screen("signup", [0, 1])],
            "taps": [
                {"from": "home", "to": "signup", "trigger": "click Sign up"},
                {"from": "home", "to": "signup", "trigger": "click the heart"},
                {"from": "home", "to": "signup", "trigger": "click Sign up"},
            ],
        }
    )
    edges = [edge for edge in scene.edges if edge.source == "home"]
    assert len(edges) == 1
    assert edges[0].label is not None
    assert edges[0].label.text == "click Sign up, click the heart"
    assert Code.LABEL_TOO_LONG not in [f.code for f in check_scene(scene)]


def test_taps_with_different_guards_stay_apart() -> None:
    """A guard is part of what an arrow means, so two guards are two arrows."""
    scene = layout(
        {
            "type": "screen",
            "screens": [
                _screen("form", [0, 0]),
                {"id": "ok", "kind": "decision", "label": "Valid?", "at": [0, 1]},
            ],
            "taps": [
                {"from": "form", "to": "ok", "trigger": "tap Send"},
                {"from": "ok", "to": "form", "guard": "too short", "kind": "failure"},
                {"from": "ok", "to": "form", "guard": "taken", "kind": "failure"},
            ],
        }
    )
    assert len([edge for edge in scene.edges if edge.source == "ok"]) == 2


def _line(edge_id: str, points: tuple[tuple[float, float], ...]) -> Edge:
    """Return a plain line through some points."""
    return Edge(edge_id, Role.NEXT, points, None, None, None)


def test_a_line_that_crosses_four_others_is_named() -> None:
    """One long line across four short ones is reported once, by its own id."""
    long_line = _line("long", ((0.0, FAR / 2), (FAR, FAR / 2)))
    shorts = [
        _line(f"short{i}", ((FAR * (i + 1) / 5, 0.0), (FAR * (i + 1) / 5, FAR))) for i in range(4)
    ]
    findings = check_busy_lines(Scene(FAR, FAR, None, None, (), (), (long_line, *shorts)))
    assert [finding.items for finding in findings] == [("long",)]


def test_a_top_bar_link_widens_to_fit_its_name() -> None:
    """A web link name longer than a phone tab's still fits on one line."""
    scene = layout(
        {
            "type": "screen",
            "screens": [
                {"id": "t-home", "kind": "tab", "label": "Home", "icon": "home", "at": [0, 0]},
                {
                    "id": "t-new",
                    "kind": "tab",
                    "label": "New Article",
                    "icon": "plus",
                    "at": [0, 1],
                },
                _screen("home", [1, 0]),
                _screen("editor", [1, 1]),
            ],
            "buses": [{"trigger": "click a top bar link", "to": ["t-home", "t-new"]}],
            "taps": [{"from": "t-home", "to": "home"}, {"from": "t-new", "to": "editor"}],
        }
    )
    nodes = {node.id: node for node in scene.nodes}
    assert nodes["t-new"].width > nodes["t-home"].width
    assert Code.TEXT_MAY_NOT_FIT not in [f.code for f in check_scene(scene)]
