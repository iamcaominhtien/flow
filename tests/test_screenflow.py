"""Tests for the screen flow of design 02: frames, fidelity, transitions, zones and round trips."""

import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib import build, import_drawio, render_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.check import Code, Severity, check_scene  # noqa: E402
from flowlib.diagrams import layout, screenflow  # noqa: E402
from flowlib.diagrams.screen_spec import uses_screen_features  # noqa: E402
from flowlib.model import ChipPlace, LabelKind, Node, Role, Scene, Shape, Tone  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402
from flowlib.screen_parts import PartKind, screen_parts  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

GAP_LABELLED_PX = 130
GAP_PLAIN_PX = 96


def screen(identifier: str, at: list[int], **keys: object) -> dict[str, object]:
    """Make a screen item of a spec."""
    return {"id": identifier, "label": identifier.upper(), "at": at, **keys}


def flow(screens: list[dict[str, object]], taps: list[dict[str, object]], **top: object) -> Scene:
    """Lay out a small screen flow."""
    return layout({"type": "screen", "screens": screens, "taps": taps, **top})


def node_of(scene: Scene, identifier: str) -> Node:
    """Return a node of a scene by its id."""
    return next(node for node in scene.nodes if node.id == identifier)


def build_example(name: str, tmp_path: Path) -> build.BuildResult:
    """Build an example spec into a temporary folder."""
    return build.build(EXAMPLES / name, tmp_path)


def test_a_spec_without_the_new_keys_is_still_drawn_as_plain_boxes() -> None:
    """The sign-up example of earlier versions keeps its look: boxes, no device frames."""
    raw = json.loads((EXAMPLES / "signup-screen.spec.json").read_text())
    assert not uses_screen_features(raw)
    scene = layout(raw)
    assert all(node.screen is None for node in scene.nodes)
    assert {node.shape for node in scene.nodes} >= {Shape.PROCESS, Shape.START}


def test_the_new_keys_switch_a_spec_to_the_screen_flow() -> None:
    """Any of the keys of design 02 selects the new drawing."""
    assert uses_screen_features({"screens": [{"id": "a", "device": "phone"}]})
    assert uses_screen_features({"screens": [], "taps": [{"from": "a", "to": "b", "guard": "x"}]})
    assert uses_screen_features({"zones": []})
    assert not uses_screen_features({"screens": [{"id": "a", "label": "A"}], "taps": []})


@pytest.mark.parametrize(
    ("keys", "size"),
    [
        ({"device": "phone"}, (156, 324)),
        ({"device": "phone", "size": "mini"}, (120, 240)),
        ({"device": "phone", "orientation": "landscape"}, (324, 156)),
        ({"device": "tablet"}, (164, 236)),
        ({"device": "tablet", "orientation": "landscape"}, (236, 164)),
        ({"device": "desktop"}, (240, 170)),
        ({"device": "watch"}, (80, 96)),
    ],
)
def test_frames_have_the_sizes_of_the_design_table(
    keys: dict[str, object], size: tuple[int, int]
) -> None:
    """Each device is drawn at the size of the frame sizes table."""
    scene = flow([screen("a", [0, 0], fidelity="L2", **keys)], [])
    node = node_of(scene, "a")
    assert (node.width, node.height) == size


def test_every_fidelity_level_has_the_same_width_and_centre_line() -> None:
    """Raising a screen from L0 to L2 never moves an arrow."""
    levels = ["L0", "L1", "L2", "L3"]
    screens = [
        screen(f"s{i}", [0, i], device="phone", fidelity=level) for i, level in enumerate(levels)
    ]
    taps = [{"from": f"s{i}", "to": f"s{i + 1}", "trigger": "tap"} for i in range(3)]
    scene = flow(screens, taps)
    nodes = [node_of(scene, f"s{i}") for i in range(4)]
    assert len({node.width for node in nodes}) == 1
    assert len({node.y + node.height / 2 for node in nodes}) == 1
    assert nodes[0].height < nodes[1].height
    assert len({round(edge.points[0][1]) for edge in scene.edges}) == 1


def test_the_id_chip_shows_the_code_the_state_and_the_overlay() -> None:
    """A state is written ``S31 · loading`` and an overlay ``S12 + modal``."""
    scene = flow(
        [
            screen("a", [0, 0], code="S31", state="loading", fidelity="L2"),
            screen("b", [0, 1], code="S12", overlay="modal", fidelity="L2"),
            screen("c", [0, 2]),
        ],
        [],
    )
    assert node_of(scene, "a").screen.code == "S31 · loading"
    assert node_of(scene, "b").screen.code == "S12 + modal"
    assert node_of(scene, "c").screen.code == "c"


def test_l1_draws_the_same_skeleton_and_l2_hatches_what_is_not_named() -> None:
    """L1 says content TBD; L2 names the elements, hatches the rest and dots the tapped one."""
    scene = flow(
        [
            screen("l1", [0, 0], fidelity="L1"),
            screen("l2", [0, 1], fidelity="L2", elements=["Buy"]),
        ],
        [],
    )
    theme = load_theme()
    one = screen_parts(node_of(scene, "l1"), theme)
    two = screen_parts(node_of(scene, "l2"), theme)
    assert any(part.text == "content TBD" for part in one)
    assert any(part.kind is PartKind.HATCH for part in two)
    assert any(part.text == "Buy" for part in two)
    dots = [p for p in two if p.kind is PartKind.CIRCLE and p.fill == theme.screen.hotspot_color]
    assert len(dots) == 1
    assert not any(part.kind is PartKind.HATCH for part in one)


def test_an_undecided_screen_is_a_dashed_card_with_a_tbd_tag_and_a_dashed_arrow() -> None:
    """Something still undecided is drawn as a card, and entered by a dashed arrow."""
    scene = flow(
        [screen("a", [0, 0], fidelity="L2"), screen("b", [0, 1], undecided=True)],
        [{"from": "a", "to": "b", "trigger": "tap Pay"}],
    )
    parts = screen_parts(node_of(scene, "b"), load_theme())
    assert parts[0].is_dashed
    assert any(part.text == "TBD" for part in parts)
    assert scene.edges[0].dashed


def test_the_gap_is_130_with_a_chip_and_96_without() -> None:
    """Frames are 130 px apart when the arrow carries a chip, and 96 px otherwise."""
    screens = [screen("a", [0, 0]), screen("b", [0, 1]), screen("c", [0, 2])]
    taps = [{"from": "a", "to": "b", "trigger": "tap"}, {"from": "b", "to": "c"}]
    scene = flow(screens, taps)
    a, b, c = (node_of(scene, name) for name in "abc")
    assert b.x - (a.x + a.width) == GAP_LABELLED_PX
    assert c.x - (b.x + b.width) == GAP_PLAIN_PX


def test_arrows_leave_the_middle_and_two_between_the_same_frames_use_the_thirds() -> None:
    """One arrow leaves the middle of an edge; a forward and a back arrow take the thirds."""
    one = flow([screen("a", [0, 0]), screen("b", [0, 1])], [{"from": "a", "to": "b"}])
    a = node_of(one, "a")
    assert one.edges[0].points[0][1] == a.y + a.height / 2
    two = flow(
        [screen("a", [0, 0]), screen("b", [0, 1])],
        [
            {"from": "a", "to": "b", "trigger": "tap"},
            {"from": "b", "to": "a", "kind": "back", "route": "direct"},
        ],
    )
    a = node_of(two, "a")
    forward, back = (edge.points[0][1] for edge in two.edges)
    assert forward == pytest.approx(a.y + a.height / 3)
    assert back == pytest.approx(a.y + 2 * a.height / 3)


def test_a_back_arrow_runs_in_a_strip_above_the_row() -> None:
    """A back arrow leaves the top of its frame and runs above the row."""
    scene = flow(
        [screen("a", [0, 0]), screen("b", [0, 1])],
        [{"from": "a", "to": "b"}, {"from": "b", "to": "a", "kind": "back", "trigger": "back"}],
    )
    back = scene.edges[1]
    top = node_of(scene, "a").y
    assert back.role is Role.BACK
    assert min(y for _, y in back.points) < top
    assert back.points[0][1] == top


def test_triggers_guards_and_effects_become_chips_and_words() -> None:
    """A user trigger is a dark chip, a system one slate with an icon; a guard is green or rose."""
    scene = flow(
        [screen("a", [0, 0]), screen("b", [0, 1]), screen("c", [1, 1])],
        [
            {"from": "a", "to": "b", "trigger": "tap Login", "guard": "valid", "effect": "save"},
            {
                "from": "a",
                "to": "c",
                "trigger": "auto 2 s",
                "system": "clock",
                "guard": "no",
                "kind": "failure",
            },
        ],
    )
    first, second = scene.edges
    assert first.label.kind is LabelKind.USER and first.label.text == "tap Login"
    assert [e.kind for e in first.extras] == [LabelKind.GUARD_OK, LabelKind.EFFECT]
    assert [e.text for e in first.extras] == ["[valid]", "/ save"]
    assert second.label.kind is LabelKind.SYSTEM and second.label.icon == "clock"
    assert second.extras[0].kind is LabelKind.GUARD_FAIL


def test_the_kind_of_a_transition_decides_its_line() -> None:
    """Main is blue, failure rose, back dashed slate, a guarded forward arrow green, else ink."""
    screens = [screen("a", [0, 0]), screen("b", [0, 1]), screen("c", [0, 2]), screen("d", [1, 0])]
    taps = [
        {"from": "a", "to": "b", "main": True},
        {"from": "b", "to": "c", "kind": "failure"},
        {"from": "c", "to": "a", "kind": "back"},
        {"from": "a", "to": "d", "guard": "ok"},
        {"from": "d", "to": "c"},
    ]
    roles = [edge.role for edge in flow(screens, taps).edges]
    assert roles == [Role.MAIN, Role.NO, Role.BACK, Role.YES, Role.NEXT]


def test_coded_conditions_put_a_code_on_the_arrow_and_the_text_in_a_table() -> None:
    """In coded mode the arrow carries C1, C2 and a table next to the diagram has the words."""
    scene = flow(
        [screen("a", [0, 0]), screen("b", [0, 1]), screen("c", [0, 2])],
        [
            {"from": "a", "to": "b", "trigger": "tap", "guard": "token is not expired"},
            {"from": "b", "to": "c", "trigger": "wait", "effect": "load"},
        ],
        conditions="coded",
    )
    assert [edge.label.text for edge in scene.edges] == ["C1", "C2"]
    assert all(edge.label.kind is LabelKind.CODE and not edge.extras for edge in scene.edges)
    table = node_of(scene, "conditions")
    assert table.shape is Shape.TABLE
    assert [row.flags for row in table.sections[0]] == [("C1",), ("C2",)]
    assert "[token is not expired]" in table.sections[0][0].right
    assert table.y > max(node.y + node.height for node in scene.nodes if node is not table)


def test_zones_are_dashed_tinted_frames_and_the_web_flow_sits_below_the_app_flow() -> None:
    """Each zone is a frame with a label and a tone; a desktop flow is laid out under the phones."""
    scene = flow(
        [
            screen("p1", [0, 0], zone="app"),
            screen("p2", [0, 1], zone="app"),
            screen("w1", [1, 0], zone="web", device="desktop"),
        ],
        [{"from": "p1", "to": "p2"}, {"from": "p2", "to": "w1"}],
        zones=[{"id": "app", "label": "App", "tone": "blue"}, {"id": "web", "label": "Web"}],
    )
    frames = {frame.id: frame for frame in scene.frames}
    assert frames["zone-app"].tone is Tone.BLUE and frames["zone-app"].label == "App"
    assert frames["zone-web"].y > frames["zone-app"].y + frames["zone-app"].height
    assert node_of(scene, "p1").tone is Tone.BLUE


def test_entry_points_are_green_pills_in_a_left_column_and_flags_are_off_page_marks() -> None:
    """Entries sit left of the flow in a green zone; a flag names another diagram."""
    scene = flow(
        [
            {"id": "app", "kind": "entry", "label": "App icon", "detail": "cold start"},
            screen("a", [0, 0]),
            {
                "id": "out",
                "kind": "flag",
                "label": "To Checkout flow",
                "detail": "diagram 02",
                "at": [0, 1],
            },
        ],
        [{"from": "app", "to": "a", "trigger": "tap app icon"}, {"from": "a", "to": "out"}],
    )
    entry = node_of(scene, "app")
    assert entry.shape is Shape.TERMINATOR and entry.x < node_of(scene, "a").x
    assert node_of(scene, "out").shape is Shape.FLAG
    entries = next(frame for frame in scene.frames if frame.id == "zone-entries")
    assert entries.tone is Tone.GREEN and entries.x < entry.x


def test_a_tab_bar_is_drawn_once_as_a_bus() -> None:
    """One line goes into all tabs, with one chip, instead of a pair of arrows per tab."""
    tabs = [{"id": f"t{i}", "kind": "tab", "label": f"Tab {i}", "at": [0, i]} for i in range(4)]
    scene = flow(
        tabs + [screen(f"s{i}", [1, i], tab=i) for i in range(4)],
        [{"from": f"t{i}", "to": f"s{i}"} for i in range(4)],
        buses=[{"trigger": "tap any tab", "to": [f"t{i}" for i in range(4)]}],
    )
    bus = next(edge for edge in scene.edges if edge.id == "bus0")
    drops = [edge for edge in scene.edges if edge.id.startswith("bus0>")]
    assert bus.label.text == "tap any tab" and len(drops) == 4
    assert all(drop.points[0][1] == bus.points[0][1] for drop in drops)
    assert node_of(scene, "s1").screen.tab_active == 1


def test_a_decision_is_a_diamond_with_no_id_and_a_system_chip() -> None:
    """A decision has a name and an optional event that decides it."""
    scene = flow(
        [
            screen("a", [0, 0]),
            {
                "id": "d",
                "kind": "decision",
                "label": "Payment ok?",
                "trigger": "API result",
                "system": "cloud",
                "at": [0, 1],
            },
        ],
        [{"from": "a", "to": "d", "trigger": "tap Pay"}],
    )
    decision = node_of(scene, "d")
    assert decision.shape is Shape.DECISION and decision.screen is None
    assert decision.chip.kind is LabelKind.SYSTEM and decision.chip.icon == "cloud"


def test_a_retry_runs_round_the_outside_and_an_id_chip_moves_off_an_arrow() -> None:
    """A retry that cannot turn once runs outside the columns; the chip leaves the arrow's way."""
    screens = [
        screen("hub", [0, 1], code="S31", state="loading", size="mini", fidelity="L2"),
        screen("data", [1, 0], fidelity="L2"),
        screen("mid", [1, 1], code="S31", state="empty", size="mini", fidelity="L2"),
    ]
    taps = [
        {"from": "hub", "to": "data"},
        {"from": "hub", "to": "mid"},
        {"from": "data", "to": "hub", "kind": "retry", "trigger": "pull"},
    ]
    scene = flow(screens, taps)
    retry = scene.edges[2]
    assert min(x for x, _ in retry.points) < node_of(scene, "data").x
    assert node_of(scene, "mid").screen.chip_place is ChipPlace.BELOW


def test_a_screen_with_the_wrong_keys_is_reported_in_full() -> None:
    """Every problem is listed, with where it is."""
    spec = {
        "type": "screen",
        "screens": [
            {"id": "a", "device": "fridge", "at": [0]},
            {"id": "b", "fidelity": "L9", "overlay": "popup", "tab": 9},
        ],
        "taps": [{"from": "a", "to": "zzz", "kind": "sideways"}],
    }
    with pytest.raises(SpecError) as problem:
        layout(spec)
    text = str(problem.value)
    for wanted in ("device", "'at'", "fidelity", "overlay", "tab", "zzz", "kind"):
        assert wanted in text


def test_two_screens_in_one_cell_are_refused() -> None:
    """A cell holds one screen."""
    with pytest.raises(SpecError, match="both at"):
        flow([screen("a", [0, 0], device="phone"), screen("b", [0, 0])], [])


def test_the_check_warns_about_words_that_are_too_long_for_an_arrow() -> None:
    """Design 02 sends a condition of more than about 20 characters to a table."""
    scene = flow(
        [screen("a", [0, 0]), screen("b", [0, 1])],
        [{"from": "a", "to": "b", "guard": "token exists and is not expired"}],
    )
    findings = check_scene(scene)
    assert any(finding.code.value == "label-too-long" for finding in findings)
    assert not [f for f in findings if f.severity is Severity.ERROR]


@pytest.mark.parametrize("name", sorted(path.name for path in EXAMPLES.glob("*screen*.spec.json")))
def test_every_screen_example_builds_without_errors(name: str, tmp_path: Path) -> None:
    """The examples of the screen flow build, and the checks find no error."""
    result = build_example(name, tmp_path)
    assert not [f for f in result.findings if f.severity is Severity.ERROR]


def test_the_shop_example_has_the_screens_and_decisions_of_the_design(tmp_path: Path) -> None:
    """Phone: 14 screens and 2 decisions; web: 8 screens and 1 decision, in four zones."""
    scene = scene_io.load(build_example("shop-screen-flow.spec.json", tmp_path).scene_path)
    screens = [node for node in scene.nodes if node.screen]
    phone = [node for node in screens if node.screen.code.startswith("S")]
    web = [node for node in screens if node.screen.code.startswith("W")]
    decisions = [node for node in scene.nodes if node.shape is Shape.DECISION]
    assert (len(phone), len(web), len(decisions)) == (14, 8, 3)
    assert len(scene.frames) == 4
    assert min(node.y for node in web) > max(node.y + node.height for node in phone)


def test_the_scene_round_trip_keeps_screens_chips_and_words(tmp_path: Path) -> None:
    """Writing a scene as JSON and reading it again gives the same scene."""
    scene = scene_io.load(build_example("shop-screen-flow.spec.json", tmp_path).scene_path)
    again = scene_io.parse(json.loads(scene_io.dumps(scene)))
    assert again == scene


def test_the_html_has_the_parts_of_a_screen_and_the_chips_of_a_transition(tmp_path: Path) -> None:
    """The page shows the device frame, the placeholder text, a hotspot and the chips."""
    scene = scene_io.load(build_example("shop-screen-flow.spec.json", tmp_path).scene_path)
    page = render_html.render(scene)
    for wanted in ("content TBD", "other content", "tap Login", "[session valid]", "/ save token"):
        assert wanted in page
    assert load_theme().screen.hotspot_color in page


def test_the_drawio_file_holds_the_screens_and_is_read_back(tmp_path: Path) -> None:
    """The draw.io file keeps each screen, its chips and its words, and imports to the same flow."""
    result = build_example("shop-screen-flow.spec.json", tmp_path)
    scene = scene_io.load(result.scene_path)
    xml = render_drawio.render(scene)
    assert "flowScreen=" in xml and "part-s10-" in xml
    imported = import_drawio.convert(result.drawio_path).scene
    screens = [node for node in imported.nodes if node.screen]
    originals = [node for node in scene.nodes if node.screen]
    assert len(screens) == len(originals)
    assert {n.screen.code for n in screens} == {n.screen.code for n in originals}
    assert len(imported.edges) == len(scene.edges)
    assert sum(len(e.extras) for e in imported.edges) == sum(len(e.extras) for e in scene.edges)
    assert {e.role for e in imported.edges} >= {Role.YES, Role.NO, Role.BACK}
    assert any(node.chip is not None for node in imported.nodes)


def test_layout_raw_falls_back_to_the_plain_boxes() -> None:
    """The entry point of the type draws an old spec with the graph layout."""
    scene = screenflow.layout_raw(
        {"type": "screen", "screens": [{"id": "a", "label": "A"}], "taps": []}
    )
    assert scene.nodes[0].shape is Shape.PROCESS


def test_modal_buttons_that_do_not_fit_side_by_side_are_stacked() -> None:
    """On a mini phone two modal buttons go one under the other, so their names are not cut."""
    elements = [{"text": "Cancel", "on": "overlay"}, {"text": "Delete", "on": "overlay"}]
    keys = {"size": "mini", "fidelity": "L2", "overlay": "modal", "elements": elements}
    scene = flow([screen("S1", [0, 0], **keys)], [])
    node = node_of(scene, "S1")
    theme = load_theme()
    buttons = [
        part
        for part in screen_parts(node, theme)
        if part.kind is PartKind.TEXT and part.text in ("Cancel", "Delete")
    ]
    assert buttons[0].bounds[0] == buttons[1].bounds[0]
    assert buttons[0].bounds[1] < buttons[1].bounds[1]
    assert not [f for f in check_scene(scene) if f.code is Code.TEXT_MAY_NOT_FIT]
