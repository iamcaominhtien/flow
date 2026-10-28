"""Write and read what a screen node shows, in the JSON of a scene and in a draw.io style.

The scene format of a screen node is ``"screen": {"code", "title", "device", "orientation",
"mini", "fidelity", "content", "hatch", "elements": [{"text", "style", "at", "on", "hotspot"}],
"overlay", "overlay_title", "tab": [active, count], "undecided", "chip_place"}``; keys that hold
their default are left out.
"""

import base64
import json
from typing import Any

from .model import (
    Capture,
    ChipPlace,
    Content,
    Device,
    ElementStyle,
    Fidelity,
    Hotspot,
    Layer,
    Orientation,
    Overlay,
    Placement,
    ScreenElement,
    ScreenView,
    WireState,
)
from .reader import Reader, is_number
from .wire_scene import dump_badges, dump_blocks, parse_badges, parse_blocks

SCREEN_KEYS = {"code", "title", "device", "orientation", "mini", "fidelity", "content", "hatch"}
SCREEN_KEYS |= {"elements", "overlay", "overlay_title", "tab", "undecided", "chip_place"}
SCREEN_KEYS |= {
    "blocks",
    "badges",
    "state",
    "scale",
    "caption_note",
    "captioned",
    "address",
    "bare",
    "plain",
    "capture",
}
CAPTURE_KEYS = {"image", "source", "hotspots"}
HOTSPOT_KEYS = {"text", "box"}
BOX_LENGTH = 4
ELEMENT_KEYS = {"text", "style", "at", "on", "hotspot"}
TAB_LENGTH = 2
DEFAULT_VIEW = ScreenView(code="")


def dump_screen(view: ScreenView) -> dict[str, Any]:
    """Turn a screen view into JSON, leaving out what holds its default.

    Args:
        view: What a screen node shows.

    Returns:
        A JSON-style dict that ``parse_screen`` accepts.
    """
    written: dict[str, Any] = {"code": view.code, "title": view.title}
    written["device"] = view.device.value
    written["fidelity"] = view.fidelity.value
    optional = {
        "orientation": view.orientation.value
        if view.orientation != DEFAULT_VIEW.orientation
        else None,
        "mini": view.is_mini,
        "content": view.content.value if view.content is not Content.HATCH else None,
        "hatch": view.hatch_label,
        "elements": [_dump_element(element) for element in view.elements],
        "overlay": view.overlay.value if view.overlay else None,
        "overlay_title": view.overlay_title,
        "tab": [view.tab_active, view.tab_count] if view.tab_active is not None else None,
        "undecided": view.is_undecided,
        "chip_place": view.chip_place.value if view.chip_place is not ChipPlace.ABOVE else None,
        "blocks": dump_blocks(view.blocks),
        "badges": dump_badges(view.badges),
        "state": view.state.value if view.state else None,
        "scale": view.scale if view.scale != DEFAULT_VIEW.scale else None,
        "caption_note": view.caption_note,
        "captioned": view.is_captioned,
        "address": view.address,
        "bare": view.is_bare,
        "plain": view.is_plain,
        "capture": dump_capture(view.capture) if view.capture else None,
    }
    written.update({key: value for key, value in optional.items() if value})
    return written


def _dump_element(element: ScreenElement) -> dict[str, Any]:
    """Write one named element of a screen."""
    written: dict[str, Any] = {"text": element.text, "style": element.style.value}
    written["at"] = element.placement.value
    if element.layer is Layer.OVERLAY:
        written["on"] = element.layer.value
    if not element.is_hotspot:
        written["hotspot"] = False
    return written


def parse_screen(raw: object, where: str, read: Reader) -> ScreenView | None:
    """Read a screen view from its JSON, or report why it cannot be read.

    Args:
        raw: The ``screen`` object of a node.
        where: Where the object is, for messages.
        read: The reader that collects problems.

    Returns:
        The view, or None when it is not an object.
    """
    if not isinstance(raw, dict):
        read.report(where, "'screen' must be an object")
        return None
    read.check_keys(raw, SCREEN_KEYS, where)
    tab = raw.get("tab")
    has_tab = isinstance(tab, list) and len(tab) == TAB_LENGTH
    return ScreenView(
        code=read.text(raw, "code", where) or "",
        title=read.text(raw, "title", where) or "",
        device=read.enum(Device, raw, "device", where) or Device.PHONE,
        orientation=read.enum(Orientation, raw, "orientation", where) or Orientation.PORTRAIT,
        is_mini=raw.get("mini") is True,
        fidelity=read.enum(Fidelity, raw, "fidelity", where) or Fidelity.L0,
        content=read.enum(Content, raw, "content", where) or Content.HATCH,
        hatch_label=read.text(raw, "hatch", where) or "",
        elements=_parse_elements(raw.get("elements", []), where, read),
        overlay=read.enum(Overlay, raw, "overlay", where),
        overlay_title=read.text(raw, "overlay_title", where) or "",
        tab_active=tab[0] if has_tab else None,
        tab_count=tab[1] if has_tab else 0,
        is_undecided=raw.get("undecided") is True,
        chip_place=read.enum(ChipPlace, raw, "chip_place", where) or ChipPlace.ABOVE,
        blocks=parse_blocks(raw.get("blocks", []), f"{where}.blocks", read),
        badges=parse_badges(raw.get("badges", []), f"{where}.badges", read),
        state=read.enum(WireState, raw, "state", where),
        scale=raw["scale"] if is_number(raw.get("scale")) and raw["scale"] > 0 else 1.0,
        caption_note=read.text(raw, "caption_note", where) or "",
        is_captioned=raw.get("captioned") is True,
        address=read.text(raw, "address", where) or "",
        is_bare=raw.get("bare") is True,
        is_plain=raw.get("plain") is True,
        capture=parse_capture(raw["capture"], f"{where}.capture", read)
        if "capture" in raw
        else None,
    )


def dump_capture(capture: Capture) -> dict[str, Any]:
    """Write the screenshot of an L4 screen: its image, its source file and its hotspots.

    Args:
        capture: The capture.

    Returns:
        A JSON-style dict that ``parse_capture`` accepts.
    """
    written: dict[str, Any] = {"image": capture.image}
    if capture.source:
        written["source"] = capture.source
    if capture.hotspots:
        written["hotspots"] = [
            {"text": hotspot.text, "box": list(hotspot.box)} for hotspot in capture.hotspots
        ]
    return written


def parse_capture(raw: object, where: str, read: Reader) -> Capture | None:
    """Read the screenshot of an L4 screen, from a spec or a scene.

    Args:
        raw: ``{"image": "a.png", "source": "src/a.ts", "hotspots": [{"text", "box"}]}``; the
            box is left, top, width and height in the screenshot's pixels.
        where: Where the object is, for messages.
        read: The reader that collects problems.

    Returns:
        The capture, or None when it has no image.
    """
    if isinstance(raw, str):
        read.report(
            where, f'\'{raw}\' names a screen of a manifest; add "captures": "<manifest.json>"'
        )
        return None
    if not isinstance(raw, dict):
        read.report(where, "'capture' must be an object with an 'image'")
        return None
    read.check_keys(raw, CAPTURE_KEYS, where)
    image = read.text(raw, "image", where)
    if not image:
        read.report(where, "'image' is required: the path of a PNG screenshot")
        return None
    hotspots = raw.get("hotspots", [])
    if not isinstance(hotspots, list):
        read.report(where, "'hotspots' must be a list")
        hotspots = []
    found = [_hotspot(item, f"{where}.hotspots[{i}]", read) for i, item in enumerate(hotspots)]
    return Capture(
        image=image,
        source=read.text(raw, "source", where) or "",
        hotspots=tuple(hotspot for hotspot in found if hotspot is not None),
    )


def _hotspot(raw: object, where: str, read: Reader) -> Hotspot | None:
    """Read one hotspot: the text of the element and its box in the screenshot."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, HOTSPOT_KEYS, where)
    box = raw.get("box")
    is_box = isinstance(box, list) and len(box) == BOX_LENGTH and all(map(is_number, box))
    if not is_box:
        read.report(where, "'box' must be [left, top, width, height] in pixels")
        return None
    left, top, width, height = box
    return Hotspot(read.text(raw, "text", where) or "", (left, top, width, height))


def _parse_elements(raw: object, where: str, read: Reader) -> tuple[ScreenElement, ...]:
    """Read the named elements of a screen."""
    if not isinstance(raw, list):
        read.report(where, "'elements' must be a list")
        return ()
    found = []
    for index, item in enumerate(raw):
        place = f"{where}.elements[{index}]"
        if not isinstance(item, dict):
            read.report(place, "must be an object")
            continue
        read.check_keys(item, ELEMENT_KEYS, place)
        found.append(
            ScreenElement(
                text=read.text(item, "text", place) or "",
                style=read.enum(ElementStyle, item, "style", place) or ElementStyle.PRIMARY,
                placement=read.enum(Placement, item, "at", place) or Placement.BOTTOM,
                layer=Layer.OVERLAY if item.get("on") == Layer.OVERLAY.value else Layer.BASE,
                is_hotspot=item.get("hotspot", True) is not False,
            )
        )
    return tuple(found)


def encode_screen(view: ScreenView) -> str:
    """Pack a screen view into one word that fits in a draw.io style, which has no semicolons."""
    text = json.dumps(dump_screen(view), separators=(",", ":"))
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def decode_screen(packed: str) -> ScreenView | None:
    """Unpack what ``encode_screen`` wrote, or return None when it cannot be read."""
    padded = packed + "=" * (-len(packed) % 4)
    try:
        raw = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
    except ValueError:
        return None
    return parse_screen(raw, "screen", Reader())
