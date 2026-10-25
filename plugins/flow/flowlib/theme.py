"""Design tokens: colours, line roles, animation. Loaded from theme.json and icons.json."""

import json
from functools import cache
from pathlib import Path

HERE = Path(__file__).parent


@cache
def theme():
    return json.loads((HERE / "theme.json").read_text(encoding="utf-8"))


@cache
def icons():
    """Simple line icons: name -> inner SVG of a 24 x 24 viewBox (stroke 2, no fill)."""
    return json.loads((HERE / "icons.json").read_text(encoding="utf-8"))
