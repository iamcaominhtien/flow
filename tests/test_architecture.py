"""Tests for the architecture diagram: zones, component shapes, link styles and errors."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
SHOP = ROOT / "examples" / "shop-architecture.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.model import Scene, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


def shop_raw() -> dict:
    """Load the shop example as a fresh dictionary.

    Returns:
        The parsed spec, safe to modify.
    """
    return copy.deepcopy(json.loads(SHOP.read_text()))


def shop_scene() -> Scene:
    """Lay out the shop example.

    Returns:
        The scene.
    """
    return diagrams.layout(shop_raw())


def test_example_has_no_errors() -> None:
    """The shop example passes the checks with no error."""
    errors = [f.message for f in check_scene(shop_scene()) if f.severity is Severity.ERROR]
    assert errors == []


def test_kind_decides_the_shape() -> None:
    """A database is a cylinder, a queue a preparation hexagon, an external system a subprocess."""
    shapes = {node.id: node.shape for node in shop_scene().nodes}
    assert shapes["db"] is Shape.CYLINDER
    assert shapes["queue"] is Shape.PREPARATION
    assert shapes["psp"] is Shape.SUBPROCESS


def test_inner_zone_frame_lies_inside_the_outer_one() -> None:
    """The backend frame sits inside the cloud frame, and the cloud is drawn first."""
    frames = shop_scene().frames
    assert [frame.label for frame in frames] == ["Cloud", "Backend"]
    outer, inner = frames
    assert outer.x <= inner.x
    assert outer.y <= inner.y
    assert inner.x + inner.width <= outer.x + outer.width
    assert inner.y + inner.height <= outer.y + outer.height


def test_async_link_is_dashed() -> None:
    """An async link is dashed and a call is not."""
    edges = {(edge.source, edge.target): edge for edge in shop_scene().edges}
    assert edges[("api", "queue")].dashed
    assert not edges[("api", "db")].dashed


def test_unknown_zone_is_rejected_with_a_suggestion() -> None:
    """A component in a misspelt zone fails and names the likely zone."""
    raw = shop_raw()
    raw["components"][1]["zone"] = "clouds"
    with pytest.raises(SpecError, match="cloud"):
        diagrams.layout(raw)


def test_zone_parents_that_loop_are_rejected() -> None:
    """Two zones that are each other's parent fail."""
    raw = shop_raw()
    raw["zones"][0]["parent"] = "backend"
    with pytest.raises(SpecError, match="loop"):
        diagrams.layout(raw)


def test_drawio_output_has_a_frame_per_zone() -> None:
    """The draw.io file holds both zone frames."""
    xml = render_drawio.render(shop_scene())
    assert "Cloud" in xml
    assert "Backend" in xml
