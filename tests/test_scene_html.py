import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "flow"))

from flowlib import render_html, scene  # noqa: E402

EXAMPLES = sorted((ROOT / "examples").glob("*.scene.json"))


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        self.ids.update(v for k, v in attrs if k == "data-id")


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_renders_every_item(path):
    data = scene.load(path)
    parser = Collector()
    parser.feed(render_html.render(data))
    expected = {i["id"] for key in ("frames", "nodes", "edges") for i in data.get(key, [])}
    assert parser.ids == expected


def test_main_edge_is_animated_and_headed():
    data = scene.load(ROOT / "examples" / "shapes.scene.json")
    out = render_html.render(data)
    assert 'class="flow"' in out
    assert 'marker-end="url(#head-main)"' in out


def test_text_is_escaped():
    data = {
        "size": [200, 100],
        "nodes": [
            {
                "id": "a",
                "shape": "process",
                "x": 10,
                "y": 10,
                "w": 100,
                "h": 50,
                "text": "<script>alert(1)</script>",
            },
        ],
    }
    scene.validate(data)
    out = render_html.render(data)
    assert "<script>alert" not in out
    assert "&lt;script&gt;" in out


def test_validate_lists_every_problem():
    bad = {
        "size": [100],
        "nodes": [{"id": "a", "shape": "blob", "x": 0, "y": 0, "w": 10, "h": 10, "icon": "nope"}],
        "edges": [{"id": "e", "role": "wiggly", "points": [[0, 0]], "to": "ghost"}],
    }
    with pytest.raises(scene.SceneError) as err:
        scene.validate(bad)
    text = str(err.value)
    for needle in ("size", "blob", "nope", "wiggly", "points", "ghost"):
        assert needle in text


def test_cli_rejects_bad_scene(tmp_path):
    path = tmp_path / "bad.scene.json"
    path.write_text(json.dumps({"size": "x"}))
    run = subprocess.run(
        [sys.executable, str(ROOT / "plugins/flow/scripts/flow.py"), "render", str(path)],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 1
    assert "not a valid scene" in run.stderr
