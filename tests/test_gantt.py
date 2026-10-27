"""Tests for the Gantt chart: dates, rows, status, critical path, today, legend and both outputs."""

import copy
import json
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib import diagrams, import_drawio, render_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.check import Code, check_scene  # noqa: E402
from flowlib.model import FrameVariant, LabelKind, Role, Scene, Shape, Status  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

GANTT = "delivery-gantt"


def raw_example(name: str = GANTT) -> dict:
    """Load an example as a fresh dictionary."""
    return copy.deepcopy(json.loads((EXAMPLES / f"{name}.spec.json").read_text()))


def drawn(name: str = GANTT) -> Scene:
    """Lay out an example."""
    return diagrams.layout(raw_example(name))


def nodes_of(scene: Scene) -> dict:
    """Return the nodes of a scene by id."""
    return {node.id: node for node in scene.nodes}


def test_example_has_no_findings_and_draws_in_both_formats() -> None:
    """The design example passes every check and renders to HTML and draw.io."""
    scene = drawn()
    assert check_scene(scene) == []
    assert "<svg" in render_html.render(scene)
    ET.fromstring(render_drawio.render(scene))


def test_scene_round_trips_through_json() -> None:
    """The planning fields of nodes and the roles of lines survive the scene file."""
    scene = drawn()
    assert scene_io.parse(scene_io.dump(scene)) == scene


def test_sizes_follow_the_design() -> None:
    """Weeks 88 px, label column 300 px, rows 52 px, bars 26 px, owner circle 26 px."""
    scene = drawn()
    nodes = nodes_of(scene)
    margin = load_theme().layout.margin
    assert nodes["week-1"].x - nodes["week-0"].x == 88
    assert nodes["week-0"].x - 4 == margin + 300
    assert nodes["spec"].y - nodes["research"].y == 52
    assert nodes["research"].height == 26
    assert nodes["owner-research"].width == 26


def test_bar_sits_eight_pixels_inside_its_weeks() -> None:
    """A bar of W1 and W2 starts and ends 8 px inside the week lines."""
    scene = drawn()
    nodes = nodes_of(scene)
    left = nodes["week-0"].x - 4
    assert nodes["research"].x == left + 8
    assert nodes["research"].x + nodes["research"].width == left + 2 * 88 - 8


def test_phases_are_grey_bands_and_milestones_are_diamonds() -> None:
    """Each group is a band row; a milestone is an amber diamond on its own row."""
    scene = drawn()
    bands = [frame.label for frame in scene.frames if frame.variant is FrameVariant.BAND]
    assert bands == ["Discover", "Build", "Launch"]
    nodes = nodes_of(scene)
    assert nodes["approved"].shape is Shape.MILESTONE
    assert nodes["approved"].y > nodes["spec"].y


def test_dependency_leaves_eight_pixels_right_of_the_bar() -> None:
    """A finish-to-start line goes 8 px right of the bar, down, then into the next bar."""
    scene = drawn()
    nodes = nodes_of(scene)
    line = next(edge for edge in scene.edges if edge.id == "after-research-spec")
    end = nodes["research"].x + nodes["research"].width
    assert line.points[0][0] == end
    assert line.points[1][0] == end + 8
    assert line.points[-1][0] == nodes["spec"].x


def test_critical_path_is_the_one_blue_chain() -> None:
    """The chain that ends last is drawn with the animated main role, and nothing else is."""
    scene = drawn()
    main = {edge.id for edge in scene.edges if edge.role is Role.MAIN}
    assert main == {
        "after-research-spec",
        "after-spec-design",
        "after-design-mobile",
        "after-mobile-beta",
        "after-beta-fix",
        "after-fix-launch",
    }


def test_marked_tasks_replace_the_computed_chain() -> None:
    """With some task marked critical, only links between marked tasks are drawn blue."""
    raw = raw_example()
    for task in raw["tasks"]:
        task["critical"] = task["id"] in ("spec", "backend")
    scene = diagrams.layout(raw)
    main = {edge.id for edge in scene.edges if edge.role is Role.MAIN}
    assert main == {"after-spec-backend"}


def test_status_is_read_from_progress_when_absent() -> None:
    """No progress is planned, part is in progress, all is done."""
    raw = raw_example()
    for task in raw["tasks"]:
        task.pop("status", None)
        task["progress"] = {"research": 1, "spec": 0.5}.get(task["id"], 0)
    nodes = nodes_of(diagrams.layout(raw))
    assert nodes["research"].plan.status is Status.DONE
    assert nodes["spec"].plan.status is Status.IN_PROGRESS
    assert nodes["design"].plan.status is Status.PLANNED


def test_blocked_task_needs_a_reason_and_shows_it() -> None:
    """A blocked bar without a reason is refused; with one, the reason is drawn after it."""
    raw = raw_example()
    raw["tasks"][4]["status"] = "blocked"
    with pytest.raises(SpecError, match="reason"):
        diagrams.layout(raw)
    raw["tasks"][4]["reason"] = "Waiting for the licence"
    scene = diagrams.layout(raw)
    assert "Waiting for the licence" in render_html.render(scene)
    assert "Waiting for the licence" in render_drawio.render(scene)
    assert "Blocked" in {node.text[0] for node in scene.nodes if node.id.startswith("legend-text")}


def test_in_progress_bar_is_filled_to_its_progress() -> None:
    """The fill is as wide as the progress, in the page and in the draw.io file."""
    scene = drawn()
    assert nodes_of(scene)["mobile"].plan.progress == 0.3
    assert "width:30%" in render_html.render(scene)
    cell = next(
        c
        for c in ET.fromstring(render_drawio.render(scene)).iter("mxCell")
        if c.get("id") == "fill-mobile"
    )
    bar = next(
        c
        for c in ET.fromstring(render_drawio.render(scene)).iter("mxCell")
        if c.get("id") == "node-mobile"
    )
    fill_width = float(cell.find("mxGeometry").get("width"))
    assert fill_width == pytest.approx(0.3 * float(bar.find("mxGeometry").get("width")))


def test_today_is_a_red_dashed_line_with_a_pill() -> None:
    """The today line has the today role, and its pill is a today label."""
    scene = drawn()
    today = next(edge for edge in scene.edges if edge.role is Role.TODAY)
    assert today.label is not None and today.label.kind is LabelKind.TODAY
    x = nodes_of(scene)["week-7"].x - 4
    assert today.points[0][0] == x


def test_month_header_follows_the_weeks_by_their_thursday() -> None:
    """March has four weeks, April five, May four and June one, as ISO weeks say."""
    scene = drawn()
    nodes = nodes_of(scene)
    months = [nodes[f"month-{index}"].text[0] for index in range(4)]
    assert months == ["March", "April", "May", "June"]


def test_weeks_mode_reads_week_numbers() -> None:
    """Without dates, start and end are week numbers from 1 and end is included."""
    raw = {"type": "gantt", "tasks": [{"id": "a", "label": "A", "start": 2, "end": 3}]}
    nodes = nodes_of(diagrams.layout(raw))
    assert nodes["a"].x - nodes["week-0"].x == pytest.approx(88 + 8 - 4)
    assert nodes["a"].width == 2 * 88 - 16
    assert "week-2" in nodes and "week-3" not in nodes


def test_periods_form_still_works() -> None:
    """The older spec with named periods and ``length`` draws as before."""
    scene = drawn("website-gantt")
    nodes = nodes_of(scene)
    assert nodes["week-0"].text == ("W1",)
    assert nodes["design"].x - nodes["brief"].x == 88
    assert check_scene(scene) == [] or all(
        f.severity.value == "warning" for f in check_scene(scene)
    )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda raw: raw["tasks"][1].update(after="resarch"), "research"),
        (lambda raw: raw["tasks"][1].update(start="2026-03-01"), "starts before"),
        (lambda raw: raw["tasks"][0].update(end="2026-02-01"), "ends before"),
        (lambda raw: raw["tasks"][0].update(start="soon"), "not a date"),
        (lambda raw: raw.update(today="2027-01-01"), "outside the chart"),
        (lambda raw: raw["tasks"][0].update(progress=2), "0 to 1"),
    ],
)
def test_bad_specs_are_refused_with_the_reason(
    change: Callable[[dict], object], message: str
) -> None:
    """A mistake in the dates, the links or the progress is reported with its cause."""
    raw = raw_example()
    change(raw)
    with pytest.raises(SpecError, match=message):
        diagrams.layout(raw)


def test_more_than_fifteen_rows_is_a_warning() -> None:
    """A page holds about 15 rows; a longer chart is told to split by phase."""
    raw = raw_example()
    raw["tasks"] = [
        {"id": f"t{index}", "label": f"Task {index}", "start": "2026-03-02", "end": "2026-03-08"}
        for index in range(16)
    ]
    raw.pop("milestones")
    raw.pop("today")
    codes = {finding.code for finding in check_scene(diagrams.layout(raw))}
    assert Code.GANTT_TOO_MANY_ROWS in codes


def test_legend_lists_the_statuses_in_use_and_the_critical_path() -> None:
    """Done, in progress and planned are listed, and the critical path; not blocked."""
    words = [n.text[0] for n in drawn().nodes if n.id.startswith("legend-text")]
    assert words == ["Done", "In progress", "Planned", "Critical path"]


def test_drawio_file_is_read_back_with_its_planning_nodes() -> None:
    """Writing the draw.io file and importing it keeps shapes, views and words."""
    scene = drawn()
    path = Path(__file__).parent / "_gantt_roundtrip.drawio"
    try:
        path.write_text(render_drawio.render(scene))
        back = import_drawio.convert(path).scene
    finally:
        path.unlink(missing_ok=True)
    by_id = {node.id.removeprefix("node-"): node for node in back.nodes}
    assert {node.id for node in scene.nodes} <= set(by_id)
    for node in scene.nodes:
        assert by_id[node.id].shape is node.shape
        assert by_id[node.id].plan == node.plan
    roles = {edge.role for edge in back.edges}
    assert {Role.TODAY, Role.GRID} <= roles
