"""Measure the layout of a drawn scene: size, text at the medium, empty zones, long lines.

Usage: python3 benchmarks/large/measure.py MEDIUM SCENE.json [SCENE.json ...]

MEDIUM is the width the reader sees, in css px (390 a phone, 1440 a screen). For each scene it
prints one line:

- ``nodes``: how many nodes;
- ``page``: width x height in css px, and ``screens``: how many screens of the medium's width
  and a 16:10 height the whole page fills when shown at 100%;
- ``text@medium``: the smallest node text when the whole page is fitted to the medium's width;
- ``zone_empty``: the share of the zones' area that no node covers (a zone inside another counts
  once, by its own area);
- ``longest_line``: the longest line as a share of the page's diagonal;
- ``backward``: lines whose last stretch points left or up, against the reading order;
- ``ink``: the share of the page that nodes cover.

The numbers describe a layout; they do not judge it. Compare two layouts of the same content.
"""

import json
import math
import sys
from itertools import pairwise
from pathlib import Path

SCREEN_RATIO = 10 / 16  # height of a screen for its width
MIN_STRETCH_PX = 1.0  # a last stretch shorter than this has no direction


def _area(box: dict[str, float]) -> float:
    """Return the area of a box with x, y, width and height."""
    return box["width"] * box["height"]


def _overlap(first: dict[str, float], second: dict[str, float]) -> float:
    """Return the area two boxes share."""
    width = min(first["x"] + first["width"], second["x"] + second["width"]) - max(
        first["x"], second["x"]
    )
    height = min(first["y"] + first["height"], second["y"] + second["height"]) - max(
        first["y"], second["y"]
    )
    return max(0.0, width) * max(0.0, height)


def _zone_empty(scene: dict[str, object]) -> float:
    """Return the share of the area of the zones that no node covers."""
    zones = [frame for frame in scene.get("frames", []) if frame.get("variant") == "area"]
    total = sum(_area(zone) for zone in zones)
    if not total:
        return 0.0
    covered = sum(_overlap(zone, node) for zone in zones for node in scene["nodes"])
    return max(0.0, 1 - covered / total)


def _backward(edge: dict[str, object]) -> bool:
    """Return whether a line ends going left or up."""
    points = edge["points"]
    (x1, y1), (x2, y2) = points[-2], points[-1]
    if abs(x2 - x1) >= MIN_STRETCH_PX:
        return x2 < x1
    return y2 < y1 - MIN_STRETCH_PX


def _length(edge: dict[str, object]) -> float:
    """Return the length of a line along its points."""
    points = edge["points"]
    return sum(math.dist(a, b) for a, b in pairwise(points))


def measure(path: Path, medium: float) -> dict[str, object]:
    """Return the measures of one scene.

    Args:
        path: A ``.scene.json`` file.
        medium: The reader's width in css px.

    Returns:
        The measures, by name.
    """
    scene = json.loads(path.read_text(encoding="utf-8"))
    width, height = scene["size"]
    nodes, edges = scene["nodes"], scene["edges"]
    fonts = [node.get("font_size") or 0 for node in nodes if node.get("font_size")]
    scale = min(1.0, medium / width)
    screens = (width / medium) * (height / (medium * SCREEN_RATIO))
    return {
        "nodes": len(nodes),
        "page": f"{width:.0f}x{height:.0f}",
        "screens": round(max(1.0, screens), 1),
        "text@medium": round(min(fonts) * scale, 1) if fonts else None,
        "zone_empty": round(_zone_empty(scene), 2),
        "longest_line": round(
            max((_length(e) for e in edges), default=0) / math.hypot(width, height), 2
        ),
        "backward": sum(_backward(edge) for edge in edges),
        "ink": round(sum(_area(node) for node in nodes) / (width * height), 2),
    }


if __name__ == "__main__":
    medium_width = float(sys.argv[1])
    for name in sys.argv[2:]:
        row = measure(Path(name), medium_width)
        print(f"{name}: " + "  ".join(f"{key}={value}" for key, value in row.items()))
