"""Tests for custom icons: what is allowed, what is refused, and the library size."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
FLOW = PLUGIN_DIR / "scripts" / "flow.py"
SHOP = ROOT / "examples" / "shop-architecture.spec.json"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import icon_check  # noqa: E402
from flowlib.theme import load_icons  # noqa: E402

SAFE_ICON = '<circle cx="12" cy="12" r="8"/><path d="M8 12h8"/>'


def test_library_icons_all_pass_the_check() -> None:
    """Every built-in icon passes the same check as a custom one."""
    failures = {name: icon_check.validate_icon(markup) for name, markup in load_icons().items()}
    assert {name: found for name, found in failures.items() if found} == {}


def test_a_plain_icon_is_accepted() -> None:
    """Circles and paths inside the 24 x 24 box are fine."""
    assert icon_check.validate_icon(SAFE_ICON) == []


@pytest.mark.parametrize(
    ("markup", "fragment"),
    [
        ("<script>alert(1)</script>", "script"),
        ('<image href="https://example.com/x.png"/>', "image"),
        ('<path d="M0 0" onload="x()"/>', "onload"),
        ('<path d="M0 0" style="fill:url(#a)"/>', "style"),
        ('<circle cx="12" cy="12" r="900"/>', "outside"),
        ('<path d="M0 0 <b>"/>', "well-formed"),
        ('<path d="javascript:alert(1)"/>', "path"),
        ("", "non-empty"),
    ],
)
def test_unsafe_markup_is_refused(markup: str, fragment: str) -> None:
    """Elements and attributes outside the allow-list, and bad numbers, are reported."""
    problems = icon_check.validate_icon(markup)
    assert problems
    assert fragment in " ".join(problems)


def test_a_local_icon_file_is_used_by_the_build(tmp_path: Path) -> None:
    """An icon from icons.local.json can be named in a spec and appears in the HTML."""
    spec = json.loads(SHOP.read_text())
    spec["components"][1]["icon"] = "teapot"
    (tmp_path / "shop.spec.json").write_text(json.dumps(spec))
    (tmp_path / "icons.local.json").write_text(json.dumps({"teapot": SAFE_ICON}))
    result = subprocess.run(
        [sys.executable, str(FLOW), "build", str(tmp_path / "shop.spec.json")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "M8 12h8" in (tmp_path / "shop.html").read_text()


def test_an_unsafe_local_icon_stops_the_build(tmp_path: Path) -> None:
    """A bad icons.local.json is reported with exit code 1 and writes nothing."""
    (tmp_path / "shop.spec.json").write_text(SHOP.read_text())
    (tmp_path / "icons.local.json").write_text(json.dumps({"bad": "<script/>"}))
    result = subprocess.run(
        [sys.executable, str(FLOW), "build", str(tmp_path / "shop.spec.json")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "script" in result.stderr
    assert not (tmp_path / "shop.html").exists()
