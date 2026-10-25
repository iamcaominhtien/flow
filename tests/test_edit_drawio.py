"""Tests for editing an existing .drawio file."""

import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
FLOW = PLUGIN_DIR / "scripts" / "flow.py"
SHOP = ROOT / "examples" / "shop-architecture.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, edit_drawio, render_drawio  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


@pytest.fixture
def shop_file(tmp_path: Path) -> Path:
    """Write the shop architecture as a .drawio file and a second, untouched page.

    Args:
        tmp_path: The folder to write in.

    Returns:
        The path of the file.
    """
    scene = diagrams.layout(json.loads(SHOP.read_text()))
    document = ET.fromstring(render_drawio.render(scene))
    other = ET.SubElement(document, "diagram", {"id": "other", "name": "Notes"})
    ET.SubElement(other, "mxGraphModel")
    path = tmp_path / "shop.drawio"
    path.write_text(ET.tostring(document, encoding="unicode"))
    return path


def edited(path: Path, operations: list[dict]) -> tuple[ET.Element, list[str]]:
    """Apply operations and return the model and notes.

    Args:
        path: The file to edit.
        operations: The operations.

    Returns:
        The edited ``mxGraphModel`` and the notes.
    """
    return edit_drawio.apply_operations(path, operations)


def cell(model: ET.Element, cell_id: str) -> ET.Element | None:
    """Find a cell in a model.

    Args:
        model: The ``mxGraphModel``.
        cell_id: The cell id.

    Returns:
        The cell, or None.
    """
    return next((each for each in model.iter("mxCell") if each.get("id") == cell_id), None)


def test_set_text_move_and_tone_change_only_what_they_name(shop_file: Path) -> None:
    """Rename, move and recolour one box; the others keep their values."""
    before, _ = edited(shop_file, [{"op": "set_text", "id": "node-web", "text": "x"}])
    api_before = cell(before, "node-api").get("value")
    model, _ = edited(
        shop_file,
        [
            {"op": "set_text", "id": "node-web", "text": "Site & shop\nv2"},
            {"op": "move", "id": "node-web", "x": 500, "y": 300},
            {"op": "tone", "id": "node-web", "tone": "green"},
        ],
    )
    web = cell(model, "node-web")
    assert web.get("value") == "Site &amp; shop<br>v2"
    assert web.find("mxGeometry").get("x") == "500"
    assert "fillColor=#DCF5E1" in web.get("style")
    assert cell(model, "node-api").get("value") == api_before


def test_moving_a_box_resets_the_bends_of_its_lines(shop_file: Path) -> None:
    """A line that ends on a moved box loses its stored bends, and the user is told."""
    model, notes = edited(shop_file, [{"op": "move", "id": "node-api", "x": 10, "y": 10}])
    touched = [
        c
        for c in model.iter("mxCell")
        if c.get("edge") == "1" and "node-api" in (c.get("source"), c.get("target"))
    ]
    assert touched
    assert all(c.find("mxGeometry/Array") is None for c in touched)
    assert any("routed again" in note for note in notes)


def test_delete_removes_children_and_lines(shop_file: Path) -> None:
    """Deleting a box also removes its icon cell and the lines that end on it."""
    model, _ = edited(shop_file, [{"op": "delete", "id": "node-web"}])
    assert cell(model, "node-web") is None
    assert cell(model, "icon-web") is None
    remaining = {c.get("source") for c in model.iter("mxCell")} | {
        c.get("target") for c in model.iter("mxCell")
    }
    assert "node-web" not in remaining


def test_added_node_and_edge_exist_and_are_connected(shop_file: Path) -> None:
    """An added box and a line to it appear, and the id can be used by the next operation."""
    model, _ = edited(
        shop_file,
        [
            {"op": "add_node", "id": "cache", "text": "Cache", "x": 5, "y": 5, "tone": "amber"},
            {
                "op": "add_edge",
                "id": "api-cache",
                "from": "node-api",
                "to": "cache",
                "label": "reads",
            },
        ],
    )
    line = cell(model, "edge-api-cache")
    assert line.get("source") == "node-api"
    assert line.get("target") == "node-cache"


def test_one_bad_operation_changes_nothing_and_all_problems_are_listed(shop_file: Path) -> None:
    """The whole list is refused with every problem, and the file is unchanged."""
    original = shop_file.read_text()
    with pytest.raises(SpecError) as caught:
        edited(
            shop_file,
            [
                {"op": "move", "id": "node-web", "x": 1, "y": 1},
                {"op": "move", "id": "node-apii", "x": 1, "y": 1},
                {"op": "tone", "id": "node-web", "tone": "pink"},
                {"op": "spin", "id": "node-web"},
            ],
        )
    message = str(caught.value)
    assert "node-api" in message
    assert "pink" in message
    assert "spin" in message
    assert shop_file.read_text() == original


def test_cli_edits_in_place_keeps_a_backup_and_the_other_page(
    shop_file: Path, tmp_path: Path
) -> None:
    """--in-place overwrites the file, keeps a .bak copy and leaves the second page alone."""
    original = shop_file.read_text()
    operations = tmp_path / "ops.json"
    operations.write_text(json.dumps([{"op": "set_text", "id": "node-web", "text": "Site"}]))
    result = subprocess.run(
        [sys.executable, str(FLOW), "edit", str(shop_file), str(operations), "--in-place"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "shop.drawio.bak").read_text() == original
    document = ET.fromstring(shop_file.read_text())
    assert [d.get("name") for d in document.findall("diagram")][-1] == "Notes"
    assert "Site" in shop_file.read_text()


def test_cli_default_writes_next_to_the_file_and_leaves_it_alone(
    shop_file: Path, tmp_path: Path
) -> None:
    """Without --in-place the result goes to <name>.edited.drawio."""
    original = shop_file.read_text()
    operations = tmp_path / "ops.json"
    operations.write_text(json.dumps([{"op": "set_text", "id": "node-web", "text": "Site"}]))
    subprocess.run(
        [sys.executable, str(FLOW), "edit", str(shop_file), str(operations)],
        capture_output=True,
        check=True,
    )
    assert shop_file.read_text() == original
    assert (tmp_path / "shop.edited.drawio").is_file()
