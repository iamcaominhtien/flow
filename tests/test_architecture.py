"""Tests for the architecture diagram: layers, third parties, frame-edge lines, line kinds."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"
PLAIN = EXAMPLES / "delivery-architecture.spec.json"
ILLUSTRATED = EXAMPLES / "delivery-architecture-illustrated.spec.json"
STREAMING = EXAMPLES / "streaming-architecture.spec.json"
SHOP = EXAMPLES / "shop-architecture.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, import_drawio, render_drawio, render_html, scene  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.diagrams.grid_frames import pill_rect  # noqa: E402
from flowlib.model import FrameVariant, Role, Scene, Shape, Tone  # noqa: E402
from flowlib.orthogonal import is_clear  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

LAYER_PITCH_PLAIN_PX = 260
LAYER_PITCH_CARDS_PX = 240
FRAME_GAP_PX = 30


def raw_of(path: Path) -> dict:
    """Load a spec as a fresh dictionary.

    Args:
        path: The spec file.

    Returns:
        The parsed spec, safe to modify.
    """
    return copy.deepcopy(json.loads(path.read_text()))


def drawn(path: Path) -> Scene:
    """Lay out an example.

    Args:
        path: The spec file.

    Returns:
        The scene.
    """
    return diagrams.layout(raw_of(path))


@pytest.mark.parametrize("path", [PLAIN, ILLUSTRATED, STREAMING, SHOP])
def test_examples_have_no_errors_and_draw_in_both_formats(path: Path) -> None:
    """Each example passes the checks and renders to HTML and draw.io."""
    found = check_scene(drawn(path))
    assert [f.message for f in found if f.severity is Severity.ERROR] == []
    assert "<mxGraphModel" in render_drawio.render(drawn(path))
    assert "<svg" in render_html.render(drawn(path))


def test_plain_parts_are_196_by_68_and_layers_260_apart() -> None:
    """A plain part is 196 x 68; the centre lines of two layers are 260 px apart."""
    nodes = {node.id: node for node in drawn(PLAIN).nodes}
    assert (nodes["order"].width, nodes["order"].height) == (196, 68)
    assert nodes["order"].shape is Shape.PROCESS
    centre = lambda name: nodes[name].y + nodes[name].height / 2  # noqa: E731
    assert centre("order") - centre("gateway") == LAYER_PITCH_PLAIN_PX


def test_illustrated_cards_are_232_by_96_and_layers_240_apart() -> None:
    """A card is 232 x 96 and layers are 240 px apart."""
    nodes = {node.id: node for node in drawn(ILLUSTRATED).nodes}
    assert (nodes["order"].width, nodes["order"].height) == (232, 96)
    assert nodes["order"].shape is Shape.WIDE_CARD
    centre = lambda name: nodes[name].y + nodes[name].height / 2  # noqa: E731
    assert centre("order") - centre("gateway") == LAYER_PITCH_CARDS_PX


def test_layers_have_their_tints_and_a_dark_pill_frame() -> None:
    """Clients blue, edge violet, services green, data amber, third party grey."""
    frames = {frame.id: frame for frame in drawn(PLAIN).frames}
    tones = {name: frame.tone for name, frame in frames.items()}
    assert tones == {
        "clients": Tone.BLUE,
        "edge": Tone.VIOLET,
        "services": Tone.GREEN,
        "data": Tone.AMBER,
        "third": Tone.GRAY,
    }
    assert {frame.variant for frame in frames.values()} == {FrameVariant.LAYER}


def test_parts_sit_30_px_inside_their_frame() -> None:
    """The distance between the edge of a frame and the parts it holds is 30 px."""
    result = drawn(PLAIN)
    frame = next(item for item in result.frames if item.id == "clients")
    members = [node for node in result.nodes if node.id in ("customer", "tablet", "courier")]
    assert frame.x == min(node.x for node in members) - FRAME_GAP_PX
    assert frame.y == min(node.y for node in members) - FRAME_GAP_PX


def test_third_party_frame_is_to_the_right_of_the_services_row() -> None:
    """A zone placed beside a layer shares its row and sits right of the layer's frame."""
    frames = {frame.id: frame for frame in drawn(PLAIN).frames}
    assert frames["third"].x >= frames["services"].x + frames["services"].width
    assert frames["third"].y == frames["services"].y


def test_line_kinds_decide_the_role() -> None:
    """Call is ink, main is blue, event is violet and copy is dashed slate."""
    raw = raw_of(PLAIN)
    raw["links"].append({"from": "cache", "to": "db", "label": "warm up", "kind": "copy"})
    roles = {(e.source, e.target): e.role for e in diagrams.layout(raw).edges}
    assert roles[("gateway", "auth")] is Role.NEXT
    assert roles[("order", "payment")] is Role.MAIN
    assert roles[("order", "bus")] is Role.DATA
    assert roles[("cache", "db")] is Role.BACK


def test_a_line_from_a_frame_edge_starts_on_the_frame() -> None:
    """A link that names a zone is drawn from the edge of its frame, to or from any part."""
    result = drawn(STREAMING)
    frames = {frame.id: frame for frame in result.frames}
    edge = next(e for e in result.edges if e.label and e.label.text == "REST, gRPC")
    assert edge.target is None
    x, y = edge.points[-1]
    box = frames["services"]
    on_border = x in (box.x, box.x + box.width) or y in (box.y, box.y + box.height)
    assert on_border


def test_lines_keep_out_of_the_pill_of_a_frame() -> None:
    """No line crosses the pill that names a frame."""
    result = drawn(PLAIN)
    theme = load_theme()
    for frame in result.frames:
        pill = pill_rect(frame, theme)
        for edge in result.edges:
            assert is_clear(list(edge.points), [pill])


def test_every_line_needs_a_label() -> None:
    """A link with no label is refused and says what to write."""
    raw = raw_of(PLAIN)
    del raw["links"][0]["label"]
    with pytest.raises(SpecError, match="label"):
        diagrams.layout(raw)


def test_unknown_zone_is_rejected_with_a_suggestion() -> None:
    """A component in a misspelt zone fails and names the likely zone."""
    raw = raw_of(PLAIN)
    raw["components"][1]["zone"] = "client"
    with pytest.raises(SpecError, match="clients"):
        diagrams.layout(raw)


def test_zone_parents_that_loop_are_rejected() -> None:
    """Two zones that are each other's parent fail."""
    raw = raw_of(PLAIN)
    raw["zones"][0]["parent"] = "edge"
    raw["zones"][1]["parent"] = "clients"
    with pytest.raises(SpecError, match="loop"):
        diagrams.layout(raw)


def test_beside_must_name_a_layer() -> None:
    """A third party beside a zone that is itself inside another zone is refused."""
    raw = raw_of(PLAIN)
    raw["zones"][1]["parent"] = "clients"
    raw["zones"][4]["beside"] = "edge"
    with pytest.raises(SpecError, match="layer"):
        diagrams.layout(raw)


def test_scene_file_round_trip_keeps_frames_and_cards() -> None:
    """Writing a scene and reading it back keeps the layer frames and the card shapes."""
    original = drawn(ILLUSTRATED)
    again = scene.parse(scene.dump(original))
    assert [f.variant for f in again.frames] == [f.variant for f in original.frames]
    assert [n.shape for n in again.nodes] == [n.shape for n in original.nodes]


def test_drawio_has_a_pill_per_frame_and_imports_back(tmp_path: Path) -> None:
    """The draw.io file holds a pill per layer; importing it brings frames and cards back."""
    original = drawn(ILLUSTRATED)
    xml = render_drawio.render(original)
    assert xml.count('id="label-frame-') == len(original.frames)
    path = tmp_path / "out.drawio"
    path.write_text(xml)
    result = import_drawio.convert(path).scene
    assert [f.label for f in result.frames] == [f.label for f in original.frames]
    assert {f.variant for f in result.frames} == {FrameVariant.LAYER}
    order = next(node for node in result.nodes if node.id == "node-order")
    assert order.shape is Shape.WIDE_CARD
    assert order.text == ("Order service",)
    assert order.detail == ("checkout, status",)


def test_the_spec_in_the_skill_is_valid() -> None:
    """The first JSON block of the skill builds."""
    text = (PLUGIN_DIR / "skills" / "architecture" / "SKILL.md").read_text()
    block = text.split("```json")[1].split("```")[0]
    assert diagrams.layout(json.loads(block)).nodes


def test_the_six_patterns_of_the_skill_can_be_written_and_drawn() -> None:
    """Gateway, queue and worker, cache-aside, CDN, publish and subscribe and read replica draw."""
    zones = [
        {"id": "edge", "label": "Edge", "tone": "violet"},
        {"id": "services", "label": "Services", "tone": "green"},
        {"id": "data", "label": "Data", "tone": "amber"},
    ]
    names = {
        "edge": ["gateway", "cdn"],
        "services": ["api", "worker", "publisher", "subscriber", "service"],
        "data": ["queue", "cache", "db", "origin", "topic", "primary", "replica"],
    }
    components = [{"id": i, "label": i.title(), "zone": z} for z, ids in names.items() for i in ids]
    pairs = [
        ("gateway", "api", "route"),
        ("api", "queue", "enqueue"),
        ("queue", "worker", "job"),
        ("service", "cache", "get"),
        ("service", "db", "read on a miss"),
        ("cdn", "origin", "on a miss"),
        ("publisher", "topic", "publish"),
        ("topic", "subscriber", "consume"),
        ("service", "primary", "write"),
        ("service", "replica", "read"),
        ("primary", "replica", "replication"),
    ]
    links = [{"from": a, "to": b, "label": label} for a, b, label in pairs]
    links.append({"from": "edge", "to": "gateway", "label": "HTTPS"})
    raw = {"type": "architecture", "zones": zones, "components": components, "links": links}
    assert len(diagrams.layout(raw).edges) == len(links)
