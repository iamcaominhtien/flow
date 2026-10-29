"""Tests for the passes that tidy the arrows of a screen flow after they are routed."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "flow"))

from flowlib.check import Code, Severity, check_scene  # noqa: E402
from flowlib.diagrams import layout  # noqa: E402
from flowlib.diagrams.screen_untangle import untangle  # noqa: E402
from flowlib.model import Point, Scene  # noqa: E402

TOP = 600.0  # the top edge of the frame both test arrows enter
HIGH, LOW = 300.0, 450.0  # the heights of the two arrows' horizontal runs
FAR = 900.0


def _arrive(level: float, port_x: float) -> tuple[Point, ...]:
    """Draw an arrow that comes from the right at a height and turns down into a top port."""
    return ((FAR, level), (port_x, level), (port_x, TOP))


def test_two_arrows_into_one_side_swap_ports_when_they_cross() -> None:
    """The higher arrow must enter outside the lower one; a crossing order is swapped."""
    keys = [(0, "target"), (1, "target")]
    offsets = {keys[0]: 30.0, keys[1]: 10.0}  # the higher arrow nearer the source: they cross
    levels = {0: HIGH, 1: LOW}

    def route(index: int, trial: dict) -> tuple[Point, ...]:
        """Draw arrow ``index`` with the trial offsets, around a port at x = 500."""
        return _arrive(levels[index], 500 + trial[(index, "target")])

    tidy = untangle([keys], offsets, route)
    assert tidy[keys[0]] < tidy[keys[1]]


def _pair_flow() -> Scene:
    """Lay out a screen above a decision, with an arrow each way between them."""
    return layout(
        {
            "type": "screen",
            "screens": [
                {"id": "form", "label": "Form", "fidelity": "L2", "at": [0, 0]},
                {"id": "ok", "kind": "decision", "label": "Valid?", "at": [1, 0]},
                {"id": "done", "label": "Done", "fidelity": "L2", "at": [1, 1]},
            ],
            "taps": [
                {"from": "form", "to": "ok", "trigger": "tap Send"},
                {"from": "ok", "to": "form", "guard": "invalid", "kind": "failure"},
                {"from": "ok", "to": "done", "guard": "valid"},
            ],
        }
    )


def test_a_frame_and_a_decision_joined_both_ways_do_not_share_a_tip() -> None:
    """The arrow back to the frame leaves a side tip; the one into the decision is straight."""
    scene = _pair_flow()
    edges = {edge.id: edge for edge in scene.edges}
    into, back = edges["form>ok"], edges["ok>form"]
    decision = next(node for node in scene.nodes if node.id == "ok")
    middle_y = decision.y + decision.height / 2
    assert into.points[0][0] == into.points[-1][0]  # straight down
    assert back.points[0][1] == middle_y  # a side tip, not the top tip
    assert back.points[0] != into.points[-1]
    codes = [finding.code for finding in check_scene(scene)]
    assert Code.LINES_OVERLAP not in codes


def test_a_jump_is_two_short_arrows_and_two_circles_with_one_letter() -> None:
    """A jump leaves its source into circle A and comes out of circle A into its target."""
    scene = layout(
        {
            "type": "screen",
            "screens": [
                {"id": "home", "label": "Home", "fidelity": "L2", "at": [0, 0]},
                {"id": "list", "label": "List", "fidelity": "L2", "at": [1, 1]},
                {"id": "settings", "label": "Settings", "fidelity": "L2", "at": [2, 2]},
            ],
            "taps": [
                {"from": "home", "to": "list", "trigger": "tap List"},
                {"from": "list", "to": "settings", "trigger": "tap Settings"},
                {"from": "settings", "to": "home", "trigger": "tap Log out", "route": "jump"},
            ],
        }
    )
    marks = [node for node in scene.nodes if node.id.startswith("jump-")]
    assert [mark.text for mark in marks] == [("A",), ("A",)]
    edges = {edge.id: edge for edge in scene.edges}
    first, second = edges["settings>home"], edges["settings>home~A"]
    assert first.label is not None  # the words stay on the first part
    assert second.source == "jump-A-in" and second.target == "home"
    assert all(len(edge.points) == 2 for edge in (first, second))  # two short straight arrows
    assert not [finding for finding in check_scene(scene) if finding.severity is Severity.ERROR]
