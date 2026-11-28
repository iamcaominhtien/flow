"""Lines a script draws by hand are given ways of their own where lines of different kinds meet."""

import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"
sys.path.insert(0, str(PLUGIN_DIR))

from flowlib.author import Canvas, NodeOptions, Route  # noqa: E402
from flowlib.model import Edge, Role, Scene, Shape  # noqa: E402
from flowlib.untangle import MIN_OVERLAP_PX, shared_length  # noqa: E402


def _by_target(scene: Scene, source: str, target: str) -> Edge:
    """Return the line between two nodes."""
    return next(edge for edge in scene.edges if edge.source == source and edge.target == target)


def _decision_with_two_exits_down() -> Canvas:
    """Draw a decision whose two answers both leave by the bottom tip, as a hand might."""
    canvas = Canvas("Exits", None)
    canvas.node("ask", Shape.DECISION, "Cached?", NodeOptions((300, 200)))
    canvas.node("use", Shape.PROCESS, "Use it", NodeOptions((300, 400)))
    canvas.node("load", Shape.PROCESS, "Load it", NodeOptions((560, 400)))
    canvas.edge("ask", "use", Route(leave="bottom", role=Role.MAIN, label="Yes"))
    canvas.edge("ask", "load", Route(leave="bottom", via=((300, 300), (560, 300)), role=Role.NO))
    return canvas


def test_two_answers_of_a_decision_leave_by_two_tips() -> None:
    """The answer off the main path moves to a free tip that faces its target."""
    scene = _decision_with_two_exits_down().scene()
    main, other = _by_target(scene, "ask", "use"), _by_target(scene, "ask", "load")
    assert main.points[0] != other.points[0]
    assert shared_length(list(main.points), list(other.points)) < MIN_OVERLAP_PX


def test_lines_of_different_kinds_into_one_point_are_spread() -> None:
    """A main line and a failure line drawn into one point of a side end apart."""
    canvas = Canvas("Ends", None)
    canvas.node("a", Shape.PROCESS, "First", NodeOptions((200, 100)))
    canvas.node("b", Shape.PROCESS, "Second", NodeOptions((600, 100)))
    canvas.node("t", Shape.PROCESS, "Target", NodeOptions((400, 300)))
    canvas.edge(
        "a", "t", Route(leave="bottom", arrive="top", role=Role.MAIN, via=((200, 220), (400, 220)))
    )
    canvas.edge(
        "b", "t", Route(leave="bottom", arrive="top", role=Role.NO, via=((600, 220), (400, 220)))
    )
    scene = canvas.scene()
    assert _by_target(scene, "a", "t").points[-1] != _by_target(scene, "b", "t").points[-1]


def test_a_stretch_on_top_of_another_kind_is_pushed_aside() -> None:
    """Two lines of different kinds drawn along one column part by a track."""
    canvas = Canvas("Overlap", None)
    for name, centre in (
        ("a", (100, 100)),
        ("b", (100, 500)),
        ("c", (400, 100)),
        ("d", (400, 500)),
    ):
        canvas.node(name, Shape.PROCESS, name.upper(), NodeOptions(centre))
    canvas.edge("a", "d", Route(leave="right", arrive="left", via=((250, 100), (250, 500))))
    canvas.edge(
        "c", "b", Route(leave="left", arrive="right", role=Role.NO, via=((250, 100), (250, 500)))
    )
    scene = canvas.scene()
    first, second = _by_target(scene, "a", "d"), _by_target(scene, "c", "b")
    assert shared_length(list(first.points), list(second.points)) < MIN_OVERLAP_PX


def test_lines_of_one_kind_keep_their_shared_trunk() -> None:
    """Branches of a switch drawn from one tip stay together: they are one kind."""
    canvas = Canvas("Switch", None)
    canvas.node("which", Shape.DECISION, "Which?", NodeOptions((200, 200)))
    for index, name in enumerate(("x", "y", "z")):
        canvas.node(name, Shape.PROCESS, name.upper(), NodeOptions((500, 200 + 120 * index)))
        canvas.edge("which", name, Route(leave="right", via=((360, 200), (360, 200 + 120 * index))))
    scene = canvas.scene()
    starts = {edge.points[0] for edge in scene.edges if edge.source == "which"}
    assert len(starts) == 1
