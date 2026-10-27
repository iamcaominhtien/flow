"""The spec of a Kanban board, read and checked (design 08 section 5).

The JSON format::

    {"type": "kanban", "title": "...", "desc": "...",
     "columns": [{"label": "In progress", "tone": "blue", "limit": 3, "done": false,
                  "cards": [{"label": "Live order tracking", "kind": "Feature",
                             "owner": "Kai Novak", "detail": "...", "done": false}]}],
     "people": {"Kai Novak": {"initials": "KN", "tone": "green"}}}

Cards are written in priority order, the first at the top. A board with a ``kind``, an
``owner``, a ``limit`` or ``done`` is drawn as a work board (``use: board``); otherwise the
columns are options to compare (``use: compare``, the older look, drawn by ``boards``).
"""

from dataclasses import dataclass, field
from typing import Any

from ..model import Tone
from ..reader import Reader, SpecError
from .people import Person, person_of, read_people

BOARD = "board"
COMPARE = "compare"
SPEC_KEYS = {"type", "title", "desc", "theme", "style", "use", "columns", "people"}
COLUMN_KEYS = {"label", "tone", "limit", "done", "cards"}
CARD_KEYS = {"label", "detail", "kind", "owner", "done", "tone"}
BOARD_ONLY_COLUMN_KEYS = {"limit", "done"}
BOARD_ONLY_CARD_KEYS = {"kind", "owner", "done"}
KIND_TONES = {"feature": Tone.BLUE, "bug": Tone.RED, "chore": Tone.GRAY}
DEFAULT_KIND_TONE = Tone.GRAY


@dataclass(frozen=True)
class Card:
    """One card as written."""

    label: str
    detail: str
    kind: str
    tag_tone: Tone
    owner: Person | None
    is_done: bool


@dataclass
class Column:
    """One column as written, with its limit when it has one."""

    label: str
    tone: Tone
    limit: int | None
    cards: list[Card] = field(default_factory=list)


@dataclass(frozen=True)
class KanbanSpec:
    """A checked Kanban board."""

    title: str | None
    description: str | None
    columns: tuple[Column, ...]


def is_board(raw: object) -> bool:
    """Tell whether a Kanban spec is a work board rather than a comparison.

    Args:
        raw: The result of ``json.loads`` on a ``kanban`` spec.

    Returns:
        True when ``use`` says ``board``, or when ``use`` is absent and the spec has a kind, an
        owner, a limit or a done mark somewhere.
    """
    if not isinstance(raw, dict):
        return False
    if raw.get("use") in (BOARD, COMPARE):
        return raw["use"] == BOARD
    columns = [column for column in _list(raw, "columns") if isinstance(column, dict)]
    cards = [card for column in columns for card in _list(column, "cards")]
    return any(BOARD_ONLY_COLUMN_KEYS & set(column) for column in columns) or any(
        isinstance(card, dict) and BOARD_ONLY_CARD_KEYS & set(card) for card in cards
    )


def read_spec(raw: object) -> KanbanSpec:
    """Check a work board spec and turn it into the description the layout works on.

    Args:
        raw: The result of ``json.loads`` on the spec.

    Returns:
        The checked spec.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    if read.illustrated(raw, "spec"):
        read.report("spec", "a Kanban board is plain only; remove 'style' or use 'use': 'compare'")
    pinned = read_people(raw, read)
    columns = [
        _column(item, index, pinned, read) for index, item in enumerate(_list(raw, "columns"))
    ]
    if not columns:
        read.report("spec", "'columns' must list at least one column")
    if read.problems:
        raise SpecError(read.problems)
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    return KanbanSpec(title, description, tuple(column for column in columns if column))


def _list(raw: dict[str, Any], key: str) -> list[Any]:
    """Return a list field, or an empty list when it is absent or not a list."""
    value = raw.get(key, [])
    return value if isinstance(value, list) else []


def _column(
    raw: object, index: int, pinned: dict[str, dict[str, object]], read: Reader
) -> Column | None:
    """Read one column and its cards."""
    where = f"columns[{index}]"
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, COLUMN_KEYS, where)
    limit = _limit(raw, where, read)
    column = Column(
        read.text(raw, "label", where) or "",
        read.enum(Tone, raw, "tone", where) or Tone.GRAY,
        limit,
    )
    is_done = _flag(raw, "done", where, read)
    for number, item in enumerate(_list(raw, "cards")):
        card = _card(item, f"{where}.cards[{number}]", (is_done, pinned), read)
        if card is not None:
            column.cards.append(card)
    return column


def _limit(raw: dict[str, Any], where: str, read: Reader) -> int | None:
    """Read the work-in-progress limit of a column: a whole number of 1 or more, or none."""
    if "limit" not in raw:
        return None
    value = raw["limit"]
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
        return value
    read.report(where, "'limit' must be a whole number, 1 or more")
    return None


def _flag(raw: dict[str, Any], key: str, where: str, read: Reader) -> bool:
    """Read an optional true or false field."""
    value = raw.get(key, False)
    if not isinstance(value, bool):
        read.report(where, f"'{key}' must be true or false")
    return value is True


def _card(
    raw: object, where: str, context: tuple[bool, dict[str, dict[str, object]]], read: Reader
) -> Card | None:
    """Read one card; ``context`` says whether its column is done, and who is pinned."""
    column_is_done, pinned = context
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, CARD_KEYS, where)
    label = read.text(raw, "label", where)
    if not label:
        read.report(where, "'label' is required")
    kind = read.text(raw, "kind", where) or ""
    owner = read.text(raw, "owner", where)
    return Card(
        label or "",
        read.text(raw, "detail", where) or "",
        kind,
        read.enum(Tone, raw, "tone", where) or KIND_TONES.get(kind.casefold(), DEFAULT_KIND_TONE),
        person_of(owner, pinned) if owner else None,
        column_is_done or _flag(raw, "done", where, read),
    )
