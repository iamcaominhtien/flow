"""Tests for the roadmap: rows and columns, committed and idea cards, the one arrow, the note."""

import copy
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib import diagrams, import_drawio, render_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.check import Code, check_scene  # noqa: E402
from flowlib.model import Role, Scene, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402

NAME = "delivery-roadmap"


def raw_example() -> dict:
    """Load the example as a fresh dictionary."""
    return copy.deepcopy(json.loads((EXAMPLES / f"{NAME}.spec.json").read_text()))


def drawn(raw: dict | None = None) -> Scene:
    """Lay out a spec, the example by default."""
    return diagrams.layout(raw if raw is not None else raw_example())


def cards_of(scene: Scene) -> dict:
    """Return the cards of a scene by id."""
    return {n.id: n for n in scene.nodes if n.shape is Shape.ROADMAP_CARD}


def test_example_has_no_findings_and_draws_in_both_formats() -> None:
    """The design example passes every check and renders to HTML, draw.io and scene.json."""
    scene = drawn()
    assert check_scene(scene) == []
    assert "<svg" in render_html.render(scene)
    ET.fromstring(render_drawio.render(scene))
    assert scene_io.parse(scene_io.dump(scene)) == scene


def test_rows_columns_and_cards_are_placed_on_a_grid() -> None:
    """Three rows of three cards: the same x in a column, the same y in a row."""
    cards = list(cards_of(drawn()).values())
    assert len(cards) == 9
    assert len({round(card.x) for card in cards}) == 3
    assert len({round(card.y) for card in cards}) == 3
    assert {card.height for card in cards} == {144}


def test_dashed_cards_are_the_ideas() -> None:
    """``committed: false`` is dashed and tagged Exploring; the rest are solid and Committed."""
    cards = cards_of(drawn()).values()
    assert sum(card.dashed for card in cards) == 4
    assert {card.plan.tag for card in cards if card.dashed} == {"Exploring"}
    assert {card.plan.tag for card in cards if not card.dashed} == {"Committed"}


def test_one_blue_arrow_and_its_note() -> None:
    """The dependency is one animated blue arrow, and the note below names both items."""
    scene = drawn()
    arrows = [edge for edge in scene.edges if edge.role is Role.MAIN]
    assert [(a.source, a.target) for a in arrows] == [("tracking", "tips")]
    note = next(n for n in scene.nodes if n.id == "note")
    assert "Courier tips cannot start before Live order tracking is done" in note.text[0]
    assert note.y > max(frame.y + frame.height for frame in scene.frames)


def test_blocks_is_the_same_arrow_the_other_way_round() -> None:
    """``blocks`` on the first item draws the same arrow as ``depends_on`` on the second."""
    raw = raw_example()
    del raw["lanes"][1]["items"][1]["depends_on"]
    raw["lanes"][0]["items"][0]["blocks"] = "Courier tips"
    arrows = [edge for edge in drawn(raw).edges if edge.role is Role.MAIN]
    assert [(a.source, a.target) for a in arrows] == [("tracking", "tips")]


def test_a_second_dependency_is_an_error() -> None:
    """Only the one dependency that decides the order is allowed."""
    raw = raw_example()
    raw["lanes"][0]["items"][1]["depends_on"] = "tracking"
    with pytest.raises(SpecError, match="2 dependencies"):
        drawn(raw)


def test_dependency_must_name_an_item_and_not_go_back_in_time() -> None:
    """An unknown name, and a card that depends on a later one, are errors."""
    raw = raw_example()
    raw["lanes"][1]["items"][1]["depends_on"] = "trackin"
    with pytest.raises(SpecError, match="did you mean 'tracking'"):
        drawn(raw)
    raw = raw_example()
    raw["lanes"][1]["items"][1]["depends_on"] = "New cities"
    with pytest.raises(SpecError, match="earlier period"):
        drawn(raw)


def test_exact_date_is_a_warning() -> None:
    """A date in a card is warned about; months in words are fine."""
    assert Code.ROADMAP_EXACT_DATE not in {f.code for f in check_scene(drawn())}
    raw = raw_example()
    raw["lanes"][0]["items"][0]["detail"] = "Ship on 2026-03-14"
    assert Code.ROADMAP_EXACT_DATE in {f.code for f in check_scene(drawn(raw))}


def test_owner_circle_and_quarters_with_spans() -> None:
    """An owner shows as a circle; periods can be quarters and a card can span two."""
    raw = {
        "type": "roadmap",
        "periods": ["Q1", "Q2", "Q3", "Q4"],
        "lanes": [
            {"label": "Product", "tone": "blue", "items": [
                {"label": "Search", "period": "Q2", "length": 2, "owner": "Ava Lopez"},
                {"label": "Onboarding", "start": 0},
            ]}
        ],
    }  # fmt: skip
    scene = drawn(raw)
    cards = cards_of(scene)
    assert cards["i0-0"].plan.initials == "AL"
    assert cards["i0-0"].width > cards["i0-1"].width
    assert check_scene(scene) == []


def test_bad_period_and_length_are_reported() -> None:
    """A period that does not exist and a card past the last period are errors."""
    raw = raw_example()
    raw["lanes"][0]["items"][0]["period"] = "Soon"
    with pytest.raises(SpecError, match="'period' must be one of Now, Next, Later"):
        drawn(raw)
    raw = raw_example()
    raw["lanes"][0]["items"][2]["length"] = 2
    with pytest.raises(SpecError, match="only 3"):
        drawn(raw)


def test_drawio_file_is_read_back() -> None:
    """Titles, tags, dashes, period names and the arrow survive the draw.io file."""
    scene = drawn()
    path = Path(__file__).parent / "_roadmap_roundtrip.drawio"
    try:
        path.write_text(render_drawio.render(scene))
        back = import_drawio.convert(path).scene
    finally:
        path.unlink(missing_ok=True)
    by_id = {node.id.removeprefix("node-"): node for node in back.nodes}
    assert by_id["period-0"].text == ("Now",) and by_id["period-0"].detail == ("March to April",)
    assert by_id["tips"].text == ("Courier tips",) and not by_id["tips"].dashed
    assert [n.dashed for n in back.nodes if n.shape is Shape.ROADMAP_CARD].count(True) == 4
    assert by_id["lane-0"].text == ("Ordering",)
    assert len([edge for edge in back.edges if edge.role is Role.MAIN]) == 1
