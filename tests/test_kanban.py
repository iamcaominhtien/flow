"""Tests for the Kanban board: columns, cards, limits, done cards, owners and the comparison."""

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
from flowlib.diagrams.people import person_of  # noqa: E402
from flowlib.model import PillKind, Scene, Shape, Status  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402

BOARD = "delivery-kanban"
COMPARE = "sprint-kanban"


def raw_example(name: str = BOARD) -> dict:
    """Load an example as a fresh dictionary."""
    return copy.deepcopy(json.loads((EXAMPLES / f"{name}.spec.json").read_text()))


def drawn(raw: dict | None = None) -> Scene:
    """Lay out a spec, the board example by default."""
    return diagrams.layout(raw if raw is not None else raw_example())


def cards_of(scene: Scene) -> dict:
    """Return the cards of a scene by id."""
    return {n.id: n for n in scene.nodes if n.shape is Shape.KANBAN_CARD}


def test_example_has_no_findings_and_draws_in_both_formats() -> None:
    """The design example passes every check and renders to HTML, draw.io and scene.json."""
    scene = drawn()
    assert check_scene(scene) == []
    assert "Live order tracking" in render_html.render(scene)
    ET.fromstring(render_drawio.render(scene))
    assert scene_io.parse(scene_io.dump(scene)) == scene


def test_sizes_follow_the_design() -> None:
    """Columns are 360 px wide, cards 100 px high; cards of a column are 128 px apart."""
    scene = drawn()
    assert {frame.width for frame in scene.frames} == {360}
    cards = cards_of(scene)
    assert {card.height for card in cards.values()} == {100}
    assert cards["c0-1"].y - cards["c0-0"].y == 128
    assert len(scene.frames) == 4


def test_cards_keep_the_order_written() -> None:
    """The first card written is the highest in its column."""
    ys = [card.y for card in cards_of(drawn()).values() if card.id.startswith("c1-")]
    assert ys == sorted(ys)
    assert [n.text[0] for n in cards_of(drawn()).values()][:2] == ["Courier tips", "Refund screen"]


def test_limit_pill_is_red_when_the_column_is_full() -> None:
    """A column with a limit shows ``3 / 3``, in the full kind; below its limit it is an outline."""
    scene = drawn()
    pill = next(n for n in scene.nodes if n.id == "count-1")
    assert (pill.text, pill.plan.pill) == (("3 / 3",), PillKind.FULL)
    raw = raw_example()
    raw["columns"][1]["limit"] = 4
    roomy = next(n for n in drawn(raw).nodes if n.id == "count-1")
    assert (roomy.text, roomy.plan.pill) == (("3 / 4",), PillKind.LIMIT)
    counted = next(n for n in scene.nodes if n.id == "count-0")
    assert (counted.text, counted.plan.pill) == (("4",), PillKind.COUNT)


def test_column_over_its_limit_is_warned_about() -> None:
    """More cards than the limit is a warning that says to finish something first."""
    raw = raw_example()
    raw["columns"][1]["limit"] = 2
    codes = {finding.code for finding in check_scene(drawn(raw))}
    assert Code.KANBAN_OVER_LIMIT in codes


def test_done_column_strikes_its_cards_and_card_can_be_done_alone() -> None:
    """Cards of a done column are done; so is a card marked ``done``."""
    scene = drawn()
    assert {c.plan.status for n, c in cards_of(scene).items() if n.startswith("c3-")} == {
        Status.DONE
    }
    raw = raw_example()
    raw["columns"][0]["cards"][0]["done"] = True
    first = cards_of(drawn(raw))["c0-0"]
    assert first.plan.status is Status.DONE
    assert "text-decoration:line-through" in render_html.render(drawn(raw))


def test_owner_circle_matches_the_other_planning_diagrams() -> None:
    """The initials and the tint come from the same helper as a Gantt row or an org card."""
    pinned = {"Kai Novak": {"tone": "green"}}
    expected = person_of("Kai Novak", pinned)
    card = cards_of(drawn())["c1-0"]
    assert (card.plan.initials, card.plan.person_tone) == (expected.initials, expected.tone)


def test_kind_tags_have_their_tints() -> None:
    """Feature is blue, Bug red and Chore grey."""
    cards = cards_of(drawn())
    assert [cards[i].plan.tag_tone.value for i in ("c0-0", "c0-2", "c0-3")] == [
        "blue",
        "red",
        "gray",
    ]


def test_board_refuses_icons_and_illustrated_style() -> None:
    """A work board is plain: an icon or the illustrated style is an error that says so."""
    raw = raw_example()
    raw["columns"][0]["cards"][0]["icon"] = "bug"
    with pytest.raises(SpecError, match="unknown field 'icon'"):
        drawn(raw)
    raw = raw_example()
    raw["style"] = "illustrated"
    with pytest.raises(SpecError, match="plain only"):
        drawn(raw)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda raw: raw["columns"][0].update(limit=0), "'limit' must be a whole number"),
        (lambda raw: raw["columns"][0]["cards"][0].update(owner=3), "'owner' must be a string"),
        (lambda raw: raw["columns"][0]["cards"][0].pop("label"), "'label' is required"),
    ],
)
def test_bad_fields_are_reported(change: Callable[[dict], object], message: str) -> None:
    """Each problem is reported with where it is."""
    raw = raw_example()
    change(raw)
    with pytest.raises(SpecError, match=message):
        drawn(raw)


def test_comparison_keeps_working() -> None:
    """Columns of options, with icons and details, are still drawn as before."""
    scene = drawn(raw_example(COMPARE))
    assert not any(n.shape is Shape.KANBAN_CARD for n in scene.nodes)
    assert check_scene(scene) == []
    explicit = raw_example(BOARD)
    explicit["use"] = "compare"
    with pytest.raises(SpecError):
        drawn(explicit)


def test_drawio_file_is_read_back() -> None:
    """Titles, tags, owners and the done mark survive the draw.io file."""
    scene = drawn()
    path = Path(__file__).parent / "_kanban_roundtrip.drawio"
    try:
        path.write_text(render_drawio.render(scene))
        back = import_drawio.convert(path).scene
    finally:
        path.unlink(missing_ok=True)
    by_id = {node.id.removeprefix("node-"): node for node in back.nodes}
    done = by_id["c3-0"]
    assert (done.text, done.plan.tag, done.plan.initials) == (
        ("Sign-in with phone",),
        "Feature",
        "AL",
    )
    assert done.plan.status is Status.DONE
    assert by_id["count-1"].plan.pill is PillKind.FULL
    assert [f.variant.value for f in back.frames] == ["column"] * 4
