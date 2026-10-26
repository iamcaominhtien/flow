"""Tests for the detailed icon library."""

import json
import sys
from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
SHOP = ROOT / "examples" / "shop-illustrated.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_html  # noqa: E402
from flowlib.theme import icon_names, load_detailed_icons, load_icons  # noqa: E402

ALLOWED_TAGS = {
    "svg",
    "path",
    "circle",
    "ellipse",
    "rect",
    "line",
    "polyline",
    "polygon",
    "g",
    "text",
}
FORBIDDEN_TEXT = ("script", "href", "javascript", "onload", "<style", "url(")


def test_library_has_about_a_hundred_icons() -> None:
    """The detailed set was taken from the design: roughly one hundred drawings."""
    assert len(load_detailed_icons()) >= 90


@pytest.mark.parametrize("name", sorted(load_detailed_icons()))
def test_each_detailed_icon_is_well_formed_and_safe(name: str) -> None:
    """Each icon parses as XML, uses only drawing elements and holds nothing that can run."""
    markup = load_detailed_icons()[name]
    root = ElementTree.fromstring(f"<svg>{markup}</svg>")
    assert {element.tag for element in root.iter()} <= ALLOWED_TAGS
    assert not [word for word in FORBIDDEN_TEXT if word in markup.lower()]


def test_every_flat_twin_is_known_by_name() -> None:
    """Spec validation accepts the flat names, the custom names and the detailed-only names."""
    assert set(load_icons()) <= icon_names()
    assert {"api-gateway", "sql-database", "kubernetes"} <= icon_names()


def test_plain_style_draws_a_detailed_only_icon_small() -> None:
    """In a plain diagram an icon that only has a detailed drawing is drawn as that, small."""
    raw = json.loads(SHOP.read_text())
    del raw["style"]
    raw["components"][0]["icon"] = "kubernetes"
    assert 'viewBox="0 0 64 64"' in render_html.render(diagrams.layout(raw))
