"""Tests for ER tables: key chips, nullable types and the illustrated header."""

import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import render_drawio, render_html  # noqa: E402
from flowlib.diagrams import er  # noqa: E402

SPEC = {
    "type": "er",
    "title": "Orders",
    "desc": "Two tables.",
    "tables": [
        {
            "id": "customers",
            "name": "customers",
            "icon": "user",
            "columns": [{"name": "id", "type": "uuid", "flags": ["pk"]}],
        },
        {
            "id": "orders",
            "name": "orders",
            "columns": [
                {"name": "id", "type": "uuid", "flags": ["pk"]},
                {"name": "customer_id", "type": "uuid", "flags": ["fk", "uq"]},
                {"name": "note", "type": "text", "flags": ["null"]},
            ],
        },
    ],
    "relations": [{"from": "customers", "to": "orders"}],
}


def test_flags_become_chips_and_a_nullable_type_gets_a_question_mark() -> None:
    """The key flags are kept apart from the type; null marks the type."""
    scene = er.layout_raw(SPEC)
    orders = next(node for node in scene.nodes if node.id == "orders")
    rows = orders.sections[0]
    assert rows[1].flags == ("FK", "UQ")
    assert rows[1].right == "uuid"
    assert rows[2].right == "text?"


def test_the_illustrated_style_makes_tall_headers_with_a_large_icon() -> None:
    """Every table becomes a card-style table; one without an icon gets the table icon."""
    plain = er.layout_raw(SPEC)
    drawn = er.layout_raw({**SPEC, "style": "illustrated"})
    first = {node.id: node for node in plain.nodes}["orders"]
    second = {node.id: node for node in drawn.nodes}["orders"]
    assert second.card and not first.card
    assert second.height - first.height == 28
    assert second.icon == er.TABLE_ICON


def test_both_outputs_draw_the_chips() -> None:
    """The HTML page and the draw.io file both carry the PK and FK marks."""
    scene = er.layout_raw({**SPEC, "style": "illustrated"})
    html = render_html.render(scene)
    drawio = render_drawio.render(scene)
    assert ">PK<" in html and ">FK<" in html
    assert "PK" in drawio and "FK" in drawio


def test_tables_in_one_row_line_up_at_their_tops() -> None:
    """A short table and a tall one in the same grid row start at the same y."""
    spec = {
        **SPEC,
        "tables": [
            {**SPEC["tables"][0], "at": [0, 0]},
            {**SPEC["tables"][1], "at": [0, 1]},
        ],
    }
    nodes = {node.id: node for node in er.layout_raw(spec).nodes}
    assert nodes["customers"].height != nodes["orders"].height
    assert nodes["customers"].y == nodes["orders"].y
