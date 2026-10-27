"""Tests for the wireframe of design 10: blocks on a grid, notes, state and responsive sets."""

import copy
import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib import build, diagrams, import_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.check import Code, Severity, check_scene  # noqa: E402
from flowlib.model import BlockKind, Scene  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

NAMES = ["mobile", "desktop", "states", "responsive"]
PHONE_SIZE = (330, 680)
DESKTOP_SIZE = (1320, 760)
FIGURE_COUNT = 4
FOUR_STATES = 4


def spec_of(name: str) -> dict:
    """Read an example spec."""
    return json.loads((EXAMPLES / f"wireframe-{name}.spec.json").read_text())


def phone(blocks: list[dict], **keys: object) -> dict:
    """Make a one-screen wireframe spec."""
    return {"type": "wireframe", "screens": [{"label": "S", "blocks": blocks, **keys}]}


def screens_of(scene: Scene) -> list:
    """Return the nodes that are screens, not notes."""
    return [n for n in scene.nodes if n.screen and not n.screen.is_bare]


def findings_of(raw: dict) -> list:
    """Lay out a spec and check it."""
    return check_scene(diagrams.layout(raw))


@pytest.mark.parametrize("name", NAMES)
def test_examples_build_without_errors_or_warnings(name: str, tmp_path: Path) -> None:
    """Each design example builds both files and the checks find nothing."""
    result = build.build(EXAMPLES / f"wireframe-{name}.spec.json", tmp_path)
    assert result.findings == []
    assert result.html_path.read_text().startswith("<!")
    assert "<mxfile" in result.drawio_path.read_text()
    assert result.scene_path.exists()


def test_mobile_has_three_phone_screens_and_twelve_numbered_notes() -> None:
    """The checkout example: 3 phones of 330 x 680 and notes 1 to 12."""
    scene = diagrams.layout(spec_of("mobile"))
    screens = screens_of(scene)
    assert [(n.width, n.height) for n in screens] == [PHONE_SIZE] * 3
    notes = [n for n in scene.nodes if n.screen and n.screen.is_bare]
    assert [n.screen.blocks[0].value for n in notes] == [str(i) for i in range(1, 13)]


def test_desktop_frame_and_grid_columns() -> None:
    """Desktop is 1320 x 760; four figures share a row and each spans three columns."""
    scene = diagrams.layout(spec_of("desktop"))
    (screen,) = screens_of(scene)
    assert (screen.width, screen.height) == DESKTOP_SIZE
    from flowlib.wire_layout import plan_screen

    plan = plan_screen(screen.screen, load_theme())
    figures = [i for i, b in enumerate(screen.screen.blocks) if b.kind is BlockKind.FIGURE]
    assert len(figures) == FIGURE_COUNT
    boxes = [plan.boxes[i] for i in figures]
    assert len({round(box[1]) for box in boxes}) == 1
    assert [round(box[0]) for box in boxes] == sorted(round(box[0]) for box in boxes)
    margin, gap = 28, 16
    assert round(boxes[1][0] - boxes[0][0] - boxes[0][2]) == gap
    assert round(boxes[0][0]) == 220 + margin


def test_state_set_has_four_screens_in_order() -> None:
    """A state set draws normal, loading, empty and error, each with its block."""
    scene = diagrams.layout(spec_of("states"))
    states = [n.screen.state.value for n in screens_of(scene)]
    assert states == ["normal", "loading", "empty", "error"]
    kinds = [{b.kind for b in n.screen.blocks} for n in screens_of(scene)]
    assert BlockKind.LOADING in kinds[1]
    assert BlockKind.EMPTY in kinds[2]
    assert BlockKind.ERROR in kinds[3]


def test_state_set_without_a_state_is_refused() -> None:
    """Three of the four states fail and the message names the missing one."""
    raw = spec_of("states")
    raw["screens"].pop()
    with pytest.raises(SpecError, match="missing: error"):
        diagrams.layout(raw)


def test_responsive_set_has_equal_heights_and_shared_numbers() -> None:
    """Three widths, the same height, and one note number shared by two screens."""
    scene = diagrams.layout(spec_of("responsive"))
    screens = screens_of(scene)
    assert [n.screen.device.value for n in screens] == ["desktop", "tablet", "phone"]
    assert len({n.height for n in screens}) == 1
    assert [n.width for n in screens] == [760, 470, 230]
    numbers = [[b.number for b in n.screen.badges] for n in screens]
    assert numbers == [["2", "3"], ["1"], ["1", "3"]]


def test_responsive_set_without_a_width_is_refused() -> None:
    """Desktop and phone only: the tablet is missing."""
    raw = spec_of("responsive")
    del raw["screens"][1]
    with pytest.raises(SpecError, match="missing: tablet"):
        diagrams.layout(raw)


def test_two_primary_buttons_are_an_error() -> None:
    """One primary button per screen: the second makes an error finding."""
    raw = phone([{"kind": "button", "text": "Pay"}, {"kind": "button", "text": "Save"}])
    errors = [f for f in findings_of(raw) if f.severity is Severity.ERROR]
    assert [f.code for f in errors] == [Code.WIREFRAME_TWO_PRIMARY]


def test_secondary_buttons_are_not_counted() -> None:
    """A primary and an outlined button is fine."""
    raw = phone(
        [
            {"kind": "button", "text": "Pay"},
            {"kind": "button", "text": "Back", "style": "secondary"},
        ]
    )
    assert findings_of(raw) == []


def test_a_modal_has_its_own_primary_action() -> None:
    """The primary button under a modal and the one in the modal do not count together."""
    raw = phone(
        [
            {"kind": "button", "text": "Delete account", "style": "danger"},
            {"kind": "button", "text": "Pay"},
            {"kind": "modal", "text": "Delete?", "items": ["Cancel", "Delete"]},
        ]
    )
    assert findings_of(raw) == []


def test_table_primary_buttons_are_counted() -> None:
    """Two primary buttons in one table are two primary actions."""
    columns = [{"label": "A"}, {"label": "", "kind": "button"}]
    cell = {"text": "Accept", "style": "primary"}
    table = {"kind": "table", "columns": columns, "data": [["x", cell], ["y", cell]]}
    errors = [f for f in findings_of(phone([table])) if f.severity is Severity.ERROR]
    assert errors


def test_badge_over_text_is_a_warning() -> None:
    """A badge centred on the left end of a title covers its first letters."""
    raw = phone(
        [{"kind": "list_item", "id": "a", "text": "Pad thai"}],
        annotations=[{"target": "a", "part": "title", "corner": "tl", "title": "T", "text": "x"}],
    )
    assert Code.WIREFRAME_BADGE_ON_TEXT in {f.code for f in findings_of(raw)}


def test_placeholder_words_are_a_warning() -> None:
    """A button that says Button has no real words."""
    codes = {f.code for f in findings_of(phone([{"kind": "button", "text": "Button"}]))}
    assert Code.WIREFRAME_PLACEHOLDER in codes


def test_unknown_annotation_target_and_part_are_refused() -> None:
    """A note must point at a block id, and at a part the block has."""
    base = phone([{"kind": "button", "id": "go", "text": "Go"}])
    bad_target = copy.deepcopy(base)
    bad_target["screens"][0]["annotations"] = [{"target": "gos", "title": "t", "text": "x"}]
    with pytest.raises(SpecError, match="did you mean 'go'"):
        diagrams.layout(bad_target)
    bad_part = copy.deepcopy(base)
    bad_part["screens"][0]["annotations"] = [
        {"target": "go", "part": "wheel", "title": "t", "text": "x"}
    ]
    with pytest.raises(SpecError, match="has no part 'wheel'"):
        diagrams.layout(bad_part)


def test_unknown_block_kind_and_second_style_are_refused() -> None:
    """Block kinds are a closed set and a wireframe has one style."""
    with pytest.raises(SpecError, match="unknown kind 'carousel'"):
        diagrams.layout(phone([{"kind": "carousel"}]))
    raw = phone([{"kind": "button", "text": "Go"}])
    raw["style"] = "illustrated"
    with pytest.raises(SpecError, match="one style"):
        diagrams.layout(raw)


def test_blocks_are_placed_by_row_column_and_span() -> None:
    """Two blocks with columns share a row; a block with no row goes below."""
    raw = phone(
        [
            {"kind": "button", "text": "One", "span": 6, "style": "secondary"},
            {"kind": "button", "text": "Two", "col": 7, "span": 6, "style": "secondary"},
            {"kind": "button", "text": "Three", "style": "secondary"},
        ]
    )
    from flowlib.wire_layout import plan_screen

    (screen,) = screens_of(diagrams.layout(raw))
    boxes = plan_screen(screen.screen, load_theme()).boxes
    assert boxes[0][1] == boxes[1][1] < boxes[2][1]
    assert boxes[1][0] > boxes[0][0] + boxes[0][2]
    assert boxes[2][2] > boxes[0][2] * 2


def test_older_elements_still_build() -> None:
    """The header, text, input, button, image and list kinds are stacked as blocks."""
    raw = json.loads((EXAMPLES / "login-wireframe.spec.json").read_text())
    scene = diagrams.layout(raw)
    kinds = {b.kind for n in screens_of(scene) for b in n.screen.blocks}
    assert {BlockKind.NAVBAR, BlockKind.FORM_FIELD, BlockKind.LIST_ITEM} <= kinds
    assert not [f for f in check_scene(scene) if f.severity is Severity.ERROR]


def test_a_wireframe_does_not_animate(tmp_path: Path) -> None:
    """Nothing moves: no animated line in the page and no draw.io flow animation."""
    result = build.build(EXAMPLES / "wireframe-states.spec.json", tmp_path)
    page = result.html_path.read_text() + result.drawio_path.read_text()
    assert 'class="flow' not in page
    assert "flowAnimation" not in page
    assert "<animate" not in page


def test_palette_is_grey_with_blue_rose_green_and_amber_only() -> None:
    """The wireframe palette is the one of design 10 section 1."""
    colors = load_theme().wire.colors
    assert (colors.line, colors.fill, colors.text) == ("#CBD5E1", "#F1F5F9", "#334155")


def test_scene_round_trip_keeps_blocks_and_badges() -> None:
    """The scene file holds every block and badge; reading it back changes nothing."""
    scene = diagrams.layout(spec_of("desktop"))
    again = scene_io.parse(json.loads(scene_io.dumps(scene)))
    assert again == scene


def test_drawio_round_trip_keeps_the_screen_blocks(tmp_path: Path) -> None:
    """A draw.io file written by Flow reads back with the blocks of each screen."""
    result = build.build(EXAMPLES / "wireframe-mobile.spec.json", tmp_path)
    original = diagrams.layout(spec_of("mobile"))
    imported = import_drawio.convert(result.drawio_path).scene
    back = [n.screen.blocks for n in imported.nodes if n.screen and not n.screen.is_bare]
    assert back == [n.screen.blocks for n in screens_of(original)]


def test_html_draws_the_tap_dot_and_every_badge(tmp_path: Path) -> None:
    """Every badge number is in the page; the tap dot is drawn on the primary button."""
    scene = diagrams.layout(spec_of("mobile"))
    page = render_html.render(scene)
    for number in range(1, 13):
        assert f">{number}</div>" in page
    assert "#DC2626" in page


def test_screen_flow_at_l3_uses_the_same_blocks() -> None:
    """A flow screen with blocks is a wireframe at a smaller size, with its id chip."""
    raw = json.loads((EXAMPLES / "shop-wireframe-screen-flow.spec.json").read_text())
    scene = diagrams.layout(raw)
    node = next(n for n in scene.nodes if n.id == "s01")
    assert node.screen.blocks
    assert node.width == pytest.approx(PHONE_SIZE[0] * node.screen.scale)
    assert node.screen.code == "S01"
    assert not [f for f in check_scene(scene) if f.severity is Severity.ERROR]


def test_blocks_need_fidelity_l3_in_a_flow() -> None:
    """Blocks on a screen that is not at L3 are refused."""
    raw = {
        "type": "screen",
        "screens": [
            {
                "id": "a",
                "label": "A",
                "at": [0, 0],
                "fidelity": "L2",
                "blocks": [{"kind": "button", "text": "Go"}],
            }
        ],
        "taps": [],
    }
    with pytest.raises(SpecError, match="fidelity L3"):
        diagrams.layout(raw)
