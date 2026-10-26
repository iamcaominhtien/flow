"""Tests for the spec, the layout, the routing, the checks and the build command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
FLOW_CLI = PLUGIN_DIR / "scripts" / "flow.py"
EXAMPLE_SPECS = [
    path
    for path in sorted((ROOT / "examples").glob("*.spec.json"))
    if json.loads(path.read_text())["type"] == "flowchart"
]
LOGIN_SPEC = ROOT / "examples" / "login-flow.spec.json"
REFUND_SPEC = ROOT / "examples" / "refund-swimlane.spec.json"
EXIT_OK = 0
EXIT_INVALID_INPUT = 1

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import build, overrides, scene, spec  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.diagrams import flowchart  # noqa: E402
from flowlib.model import Role, Scene  # noqa: E402


def laid_out(path: Path) -> Scene:
    """Read a spec file and lay it out.

    Args:
        path: A spec file.

    Returns:
        The scene.
    """
    return flowchart.layout(spec.load(path))


def centers_x(scene_to_read: Scene, node_ids: list[str]) -> set[float]:
    """Return the distinct x of the centre lines of the given nodes.

    Args:
        scene_to_read: The scene.
        node_ids: The nodes to look at.

    Returns:
        One value per distinct centre line.
    """
    by_id = {node.id: node for node in scene_to_read.nodes}
    return {by_id[node_id].x + by_id[node_id].width / 2 for node_id in node_ids}


@pytest.mark.parametrize("path", EXAMPLE_SPECS, ids=lambda path: path.name)
def test_example_has_no_errors(path: Path) -> None:
    """Both example flowcharts are laid out with no overlap, no line through a node, no clipping."""
    findings = check_scene(laid_out(path))
    errors = [finding.message for finding in findings if finding.severity is Severity.ERROR]
    assert errors == []


def test_happy_path_stays_in_one_column() -> None:
    """The main continuation of every step shares one centre line."""
    flowchart = laid_out(LOGIN_SPEC)
    column = ["start", "enter", "check", "valid", "session", "dash"]
    assert len(centers_x(flowchart, column)) == 1


def test_a_no_exit_leaves_sideways_on_the_row_of_its_decision() -> None:
    """The "no" exit of a decision with a "yes" exit sits beside it, not below it."""
    flowchart = laid_out(LOGIN_SPEC)
    by_id = {node.id: node for node in flowchart.nodes}
    valid, attempts = by_id["valid"], by_id["attempts"]
    assert attempts.y == valid.y
    assert attempts.x > valid.x + valid.width


def test_the_only_exit_of_a_decision_continues_down() -> None:
    """A "no" exit that is the decision's only way on goes down, as the canvas design shows."""
    flowchart = laid_out(LOGIN_SPEC)
    by_id = {node.id: node for node in flowchart.nodes}
    assert by_id["lock"].y > by_id["attempts"].y


def test_returning_line_runs_outside_the_flow() -> None:
    """A back edge goes around the nodes: none of its points lies inside a node."""
    flowchart = laid_out(LOGIN_SPEC)
    back = next(edge for edge in flowchart.edges if edge.role is Role.BACK)
    right_edge = max(node.x + node.width for node in flowchart.nodes)
    assert max(x for x, _ in back.points) > right_edge


def test_nodes_in_a_column_have_equal_widths() -> None:
    """The design asks for equal widths within a column."""
    flowchart = laid_out(ROOT / "examples" / "order-flow.spec.json")
    widths: dict[float, set[float]] = {}
    for node in flowchart.nodes:
        widths.setdefault(node.x + node.width / 2, set()).add(node.width)
    assert all(len(sizes) == 1 for sizes in widths.values())


def test_scene_survives_a_round_trip_through_json() -> None:
    """Saving a scene and reading it back gives the same scene."""
    flowchart = laid_out(LOGIN_SPEC)
    assert scene.parse(json.loads(scene.dumps(flowchart))) == flowchart


def test_layout_is_deterministic() -> None:
    """Building the same spec twice gives the same scene."""
    assert laid_out(LOGIN_SPEC) == laid_out(LOGIN_SPEC)


def test_spec_reports_every_problem_and_suggests_a_node() -> None:
    """A bad spec lists all problems, and a mistyped node id gets a suggestion."""
    bad = {
        "type": "flowchart",
        "nodes": [
            {"id": "pay", "kind": "process", "text": "Pay"},
            {"id": "done", "kind": "blob", "text": "Done"},
        ],
        "edges": [{"from": "payy", "to": "done", "role": "wiggly"}],
    }
    with pytest.raises(spec.SpecError) as error:
        spec.parse(bad)
    message = str(error.value)
    assert "did you mean 'pay'" in message
    assert "blob" in message
    assert "wiggly" in message


def test_spec_rejects_an_unknown_direction() -> None:
    """Only down and right are directions, and the error lists them."""
    bad = {"type": "flowchart", "direction": "diagonal", "nodes": [{"id": "a", "kind": "process"}]}
    with pytest.raises(spec.SpecError, match="down, right"):
        spec.parse(bad)


def test_spec_rejects_a_lane_without_lanes_and_a_missing_lane() -> None:
    """A node may name a lane only when lanes exist, and must name one when they do."""
    node = {"id": "a", "kind": "process", "lane": "x"}
    with pytest.raises(spec.SpecError, match="needs a 'lanes' list"):
        spec.parse({"type": "flowchart", "nodes": [node]})
    lanes = [{"id": "x", "label": "X"}]
    with pytest.raises(spec.SpecError, match="must be one of: x"):
        spec.parse({"type": "flowchart", "lanes": lanes, "nodes": [{"id": "a", "kind": "process"}]})


def test_left_to_right_flow_runs_along_x() -> None:
    """In a left-to-right chart the steps of a path have increasing x."""
    chart = laid_out(REFUND_SPEC)
    by_id = {node.id: node for node in chart.nodes}
    assert by_id["ask"].x < by_id["review"].x < by_id["eligible"].x < by_id["pay"].x


def test_every_node_sits_inside_its_lane() -> None:
    """A swimlane frame covers each of its nodes completely."""
    chart = laid_out(REFUND_SPEC)
    lane_of = {node.id: node.lane for node in spec.load(REFUND_SPEC).nodes}
    frames = {frame.id: frame for frame in chart.frames}
    for node in chart.nodes:
        frame = frames[f"lane-{lane_of[node.id]}"]
        assert frame.x <= node.x and node.x + node.width <= frame.x + frame.width
        assert frame.y <= node.y and node.y + node.height <= frame.y + frame.height


def test_overrides_move_a_node_and_a_route(tmp_path: Path) -> None:
    """An overrides file beside the spec changes the built scene, and only what it names."""
    spec_path = tmp_path / "chart.spec.json"
    spec_path.write_text(LOGIN_SPEC.read_text())
    plain = build.build(spec_path, tmp_path / "plain")
    (tmp_path / "chart.overrides.json").write_text(
        json.dumps({"nodes": {"dash": {"x": 500}}, "edges": {"e1": {"label_at": [5, 5]}}})
    )
    moved = build.build(spec_path, tmp_path / "moved")
    before = {node.id: node for node in scene.load(plain.scene_path).nodes}
    after = {node.id: node for node in scene.load(moved.scene_path).nodes}
    assert after["dash"].x == 500
    assert after["dash"].y == before["dash"].y
    assert after["start"] == before["start"]


def test_overrides_naming_a_missing_node_are_rejected() -> None:
    """An override for a node that does not exist is reported, not ignored."""
    chart = laid_out(LOGIN_SPEC)
    with pytest.raises(overrides.OverridesError, match="no such node"):
        overrides.apply(chart, overrides.parse({"nodes": {"ghost": {"x": 1}}}))


def test_build_command_writes_the_files(tmp_path: Path) -> None:
    """The build command writes the scene, the page and the draw.io file to the folder."""
    run = subprocess.run(
        [sys.executable, str(FLOW_CLI), "build", str(LOGIN_SPEC), "-o", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == EXIT_OK, run.stderr
    assert (tmp_path / "login-flow.scene.json").is_file()
    assert (tmp_path / "login-flow.html").is_file()
    assert (tmp_path / "login-flow.drawio").is_file()
    assert "no problems found" in run.stdout


def test_build_command_rejects_a_bad_spec(tmp_path: Path) -> None:
    """The build command lists the problems and exits with code 1."""
    path = tmp_path / "bad.spec.json"
    path.write_text(json.dumps({"type": "pie"}))
    run = subprocess.run(
        [sys.executable, str(FLOW_CLI), "build", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == EXIT_INVALID_INPUT
    assert "not a valid spec" in run.stderr


def hand_scene(nodes: list[dict], edges: list[dict]) -> Scene:
    """Build a scene from hand-written nodes and edges, on a 400 x 400 canvas.

    Args:
        nodes: Node objects in the JSON format.
        edges: Edge objects in the JSON format.

    Returns:
        The scene.
    """
    return scene.parse({"size": [400, 400], "nodes": nodes, "edges": edges})


def box(node_id: str, x: float, y: float) -> dict:
    """Return a 100 x 50 process node at the given position.

    Args:
        node_id: The node id.
        x: Left edge.
        y: Top edge.

    Returns:
        A node object in the JSON format.
    """
    return {"id": node_id, "shape": "process", "x": x, "y": y, "width": 100, "height": 50}


def test_check_finds_overlapping_nodes() -> None:
    """Two nodes that share area are reported as an error."""
    findings = check_scene(hand_scene([box("a", 10, 10), box("b", 60, 30)], []))
    assert [finding.code.value for finding in findings] == ["nodes-overlap"]


def test_check_finds_a_line_through_a_node() -> None:
    """A line that crosses a third node is reported."""
    nodes = [box("a", 10, 10), box("b", 10, 150), box("c", 10, 300)]
    edge = {"id": "e", "from": "a", "to": "c", "points": [[60, 60], [60, 300]]}
    codes = [finding.code.value for finding in check_scene(hand_scene(nodes, [edge]))]
    assert codes == ["line-through-node"]


def test_check_finds_a_node_outside_the_canvas() -> None:
    """A node that reaches past the canvas edge is reported."""
    findings = check_scene(hand_scene([box("a", 350, 10)], []))
    assert [finding.code.value for finding in findings] == ["outside-canvas"]


def test_check_counts_crossing_lines_as_warnings() -> None:
    """Two lines that cross are a warning, not an error."""
    nodes = [box("a", 10, 10), box("b", 250, 10), box("c", 130, 200), box("d", 130, 300)]
    edges = [
        {"id": "e1", "points": [[0, 100], [380, 100]]},
        {"id": "e2", "points": [[190, 60], [190, 400]]},
    ]
    findings = check_scene(hand_scene(nodes, edges))
    assert [finding.severity for finding in findings].count(Severity.WARNING) >= 1
    assert any(finding.code.value == "lines-cross" for finding in findings)
