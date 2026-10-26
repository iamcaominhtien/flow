"""Tests for the illustrated style: cards with a large icon, a name pill and a detail line."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"
SHOP = EXAMPLES / "shop-illustrated.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio, render_html, scene  # noqa: E402
from flowlib.check import Code, Severity, check_scene  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


def shop_raw() -> dict:
    """Load the illustrated example as a fresh dictionary.

    Returns:
        The parsed spec, safe to modify.
    """
    return copy.deepcopy(json.loads(SHOP.read_text()))


def test_example_has_no_errors() -> None:
    """The illustrated example passes the checks with no error."""
    found = check_scene(diagrams.layout(shop_raw()))
    assert [f for f in found if f.severity is Severity.ERROR] == []


def test_boxes_with_an_icon_become_cards_and_the_others_stay_plain() -> None:
    """A component with an icon is a card; one without is a plain box."""
    raw = shop_raw()
    del raw["components"][1]["icon"]
    cards = {node.id: node.card for node in diagrams.layout(raw).nodes}
    assert cards == {"web": True, "api": False, "db": True, "pay": True}


def test_plain_style_has_no_cards() -> None:
    """The same spec without 'style' draws no card."""
    raw = shop_raw()
    del raw["style"]
    assert not any(node.card for node in diagrams.layout(raw).nodes)


def test_cards_are_taller_than_plain_boxes() -> None:
    """A card holds a disc, a pill and a detail line, so it is taller than a plain box."""
    raw = shop_raw()
    card = diagrams.layout(raw).nodes[0]
    del raw["style"]
    plain = diagrams.layout(raw).nodes[0]
    assert card.height > plain.height


def test_card_flag_survives_the_scene_file() -> None:
    """Writing a scene and reading it back keeps the card flag."""
    original = diagrams.layout(shop_raw())
    again = scene.parse(scene.dump(original))
    assert [node.card for node in again.nodes] == [True] * 4


def test_both_renderers_draw_pills_and_use_the_detailed_icon_when_there_is_one() -> None:
    """Every card has a pill; a card whose icon has a detailed drawing has no disc."""
    drawn = diagrams.layout(shop_raw())
    html = render_html.render(drawn)
    assert "border-radius:50%" not in html
    assert 'viewBox="0 0 64 64"' in html
    xml = render_drawio.render(drawn)
    assert xml.count('id="pill-') == 4
    assert xml.count('id="disc-') == 0


def test_an_icon_without_a_detailed_drawing_gets_a_disc() -> None:
    """The bike icon has no detailed twin, so its card keeps the tinted disc in both outputs."""
    raw = shop_raw()
    raw["components"][0]["icon"] = "bike"
    drawn = diagrams.layout(raw)
    assert "border-radius:50%" in render_html.render(drawn)
    assert render_drawio.render(drawn).count('id="disc-') == 1


def test_a_name_too_long_for_the_pill_is_flagged() -> None:
    """A card name wider than the card is reported by the text-fit check."""
    raw = shop_raw()
    raw["components"][0]["label"] = "A very long component name that cannot sit in a pill " * 3
    codes = [f.code for f in check_scene(diagrams.layout(raw))]
    assert Code.TEXT_MAY_NOT_FIT in codes


def test_unknown_style_is_refused() -> None:
    """A style other than plain or illustrated fails and says what is allowed."""
    raw = shop_raw()
    raw["style"] = "sketchy"
    with pytest.raises(SpecError, match="plain or illustrated"):
        diagrams.layout(raw)


def test_flowchart_and_kanban_accept_the_style() -> None:
    """The flowchart and the Kanban board take 'style' as well."""
    flow = json.loads((EXAMPLES / "order-flow.spec.json").read_text())
    flow["style"] = "illustrated"
    assert any(node.card for node in diagrams.layout(flow).nodes)
    board = json.loads((EXAMPLES / "sprint-kanban.spec.json").read_text())
    board["style"] = "illustrated"
    assert any(node.card for node in diagrams.layout(board).nodes)


def test_flowchart_node_detail_shows_under_the_text() -> None:
    """A flowchart node can carry a detail line, which a card shows under its pill."""
    flow = json.loads((EXAMPLES / "order-flow.spec.json").read_text())
    flow["style"] = "illustrated"
    node = next(item for item in flow["nodes"] if item.get("icon"))
    node["detail"] = "One line about it"
    shown = next(each for each in diagrams.layout(flow).nodes if each.id == node["id"])
    assert shown.detail == ("One line about it",)
