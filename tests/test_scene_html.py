"""Tests for the scene format, the theme and the HTML renderer."""

import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
FLOW_CLI = PLUGIN_DIR / "scripts" / "flow.py"
EXAMPLE_SCENES = sorted((ROOT / "examples").glob("*.scene.json"))
SHAPES_SCENE = ROOT / "examples" / "shapes.scene.json"
EXIT_INVALID_SCENE = 1

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import render_html, scene  # noqa: E402
from flowlib.model import Animation, LabelKind, Role, Shape, Tone  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402


class IdCollector(HTMLParser):
    """Collects the ``data-id`` of every element in a page."""

    def __init__(self) -> None:
        """Start with no ids."""
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Remember the ``data-id`` of an element, if it has one.

        Args:
            tag: The element name; not used.
            attrs: The attributes of the element.
        """
        self.ids.update(value for name, value in attrs if name == "data-id" and value)


def minimal_scene(text: str) -> dict:
    """Return a scene document with one node that holds the given text.

    Args:
        text: The text of the node.

    Returns:
        A JSON-style scene.
    """
    node = {"id": "a", "shape": "process", "x": 10, "y": 10, "width": 100, "height": 50}
    return {"size": [200, 100], "nodes": [{**node, "text": text}]}


@pytest.mark.parametrize("path", EXAMPLE_SCENES, ids=lambda path: path.name)
def test_example_draws_every_item(path: Path) -> None:
    """Every frame, node and edge of an example scene appears in its page."""
    parsed = scene.load(path)
    collector = IdCollector()
    collector.feed(render_html.render(parsed))
    expected = {item.id for item in (*parsed.frames, *parsed.nodes, *parsed.edges)}
    assert collector.ids == expected


def test_main_line_is_animated_and_has_an_arrowhead() -> None:
    """The main role gets the animation class and an arrowhead marker."""
    page = render_html.render(scene.load(SHAPES_SCENE))
    assert f'class="{Animation.FLOW.value}"' in page
    assert 'marker-end="url(#head-main-filled)"' in page


def test_theme_styles_every_member_of_every_enum() -> None:
    """A new shape, role, tone or label kind cannot be added without a style for it."""
    theme = load_theme()
    assert set(theme.shapes) == set(Shape)
    assert set(theme.roles) == set(Role)
    assert set(theme.tones) == set(Tone)
    assert set(theme.chips) == set(LabelKind)
    assert set(theme.animations) == set(Animation)


def test_text_is_escaped() -> None:
    """Markup in node text is shown as text, not run."""
    page = render_html.render(scene.parse(minimal_scene("<script>alert(1)</script>")))
    assert "<script>alert" not in page
    assert "&lt;script&gt;" in page


def test_parse_lists_every_problem() -> None:
    """A bad scene reports all of its problems at once, each with its location."""
    bad_node = {"id": "a", "shape": "blob", "x": 0, "y": 0, "width": 10, "height": 10}
    bad_node["icon"] = "nope"
    bad_edge = {"id": "e", "role": "wiggly", "points": [[0, 0]], "to": "ghost"}
    bad_scene = {"size": [100], "nodes": [bad_node], "edges": [bad_edge]}
    with pytest.raises(scene.SceneError) as error:
        scene.parse(bad_scene)
    message = str(error.value)
    for expected in ("size", "blob", "nope", "wiggly", "points", "ghost"):
        assert expected in message


def test_command_line_rejects_a_bad_scene(tmp_path: Path) -> None:
    """The render command prints the problems and exits with code 1."""
    path = tmp_path / "bad.scene.json"
    path.write_text(json.dumps({"size": "x"}))
    run = subprocess.run(
        [sys.executable, str(FLOW_CLI), "render", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == EXIT_INVALID_SCENE
    assert "not a valid scene" in run.stderr
