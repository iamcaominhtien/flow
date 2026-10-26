"""Tests for the sequence diagram: spec, layout, bars, fragments and the draw.io output."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
SPECS = sorted(path for path in (ROOT / "examples").glob("*-sequence.spec.json"))
SIGNIN = ROOT / "examples" / "signin-sequence.spec.json"
PAYMENT = ROOT / "examples" / "payment-sequence.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.diagrams import sequence_spec  # noqa: E402
from flowlib.model import FrameVariant, Head, Role, Scene, Shape  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402


def laid_out(path: Path) -> Scene:
    """Lay out a sequence spec file.

    Args:
        path: A spec file.

    Returns:
        The scene.
    """
    return diagrams.layout(json.loads(path.read_text()))


@pytest.mark.parametrize("path", SPECS, ids=lambda path: path.name)
def test_example_has_no_errors(path: Path) -> None:
    """Both example sequence diagrams pass the checks with no error."""
    errors = [f.message for f in check_scene(laid_out(path)) if f.severity is Severity.ERROR]
    assert errors == []


def test_each_participant_has_a_lifeline_below_its_box() -> None:
    """A lifeline starts at the bottom of its participant's box and runs down."""
    scene = laid_out(SIGNIN)
    boxes = {node.id: node for node in scene.nodes if node.shape is Shape.HEADER}
    lifelines = {edge.id: edge for edge in scene.edges if edge.role is Role.LIFELINE}
    assert set(lifelines) == {f"life-{name}" for name in boxes}
    for name, box in boxes.items():
        start, end = lifelines[f"life-{name}"].points
        assert start[1] == box.y + box.height
        assert end[1] > start[1]


def test_activation_bars_come_from_call_and_return_pairs() -> None:
    """Each answered call makes one bar; the unanswered 'Show error' call makes none."""
    bars = [node for node in laid_out(SIGNIN).nodes if node.shape is Shape.BAR]
    assert len(bars) == 4


def test_a_call_answered_in_two_sections_is_one_bar() -> None:
    """The auth service is called once and answers in both alt sections: a single bar."""
    scene = laid_out(SIGNIN)
    by_height = sorted((n for n in scene.nodes if n.shape is Shape.BAR), key=lambda n: n.x)
    auth_x = next(n.x for n in scene.nodes if n.id == "auth") + 60
    auth_bars = [bar for bar in by_height if abs(bar.x - auth_x) < 60]
    assert len(auth_bars) == 1


def test_outer_fragment_is_drawn_before_the_inner_one() -> None:
    """A nested fragment comes later in the frame list, so it is drawn on top of its parent."""
    frames = [f for f in laid_out(PAYMENT).frames if f.variant is FrameVariant.FRAGMENT]
    assert [frame.label for frame in frames] == ["alt", "loop"]
    outer, inner = frames
    assert outer.x < inner.x and inner.x + inner.width < outer.x + outer.width


def test_message_kinds_choose_the_line() -> None:
    """Return is dashed with an open head, lost ends in a dot, found starts from a dot."""
    edges = {edge.label.text: edge for edge in laid_out(PAYMENT).edges if edge.label}
    assert edges["Paid"].dashed and edges["Paid"].head is Head.OPEN
    assert edges["timeout"].head is Head.DOT
    assert edges["webhook: chargeback"].tail is Head.DOT
    assert len(edges["validate"].points) == 4


def test_a_created_participant_starts_at_its_create_message() -> None:
    """The box of a created participant sits lower than the boxes of the others."""
    scene = laid_out(PAYMENT)
    tops = {node.id: node.y for node in scene.nodes if node.shape is Shape.HEADER}
    assert tops["worker"] > tops["app"]


def test_a_destroyed_participant_ends_with_a_cross() -> None:
    """A destroy item ends the lifeline with a cross."""
    scene = laid_out(PAYMENT)
    assert any(node.shape is Shape.CROSS for node in scene.nodes)


def test_unknown_participant_is_suggested() -> None:
    """A mistyped participant id gets a suggestion, like a mistyped node id in a flowchart."""
    bad = {
        "type": "sequence",
        "participants": [{"id": "app", "label": "App"}, {"id": "api", "label": "API"}],
        "items": [{"kind": "sync", "from": "app", "to": "apii", "label": "x"}],
    }
    with pytest.raises(SpecError, match="did you mean 'api'"):
        sequence_spec.parse(bad)


def test_fragments_nest_at_most_two_levels() -> None:
    """The design allows two levels of fragments; a third is rejected."""
    item: dict = {"kind": "sync", "from": "a", "to": "a", "label": "x"}
    for _ in range(3):
        item = {"fragment": "opt", "sections": [{"guard": "g", "items": [item]}]}
    bad = {"type": "sequence", "participants": [{"id": "a", "label": "A"}], "items": [item]}
    with pytest.raises(SpecError, match="at most 2 levels"):
        sequence_spec.parse(bad)


def test_drawio_uses_frame_shape_for_fragments_and_plain_lifelines() -> None:
    """Fragments become draw.io frames and lifelines are dashed lines without heads."""
    text = render_drawio.render(laid_out(SIGNIN))
    assert "shape=umlFrame" in text
    lifeline = next(line for line in text.splitlines() if 'id="edge-life-user"' in line)
    assert "endArrow=none" in lifeline
    assert "dashed=1" in lifeline


def test_unknown_diagram_type_lists_the_types() -> None:
    """A spec with an unknown type is rejected with the list of known types."""
    with pytest.raises(SpecError, match=r"flowchart.*sequence"):
        diagrams.layout({"type": "pie"})
