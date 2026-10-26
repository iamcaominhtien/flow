"""Tests for ER tables: key chips, nullable types and the illustrated header."""

import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import render_drawio, render_html  # noqa: E402
from flowlib.diagrams import er  # noqa: E402
from flowlib.model import Role  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

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
    assert second.height - first.height == 24
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


def _scene_with(relations: list[dict[str, object]]) -> object:
    """Lay out the two-table spec with the given relations."""
    return er.layout_raw({**SPEC, "relations": relations})


def test_a_logical_relation_is_a_dashed_slate_line_of_its_own_role() -> None:
    """The design draws a link with no constraint dashed and slate, not as a plain line."""
    scene = _scene_with([{"from": "customers", "to": "orders", "style": "logical"}])
    assert scene.edges[0].role is Role.LOGICAL
    assert scene.edges[0].dashed


def test_a_line_meets_a_table_at_the_row_of_its_column() -> None:
    """A relation that names its columns starts and ends level with those rows."""
    spec = {
        **SPEC,
        "tables": [
            {**SPEC["tables"][0], "at": [0, 0]},
            {**SPEC["tables"][1], "at": [0, 1]},
        ],
        "relations": [
            {"from": "customers", "to": "orders", "from_column": "id", "to_column": "customer_id"}
        ],
    }
    scene = er.layout_raw(spec)
    nodes = {node.id: node for node in scene.nodes}
    rules = load_theme().layout
    line = scene.edges[0].points
    first_row = nodes["customers"].y + rules.table_header_height + 1 + rules.table_row_height / 2
    second_row = nodes["orders"].y + rules.table_header_height + 1 + 1.5 * rules.table_row_height
    assert line[0][1] == first_row
    assert line[-1][1] == second_row


def test_a_table_that_points_at_itself_gets_a_loop_beside_it() -> None:
    """A self reference leaves and re-enters the right side, with its label beside the loop."""
    scene = _scene_with(
        [{"from": "orders", "to": "orders", "label": "replaces", "to_column": "customer_id"}]
    )
    orders = next(node for node in scene.nodes if node.id == "orders")
    points = scene.edges[0].points
    assert len(points) == 4
    assert points[0][0] == points[-1][0] == orders.x + orders.width
    assert scene.edges[0].label.at[0] > points[1][0]
