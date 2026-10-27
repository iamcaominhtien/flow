"""The spec of a roadmap, read and checked (design 08 section 6).

The JSON format::

    {"type": "roadmap", "title": "...", "desc": "...",
     "periods": ["Now", {"label": "Next", "detail": "May to June", "tone": "amber"}],
     "lanes": [{"label": "Ordering", "tone": "blue", "icon": "cart", "items": [
         {"id": "tracking", "label": "Live order tracking", "period": "Now", "length": 1,
          "committed": true, "owner": "Kai Novak", "detail": "...", "blocks": "tips"}]}],
     "note": "...", "people": {"Kai Novak": {"tone": "green"}}}

``period`` is the name of a period or its number from 0 (``start`` is the older name for the
number); ``length`` is how many periods a card spans. A card with ``committed: false`` is an idea
under study and is drawn dashed. There are no exact dates. At most one dependency may be drawn:
``depends_on`` (this item cannot start before the other is done) or ``blocks`` (the other cannot
start before this one is done).
"""

from dataclasses import dataclass, field
from typing import Any

from ..model import Tone
from ..reader import Reader, SpecError, is_number, suggestion
from ..theme import icon_names
from .people import Person, person_of, read_people

SPEC_KEYS = {"type", "title", "desc", "theme", "periods", "lanes", "note", "people"}
PERIOD_KEYS = {"label", "detail", "tone"}
LANE_KEYS = {"label", "tone", "icon", "items"}
ITEM_KEYS = {
    "id", "label", "period", "start", "length", "committed", "owner", "detail", "depends_on",
    "blocks",
}  # fmt: skip
PERIOD_TONES = {"now": Tone.GREEN, "next": Tone.AMBER, "later": Tone.GRAY}
DEFAULT_PERIOD_TONE = Tone.GRAY


@dataclass(frozen=True)
class Period:
    """A column of the roadmap: its name, its dates in words and its tint."""

    label: str
    detail: str
    tone: Tone


@dataclass
class Item:
    """A card of the roadmap as written."""

    id: str
    label: str
    first: int
    length: int
    is_committed: bool
    detail: str
    owner: Person | None
    depends_on: str = ""
    blocks: str = ""


@dataclass
class Lane:
    """A row of the roadmap: a theme, and its cards."""

    label: str
    tone: Tone
    icon: str | None
    items: list[Item] = field(default_factory=list)


@dataclass(frozen=True)
class Dependency:
    """The one arrow of the roadmap: ``after`` cannot start before ``before`` is done."""

    before: str
    after: str


@dataclass(frozen=True)
class RoadmapSpec:
    """A checked roadmap."""

    title: str | None
    description: str | None
    periods: tuple[Period, ...]
    lanes: tuple[Lane, ...]
    dependency: Dependency | None
    note: str | None


def read_spec(raw: object) -> RoadmapSpec:
    """Check a roadmap spec and turn it into the description the layout works on.

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
    periods = _periods(raw, read)
    pinned = read_people(raw, read)
    lanes = _lanes(raw, (periods, pinned), read)
    dependency = _dependency(lanes, read)
    if read.problems:
        raise SpecError(read.problems)
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    return RoadmapSpec(
        title, description, tuple(periods), tuple(lanes), dependency, read.text(raw, "note", "spec")
    )


def _periods(raw: dict[str, Any], read: Reader) -> list[Period]:
    """Read the columns: a name, or an object with a name, its dates in words and a tone."""
    listed = raw.get("periods")
    if not isinstance(listed, list) or not listed:
        read.report("spec", "'periods' must be a non-empty list such as Now, Next, Later")
        return []
    return [_period(item, f"periods[{index}]", read) for index, item in enumerate(listed)]


def _period(item: object, where: str, read: Reader) -> Period:
    """Read one period; a plain name gets the tone of now, next or later, else grey."""
    if isinstance(item, str):
        return Period(item, "", PERIOD_TONES.get(item.casefold(), DEFAULT_PERIOD_TONE))
    if not isinstance(item, dict):
        read.report(where, "must be a name or an object with a 'label'")
        return Period("", "", DEFAULT_PERIOD_TONE)
    read.check_keys(item, PERIOD_KEYS, where)
    label = read.text(item, "label", where) or ""
    if not label:
        read.report(where, "'label' is required")
    tone = read.enum(Tone, item, "tone", where)
    return Period(
        label,
        read.text(item, "detail", where) or "",
        tone or PERIOD_TONES.get(label.casefold(), DEFAULT_PERIOD_TONE),
    )


def _lanes(
    raw: dict[str, Any], context: tuple[list[Period], dict[str, dict[str, object]]], read: Reader
) -> list[Lane]:
    """Read the rows and their cards."""
    listed = raw.get("lanes")
    if not isinstance(listed, list) or not listed:
        read.report("spec", "'lanes' must list at least one lane")
        return []
    lanes = []
    for index, item in enumerate(listed):
        where = f"lanes[{index}]"
        if not isinstance(item, dict):
            read.report(where, "must be an object")
            continue
        lanes.append(_lane(item, index, where, (context, read)))
    return lanes


def _lane(
    raw: dict[str, Any],
    index: int,
    where: str,
    context: tuple[tuple[list[Period], dict[str, dict[str, object]]], Reader],
) -> Lane:
    """Read one row: its theme, its icon and its cards."""
    (periods, pinned), read = context
    read.check_keys(raw, LANE_KEYS, where)
    icon = read.text(raw, "icon", where)
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    lane = Lane(
        read.text(raw, "label", where) or "",
        read.enum(Tone, raw, "tone", where) or Tone.GRAY,
        icon,
    )
    items = raw.get("items", [])
    for number, entry in enumerate(items if isinstance(items, list) else []):
        item = _item(entry, (index, number), (periods, pinned), read)
        if item is not None:
            lane.items.append(item)
    return lane


def _item(
    raw: object,
    position: tuple[int, int],
    context: tuple[list[Period], dict[str, dict[str, object]]],
    read: Reader,
) -> Item | None:
    """Read one card: where it sits, whether it is committed, and who owns it."""
    where = f"lanes[{position[0]}].items[{position[1]}]"
    periods, pinned = context
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ITEM_KEYS, where)
    first = _first(raw, periods, where, read)
    length = _length(raw, first, (len(periods), where), read)
    label = read.text(raw, "label", where) or ""
    if not label:
        read.report(where, "'label' is required")
    committed = raw.get("committed", True)
    if not isinstance(committed, bool):
        read.report(where, "'committed' must be true or false")
    owner = read.text(raw, "owner", where)
    return Item(
        read.identifier(raw, where) if "id" in raw else f"i{position[0]}-{position[1]}",
        label,
        first,
        length,
        committed is not False,
        read.text(raw, "detail", where) or "",
        person_of(owner, pinned) if owner else None,
        read.text(raw, "depends_on", where) or "",
        read.text(raw, "blocks", where) or "",
    )


def _first(raw: dict[str, Any], periods: list[Period], where: str, read: Reader) -> int:
    """Read the column a card starts in: a period name, or a number from 0."""
    if "period" in raw and "start" in raw:
        read.report(where, "write 'period' or 'start', not both")
    value = raw.get("period", raw.get("start"))
    names = [period.label for period in periods]
    if isinstance(value, str) and value in names:
        return names.index(value)
    if is_number(value) and int(value) == value and 0 <= value < len(periods):
        return int(value)
    hint = suggestion(value, names)
    read.report(where, f"'period' must be one of {', '.join(names)} or a number from 0{hint}")
    return 0


def _length(raw: dict[str, Any], first: int, context: tuple[int, str], read: Reader) -> int:
    """Read how many periods a card spans, which must keep it inside the roadmap."""
    count, where = context
    length = raw.get("length", 1)
    if not isinstance(length, int) or isinstance(length, bool) or length < 1:
        read.report(where, "'length' must be a whole number, 1 or more")
        return 1
    if first + length > count:
        read.report(where, f"ends in period {first + length}, but there are only {count}")
    return length


def _dependency(lanes: list[Lane], read: Reader) -> Dependency | None:
    """Find the one dependency; a second one is an error, as is one that cannot be followed."""
    items = [item for lane in lanes for item in lane.items]
    found = [
        (item, other, is_blocking)
        for item in items
        for other, is_blocking in ((item.depends_on, False), (item.blocks, True))
        if other
    ]
    if len(found) > 1:
        read.report(
            "spec",
            f"{len(found)} dependencies; a roadmap draws only the one that decides the order",
        )
        return None
    if not found:
        return None
    item, name, is_blocking = found[0]
    other = _lookup(name, items)
    if other is None:
        hint = suggestion(name, [each.id for each in items])
        read.report("spec", f"dependency on '{name}', which is not an item{hint}")
        return None
    before, after = (item, other) if is_blocking else (other, item)
    if before is after or after.first < before.first:
        read.report(
            "spec", f"'{after.label}' cannot start before '{before.label}' (earlier period)"
        )
        return None
    return Dependency(before.id, after.id)


def _lookup(name: str, items: list[Item]) -> Item | None:
    """Find an item by its id, or else by its label."""
    by_id = next((item for item in items if item.id == name), None)
    return by_id or next((item for item in items if item.label.casefold() == name.casefold()), None)
