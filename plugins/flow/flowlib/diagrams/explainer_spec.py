"""The spec of an explainer, read and checked (design 07).

The JSON format, one shape on a page::

    {"type": "explainer", "shape": "layers", "title": "How a web page reaches you",
     "desc": "...", "numbers": true, "closing": "...",
     "bands": [{"label": "You", "tone": "blue", "remark": "...",
                "cards": [{"id": "browser", "name": "Your browser", "text": "...",
                           "icon": "browser", "tone": "blue", "number": "1", "col": 0,
                           "stack": 0, "branch": false}]}],
     "links": [{"from": "browser", "to": "dns", "label": "asks where it is",
                "kind": "path"}]}

The other shapes are ``tree`` (``root``, ``rows``, ``note``), ``comparison`` (``left``,
``right``, ``rows``, ``rule``) and ``concept`` (``hub``, ``facts``, ``analogy``). A page that
combines several has ``sections`` instead: each is one shape with a ``title`` and a ``column``
(``left``, ``right`` or ``full``) and may also be an ``analogy``.
"""

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..model import Role, Tone
from ..reader import Reader, SpecError
from ..theme import icon_names

EXPLAINER = "explainer"
TOP_KEYS = {"type", "theme", "title", "desc", "shape", "sections"}
SECTION_KEYS = {"shape", "title", "column"}
CARD_KEYS = {"id", "name", "text", "icon", "tone", "number", "col", "stack", "branch"}
BAND_KEYS = {"label", "tone", "cards", "remark"}
LINK_KEYS = {"from", "to", "label", "kind"}
ROW_KEYS = {"name", "text", "icon", "tone", "inside"}
COMPARE_ROW_KEYS = {"label", "left", "right"}
RULE_KEYS = {"title", "text"}
ANALOGY_KEYS = {"label", "tone", "left", "right", "link", "closing"}
SLUG = re.compile(r"[^a-z0-9]+")
MAX_FACTS = 4
MIN_FACTS = 2


class Shape(StrEnum):
    """The shapes of an explainer."""

    LAYERS = "layers"
    TREE = "tree"
    COMPARISON = "comparison"
    CONCEPT = "concept"
    ANALOGY = "analogy"


class Column(StrEnum):
    """Which column of a page of sections a section sits in."""

    LEFT = "left"
    RIGHT = "right"
    FULL = "full"


class LinkKind(StrEnum):
    """What a line between two cards says."""

    PATH = "path"
    STEP = "step"
    RETURN = "return"
    YES = "yes"
    NO = "no"


LINK_ROLES: dict[LinkKind, Role] = {
    LinkKind.PATH: Role.MAIN,
    LinkKind.STEP: Role.NEXT,
    LinkKind.RETURN: Role.BACK,
    LinkKind.YES: Role.YES,
    LinkKind.NO: Role.NO,
}


@dataclass(frozen=True)
class Card:
    """One card as written: a name, one or two lines of text, an icon and a place."""

    key: str
    name: str
    text: str
    icon: str | None
    tone: Tone | None
    number: str | None = None
    col: int | None = None
    stack: int = 0
    is_branch: bool = False


@dataclass(frozen=True)
class Band:
    """A band of a layered flow: a label, a tint, its cards and an optional bold remark."""

    label: str
    tone: Tone
    cards: tuple[Card, ...]
    remark: str


@dataclass(frozen=True)
class Link:
    """A line between two cards and what it says in everyday words."""

    source: str
    target: str
    label: str
    kind: LinkKind


@dataclass(frozen=True)
class Layers:
    """A journey through bands."""

    bands: tuple[Band, ...]
    links: tuple[Link, ...]
    closing: str
    has_numbers: bool


@dataclass(frozen=True)
class Row:
    """One row of a tree: a name, a line of purpose and, for a folder, what is inside."""

    name: str
    text: str
    icon: str | None
    tone: Tone | None
    inside: tuple[str, ...]


@dataclass(frozen=True)
class Tree:
    """A root card and the rows of its parts."""

    root: Card
    rows: tuple[Row, ...]
    note: str
    is_code: bool


@dataclass(frozen=True)
class CompareRow:
    """One row of a comparison: a label and a text for each side."""

    label: str
    left: str
    right: str


@dataclass(frozen=True)
class Comparison:
    """Two panels and the rows that read across them, with a rule of thumb."""

    left: Card
    right: Card
    rows: tuple[CompareRow, ...]
    rule_title: str
    rule_text: str


@dataclass(frozen=True)
class Analogy:
    """Two cards joined by a spoken label, in a band of their own."""

    label: str
    tone: Tone
    left: Card
    right: Card
    link: str
    closing: str


@dataclass(frozen=True)
class Concept:
    """One idea in the middle, short facts around it and an analogy below."""

    hub: Card
    facts: tuple[Card, ...]
    analogy: Analogy | None


Body = Layers | Tree | Comparison | Concept | Analogy


@dataclass(frozen=True)
class Section:
    """One part of a page that combines shapes."""

    title: str
    column: Column
    body: Body


@dataclass(frozen=True)
class ExplainerSpec:
    """A checked explainer: a title and either one body or several sections."""

    title: str | None
    description: str | None
    body: Body | None
    sections: tuple[Section, ...]


def read_spec(raw: object) -> ExplainerSpec:
    """Read and check an explainer spec.

    Args:
        raw: The result of ``json.loads`` on an ``explainer`` spec.

    Returns:
        The checked spec.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    sections = _sections(raw, read)
    body = None if "sections" in raw else _body(raw, "spec", read)
    if "sections" not in raw and "shape" not in raw:
        read.report("spec", "'shape' or 'sections' is required")
    allowed = TOP_KEYS | (_shape_keys(raw) if body is not None else set())
    read.check_keys(raw, allowed, "spec")
    if read.problems:
        raise SpecError(read.problems)
    return ExplainerSpec(
        read.text(raw, "title", "spec"), read.text(raw, "desc", "spec"), body, sections
    )


def _shape_keys(raw: dict[str, Any]) -> set[str]:
    """Return the keys the shape of a spec adds to the top-level keys."""
    return SHAPE_KEYS.get(raw.get("shape", ""), set())


SHAPE_KEYS: dict[str, set[str]] = {
    Shape.LAYERS: {"bands", "links", "closing", "numbers"},
    Shape.TREE: {"root", "rows", "note", "names"},
    Shape.COMPARISON: {"left", "right", "rows", "rule"},
    Shape.CONCEPT: {"hub", "facts", "analogy"},
    Shape.ANALOGY: ANALOGY_KEYS,
}


def _sections(raw: dict[str, Any], read: Reader) -> tuple[Section, ...]:
    """Read the sections of a page, or return none when the spec has one shape."""
    listed = raw.get("sections")
    if listed is None:
        return ()
    if not isinstance(listed, list) or not listed:
        read.report("spec", "'sections' must be a non-empty list")
        return ()
    found = [_section(item, f"sections[{index}]", read) for index, item in enumerate(listed)]
    return tuple(section for section in found if section is not None)


def _section(raw: object, where: str, read: Reader) -> Section | None:
    """Read one section: its title, its column and the shape it holds."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    body = _body(raw, where, read)
    allowed = SECTION_KEYS | _shape_keys(raw)
    read.check_keys(raw, allowed, where)
    column = read.enum(Column, raw, "column", where) or Column.LEFT
    title = read.text(raw, "title", where)
    if not title and not isinstance(body, Analogy):
        read.report(where, "'title' is required")
    return None if body is None else Section(title or "", column, body)


def _body(raw: dict[str, Any], where: str, read: Reader) -> Body | None:
    """Read the shape of a spec or of a section."""
    shape = read.enum(Shape, raw, "shape", where)
    if shape is None:
        return None
    readers = {
        Shape.LAYERS: _layers,
        Shape.TREE: _tree,
        Shape.COMPARISON: _comparison,
        Shape.CONCEPT: _concept,
        Shape.ANALOGY: _analogy,
    }
    return readers[shape](raw, where, read)


def _slug(name: str) -> str:
    """Turn a name into an id: lowercase letters and digits joined by dashes."""
    return SLUG.sub("-", name.lower()).strip("-")


def _card(raw: object, where: str, read: Reader) -> Card:
    """Read one card; the id defaults to the name."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return Card("", "", "", None, None)
    read.check_keys(raw, CARD_KEYS, where)
    name = read.text(raw, "name", where) or ""
    if not name:
        read.report(where, "'name' is required")
    icon = read.text(raw, "icon", where)
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    return Card(
        key=read.text(raw, "id", where) or _slug(name),
        name=name,
        text=read.text(raw, "text", where) or "",
        icon=icon,
        tone=read.enum(Tone, raw, "tone", where),
        number=read.text(raw, "number", where),
        col=_whole(raw, "col", where, read),
        stack=_whole(raw, "stack", where, read) or 0,
        is_branch=raw.get("branch") is True,
    )


def _whole(raw: dict[str, Any], key: str, where: str, read: Reader) -> int | None:
    """Read an optional whole number that is not negative."""
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    read.report(where, f"'{key}' must be a whole number, 0 or more")
    return None


def _list(raw: dict[str, Any], key: str, where: str, read: Reader) -> list[Any]:
    """Read a list field, reporting a problem when it is not a list."""
    value = raw.get(key, [])
    if isinstance(value, list):
        return value
    read.report(where, f"'{key}' must be a list")
    return []


def _layers(raw: dict[str, Any], where: str, read: Reader) -> Layers:
    """Read a layered flow: its bands, its links and its closing line."""
    bands = tuple(
        _band(item, f"{where}.bands[{index}]", read)
        for index, item in enumerate(_list(raw, "bands", where, read))
    )
    if not bands:
        read.report(where, "'bands' must list at least one band")
    keys = [card.key for band in bands for card in band.cards]
    if len(keys) != len(set(keys)):
        read.report(where, "two cards have the same id; give each card an 'id'")
    links = tuple(
        _link(item, f"{where}.links[{index}]", keys, read)
        for index, item in enumerate(_list(raw, "links", where, read))
    )
    return Layers(
        bands, links, read.text(raw, "closing", where) or "", raw.get("numbers", True) is not False
    )


def _band(raw: object, where: str, read: Reader) -> Band:
    """Read one band."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return Band("", Tone.GRAY, (), "")
    read.check_keys(raw, BAND_KEYS, where)
    cards = tuple(
        _card(item, f"{where}.cards[{index}]", read)
        for index, item in enumerate(_list(raw, "cards", where, read))
    )
    if not cards:
        read.report(where, "'cards' must list at least one card")
    return Band(
        read.text(raw, "label", where) or "",
        read.enum(Tone, raw, "tone", where) or Tone.GRAY,
        cards,
        read.text(raw, "remark", where) or "",
    )


def _link(raw: object, where: str, keys: list[str], read: Reader) -> Link:
    """Read one link between two cards of a layered flow."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return Link("", "", "", LinkKind.PATH)
    read.check_keys(raw, LINK_KEYS, where)
    for end in ("from", "to"):
        if raw.get(end) not in keys:
            read.report(where, f"'{end}' names '{raw.get(end)}', which is not a card")
    return Link(
        str(raw.get("from", "")),
        str(raw.get("to", "")),
        read.text(raw, "label", where) or "",
        read.enum(LinkKind, raw, "kind", where) or LinkKind.PATH,
    )


def _tree(raw: dict[str, Any], where: str, read: Reader) -> Tree:
    """Read a tree: a root and its rows."""
    root = _card(raw.get("root"), f"{where}.root", read)
    rows = tuple(
        _row(item, f"{where}.rows[{index}]", read)
        for index, item in enumerate(_list(raw, "rows", where, read))
    )
    if not rows:
        read.report(where, "'rows' must list at least one row")
    names = raw.get("names", "code")
    if names not in ("code", "plain"):
        read.report(where, "'names' must be code or plain")
    return Tree(root, rows, read.text(raw, "note", where) or "", names == "code")


def _row(raw: object, where: str, read: Reader) -> Row:
    """Read one row of a tree."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return Row("", "", None, None, ())
    read.check_keys(raw, ROW_KEYS, where)
    card = _card({key: raw[key] for key in raw if key != "inside"}, where, read)
    inside = raw.get("inside", [])
    if not isinstance(inside, list) or not all(isinstance(each, str) for each in inside):
        read.report(where, "'inside' must be a list of names")
        inside = []
    return Row(card.name, card.text, card.icon, card.tone, tuple(inside))


def _comparison(raw: dict[str, Any], where: str, read: Reader) -> Comparison:
    """Read a comparison: two cards, the rows across and the rule of thumb."""
    left = _card(raw.get("left"), f"{where}.left", read)
    right = _card(raw.get("right"), f"{where}.right", read)
    rows = []
    for index, item in enumerate(_list(raw, "rows", where, read)):
        place = f"{where}.rows[{index}]"
        if not isinstance(item, dict):
            read.report(place, "must be an object")
            continue
        read.check_keys(item, COMPARE_ROW_KEYS, place)
        rows.append(
            CompareRow(
                read.text(item, "label", place) or "",
                read.text(item, "left", place) or "",
                read.text(item, "right", place) or "",
            )
        )
    if not rows:
        read.report(where, "'rows' must list at least one row")
    rule = raw.get("rule", {})
    rule = rule if isinstance(rule, dict) else {}
    read.check_keys(rule, RULE_KEYS, f"{where}.rule")
    return Comparison(
        left,
        right,
        tuple(rows),
        read.text(rule, "title", where) or "",
        read.text(rule, "text", where) or "",
    )


def _analogy(raw: dict[str, Any], where: str, read: Reader) -> Analogy:
    """Read an analogy: two cards joined by a spoken label."""
    read.check_keys(raw, ANALOGY_KEYS | {"shape", "title", "column"}, where)
    return Analogy(
        read.text(raw, "label", where) or "",
        read.enum(Tone, raw, "tone", where) or Tone.AMBER,
        _card(raw.get("left"), f"{where}.left", read),
        _card(raw.get("right"), f"{where}.right", read),
        read.text(raw, "link", where) or "",
        read.text(raw, "closing", where) or "",
    )


def _concept(raw: dict[str, Any], where: str, read: Reader) -> Concept:
    """Read a concept: the hub, its facts and an optional analogy."""
    hub = _card(raw.get("hub"), f"{where}.hub", read)
    facts = tuple(
        _card(item, f"{where}.facts[{index}]", read)
        for index, item in enumerate(_list(raw, "facts", where, read))
    )
    if not MIN_FACTS <= len(facts) <= MAX_FACTS:
        read.report(where, f"'facts' must list between {MIN_FACTS} and {MAX_FACTS} facts")
    analogy = raw.get("analogy")
    return Concept(
        hub,
        facts,
        _analogy(analogy, f"{where}.analogy", read) if isinstance(analogy, dict) else None,
    )
