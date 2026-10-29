"""Put the screenshots named in a capture manifest into a screen flow spec.

``skills/screen-flow/capture.js`` writes ``manifest.json`` next to the screenshots it takes: one
entry per screen code, with the image, the source file and the hotspot boxes. A spec names the
manifest once (``"captures": "captures/manifest.json"``) and each L4 screen by its code
(``"capture": "W02"``), so taking the screenshots again needs no edit of the spec.
"""

import json
from pathlib import Path
from typing import Any

from ..reader import SpecError

MANIFEST_KEY = "captures"
KEPT_KEYS = ("source", "hotspots")  # besides the image; the address and the misses stay behind


def with_manifest(raw: object, folder: Path) -> object:
    """Replace every capture named by a code with its entry in the spec's manifest.

    Args:
        raw: The result of ``json.loads`` on a screen flow spec.
        folder: The folder of the spec; the manifest's path is read from it.

    Returns:
        The spec without the ``captures`` key and with every ``"capture": "<code>"`` written out;
        the spec itself when it names no manifest.

    Raises:
        SpecError: If the manifest cannot be read or a code is not in it.
    """
    if not isinstance(raw, dict) or MANIFEST_KEY not in raw:
        return raw
    reference = raw[MANIFEST_KEY]
    if not isinstance(reference, str):
        raise SpecError(["spec: 'captures' must be the path of a manifest.json"])
    entries = _entries(folder / reference, reference)
    screens = raw.get("screens", [])
    if not isinstance(screens, list):
        return raw
    problems = [
        f"screens[{index}]: '{item['capture']}' is not in {reference}"
        for index, item in enumerate(screens)
        if _is_named(item) and item["capture"] not in entries
    ]
    if problems:
        raise SpecError(problems)
    base = Path(reference).parent
    written = [
        {**item, "capture": _capture(entries[item["capture"]], base)} if _is_named(item) else item
        for item in screens
    ]
    kept = {key: value for key, value in raw.items() if key != MANIFEST_KEY}
    return {**kept, "screens": written}


def _entries(path: Path, reference: str) -> dict[str, Any]:
    """Read the screens of a manifest by code, or say why it cannot be read."""
    if not path.is_file():
        raise SpecError([f"spec: the manifest '{reference}' does not exist; run capture.js first"])
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SpecError([f"spec: the manifest '{reference}' is not JSON: {error}"]) from error
    screens = manifest.get("screens") if isinstance(manifest, dict) else None
    if not isinstance(screens, dict):
        raise SpecError([f"spec: the manifest '{reference}' has no 'screens' object"])
    return screens


def _is_named(item: object) -> bool:
    """Tell whether a screen item names its capture by a code of the manifest."""
    return isinstance(item, dict) and isinstance(item.get("capture"), str)


def _capture(entry: dict[str, Any], base: Path) -> dict[str, Any]:
    """Write a manifest entry as a capture, with the image's path read from the spec's folder."""
    capture: dict[str, Any] = {"image": str(base / entry.get("image", ""))}
    capture.update({key: entry[key] for key in KEPT_KEYS if entry.get(key)})
    return capture
