"""Tests for the draw.io renderer."""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLE_SCENES = sorted((ROOT / "examples").glob("*.scene.json"))
SHAPES_SCENE = ROOT / "examples" / "shapes.scene.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import build, render_drawio, scene, spec  # noqa: E402
from flowlib.model import Scene  # noqa: E402


def cells_of(rendered: str) -> dict[str, ET.Element]:
    """Parse a draw.io document and index its cells by id.

    Args:
        rendered: The text of an ``mxfile`` document.

    Returns:
        Cell id to its ``mxCell`` element.
    """
    return {cell.get("id"): cell for cell in ET.fromstring(rendered).iter("mxCell")}


def style_of(cell: ET.Element) -> dict[str, str]:
    """Split the style string of a cell into a dict; a bare key maps to an empty string.

    Args:
        cell: An ``mxCell`` element.

    Returns:
        Style key to value.
    """
    pairs = (part.partition("=") for part in cell.get("style", "").split(";") if part)
    return {key: value for key, _, value in pairs}


def example_scene(path: Path) -> Scene:
    """Read a scene file.

    Args:
        path: A scene file.

    Returns:
        The scene.
    """
    return scene.load(path)


@pytest.mark.parametrize("path", EXAMPLE_SCENES, ids=lambda path: path.name)
def test_every_scene_item_becomes_a_cell(path: Path) -> None:
    """Each frame, node and edge of a scene has a cell with the matching id."""
    parsed = example_scene(path)
    cells = cells_of(render_drawio.render(parsed))
    assert {f"frame-{frame.id}" for frame in parsed.frames} <= cells.keys()
    assert {f"node-{node.id}" for node in parsed.nodes} <= cells.keys()
    assert {f"edge-{edge.id}" for edge in parsed.edges} <= cells.keys()


def test_edges_keep_their_waypoints_and_terminals() -> None:
    """An edge from a built flowchart keeps its interior points and joins its two nodes."""
    flowchart = build.layout(spec.load(ROOT / "examples" / "login-flow.spec.json"))
    cells = cells_of(render_drawio.render(flowchart))
    back = next(
        edge for edge in flowchart.edges if edge.source == "attempts" and edge.target == "enter"
    )
    cell = cells[f"edge-{back.id}"]
    points = cell.findall("./mxGeometry/Array[@as='points']/mxPoint")
    assert len(points) == len(back.points) - 2
    assert cell.get("source") == "node-attempts"
    assert cell.get("target") == "node-enter"


def test_edge_without_terminals_still_has_end_points() -> None:
    """A hand-written edge that names no node still draws, because its end points are given."""
    cells = cells_of(render_drawio.render(example_scene(SHAPES_SCENE)))
    cell = cells["edge-m1"]
    names = {point.get("as") for point in cell.findall("./mxGeometry/mxPoint")}
    assert {"sourcePoint", "targetPoint"} <= names


def test_animated_roles_use_flow_animation_at_the_speed_of_the_page() -> None:
    """Main and data lines are animated; a normal line is not."""
    cells = cells_of(render_drawio.render(example_scene(SHAPES_SCENE)))
    main, data, normal = (style_of(cells[f"edge-{name}"]) for name in ("m1", "d1", "n1"))
    assert main["flowAnimation"] == "1"
    assert int(data["flowAnimationDuration"]) > int(main["flowAnimationDuration"])
    assert "flowAnimation" not in normal


def test_dash_pattern_is_in_multiples_of_the_line_width() -> None:
    """A 6 5 dash on a 2 px line is written 3 2.5, because draw.io multiplies by the width."""
    cells = cells_of(render_drawio.render(example_scene(SHAPES_SCENE)))
    assert style_of(cells["edge-b1"])["dashPattern"] == "3 2.5"


def test_icon_is_a_child_cell_of_its_node() -> None:
    """An icon moves with its node because it is a child cell."""
    cells = cells_of(render_drawio.render(example_scene(SHAPES_SCENE)))
    icon = cells["icon-b"]
    assert icon.get("parent") == "node-b"
    assert style_of(icon)["image"].startswith("data:image/svg+xml,")


def test_markup_in_text_stays_text() -> None:
    """Text such as ``<b>`` is escaped twice, so draw.io shows it instead of rendering it."""
    document = {
        "size": [200, 100],
        "nodes": [
            {
                "id": "a",
                "shape": "process",
                "x": 10,
                "y": 10,
                "width": 100,
                "height": 50,
                "text": "<b>x</b>",
            }
        ],
    }
    cells = cells_of(render_drawio.render(scene.parse(document)))
    assert cells["node-a"].get("value") == "&lt;b&gt;x&lt;/b&gt;"


def test_bare_style_keys_have_no_equals_sign() -> None:
    """Shape names such as ``rhombus`` are written without ``=``, as draw.io expects."""
    cells = cells_of(render_drawio.render(example_scene(SHAPES_SCENE)))
    assert not re.search(r"(^|;)(rhombus|ellipse|text)=", cells["node-c"].get("style", ""))
    assert "rhombus" in style_of(cells["node-c"])
