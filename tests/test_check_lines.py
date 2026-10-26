"""Tests for the checks on overlapping lines and covered captions, and for label placement."""

import sys
from dataclasses import replace
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams  # noqa: E402
from flowlib.check import Code, check_scene  # noqa: E402
from flowlib.labels import place_labels  # noqa: E402
from flowlib.model import Edge, EdgeLabel, LabelKind, Node, Role, Scene, Shape  # noqa: E402


def _node(node_id: str, x: float, y: float, caption: str | None = None) -> Node:
    """Return a small box, optionally with a caption."""
    return Node(
        id=node_id,
        shape=Shape.INTERMEDIATE,
        x=x,
        y=y,
        width=38,
        height=38,
        text=(),
        icon=None,
        tone=None,
        number=None,
        font_size=13,
        caption=caption,
    )


def _edge(edge_id: str, points: tuple[tuple[float, float], ...], dashed: bool = False) -> Edge:
    """Return a line between points with no label and no node ends."""
    return Edge(edge_id, Role.NEXT, points, None, None, None, dashed=dashed)


def _scene(nodes: tuple[Node, ...], edges: tuple[Edge, ...]) -> Scene:
    """Return a scene around some nodes and lines."""
    return Scene(1000, 1000, None, None, (), nodes, edges)


def _codes(scene: Scene) -> list[Code]:
    """Return the codes of the findings on a scene."""
    return [finding.code for finding in check_scene(scene)]


def test_a_line_over_a_caption_is_an_error() -> None:
    """A vertical line through the name under an event is reported."""
    scene = _scene((_node("a", 100, 100, "Name"),), (_edge("e1", ((119, 150), (119, 300))),))
    assert Code.CAPTION_COVERED in _codes(scene)


def test_a_line_beside_a_caption_is_fine() -> None:
    """A line that leaves the side of an event does not touch its caption."""
    scene = _scene((_node("a", 100, 100, "Name"),), (_edge("e1", ((138, 119), (300, 119))),))
    assert Code.CAPTION_COVERED not in _codes(scene)


def test_two_lines_of_different_kinds_on_one_stretch_overlap() -> None:
    """A dashed line over a solid one for a long way is reported."""
    first = _edge("e1", ((0, 500), (200, 500)))
    second = _edge("e2", ((50, 500), (180, 500)), dashed=True)
    assert Code.LINES_OVERLAP in _codes(_scene((), (first, second)))


def test_lines_that_only_touch_do_not_overlap() -> None:
    """Two lines that meet at a corner share no stretch."""
    first = _edge("e1", ((0, 500), (200, 500)))
    second = _edge("e2", ((200, 500), (200, 700)))
    assert Code.LINES_OVERLAP not in _codes(_scene((), (first, second)))


def test_a_label_over_a_caption_is_moved_off_it() -> None:
    """A chip that covers a caption is slid along its line to a clear place."""
    node = _node("a", 100, 100, "Extended review")
    label = EdgeLabel("More time", (119, 160), LabelKind.PLAIN)
    edge = replace(_edge("e1", ((119, 100), (119, 400))), label=label)
    scene = place_labels(_scene((node,), (edge,)))
    assert scene.edges[0].label is not None
    assert scene.edges[0].label.at != (119, 160)
    messages = [finding.message for finding in check_scene(scene)]
    assert not any("label of" in message for message in messages)


def test_a_message_and_a_flow_leaving_one_gateway_are_not_drawn_on_top_of_each_other() -> None:
    """The message line takes the side of the gateway, so it shares no stretch with the flow."""
    spec = {
        "type": "bpmn",
        "zones": [
            {"id": "a", "label": "A", "tone": "blue"},
            {"id": "b", "label": "B", "tone": "green"},
        ],
        "elements": [
            {"id": "g", "label": "Choose", "kind": "exclusive", "zone": "a"},
            {"id": "t", "label": "Do it", "zone": "a"},
            {"id": "m", "label": "Ask", "zone": "b"},
            {"id": "x", "label": "Stop", "kind": "end", "zone": "a"},
        ],
        "flows": [
            {"from": "g", "to": "t"},
            {"from": "t", "to": "x"},
            {"from": "g", "to": "m", "style": "message"},
        ],
        "direction": "right",
    }
    findings = check_scene(diagrams.layout(spec))
    assert Code.LINES_OVERLAP not in [finding.code for finding in findings]
