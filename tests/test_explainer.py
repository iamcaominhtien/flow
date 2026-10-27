"""Tests for the explainer: four shapes, sections, the rules of design 07 and the files."""

import copy
import json
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib import diagrams, import_drawio, render_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.check import Code, check_scene  # noqa: E402
from flowlib.model import FrameVariant, Role, Scene, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402

NAMES = ("layers", "tree", "compare", "concept", "payment")


def raw_example(name: str) -> dict:
    """Load an explainer example as a fresh dictionary."""
    return copy.deepcopy(json.loads((EXAMPLES / f"explainer-{name}.spec.json").read_text()))


def drawn(name: str) -> Scene:
    """Lay out an explainer example."""
    return diagrams.layout(raw_example(name))


def nodes_of(scene: Scene) -> dict:
    """Return the nodes of a scene by id."""
    return {node.id: node for node in scene.nodes}


@pytest.mark.parametrize("name", NAMES)
def test_examples_build_with_no_error(name: str) -> None:
    """Check that examples build with no error."""
    scene = drawn(name)
    assert scene.diagram == "explainer"
    assert not [f for f in check_scene(scene) if f.severity.value == "error"]


def test_layers_follow_the_design_sizes() -> None:
    """Check that layers follow the design sizes."""
    scene = drawn("layers")
    assert scene.width == 1500
    bands = [frame for frame in scene.frames if frame.variant is FrameVariant.STRIP]
    assert len(bands) == 5
    assert {band.height for band in bands} == {248}
    assert [b2.y - b1.y for b1, b2 in pairwise(bands)] == [290] * 4
    cards = [n for n in scene.nodes if n.shape is Shape.EXPLAIN_CARD]
    assert {(card.width, card.height) for card in cards} == {(260, 200)}
    assert [card.number for card in cards] == ["1", "2", "3", "4", "5", "6", "7"]


def test_layers_path_is_the_blue_animated_role_and_a_step_is_ink() -> None:
    """Check that layers path is the blue animated role and a step is ink."""
    scene = drawn("layers")
    roles = {edge.id: edge.role for edge in scene.edges}
    assert roles["e1"] is Role.MAIN
    assert roles["e3"] is Role.NEXT
    assert all(len(edge.points) <= 4 for edge in scene.edges)


def test_tree_rows_are_700_by_92_and_112_apart_with_no_numbers() -> None:
    """Check that tree rows are 700 by 92 and 112 apart with no numbers."""
    scene = drawn("tree")
    rows = [n for n in scene.nodes if n.shape is Shape.ROW_CARD]
    assert len(rows) == 7
    assert {(row.width, row.height) for row in rows} == {(700, 92)}
    assert {b.y - a.y for a, b in pairwise(rows)} == {112}
    assert all(row.number is None and row.is_mono for row in rows)
    assert rows[0].chips == ("components/", "pages/", "api/")


def test_comparison_rows_are_124_apart_and_read_across() -> None:
    """Check that comparison rows are 124 apart and read across."""
    scene = drawn("compare")
    cells = nodes_of(scene)
    assert cells["left-1"].y - cells["left-0"].y == 124
    assert cells["left-0"].y == cells["right-0"].y == cells["label-0"].y - 24
    assert cells["vs"].tone is None


def test_concept_has_a_hub_four_numbered_facts_and_an_analogy() -> None:
    """Check that concept has a hub four numbered facts and an analogy."""
    scene = drawn("concept")
    nodes = nodes_of(scene)
    assert [nodes[f"fact-{i}"].number for i in range(4)] == ["1", "2", "3", "4"]
    assert nodes["hub"].number is None
    assert nodes["left"].x < nodes["hub"].x < nodes["right"].x
    assert any(frame.id == "analogy" for frame in scene.frames)


def test_payment_combines_sections_with_letters_and_branches() -> None:
    """Check that payment combines sections with letters and branches."""
    scene = drawn("payment")
    heads = [n for n in scene.nodes if n.shape is Shape.SECTION_HEAD]
    assert [head.number for head in heads] == ["A", "B", "C"]
    nodes = nodes_of(scene)
    assert nodes["s1.approved"].number == "6a"
    assert nodes["s1.declined"].number == "6b"
    assert nodes["s1.approved"].shape is Shape.ROW_CARD
    assert nodes["s1.declined"].y > nodes["s1.approved"].y


def test_more_than_eight_cards_and_long_text_and_jargon_are_warned() -> None:
    """Check that more than eight cards and long text and jargon are warned."""
    raw = raw_example("layers")
    raw["bands"][0]["cards"][0]["text"] = " ".join(["word"] * 15)
    raw["bands"][4]["cards"] += [
        {"id": f"extra{i}", "name": "Extra", "text": "More."} for i in range(2)
    ]
    raw["links"][0]["label"] = "sends HTTP"
    codes = {finding.code for finding in check_scene(diagrams.layout(raw))}
    assert {Code.EXPLAINER_TOO_MANY_CARDS, Code.EXPLAINER_TEXT_LONG, Code.EXPLAINER_JARGON} <= codes


def test_the_examples_have_no_warning() -> None:
    """Check that the examples have no warning."""
    for name in NAMES:
        assert check_scene(drawn(name)) == [], name


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda raw: raw.update(shape="pie"), "unknown shape"),
        (lambda raw: raw["links"][0].update({"to": "nowhere"}), "not a card"),
        (lambda raw: raw["bands"][0]["cards"][0].update(icon="zzz"), "unknown icon"),
        (lambda raw: raw.update(colour="red"), "unknown field"),
    ],
)
def test_bad_specs_are_refused(change: Callable[[dict], object], message: str) -> None:
    """Check that bad specs are refused."""
    raw = raw_example("layers")
    change(raw)
    with pytest.raises(SpecError, match=message):
        diagrams.layout(raw)


def test_title_is_40_px_and_the_path_is_the_only_animation() -> None:
    """Check that title is 40 px and the path is the only animation."""
    html = render_html.render(drawn("layers"))
    assert "font-size:40px" in html
    assert html.count('class="flow"') >= 1
    assert "prefers-reduced-motion" in html
    assert 'class="flow2"' not in html


def test_drawio_animates_the_path_and_keeps_parts() -> None:
    """Check that drawio animates the path and keeps parts."""
    xml = render_drawio.render(drawn("layers"))
    root = ET.fromstring(xml)
    ids = {cell.get("id") for cell in root.iter("mxCell")}
    assert {"node-browser", "pill-browser", "detail-browser", "badge-browser"} <= ids
    assert "flowAnimation=1" in xml


def test_scene_round_trip_keeps_chips_and_mono() -> None:
    """Check that scene round trip keeps chips and mono."""
    scene = drawn("tree")
    again = scene_io.parse(json.loads(scene_io.dumps(scene)))
    rows = [n for n in again.nodes if n.shape is Shape.ROW_CARD]
    assert rows[0].chips == ("components/", "pages/", "api/")
    assert rows[0].is_mono


def test_drawio_import_reads_the_explainer_back(tmp_path: Path) -> None:
    """Check that drawio import reads the explainer back."""
    path = tmp_path / "payment.drawio"
    path.write_text(render_drawio.render(drawn("payment")), encoding="utf-8")
    result = import_drawio.convert(path)
    nodes = nodes_of(result.scene)
    assert nodes["node-s1.approved"].number == "6a"
    assert nodes["node-s1.approved"].shape is Shape.ROW_CARD
    assert any(frame.variant is FrameVariant.STRIP for frame in result.scene.frames)


@pytest.mark.parametrize("theme", ["technical", "midnight"])
def test_other_themes_draw(theme: str) -> None:
    """Check that other themes draw."""
    raw = raw_example("concept")
    raw["theme"] = theme
    scene = diagrams.layout(raw)
    assert scene.theme == theme
    assert render_html.render(scene)
    assert render_drawio.render(scene)
