"""Tests for the org chart: bus lines, cards, open role, works-with line and both styles."""

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
from flowlib.diagrams.people import initials_of, tone_of  # noqa: E402
from flowlib.model import LabelKind, Role, Scene, Shape, Tone  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402

NAMES = ("delivery-org", "delivery-org-illustrated")


def raw_example(name: str = NAMES[0]) -> dict:
    """Load an example as a fresh dictionary."""
    return copy.deepcopy(json.loads((EXAMPLES / f"{name}.spec.json").read_text()))


def drawn(name: str = NAMES[0]) -> Scene:
    """Lay out an example."""
    return diagrams.layout(raw_example(name))


def cards_of(scene: Scene) -> dict:
    """Return the cards of a scene by id, without the legend."""
    return {n.id: n for n in scene.nodes if n.shape is Shape.PERSON_CARD and n.text}


@pytest.mark.parametrize("name", NAMES)
def test_example_has_no_findings_and_draws_in_both_formats(name: str) -> None:
    """Both design examples pass every check and render to HTML and draw.io."""
    scene = drawn(name)
    assert check_scene(scene) == []
    assert "<svg" in render_html.render(scene)
    ET.fromstring(render_drawio.render(scene))
    assert scene_io.parse(scene_io.dump(scene)) == scene


def test_card_sizes_and_spacing_follow_the_design() -> None:
    """Plain cards are 210 x 78, illustrated 232 x 110; 250 px apart, levels 240 or 270."""
    plain, illustrated = (cards_of(drawn(name)) for name in NAMES)
    assert (plain["dana"].width, plain["dana"].height) == (210, 78)
    assert (illustrated["dana"].width, illustrated["dana"].height) == (232, 110)
    assert plain["kai"].x + 105 - (plain["lia"].x + 105) == 250
    assert plain["minh"].y - plain["dana"].y == 240
    assert illustrated["minh"].y - illustrated["dana"].y == 270


def test_manager_stands_over_the_middle_report() -> None:
    """With an odd number of reports the manager is over the middle one."""
    cards = cards_of(drawn())
    assert cards["sam"].x == cards["kai"].x
    assert cards["minh"].x + 105 == pytest.approx((cards["noah"].x + cards["ava"].x) / 2 + 105)


def test_each_report_has_a_solid_bus_line_without_a_head() -> None:
    """A line runs from the manager down to a bar, along it and down to the report."""
    scene = drawn()
    lines = [
        edge for edge in scene.edges if edge.role is Role.REPORTS and edge.id.startswith("reports")
    ]
    assert len(lines) == len(cards_of(scene)) - 1
    line = next(edge for edge in lines if edge.target == "lia")
    assert line.head.value == "none"
    assert line.points[1][1] == line.points[2][1] == line.points[0][1] + 86
    bars = {edge.points[1][1] for edge in lines if edge.source == "sam" and len(edge.points) == 4}
    assert len(bars) == 1


def test_open_role_is_a_dashed_card_named_by_its_title() -> None:
    """The open role shows its title and the words Open role, with a question mark."""
    card = cards_of(drawn())["qa"]
    assert (card.text, card.detail) == (("QA engineer",), ("Open role",))
    assert card.plan.is_open and card.plan.initials == "?"
    assert "stroke-dasharray" not in render_html.render(drawn()) or "dashed" in render_html.render(
        drawn()
    )
    assert "dashed=1" in render_drawio.render(drawn())


def test_works_with_line_joins_two_people_with_a_pill() -> None:
    """The dashed link runs between the facing sides and carries its label."""
    scene = drawn()
    link = next(
        edge for edge in scene.edges if edge.role is Role.WORKS_WITH and edge.id == "works-1"
    )
    cards = cards_of(scene)
    assert link.points[0] == (cards["ava"].x + 210, cards["ava"].y + 39)
    assert link.points[1] == (cards["lia"].x, cards["lia"].y + 39)
    assert link.label.text == "works with" and link.label.kind is LabelKind.PLAIN


def test_link_between_levels_is_refused() -> None:
    """A working link joins two people on one level."""
    raw = raw_example()
    raw["links"] = [{"from": "ava", "to": "sam"}]
    with pytest.raises(SpecError, match="different levels"):
        diagrams.layout(raw)


def test_tint_is_stable_and_follows_the_team() -> None:
    """The same name has the same tint, and people keep the tint of their head."""
    assert tone_of("Minh Tran") is tone_of("minh tran")
    cards = cards_of(drawn())
    assert cards["noah"].tone is cards["minh"].tone is Tone.BLUE
    assert cards["joy"].tone is Tone.TEAL
    assert initials_of("Minh Tran") == "MT" and initials_of("Cher") == "C"


def test_older_label_and_detail_form_is_still_read() -> None:
    """A spec with label and detail draws a card with the label as name and detail as role."""
    raw = {
        "type": "org",
        "root": {"label": "CEO", "detail": "Ana Lee", "children": [{"label": "COO"}]},
    }
    cards = cards_of(diagrams.layout(raw))
    assert cards["n0"].text == ("CEO",) and cards["n0"].detail == ("Ana Lee",)
    assert "n1" in cards


def test_more_than_four_levels_and_sentences_are_warnings() -> None:
    """Five levels, or a role that is a sentence, are reported."""
    raw = {
        "type": "org",
        "root": {
            "name": "A",
            "role": "Founder",
            "children": [
                {
                    "name": "B",
                    "role": "Does everything for the company every day.",
                    "children": [
                        {
                            "name": "C",
                            "role": "Lead",
                            "children": [
                                {
                                    "name": "D",
                                    "role": "Dev",
                                    "children": [{"name": "E", "role": "Intern"}],
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    }
    codes = {finding.code for finding in check_scene(diagrams.layout(raw))}
    assert {Code.ORG_TOO_MANY_LEVELS, Code.ORG_ROLE_SENTENCE} <= codes


def test_drawio_file_is_read_back_as_cards() -> None:
    """Names, roles, the open role and the style of the cards survive the draw.io file."""
    scene = drawn("delivery-org-illustrated")
    path = Path(__file__).parent / "_org_roundtrip.drawio"
    try:
        path.write_text(render_drawio.render(scene))
        back = import_drawio.convert(path).scene
    finally:
        path.unlink(missing_ok=True)
    by_id = {node.id.removeprefix("node-"): node for node in back.nodes}
    card = by_id["lia"]
    assert (card.text, card.detail, card.card) == (("Lia Chen",), ("Mobile developer",), True)
    assert by_id["qa"].plan.is_open
