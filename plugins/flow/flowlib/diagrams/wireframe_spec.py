"""Read the spec of a wireframe: screens made of blocks on a grid, with notes, in sets.

The JSON format (design 10)::

    {"type": "wireframe", "title": "...", "desc": "...",
     "set": "states" | "responsive",
     "shared": [block, ...],
     "screens": [{"id": "S12", "label": "Cart", "device": "phone|tablet|desktop",
                  "state": "normal|loading|empty|error", "note": "1024 px and up",
                  "address": "example.com/orders", "blocks": [block, ...],
                  "annotations": [{"target": "block id", "part": "stepper", "corner": "tl",
                                   "title": "...", "text": "...", "number": 1}]}]}

A block is ``{"kind", "id", "text", "row", "col", "span", ...}`` (see ``wire_scene``). The older
``elements`` of a screen (header, text, input, button, image, list) are still read and stacked.
``shared`` blocks are added at the start of every screen, as the navbar of a state set is.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..model import (
    BlockKind,
    Corner,
    Device,
    ElementStyle,
    Fidelity,
    ScreenView,
    WireBadge,
    WireBlock,
    WireState,
)
from ..reader import PLAIN_STYLE, Reader, SpecError, suggestion
from ..wire_scene import parse_blocks

TOP_KEYS = {"type", "title", "desc", "set", "shared", "screens", "style"}
SCREEN_KEYS = {"id", "label", "device", "state", "note", "address", "blocks", "elements"}
SCREEN_KEYS |= {"annotations", "plain"}
ELEMENT_KEYS = {"kind", "label", "items"}
ANNOTATION_KEYS = {"target", "part", "corner", "title", "text", "number"}
RESPONSIVE_NOTES: dict[Device, str] = {
    Device.DESKTOP: "1024 px and up",
    Device.TABLET: "640 to 1023 px",
    Device.PHONE: "under 640 px",
}
WIRE_DEVICES = (Device.PHONE, Device.TABLET, Device.DESKTOP)


class SetKind(StrEnum):
    """A group of screens that must be drawn together."""

    STATES = "states"
    RESPONSIVE = "responsive"


@dataclass(frozen=True)
class Note:
    """One note below the screens: its number, a bold title and one line."""

    number: str
    title: str
    text: str


@dataclass(frozen=True)
class WireSpec:
    """A checked wireframe spec: its screens, its notes and the set they belong to."""

    title: str | None
    description: str | None
    screens: tuple[ScreenView, ...]
    notes: tuple[Note, ...]
    kind: SetKind | None


def read_spec(raw: object) -> WireSpec:
    """Read and check a wireframe spec.

    Args:
        raw: The result of ``json.loads`` on the spec.

    Returns:
        The spec, with every screen as a view and the notes numbered.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, TOP_KEYS, "spec")
    if raw.get("style", PLAIN_STYLE) != PLAIN_STYLE:
        read.report("spec", "a wireframe has one style, grey with one accent; drop 'style'")
    kind = read.enum(SetKind, raw, "set", "spec")
    shared = parse_blocks(raw.get("shared", []), "shared", read)
    screens, notes = _read_screens(raw.get("screens"), shared, (kind, read))
    if not screens and not read.problems:
        read.report("spec", "'screens' must list at least one screen")
    _check_set(kind, screens, read)
    if read.problems:
        raise SpecError(read.problems)
    return WireSpec(
        read.text(raw, "title", "spec"), read.text(raw, "desc", "spec"), tuple(screens), notes, kind
    )


def _read_screens(
    raw: object, shared: tuple[WireBlock, ...], context: tuple[SetKind | None, Reader]
) -> tuple[list[ScreenView], tuple[Note, ...]]:
    """Read every screen and number the annotations across them."""
    kind, read = context
    if not isinstance(raw, list):
        read.report("screens", "must be a list")
        return [], ()
    screens: list[ScreenView] = []
    numbering = _Numbering()
    for index, item in enumerate(raw):
        view = _read_screen(item, f"screens[{index}]", (shared, kind, read), numbering)
        if view is not None:
            screens.append(view)
    return screens, numbering.notes()


class _Numbering:
    """Gives each annotation its number: the same title keeps one number across screens."""

    def __init__(self) -> None:
        """Start with no notes."""
        self._by_title: dict[str, Note] = {}
        self._last = 0

    def take(self, title: str, text: str, wanted: int | None) -> str:
        """Return the number of a note, making the note when its title is new."""
        known = self._by_title.get(title)
        if known is not None:
            return known.number
        number = wanted if wanted is not None else self._last + 1
        self._last = max(self._last, number)
        self._by_title[title] = Note(str(number), title, text)
        return str(number)

    def notes(self) -> tuple[Note, ...]:
        """Return the notes in the order of their numbers."""
        return tuple(sorted(self._by_title.values(), key=lambda note: int(note.number)))


def _read_screen(
    raw: object,
    where: str,
    context: tuple[tuple[WireBlock, ...], SetKind | None, Reader],
    numbering: _Numbering,
) -> ScreenView | None:
    """Read one screen: its device, its blocks and its annotations."""
    shared, kind, read = context
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, SCREEN_KEYS, where)
    device = read.enum(Device, raw, "device", where) or Device.PHONE
    if device not in WIRE_DEVICES:
        read.report(where, "a wireframe is drawn on a phone, a tablet or a desktop")
    blocks = (*shared, *_screen_blocks(raw, where, read))
    ids = _block_ids(blocks, where, read)
    badges = _read_annotations(raw.get("annotations", []), (where, ids), (numbering, read))
    state = read.enum(WireState, raw, "state", where)
    return ScreenView(
        code=read.text(raw, "id", where) or "",
        title=read.text(raw, "label", where) or "",
        device=device,
        fidelity=Fidelity.L3,
        blocks=blocks,
        badges=badges,
        state=state,
        caption_note=_caption_note(raw, device, kind, read),
        is_captioned=True,
        is_plain=raw.get("plain", kind is SetKind.RESPONSIVE) is True,
        address=read.text(raw, "address", where) or "",
    )


def _caption_note(raw: dict[str, Any], device: Device, kind: SetKind | None, read: Reader) -> str:
    """Return the line under a screen name: its own, or the width range of a responsive set."""
    written = read.text(raw, "note", "screen")
    if written is not None:
        return written
    return RESPONSIVE_NOTES.get(device, "") if kind is SetKind.RESPONSIVE else ""


def _screen_blocks(raw: dict[str, Any], where: str, read: Reader) -> tuple[WireBlock, ...]:
    """Read the blocks of a screen, or convert its older ``elements``."""
    if "elements" in raw and "blocks" not in raw:
        return _convert_elements(raw["elements"], where, read)
    if "blocks" not in raw:
        read.report(where, "'blocks' is missing")
        return ()
    return parse_blocks(raw["blocks"], f"{where}.blocks", read)


def _convert_elements(raw: object, where: str, read: Reader) -> tuple[WireBlock, ...]:
    """Turn the older elements (header, text, input, button, image, list) into blocks."""
    blocks: list[WireBlock] = []
    for index, item in enumerate(raw if isinstance(raw, list) else []):
        here = f"{where}.elements[{index}]"
        if not isinstance(item, dict):
            read.report(here, "must be an object")
            continue
        read.check_keys(item, ELEMENT_KEYS, here)
        kind = item.get("kind")
        label = read.text(item, "label", here) or ""
        listed = item.get("items", [])
        items = [str(each) for each in listed] if isinstance(listed, list) else []
        converted = _convert(kind, label, items, blocks)
        if converted is None:
            read.report(here, f"unknown kind '{kind}'; use one of: {', '.join(OLD_KINDS)}")
            continue
        blocks.extend(converted)
    return tuple(blocks)


def _button_block(label: str, _items: list[str], has_primary: bool) -> list[WireBlock]:
    """Make a button; the first one of a screen is primary, the others are outlined."""
    style = ElementStyle.SECONDARY if has_primary else ElementStyle.PRIMARY
    return [WireBlock(BlockKind.BUTTON, text=label, style=style)]


def _list_blocks(_label: str, items: list[str], _has_primary: bool) -> list[WireBlock]:
    """Make one list item for each entry of an older list."""
    return [WireBlock(BlockKind.LIST_ITEM, text=each, flags=("chevron",)) for each in items]


OLD_ELEMENTS: dict[str, Callable[[str, list[str], bool], list[WireBlock]]] = {
    "header": lambda label, _items, _primary: [WireBlock(BlockKind.NAVBAR, text=label)],
    "text": lambda label, _items, _primary: [WireBlock(BlockKind.TEXT, text=label)],
    "input": lambda label, _items, _primary: [WireBlock(BlockKind.FORM_FIELD, detail=label)],
    "button": _button_block,
    "image": lambda label, _items, _primary: [WireBlock(BlockKind.IMAGE, text=label)],
    "list": _list_blocks,
}
OLD_KINDS = tuple(OLD_ELEMENTS)


def _convert(
    kind: object, label: str, items: list[str], before: list[WireBlock]
) -> list[WireBlock] | None:
    """Turn one older element into blocks, or None when its kind is not one of the older ones."""
    maker = OLD_ELEMENTS.get(str(kind))
    if maker is None:
        return None
    has_primary = any(block.kind is BlockKind.BUTTON for block in before)
    return maker(label, items, has_primary)


def _block_ids(blocks: tuple[WireBlock, ...], where: str, read: Reader) -> dict[str, int]:
    """Return the index of each block that has an id, reporting an id that is used twice."""
    ids: dict[str, int] = {}
    for index, block in enumerate(blocks):
        if not block.id:
            continue
        if block.id in ids:
            read.report(where, f"block id '{block.id}' is used twice")
        ids[block.id] = index
    return ids


def _read_annotations(
    raw: object, place: tuple[str, dict[str, int]], numbering: tuple[_Numbering, Reader]
) -> tuple[WireBadge, ...]:
    """Read the annotations of a screen as badges, numbering them."""
    where, ids = place
    counter, read = numbering
    if not isinstance(raw, list):
        read.report(where, "'annotations' must be a list")
        return ()
    badges = []
    for index, item in enumerate(raw):
        here = f"{where}.annotations[{index}]"
        badge = _read_annotation(item, here, (ids, counter, read))
        if badge is not None:
            badges.append(badge)
    return tuple(badges)


def _read_annotation(
    raw: object, where: str, context: tuple[dict[str, int], _Numbering, Reader]
) -> WireBadge | None:
    """Read one annotation: the block it points at, and the note it adds."""
    ids, counter, read = context
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ANNOTATION_KEYS, where)
    target, title, text = (read.text(raw, key, where) for key in ("target", "title", "text"))
    if not target or not title or not text:
        read.report(where, "'target', 'title' and 'text' are required")
        return None
    if target not in ids:
        read.report(where, f"no block has the id '{target}'{suggestion(target, ids)}")
        return None
    wanted = raw.get("number")
    number = counter.take(title, text, wanted if isinstance(wanted, int) else None)
    return WireBadge(
        number,
        ids[target],
        read.text(raw, "part", where) or "",
        read.enum(Corner, raw, "corner", where) or Corner.TOP_RIGHT,
    )


def _check_set(kind: SetKind | None, screens: list[ScreenView], read: Reader) -> None:
    """Check that a state set has its four states and a responsive set its three widths."""
    if kind is SetKind.STATES:
        present = {screen.state for screen in screens}
        missing = [state.value for state in WireState if state not in present]
        if missing or len(screens) != len(WireState):
            read.report(
                "spec",
                "a state set draws one screen for each of normal, loading, empty and error"
                + (f"; missing: {', '.join(missing)}" if missing else ""),
            )
    if kind is SetKind.RESPONSIVE:
        present_devices = {screen.device for screen in screens}
        missing = [device.value for device in WIRE_DEVICES if device not in present_devices]
        if missing or len(screens) != len(WIRE_DEVICES):
            read.report(
                "spec",
                "a responsive set draws desktop, tablet and phone once each"
                + (f"; missing: {', '.join(missing)}" if missing else ""),
            )
