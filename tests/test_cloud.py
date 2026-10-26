"""Tests for the cloud diagram: frame kinds, nesting, trust levels, the grid and the round trip."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"
BASIC = EXAMPLES / "web-cloud.spec.json"
DELIVERY = EXAMPLES / "delivery-cloud.spec.json"
NETWORK = EXAMPLES / "network-cloud.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, import_drawio, render_drawio, render_html, scene  # noqa: E402
from flowlib.check import Severity, check_scene  # noqa: E402
from flowlib.diagrams.grid_frames import pill_rect  # noqa: E402
from flowlib.model import FrameVariant, Role, Scene, Shape, Tone  # noqa: E402
from flowlib.orthogonal import is_clear  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

ROW_PITCH_PX = 255
FRAME_GAP_PX = 30
PART_PAD_PX = 40


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


@pytest.mark.parametrize("path", [BASIC, DELIVERY, NETWORK])
def test_examples_have_no_errors_and_draw_in_both_formats(path: Path) -> None:
    """Each example passes the checks and renders to HTML and draw.io."""
    found = check_scene(drawn(path))
    assert [f.message for f in found if f.severity is Severity.ERROR] == []
    assert "<mxGraphModel" in render_drawio.render(drawn(path))
    assert "Region eu-west" in render_html.render(drawn(path)) or path is NETWORK


def test_each_frame_kind_has_its_colour_and_line() -> None:
    """Region blue solid, VPC violet dashed, zone grey dashed, subnets green, amber, teal."""
    frames = {frame.id: frame for frame in drawn(DELIVERY).frames}
    look = {name: (frame.tone, frame.is_solid) for name, frame in frames.items()}
    assert look["region"] == (Tone.BLUE, True)
    assert look["vpc"] == (Tone.VIOLET, False)
    assert look["za"] == (Tone.GRAY, False)
    assert look["pa"] == (Tone.GREEN, False)
    assert look["ra"] == (Tone.AMBER, False)
    assert look["da"] == (Tone.TEAL, False)
    assert look["edge"] == (Tone.VIOLET, False)
    network = {frame.id: frame for frame in drawn(NETWORK).frames}
    assert (network["head"].tone, network["head"].is_solid) == (Tone.GRAY, True)
    assert network["dmz"].tone is Tone.RED
    assert {frame.variant for frame in frames.values()} == {FrameVariant.NETWORK}


def test_the_vpc_label_carries_the_address_range() -> None:
    """The range goes into the label of the VPC."""
    frames = {frame.id: frame for frame in drawn(DELIVERY).frames}
    assert frames["vpc"].label == "VPC 10.0.0.0/16"


def test_parts_are_196_by_68_and_rows_255_apart() -> None:
    """A part is 196 x 68; the centre lines of two subnet rows are 255 px apart."""
    nodes = {node.id: node for node in drawn(DELIVERY).nodes}
    assert (nodes["lba"].width, nodes["lba"].height) == (196, 68)
    assert nodes["k8sa"].y - nodes["lba"].y == ROW_PITCH_PX
    assert nodes["primary"].y - nodes["k8sa"].y == ROW_PITCH_PX


def test_frames_nest_with_30_px_and_subnets_keep_parts_40_px_in() -> None:
    """30 px between a frame and the frame inside it; 40 px between a subnet and its parts."""
    result = drawn(DELIVERY)
    frames = {frame.id: frame for frame in result.frames}
    nodes = {node.id: node for node in result.nodes}
    assert frames["za"].x - frames["vpc"].x >= FRAME_GAP_PX
    assert frames["vpc"].x - frames["region"].x == FRAME_GAP_PX
    assert frames["za"].x == frames["pa"].x - FRAME_GAP_PX
    assert nodes["lba"].x - frames["pa"].x == PART_PAD_PX
    assert nodes["lba"].y - frames["pa"].y == PART_PAD_PX


def test_zones_hold_the_same_subnets_in_the_same_order() -> None:
    """The same kind of subnet is on the same row in every zone."""
    nodes = {node.id: node for node in drawn(DELIVERY).nodes}
    assert nodes["lba"].y == nodes["lbb"].y
    assert nodes["k8sa"].y == nodes["k8sb"].y
    assert nodes["primary"].y == nodes["replica"].y


def test_zones_with_different_subnets_are_refused() -> None:
    """A zone without the data subnet that its sister has is refused."""
    raw = raw_of(DELIVERY)
    raw["frames"] = [f for f in raw["frames"] if f["id"] != "db_b"]
    raw["parts"] = [p for p in raw["parts"] if p["id"] != "replica"]
    raw["links"] = [link for link in raw["links"] if "replica" not in (link["from"], link["to"])]
    with pytest.raises(SpecError, match="same subnets"):
        diagrams.layout(raw)


def test_a_database_in_a_public_subnet_is_refused() -> None:
    """Databases belong in a data subnet."""
    raw = raw_of(BASIC)
    next(p for p in raw["parts"] if p["id"] == "db")["frame"] = "pub"
    with pytest.raises(SpecError, match="database"):
        diagrams.layout(raw)


def test_a_line_may_not_skip_two_levels() -> None:
    """A line from the internet straight to the data subnet is refused."""
    raw = raw_of(BASIC)
    raw["links"].append({"from": "customers", "to": "db", "label": "SQL"})
    with pytest.raises(SpecError, match="skips"):
        diagrams.layout(raw)


def test_a_line_may_skip_one_level() -> None:
    """From the internet to the private subnet skips only the public one, which is allowed."""
    raw = raw_of(BASIC)
    raw["links"].append({"from": "customers", "to": "appa", "label": "HTTPS"})
    assert diagrams.layout(raw).edges


def test_a_managed_service_sits_in_the_region_outside_the_vpc() -> None:
    """The queue is in the region frame and to the right of the VPC frame."""
    result = drawn(DELIVERY)
    frames = {frame.id: frame for frame in result.frames}
    queue = next(node for node in result.nodes if node.id == "queue")
    assert queue.x >= frames["vpc"].x + frames["vpc"].width
    assert queue.x + queue.width <= frames["region"].x + frames["region"].width


def test_sites_sit_left_of_the_region_and_links_join_devices() -> None:
    """On-premises sites are left of the region; a site link runs from device to device."""
    result = drawn(NETWORK)
    region = next(frame for frame in result.frames if frame.id == "region")
    nodes = {node.id: node for node in result.nodes}
    assert nodes["fw"].x + nodes["fw"].width < region.x
    link = next(e for e in result.edges if e.label and e.label.text == "IPsec VPN")
    assert (link.source, link.target) == ("fw", "vpn")


def test_lines_keep_out_of_the_pill_of_a_frame() -> None:
    """No line crosses the pill that names a frame."""
    theme = load_theme()
    for path in (BASIC, DELIVERY, NETWORK):
        result = drawn(path)
        for frame in result.frames:
            pill = pill_rect(frame, theme)
            assert all(is_clear(list(edge.points), [pill]) for edge in result.edges)


def test_the_main_route_is_blue_and_copies_are_violet() -> None:
    """The request is blue; the replication is violet."""
    edges = {(e.source, e.target): e for e in drawn(DELIVERY).edges}
    assert edges[("customer", "cdn")].role is Role.MAIN
    assert edges[("primary", "replica")].role is Role.DATA
    assert edges[("tablet", "cdn")].role is Role.NEXT


def test_every_link_needs_a_label() -> None:
    """A link with no label says what to write."""
    raw = raw_of(BASIC)
    del raw["links"][0]["label"]
    with pytest.raises(SpecError, match="label"):
        diagrams.layout(raw)


def test_cloud_is_plain_only() -> None:
    """The illustrated style is refused."""
    raw = raw_of(BASIC)
    raw["style"] = "illustrated"
    with pytest.raises(SpecError, match="plain"):
        diagrams.layout(raw)


def test_scene_file_round_trip_keeps_solid_frames() -> None:
    """Writing a scene and reading it back keeps which frames are solid."""
    original = drawn(NETWORK)
    again = scene.parse(scene.dump(original))
    assert [f.is_solid for f in again.frames] == [f.is_solid for f in original.frames]


def test_drawio_round_trip_keeps_frames(tmp_path: Path) -> None:
    """Importing the draw.io file brings back each frame with its tone, line and label."""
    original = drawn(DELIVERY)
    path = tmp_path / "out.drawio"
    path.write_text(render_drawio.render(original))
    result = import_drawio.convert(path).scene
    by_label = {frame.label: frame for frame in result.frames}
    assert set(by_label) == {frame.label for frame in original.frames}
    assert by_label["Region eu-west"].is_solid
    assert by_label["Region eu-west"].tone is Tone.BLUE
    assert not by_label["Public subnet"].is_solid
    assert {f.variant for f in result.frames} == {FrameVariant.NETWORK}
    assert Shape.PROCESS in {node.shape for node in result.nodes}


def test_the_spec_in_the_skill_is_valid() -> None:
    """The first JSON block of the skill builds."""
    text = (PLUGIN_DIR / "skills" / "cloud" / "SKILL.md").read_text()
    block = text.split("```json")[1].split("```")[0]
    assert diagrams.layout(json.loads(block)).nodes
