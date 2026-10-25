"""Read a sequence diagram spec: who talks to whom, in what order, with no coordinates.

The JSON format::

    {"type": "sequence", "title": "...", "desc": "...",
     "participants": [{"id", "label", "icon", "tone"}],
     "items": [
       {"kind": "sync|return|async|self|lost|found|create", "from", "to", "label",
        "role": "next|main|fail|event", "number": "1"},
       {"destroy": "id"},
       {"note": "text", "over": "id", "side": "left|right"},
       {"fragment": "alt|opt|loop|par|break|critical|ref",
        "sections": [{"guard": "...", "items": [...]}]}
     ]}

Rows, not coordinates: items run top to bottom in the order written.
"""

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from ..model import Side, Tone
from ..reader import Reader, SpecError, suggestion
from ..theme import load_icons, load_theme

SEQUENCE = "sequence"
SPEC_KEYS = {"type", "title", "desc", "participants", "items"}
PARTICIPANT_KEYS = {"id", "label", "icon", "tone"}
MESSAGE_KEYS = {"kind", "from", "to", "label", "role", "number"}
NOTE_KEYS = {"note", "over", "side"}
DESTROY_KEYS = {"destroy"}
FRAGMENT_KEYS = {"fragment", "sections"}
SECTION_KEYS = {"guard", "items"}
NO_OTHER_END = ("lost", "found")  # these kinds name only one participant besides the sender


class MessageKind(StrEnum):
    """How a message behaves; decides the line and the head."""

    SYNC = "sync"
    RETURN = "return"
    ASYNC = "async"
    SELF = "self"
    LOST = "lost"
    FOUND = "found"
    CREATE = "create"


class MessageRole(StrEnum):
    """How much a message matters; decides its colour."""

    NEXT = "next"
    MAIN = "main"
    FAIL = "fail"
    EVENT = "event"


class FragmentKind(StrEnum):
    """The tag of a fragment frame."""

    ALT = "alt"
    OPT = "opt"
    LOOP = "loop"
    PAR = "par"
    BREAK = "break"
    CRITICAL = "critical"
    REF = "ref"


@dataclass(frozen=True)
class Participant:
    """One lifeline: a person, an app, a service or a database."""

    id: str
    label: str
    icon: str | None
    tone: Tone


@dataclass(frozen=True)
class Message:
    """One arrow between two lifelines, or from a lifeline to itself."""

    source: str
    target: str
    kind: MessageKind
    label: str
    role: MessageRole
    number: str | None


@dataclass(frozen=True)
class Note:
    """A remark beside a lifeline."""

    text: str
    over: str
    side: Side


@dataclass(frozen=True)
class Destroy:
    """The end of a lifeline."""

    target: str


@dataclass(frozen=True)
class Section:
    """One part of a fragment: a guard and the items that happen under it."""

    guard: str | None
    items: tuple["Item", ...]


@dataclass(frozen=True)
class Fragment:
    """A frame that says under which condition its items happen."""

    kind: FragmentKind
    sections: tuple[Section, ...]


Item = Message | Note | Destroy | Fragment


@dataclass(frozen=True)
class SequenceSpec:
    """A whole sequence diagram description."""

    title: str | None
    description: str | None
    participants: tuple[Participant, ...]
    items: tuple[Item, ...]


def load(path: str | Path) -> SequenceSpec:
    """Read a sequence spec file.

    Args:
        path: A JSON file in the spec format.

    Returns:
        The spec.

    Raises:
        SpecError: If the file is not a valid spec.
    """
    return parse(json.loads(Path(path).read_text(encoding="utf-8")))


def parse(raw: object) -> SequenceSpec:
    """Check a parsed JSON value and build the spec from it.

    Args:
        raw: The result of ``json.loads`` on a sequence spec.

    Returns:
        The spec.

    Raises:
        SpecError: With every problem found.
    """
    return _Parser().spec(raw)


class _Parser:
    """Turns raw JSON into a sequence spec while collecting every problem."""

    def __init__(self) -> None:
        """Start with an empty reader and no participants known."""
        self._read = Reader()
        self._ids: list[str] = []
        self._icon_names = load_icons().keys()
        self._max_depth = load_theme().sequence.max_fragment_depth

    def spec(self, raw: object) -> SequenceSpec:
        """Build the spec, or raise if anything was wrong.

        Args:
            raw: The parsed JSON document.

        Returns:
            The spec.

        Raises:
            SpecError: If any problem was found.
        """
        if not isinstance(raw, dict):
            raise SpecError(["the spec must be a JSON object"])
        read = self._read
        read.check_keys(raw, SPEC_KEYS, "spec")
        participants = [
            self._participant(item, f"participants[{index}]")
            for index, item in enumerate(raw.get("participants", []))
        ]
        self._ids = [each.id for each in participants if each is not None]
        if len(self._ids) < 1:
            read.report("spec", "'participants' must list at least one participant")
        items = self._items(raw.get("items", []), "items", depth=0)
        title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
        if read.problems:
            raise SpecError(read.problems)
        return SequenceSpec(
            title=title,
            description=description,
            participants=tuple(each for each in participants if each is not None),
            items=tuple(items),
        )

    def _participant(self, raw: object, where: str) -> Participant | None:
        """Build one participant, or report why it cannot be built."""
        read = self._read
        if not isinstance(raw, dict):
            read.report(where, "must be an object")
            return None
        read.check_keys(raw, PARTICIPANT_KEYS, where)
        icon = raw.get("icon")
        if icon is not None and icon not in self._icon_names:
            read.report(where, f"unknown icon '{icon}'; use one of: {', '.join(self._icon_names)}")
        identifier = read.identifier(raw, where)
        return Participant(
            id=identifier,
            label=read.text(raw, "label", where) or identifier,
            icon=icon,
            tone=read.enum(Tone, raw, "tone", where) or Tone.GRAY,
        )

    def _items(self, raw: object, where: str, depth: int) -> list[Item]:
        """Build a list of items; a bad item is reported and skipped."""
        if not isinstance(raw, list):
            self._read.report(where, "must be a list")
            return []
        built = [self._item(item, f"{where}[{index}]", depth) for index, item in enumerate(raw)]
        return [item for item in built if item is not None]

    def _item(self, raw: object, where: str, depth: int) -> Item | None:
        """Build one item, choosing its type from the keys it has."""
        read = self._read
        if not isinstance(raw, dict):
            read.report(where, "must be an object")
            return None
        if "fragment" in raw:
            return self._fragment(raw, where, depth)
        if "note" in raw:
            return self._note(raw, where)
        if "destroy" in raw:
            read.check_keys(raw, DESTROY_KEYS, where)
            return Destroy(target=self._participant_id(raw, "destroy", where))
        if "kind" in raw:
            return self._message(raw, where)
        read.report(where, "needs one of: kind (a message), note, destroy, fragment")
        return None

    def _participant_id(self, raw: dict[str, Any], key: str, where: str) -> str:
        """Read a field that must name a participant, suggesting a close match for a typo."""
        name = raw.get(key)
        if name in self._ids:
            return name
        self._read.report(
            where,
            f"'{key}' names '{name}', which is not a participant{suggestion(name, self._ids)}",
        )
        return ""

    def _message(self, raw: dict[str, Any], where: str) -> Message | None:
        """Build one message."""
        read = self._read
        read.check_keys(raw, MESSAGE_KEYS, where)
        kind = read.enum(MessageKind, raw, "kind", where)
        source = self._participant_id(raw, "from", where) if "from" in raw else ""
        target = self._participant_id(raw, "to", where) if "to" in raw else ""
        if kind is MessageKind.FOUND:
            source = target
        elif kind is MessageKind.LOST:
            target = source
        elif not source or not target:
            read.report(where, "'from' and 'to' are both required")
        if kind is MessageKind.SELF:
            target = source
        return Message(
            source=source,
            target=target,
            kind=kind or MessageKind.SYNC,
            label=read.text(raw, "label", where) or "",
            role=read.enum(MessageRole, raw, "role", where) or MessageRole.NEXT,
            number=read.text(raw, "number", where),
        )

    def _note(self, raw: dict[str, Any], where: str) -> Note:
        """Build one note."""
        read = self._read
        read.check_keys(raw, NOTE_KEYS, where)
        return Note(
            text=read.text(raw, "note", where) or "",
            over=self._participant_id(raw, "over", where),
            side=read.enum(Side, raw, "side", where) or Side.RIGHT,
        )

    def _fragment(self, raw: dict[str, Any], where: str, depth: int) -> Fragment | None:
        """Build one fragment, checking how deeply fragments are nested."""
        read = self._read
        read.check_keys(raw, FRAGMENT_KEYS, where)
        kind = read.enum(FragmentKind, {"fragment": raw["fragment"]}, "fragment", where)
        if depth >= self._max_depth:
            read.report(where, f"fragments may nest at most {self._max_depth} levels deep")
            return None
        sections = raw.get("sections", [])
        if not isinstance(sections, list) or not sections:
            read.report(where, "'sections' must list at least one section")
            return None
        built = [
            self._section(item, f"{where}.sections[{index}]", depth)
            for index, item in enumerate(sections)
        ]
        return Fragment(
            kind=kind or FragmentKind.OPT,
            sections=tuple(each for each in built if each is not None),
        )

    def _section(self, raw: object, where: str, depth: int) -> Section | None:
        """Build one section of a fragment."""
        if not isinstance(raw, dict):
            self._read.report(where, "must be an object")
            return None
        self._read.check_keys(raw, SECTION_KEYS, where)
        items = self._items(raw.get("items", []), f"{where}.items", depth + 1)
        return Section(guard=self._read.text(raw, "guard", where), items=tuple(items))
