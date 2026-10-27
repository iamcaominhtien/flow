"""Write and read the blocks and badges of a wireframe screen, in a scene and in a spec.

A block is written as ``{"kind": "card", "text": "Pad thai", "row": 2, "col": 1, "span": 12,
"tap": true}``: the fields that hold their default are left out, and each flag is a key that is
``true``. A table has ``columns`` and ``data``; a panel has ``children``.
"""

from typing import Any

from .model import (
    BlockAnchor,
    BlockKind,
    CellKind,
    Corner,
    ElementStyle,
    Tone,
    WireBadge,
    WireBlock,
    WireCell,
    WireColumn,
)
from .reader import Reader, is_number

TEXT_FIELDS = (
    "id",
    "text",
    "detail",
    "value",
    "chip",
    "price",
    "action",
    "hint",
    "stepper",
    "icon",
    "image",
    "lead",
    "trail",
)
NUMBER_FIELDS = ("row", "col", "span", "rows", "height", "bars")
LIST_FIELDS = ("items", "icons")
FLAGS = (
    "back",
    "menu",
    "avatar",
    "bell",
    "logo",
    "bold",
    "heading",
    "label",
    "tap",
    "focus",
    "tinted",
    "chevron",
)
BLOCK_KEYS = {"kind", "style", "tone", "anchor", "selected", "values", "columns", "data"}
BLOCK_KEYS |= {"children", *TEXT_FIELDS, *NUMBER_FIELDS, *LIST_FIELDS, *FLAGS}
COLUMN_KEYS = {"label", "weight", "kind"}
CELL_KEYS = {"text", "style"}
BADGE_KEYS = {"number", "block", "part", "corner"}
TONE_ALIASES = {"rose": Tone.RED}  # the design says rose where the palette says red
DEFAULT_ROWS = 1


def dump_blocks(blocks: tuple[WireBlock, ...]) -> list[dict[str, Any]]:
    """Turn blocks into JSON, leaving out every field that holds its default.

    Args:
        blocks: The blocks of a screen.

    Returns:
        A list of dicts that ``parse_blocks`` accepts.
    """
    return [_dump_block(block) for block in blocks]


def _dump_block(block: WireBlock) -> dict[str, Any]:
    """Write one block."""
    written: dict[str, Any] = {"kind": block.kind.value}
    written.update(_dump_fields(block))
    written.update(_dump_marks(block))
    if block.columns:
        written["columns"] = [_dump_column(column) for column in block.columns]
        written["data"] = [[_dump_cell(cell) for cell in row] for row in block.cells]
    if block.children:
        written["children"] = dump_blocks(block.children)
    return written


def _dump_fields(block: WireBlock) -> dict[str, Any]:
    """Write the words, the lists and the grid position of a block, if they are set."""
    written: dict[str, Any] = {}
    for name in (*TEXT_FIELDS, *LIST_FIELDS):
        value = getattr(block, name)
        if value:
            written[name] = list(value) if isinstance(value, tuple) else value
    for name in NUMBER_FIELDS:
        value = getattr(block, name)
        if value and not (name == "rows" and value == DEFAULT_ROWS):
            written[name] = value
    return written


def _dump_marks(block: WireBlock) -> dict[str, Any]:
    """Write the selection, the values, the style, the tone, the anchor and the flags."""
    written: dict[str, Any] = {}
    if block.selected:
        written["selected"] = list(block.selected)
    if block.values:
        written["values"] = list(block.values)
    if block.style is not None:
        written["style"] = block.style.value
    if block.tone is not None:
        written["tone"] = block.tone.value
    if block.anchor is not BlockAnchor.GRID:
        written["anchor"] = block.anchor.value
    written.update(dict.fromkeys(block.flags, True))
    return written


def _dump_column(column: WireColumn) -> dict[str, Any]:
    """Write one column of a table."""
    return {"label": column.label, "weight": column.weight, "kind": column.kind.value}


def _dump_cell(cell: WireCell) -> str | dict[str, str]:
    """Write one cell: a plain string, or an object when it has a style."""
    return {"text": cell.text, "style": cell.style} if cell.style else cell.text


def parse_blocks(raw: object, where: str, read: Reader) -> tuple[WireBlock, ...]:
    """Read the blocks of a screen, reporting every problem.

    Args:
        raw: The ``blocks`` list.
        where: Where the list is, for messages.
        read: The reader that collects problems.

    Returns:
        The blocks that could be read.
    """
    if not isinstance(raw, list):
        read.report(where, "'blocks' must be a list")
        return ()
    found = []
    for index, item in enumerate(raw):
        block = _parse_block(item, f"{where}[{index}]", read)
        if block is not None:
            found.append(block)
    return tuple(found)


def _parse_block(raw: object, where: str, read: Reader) -> WireBlock | None:
    """Read one block, or report why it cannot be read."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, BLOCK_KEYS, where)
    kind = read.enum(BlockKind, raw, "kind", where)
    if kind is None:
        if "kind" not in raw:
            read.report(where, "'kind' is missing")
        return None
    texts = {name: read.text(raw, name, where) or "" for name in TEXT_FIELDS}
    numbers = {name: _number(raw, name, where, read) for name in NUMBER_FIELDS}
    lists = {name: _strings(raw.get(name), f"{where}.{name}", read) for name in LIST_FIELDS}
    columns = _parse_columns(raw.get("columns", []), f"{where}.columns", read)
    return WireBlock(
        kind=kind,
        **texts,
        **{name: lists[name] for name in LIST_FIELDS},
        **{name: numbers[name] for name in NUMBER_FIELDS if name not in ("rows", "height")},
        rows=int(numbers["rows"]) or DEFAULT_ROWS,
        height=numbers["height"],
        selected=_selection(raw.get("selected"), f"{where}.selected", read),
        values=_values(raw.get("values"), f"{where}.values", read),
        columns=columns,
        cells=_parse_cells(raw.get("data", []), f"{where}.data", read),
        style=read.enum(ElementStyle, raw, "style", where),
        tone=_tone(raw, where, read),
        anchor=read.enum(BlockAnchor, raw, "anchor", where) or BlockAnchor.GRID,
        flags=tuple(flag for flag in FLAGS if raw.get(flag) is True),
        children=parse_blocks(raw["children"], f"{where}.children", read)
        if "children" in raw
        else (),
    )


def _number(raw: dict[str, Any], key: str, where: str, read: Reader) -> float:
    """Read an optional non-negative number; 0 means that it is not set."""
    value = raw.get(key, 0)
    if is_number(value) and value >= 0:
        return value
    read.report(where, f"'{key}' must be a number of 0 or more")
    return 0


def _strings(raw: object, where: str, read: Reader) -> tuple[str, ...]:
    """Read a list of strings."""
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        read.report(where, "must be a list of strings")
        return ()
    return tuple(raw)


def _selection(raw: object, where: str, read: Reader) -> tuple[int, ...]:
    """Read which items are selected: one index, or a list of them."""
    if raw is None:
        return ()
    listed = raw if isinstance(raw, list) else [raw]
    if all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in listed):
        return tuple(listed)
    read.report(where, "must be an item number or a list of them, counted from 0")
    return ()


def _values(raw: object, where: str, read: Reader) -> tuple[float, ...]:
    """Read the values of a chart."""
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(is_number(item) for item in raw):
        read.report(where, "must be a list of numbers")
        return ()
    return tuple(raw)


def _tone(raw: dict[str, Any], where: str, read: Reader) -> Tone | None:
    """Read a tone; ``rose`` is another name for red."""
    name = raw.get("tone")
    if name in TONE_ALIASES:
        return TONE_ALIASES[name]
    return read.enum(Tone, raw, "tone", where)


def _parse_columns(raw: object, where: str, read: Reader) -> tuple[WireColumn, ...]:
    """Read the columns of a table."""
    if not isinstance(raw, list):
        read.report(where, "must be a list")
        return ()
    columns = []
    for index, item in enumerate(raw):
        here = f"{where}[{index}]"
        if not isinstance(item, dict):
            read.report(here, "must be an object")
            continue
        read.check_keys(item, COLUMN_KEYS, here)
        weight = item.get("weight", 1)
        columns.append(
            WireColumn(
                read.text(item, "label", here) or "",
                weight if is_number(weight) and weight > 0 else 1.0,
                read.enum(CellKind, item, "kind", here) or CellKind.TEXT,
            )
        )
    return tuple(columns)


def _parse_cells(raw: object, where: str, read: Reader) -> tuple[tuple[WireCell, ...], ...]:
    """Read the rows of a table: each cell is a string or ``{"text", "style"}``."""
    if not isinstance(raw, list):
        read.report(where, "must be a list of rows")
        return ()
    rows = []
    for number, row in enumerate(raw):
        here = f"{where}[{number}]"
        if not isinstance(row, list):
            read.report(here, "must be a list of cells")
            continue
        rows.append(
            tuple(_parse_cell(cell, f"{here}[{index}]", read) for index, cell in enumerate(row))
        )
    return tuple(rows)


def _parse_cell(raw: object, where: str, read: Reader) -> WireCell:
    """Read one cell."""
    if isinstance(raw, str | int | float) and not isinstance(raw, bool):
        return WireCell(str(raw))
    if not isinstance(raw, dict):
        read.report(where, "must be a string or an object")
        return WireCell("")
    read.check_keys(raw, CELL_KEYS, where)
    return WireCell(read.text(raw, "text", where) or "", read.text(raw, "style", where) or "")


def dump_badges(badges: tuple[WireBadge, ...]) -> list[dict[str, Any]]:
    """Turn badges into JSON."""
    written = []
    for badge in badges:
        item: dict[str, Any] = {"number": badge.number, "block": badge.block}
        if badge.part:
            item["part"] = badge.part
        item["corner"] = badge.corner.value
        written.append(item)
    return written


def parse_badges(raw: object, where: str, read: Reader) -> tuple[WireBadge, ...]:
    """Read the badges of a screen."""
    if not isinstance(raw, list):
        read.report(where, "'badges' must be a list")
        return ()
    badges = []
    for index, item in enumerate(raw):
        here = f"{where}[{index}]"
        if not isinstance(item, dict):
            read.report(here, "must be an object")
            continue
        read.check_keys(item, BADGE_KEYS, here)
        block = item.get("block")
        if not isinstance(block, int) or isinstance(block, bool):
            read.report(here, "'block' must be the number of a block")
            continue
        badges.append(
            WireBadge(
                read.text(item, "number", here) or "",
                block,
                read.text(item, "part", here) or "",
                read.enum(Corner, item, "corner", here) or Corner.TOP_RIGHT,
            )
        )
    return tuple(badges)
