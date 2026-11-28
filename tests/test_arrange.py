"""The arrangement kit: a chain reads like text, a list is one table, a zone fits its nodes."""

import sys
from itertools import pairwise
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"
sys.path.insert(0, str(PLUGIN_DIR))

from flowlib.arrange import (  # noqa: E402
    ChainSpace,
    Listing,
    Step,
    chain,
    connect,
    cover,
    fit_zone,
    listing,
)
from flowlib.author import Canvas  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.model import Shape, Tone  # noqa: E402

STEP_COUNT: int = 11
ROW_WIDTH_PX: float = 1000.0
LONG_LIST: int = 22


def _steps(count: int) -> list[Step]:
    """Return numbered steps."""
    return [Step(f"s{i}", f"Step {i}") for i in range(count)]


def test_a_chain_never_runs_right_to_left() -> None:
    """Within a row every step is right of the one before; a new row starts at the left."""
    canvas = Canvas("Chain", None)
    chain(canvas, _steps(STEP_COUNT), ChainSpace(100, 200, ROW_WIDTH_PX))
    nodes = [canvas.boxes[f"s{i}"].node for i in range(STEP_COUNT)]
    lefts = {node.x for node in nodes}
    for before, after in pairwise(nodes):
        assert after.x > before.x or (after.x == min(lefts) and after.y > before.y)
    assert max(node.x + node.width for node in nodes) <= 100 + ROW_WIDTH_PX


def test_a_chain_joins_every_step_once_and_passes_the_check() -> None:
    """One line per pair of neighbours; no overlap or crossing that the check reports."""
    canvas = Canvas("Chain", None)
    chain(canvas, _steps(STEP_COUNT), ChainSpace(100, 200, ROW_WIDTH_PX))
    pairs = [(edge.source, edge.target) for edge in canvas.edges]
    assert pairs == [(f"s{i}", f"s{i + 1}") for i in range(STEP_COUNT - 1)]
    errors = [f for f in check_scene(canvas.scene()) if f.severity is Severity.ERROR]
    assert errors == []


def test_a_long_list_is_split_into_columns_of_equal_height() -> None:
    """Twenty-two names make two tables, the second titled as the continuation."""
    canvas = Canvas("List", None)
    names = tuple(f"Loader {i}" for i in range(LONG_LIST))
    boxes = listing(canvas, Listing("hyd", "Query loaders", names), (100, 200))
    assert [box.node.shape for box in boxes] == [Shape.TABLE, Shape.TABLE]
    assert boxes[1].node.text[0].endswith("(2/2)") or "(2/2)" in "".join(boxes[1].node.text)
    assert boxes[0].node.height == boxes[1].node.height
    rows = sum(len(box.node.sections[0]) for box in boxes)
    assert rows == LONG_LIST


def test_an_ordered_list_numbers_its_entries_across_columns() -> None:
    """The second column goes on counting where the first stopped."""
    canvas = Canvas("List", None)
    names = tuple(f"Filter {i}" for i in range(LONG_LIST))
    boxes = listing(canvas, Listing("flt", "Filters", names, is_ordered=True), (100, 200))
    first = boxes[0].node.sections[0]
    second = boxes[1].node.sections[0]
    assert first[0].flags == ("1",)
    assert second[0].flags == (str(len(first) + 1),)


def test_a_fitted_zone_holds_its_members_with_room_for_its_name() -> None:
    """The zone covers every member and sits close around them."""
    canvas = Canvas("Zone", None)
    chain(canvas, _steps(4), ChainSpace(100, 200, ROW_WIDTH_PX))
    members = [f"s{i}" for i in range(4)]
    zone = fit_zone(canvas, "z", ("Group", Tone.TEAL), members)
    inner = cover(canvas, members)
    assert zone.left < inner.left and zone.top < inner.top
    assert zone.right > inner.right and zone.bottom > inner.bottom
    assert zone.width - inner.width < 100


def test_a_long_step_in_a_chain_is_tall_enough_for_its_wrapped_text() -> None:
    """Forcing the chain's width wraps the words; the box grows to hold every line."""
    canvas = Canvas("Chain", None)
    words = "Check that the order total still matches the cart"
    steps = [Step("a", "Pay"), Step("b", words, detail="against the latest prices and coupons")]
    chain(canvas, steps, ChainSpace(100, 200, ROW_WIDTH_PX))
    short, long = canvas.boxes["a"].node, canvas.boxes["b"].node
    assert long.height > short.height
    assert len(long.text) >= 2


def test_a_zone_is_wide_enough_for_its_name() -> None:
    """A long name widens the zone around a narrow member."""
    canvas = Canvas("Zone", None)
    chain(canvas, [Step("a", "Pay")], ChainSpace(100, 200, ROW_WIDTH_PX))
    name = "A rather long name for a group that holds a single small step"
    zone = fit_zone(canvas, "z", (name, Tone.TEAL), ["a"])
    assert zone.width > cover(canvas, ["a"]).width + 200


def test_connect_routes_around_the_nodes_between() -> None:
    """A line between two parts goes round a node standing between them, on facing sides."""
    canvas = Canvas("Connect", None)
    chain(canvas, [Step("a", "Start here")], ChainSpace(100, 200, ROW_WIDTH_PX))
    chain(canvas, [Step("wall", "In the way")], ChainSpace(400, 200, ROW_WIDTH_PX))
    chain(canvas, [Step("b", "End here")], ChainSpace(700, 200, ROW_WIDTH_PX))
    line = connect(canvas, "a", "b")
    wall = canvas.boxes["wall"].node
    for (x1, y1), (x2, y2) in pairwise(line.points):
        crosses_x = min(x1, x2) < wall.x + wall.width and max(x1, x2) > wall.x
        crosses_y = min(y1, y2) < wall.y + wall.height and max(y1, y2) > wall.y
        assert not (crosses_x and crosses_y)
    assert line.points[0][0] >= canvas.boxes["a"].node.x + canvas.boxes["a"].node.width - 1
