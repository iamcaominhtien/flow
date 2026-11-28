"""Lines a script draws by hand are given ways of their own where lines of different kinds meet."""

import sys
from itertools import combinations, pairwise
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"
sys.path.insert(0, str(PLUGIN_DIR))

from flowlib.author import Canvas, NodeOptions, Route  # noqa: E402
from flowlib.model import Edge, Role, Scene, Shape  # noqa: E402
from flowlib.ports import end_side  # noqa: E402
from flowlib.untangle import MIN_OVERLAP_PX, shared_length  # noqa: E402

SWITCH_BRANCHES: int = 3


def _line(scene: Scene, source: str, target: str) -> Edge:
    """Return the line between two nodes."""
    return next(edge for edge in scene.edges if edge.source == source and edge.target == target)


def _crossings(scene: Scene) -> int:
    """Return how many pairs of stretches of different lines cross away from their ends."""
    stretches = [(edge.id, pair) for edge in scene.edges for pair in pairwise(edge.points)]
    return sum(
        _cross(first, second)
        for (first_id, first), (second_id, second) in combinations(stretches, 2)
        if first_id != second_id
    )


def _cross(first: tuple, second: tuple) -> bool:
    """Tell whether a horizontal and a vertical segment cross inside both."""
    for flat, upright in ((first, second), (second, first)):
        if flat[0][1] == flat[1][1] and upright[0][0] == upright[1][0]:
            low_x, high_x = sorted((flat[0][0], flat[1][0]))
            low_y, high_y = sorted((upright[0][1], upright[1][1]))
            return low_x < upright[0][0] < high_x and low_y < flat[0][1] < high_y
    return False


def _right_angled_and_attached(scene: Scene) -> bool:
    """Tell whether every line is horizontal or vertical and starts and ends on its nodes."""
    nodes = {node.id: node for node in scene.nodes}
    for edge in scene.edges:
        if any(a[0] != b[0] and a[1] != b[1] for a, b in pairwise(edge.points)):
            return False
        for node_id, point in ((edge.source, edge.points[0]), (edge.target, edge.points[-1])):
            node = nodes[node_id]
            inside_x = node.x - 1 <= point[0] <= node.x + node.width + 1
            inside_y = node.y - 1 <= point[1] <= node.y + node.height + 1
            if not (inside_x and inside_y):
                return False
    return True


def _two_answers_down() -> Scene:
    """Draw a decision whose two answers both leave by the bottom tip, as a hand might."""
    canvas = Canvas("Exits", None)
    canvas.node("ask", Shape.DECISION, "Cached?", NodeOptions((300, 200)))
    canvas.node("use", Shape.PROCESS, "Use it", NodeOptions((300, 400)))
    canvas.node("load", Shape.PROCESS, "Load it", NodeOptions((560, 400)))
    canvas.edge("ask", "use", Route(leave="bottom", role=Role.MAIN, label="Yes"))
    route = Route(leave="bottom", via=((300, 300), (560, 300)), role=Role.NO, label="No")
    canvas.edge("ask", "load", route)
    return canvas.scene()


def _two_kinds_into_one_point() -> Scene:
    """Draw a main line and a failure line into one point, one from each way along the side."""
    canvas = Canvas("Ends", None)
    canvas.node("up", Shape.PROCESS, "Above", NodeOptions((100, 100)))
    canvas.node("down", Shape.PROCESS, "Below", NodeOptions((100, 500)))
    canvas.node("t", Shape.PROCESS, "Target", NodeOptions((400, 300)))
    canvas.edge("up", "t", Route("right", "left", via=((250, 100), (250, 300)), role=Role.MAIN))
    canvas.edge("down", "t", Route("right", "left", via=((250, 500), (250, 300)), role=Role.NO))
    return canvas.scene()


def _stacked_column() -> Scene:
    """Draw two lines of different kinds along one column, with a point mid-way on one."""
    canvas = Canvas("Overlap", None)
    for name, centre in (
        ("a", (100, 100)),
        ("b", (100, 500)),
        ("c", (400, 100)),
        ("d", (400, 500)),
    ):
        canvas.node(name, Shape.PROCESS, name.upper(), NodeOptions(centre))
    canvas.edge("a", "d", Route("right", "left", via=((250, 100), (250, 300), (250, 500))))
    canvas.edge("c", "b", Route("left", "right", via=((250, 100), (250, 500)), role=Role.NO))
    return canvas.scene()


def _switch_with_main() -> Scene:
    """Draw a switch: a main answer and three branches of one kind, all from the right tip."""
    canvas = Canvas("Switch", None)
    canvas.node("which", Shape.DECISION, "Which?", NodeOptions((200, 200)))
    canvas.node("main", Shape.PROCESS, "Main", NodeOptions((500, 200)))
    canvas.edge("which", "main", Route(leave="right", role=Role.MAIN))
    for index in range(1, SWITCH_BRANCHES + 1):
        name = f"b{index}"
        canvas.node(name, Shape.PROCESS, name, NodeOptions((500, 200 + 120 * index)))
        via = ((360, 200), (360, 200 + 120 * index))
        canvas.edge("which", name, Route(leave="right", arrive="left", via=via))
    return canvas.scene()


def test_two_answers_of_a_decision_leave_by_two_tips() -> None:
    """The answer off the main path moves to a free tip that faces its target."""
    scene = _two_answers_down()
    main, other = _line(scene, "ask", "use"), _line(scene, "ask", "load")
    assert end_side(list(main.points), True) != end_side(list(other.points), True)


def test_ends_of_different_kinds_part_without_crossing() -> None:
    """Lines of two kinds into one point end apart, each where it comes from, crossing nothing."""
    scene = _two_kinds_into_one_point()
    ends = {edge.points[-1] for edge in scene.edges if edge.target == "t"}
    assert len(ends) == len(("main", "no"))
    assert _crossings(scene) == 0


def test_a_stretch_on_top_of_another_kind_is_pushed_aside() -> None:
    """Two lines of different kinds drawn along one column part by a track."""
    scene = _stacked_column()
    first, second = _line(scene, "a", "d"), _line(scene, "c", "b")
    assert shared_length(list(first.points), list(second.points)) < MIN_OVERLAP_PX


def test_branches_of_one_kind_keep_their_trunk_and_the_main_answer_its_own() -> None:
    """Branches of a switch stay together; the main answer leaves from a place of its own."""
    scene = _switch_with_main()
    branches = {edge.points[0] for edge in scene.edges if edge.target.startswith("b")}
    assert len(branches) == 1
    assert _line(scene, "which", "main").points[0] not in branches


def test_untangled_lines_stay_right_angled_and_attached() -> None:
    """No move leaves a slanted stretch or an end off its node."""
    for scene in (_two_answers_down(), _two_kinds_into_one_point(), _stacked_column()):
        assert _right_angled_and_attached(scene)
    assert _right_angled_and_attached(_switch_with_main())


def _stack_in_a_narrow_gap() -> Scene:
    """Draw two lines of different kinds down a gap between two boxes, too narrow to push."""
    canvas = Canvas("Gap", None)
    for name, centre in (
        ("a", (100, 100)),
        ("b", (100, 600)),
        ("c", (400, 100)),
        ("d", (400, 600)),
    ):
        canvas.node(name, Shape.PROCESS, name.upper(), NodeOptions(centre))
    canvas.node("p", Shape.PROCESS, "P", NodeOptions((190, 350), width=100))
    canvas.node("q", Shape.PROCESS, "Q", NodeOptions((310, 350), width=100))
    canvas.edge("a", "d", Route("right", "left", via=((250, 100), (250, 600))))
    canvas.edge("c", "b", Route("left", "right", via=((250, 100), (250, 600)), role=Role.NO))
    return canvas.scene()


def test_a_push_keeps_the_shape_of_the_line() -> None:
    """A stack with room beside it is parted by moving one stretch: ends and bends stay."""
    scene = _stacked_column()
    pushed = _line(scene, "c", "b")
    assert len(pushed.points) == len(("start", "bend", "bend", "end"))
    assert pushed.points[0][1] == pushed.points[1][1]


def test_a_stack_with_no_room_beside_it_is_searched_anew() -> None:
    """When a push would touch a box, the line takes a new way that runs on no other kind."""
    scene = _stack_in_a_narrow_gap()
    first, second = _line(scene, "a", "d"), _line(scene, "c", "b")
    assert shared_length(list(first.points), list(second.points)) < MIN_OVERLAP_PX
    assert _right_angled_and_attached(scene)
