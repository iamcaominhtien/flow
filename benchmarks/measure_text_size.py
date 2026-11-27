"""Measure how large the node text of every example is when the diagram is fitted to a width.

Usage: python3 benchmarks/measure_text_size.py [WIDTH ...]   (default: 390 1440)

Each spec in ``examples/`` is laid out; the smallest node font size is scaled by
``min(1, width / scene width)``, which is how large it shows when the whole diagram is fitted to
a screen of that width. Edge labels (10 px in the theme) and text inside screens are not counted,
so the real smallest text is smaller still.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
DEFAULT_WIDTHS = (390, 1440)  # css px: a phone, a laptop screen

sys.path.insert(0, str(ROOT / "plugins" / "flow"))

from flowlib import diagrams  # noqa: E402


def smallest_node_text(spec_path: Path) -> tuple[float, float] | None:
    """Return the scene width and the smallest node font size of an example, or None.

    Args:
        spec_path: An example spec.

    Returns:
        The width in css px and the font size in px, or None when no node has a font size.
    """
    scene = diagrams.layout(json.loads(spec_path.read_text(encoding="utf-8")), EXAMPLES)
    sizes = [node.font_size for node in scene.nodes if node.font_size]
    return (scene.width, min(sizes)) if sizes else None


def main(widths: tuple[int, ...]) -> None:
    """Print one row per example and the range at each width.

    Args:
        widths: The widths, in css px, to fit the diagrams to.
    """
    shown: dict[int, list[float]] = {width: [] for width in widths}
    for spec_path in sorted(EXAMPLES.glob("*.spec.json")):
        measured = smallest_node_text(spec_path)
        if measured is None:
            continue
        scene_width, font = measured
        cells = []
        for width in widths:
            size = font * min(1.0, width / scene_width)
            shown[width].append(size)
            cells.append(f"{size:5.1f}")
        print(f"{spec_path.name:48} {scene_width:6.0f}  " + "  ".join(cells))
    for width, sizes in shown.items():
        low, high = min(sizes), max(sizes)
        print(
            f"at {width} px: {len(sizes)} examples, smallest node text {low:.1f} to {high:.1f} px"
        )


if __name__ == "__main__":
    main(tuple(int(arg) for arg in sys.argv[1:]) or DEFAULT_WIDTHS)
