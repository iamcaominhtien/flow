"""Tests for the ER diagram: spec, tables, cardinality heads and the draw.io output."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
DELIVERY = ROOT / "examples" / "delivery-er.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.model import Head, Role, Scene, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


def delivery_raw() -> dict:
    """Load the delivery example as a fresh dictionary.

    Returns:
        The parsed spec, safe to modify.
    """
    return copy.deepcopy(json.loads(DELIVERY.read_text()))


def delivery_scene() -> Scene:
    """Lay out the delivery example.

    Returns:
        The scene.
    """
    return diagrams.layout(delivery_raw())


def test_example_has_no_errors() -> None:
    """The delivery example passes the checks with no error."""
    errors = [f.message for f in check_scene(delivery_scene()) if f.severity is Severity.ERROR]
    assert errors == []


def test_each_table_becomes_a_table_node_with_one_row_per_column() -> None:
    """Every table is a TABLE node and its rows are the columns."""
    tables = [node for node in delivery_scene().nodes if node.shape is Shape.TABLE]
    assert len(tables) == 5
    orders = next(node for node in tables if node.id == "orders")
    assert sum(len(section) for section in orders.sections) == 5


def test_cardinality_sets_the_heads() -> None:
    """The couriers relation has a zero-or-one tail and a zero-or-many head."""
    edge = next(
        edge for edge in delivery_scene().edges if edge.label and edge.label.text == "delivers"
    )
    assert edge.tail is Head.ZERO_ONE
    assert edge.head is Head.ZERO_MANY


def test_logical_relation_is_dashed_and_main_relation_is_main() -> None:
    """A logical relation is dashed; the relation flagged main has the main role."""
    edges = {edge.label.text: edge for edge in delivery_scene().edges if edge.label}
    assert edges["is paid by"].dashed
    assert not edges["places"].dashed
    assert edges["places"].role is Role.MAIN


def test_unknown_table_in_a_relation_is_rejected_with_a_suggestion() -> None:
    """A relation to a misspelt table fails and names the likely table."""
    raw = delivery_raw()
    raw["relations"][0]["to"] = "order"
    with pytest.raises(SpecError, match="orders"):
        diagrams.layout(raw)


def test_drawio_output_has_a_swimlane_per_table_and_er_markers() -> None:
    """The draw.io file has one swimlane per table and uses ER arrow markers."""
    xml = render_drawio.render(delivery_scene())
    assert xml.count("swimlane") >= 5
    assert "ERmany" in xml or "ERzeroToMany" in xml
