"""Tests for L4 screens: screenshots of the running app in the frames of a screen flow."""

import json
import os
import struct
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
sys.path.insert(0, str(ROOT / "plugins" / "flow"))

from flowlib import build, render_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.captures import CaptureProblem, read_png  # noqa: E402
from flowlib.check import Code, Severity, check_scene  # noqa: E402
from flowlib.diagrams import layout  # noqa: E402
from flowlib.model import Node, Scene  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402
from flowlib.screen_part import PartKind  # noqa: E402
from flowlib.screen_parts import screen_parts  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

PHONE = (390, 844)
DESKTOP = (1280, 800)
WHITE = 255
STALE_SECONDS = 100


def write_png(path: Path, size: tuple[int, int]) -> Path:
    """Write a plain white PNG of a given size with the standard library.

    Args:
        path: The file to write.
        size: Width and height in pixels.

    Returns:
        The path.
    """
    width, height = size
    row = b"\x00" + bytes([WHITE]) * width
    data = zlib.compress(row * height)

    def chunk(kind: bytes, body: bytes) -> bytes:
        """Build one PNG chunk with its length and checksum."""
        return (
            struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", data) + chunk(b"IEND", b"")
    path.write_bytes(png)
    return path


def flow_with(capture: dict | str, **keys: object) -> dict:
    """Make a two-screen flow whose first screen is at L4 with a given capture."""
    first = {"id": "home", "code": "S01", "label": "Home", "fidelity": "L4", "capture": capture}
    second = {"id": "next", "code": "S02", "label": "Next", "fidelity": "L2"}
    return {
        "type": "screen",
        "screens": [{**first, "at": [0, 0], **keys}, {**second, "at": [0, 1]}],
        "taps": [{"from": "home", "to": "next", "trigger": "tap Go"}],
    }


def home(scene: Scene) -> Node:
    """Return the L4 screen of a test flow."""
    return next(node for node in scene.nodes if node.id == "home")


def codes(scene: Scene) -> list[Code]:
    """Return the codes of the check's findings."""
    return [finding.code for finding in check_scene(scene)]


def test_a_png_is_read_with_its_size(tmp_path: Path) -> None:
    """The size comes from the PNG header; a missing file and a text file are reported."""
    image = read_png(str(write_png(tmp_path / "a.png", PHONE)))
    assert not isinstance(image, CaptureProblem)
    assert (image.width, image.height) == PHONE
    assert read_png(str(tmp_path / "none.png")) is CaptureProblem.MISSING
    (tmp_path / "b.png").write_text("not a picture")
    assert read_png(str(tmp_path / "b.png")) is CaptureProblem.NOT_PNG


def test_an_l4_screen_needs_a_capture_and_only_l4_takes_one() -> None:
    """Both mistakes are spec errors that say what to set."""
    spec = flow_with({"image": "a.png"})
    del spec["screens"][0]["capture"]
    with pytest.raises(SpecError, match="needs a"):
        layout(spec)
    spec = flow_with({"image": "a.png"}, fidelity="L2")
    with pytest.raises(SpecError, match="drawn at fidelity L4"):
        layout(spec)


def test_the_screenshot_fills_the_width_of_the_body_and_is_cut_at_its_bottom(
    tmp_path: Path,
) -> None:
    """The image is as wide as the body, no taller than the body, and its path is the spec's."""
    write_png(tmp_path / "home.png", (390, 2000))
    scene = layout(flow_with({"image": "home.png"}), tmp_path)
    node = home(scene)
    assert node.screen is not None and node.screen.capture is not None
    assert node.screen.capture.image == str(tmp_path / "home.png")
    images = [p for p in screen_parts(node, load_theme()) if p.kind is PartKind.IMAGE]
    (image,) = images
    left, top, width, height = image.bounds
    assert left > 0 and width < node.width
    assert top + height < node.height


def test_hotspots_get_a_red_dot_scaled_from_the_screenshot(tmp_path: Path) -> None:
    """A hotspot inside the shown part gets a dot; one below the cut gets none."""
    write_png(tmp_path / "home.png", PHONE)
    hotspots = [
        {"text": "Go", "box": [24, 300, 342, 50]},
        {"text": "Far", "box": [24, 830, 342, 10]},
    ]
    scene = layout(flow_with({"image": "home.png", "hotspots": hotspots}), tmp_path)
    circles = [p for p in screen_parts(home(scene), load_theme()) if p.kind is PartKind.CIRCLE]
    assert len(circles) == 2  # one halo and one dot, for the first hotspot only


def test_a_missing_screenshot_is_drawn_as_a_hatch_and_is_an_error(tmp_path: Path) -> None:
    """The screen still draws; the check names the file."""
    scene = layout(flow_with({"image": "gone.png"}), tmp_path)
    kinds = [p.kind for p in screen_parts(home(scene), load_theme())]
    assert PartKind.HATCH in kinds and PartKind.IMAGE not in kinds
    errors = [f for f in check_scene(scene) if f.severity is Severity.ERROR]
    assert [f.code for f in errors] == [Code.CAPTURE_MISSING]
    assert "gone.png" in errors[0].message


def test_a_screenshot_of_the_wrong_device_and_a_far_hotspot_are_warned(tmp_path: Path) -> None:
    """A desktop picture in a phone frame, and a box beyond the picture."""
    write_png(tmp_path / "home.png", DESKTOP)
    capture = {"image": "home.png", "hotspots": [{"text": "Out", "box": [1200, 700, 200, 50]}]}
    found = codes(layout(flow_with(capture), tmp_path))
    assert Code.CAPTURE_ASPECT in found
    assert Code.HOTSPOT_OUTSIDE in found
    write_png(tmp_path / "desk.png", DESKTOP)
    assert Code.CAPTURE_ASPECT not in codes(
        layout(flow_with({"image": "desk.png"}, device="desktop"), tmp_path)
    )


def test_a_source_changed_after_the_screenshot_is_warned(tmp_path: Path) -> None:
    """The screenshot is older than the file that draws the screen."""
    image = write_png(tmp_path / "home.png", PHONE)
    source = tmp_path / "home.ts"
    source.write_text("export const home = 1;")
    old = image.stat().st_mtime - STALE_SECONDS
    os.utime(image, (old, old))
    capture = {"image": "home.png", "source": "home.ts"}
    assert Code.CAPTURE_STALE in codes(layout(flow_with(capture), tmp_path))


def test_html_and_drawio_carry_the_screenshot_and_the_scene_keeps_it(tmp_path: Path) -> None:
    """The HTML has a focusable picture, draw.io an image cell, the scene the capture."""
    write_png(tmp_path / "home.png", PHONE)
    capture = {
        "image": "home.png",
        "source": "home.ts",
        "hotspots": [{"text": "Go", "box": [1, 2, 3, 4]}],
    }
    scene = layout(flow_with(capture), tmp_path)
    page = render_html.render(scene)
    assert 'class="shot"' in page and "data:image/png;base64," in page
    assert ".shot:focus" in page
    assert "data:image/png," in render_drawio.render(scene)
    again = scene_io.parse(json.loads(scene_io.dumps(scene)))
    assert home(again).screen == home(scene).screen


def test_the_notes_example_builds_with_no_problem(tmp_path: Path) -> None:
    """Three L4 screens with hotspots beside an L2 and an L0 screen."""
    result = build.build(EXAMPLES / "notes-built-screen-flow.spec.json", tmp_path)
    assert not result.findings
    scene = scene_io.load(result.scene_path)
    levels = [n.screen.fidelity.value for n in scene.nodes if n.screen]
    assert levels.count("L4") == 3


def test_a_manifest_names_the_captures_by_code(tmp_path: Path) -> None:
    """A spec that names its manifest takes each screen's image, source and hotspots from it."""
    folder = tmp_path / "captures"
    folder.mkdir()
    write_png(folder / "S01.png", PHONE)
    entry = {
        "image": "S01.png",
        "source": "home.ts",
        "hotspots": [{"text": "Go", "box": [1, 2, 3, 4]}],
    }
    manifest = {"viewport": list(PHONE), "screens": {"S01": {**entry, "url": "http://x/"}}}
    (folder / "manifest.json").write_text(json.dumps(manifest))
    spec = flow_with("S01")
    spec["captures"] = "captures/manifest.json"
    capture = home(layout(spec, tmp_path)).screen.capture
    assert capture is not None
    assert capture.image == str(tmp_path / "captures" / "S01.png")
    assert capture.source == str(tmp_path / "home.ts")
    assert capture.hotspots[0].text == "Go"


def test_a_code_missing_from_the_manifest_or_no_manifest_is_a_spec_error(tmp_path: Path) -> None:
    """Both say what to do."""
    spec = flow_with("S09")
    with pytest.raises(SpecError, match="names a screen of a manifest"):
        layout(spec, tmp_path)
    (tmp_path / "manifest.json").write_text(json.dumps({"screens": {}}))
    spec["captures"] = "manifest.json"
    with pytest.raises(SpecError, match=r"'S09' is not in manifest\.json"):
        layout(spec, tmp_path)
    spec["captures"] = "none.json"
    with pytest.raises(SpecError, match=r"run capture\.js first"):
        layout(spec, tmp_path)
