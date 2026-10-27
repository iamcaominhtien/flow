"""The look of a person in the planning diagrams: initials, and a tint that stays the same.

A person is drawn as a circle with initials. The tint belongs to the person, or to the team the
person is in, and is chosen from the name, so the same name has the same tint in a Gantt chart,
an org chart and a mind map, with no table to keep in step.
"""

import zlib
from dataclasses import dataclass

from ..model import Tone
from ..reader import Reader

PERSON_TONES = (Tone.BLUE, Tone.GREEN, Tone.TEAL, Tone.VIOLET, Tone.AMBER, Tone.RED)
MAX_INITIALS = 2
PEOPLE_KEY = "people"
PERSON_KEYS = {"initials", "tone"}


@dataclass(frozen=True)
class Person:
    """A person as the circle shows them."""

    name: str
    initials: str
    tone: Tone


def initials_of(name: str) -> str:
    """Return the initials of a name: the first letters of its first two words, in capitals.

    Args:
        name: A name such as ``Minh Tran``.

    Returns:
        ``MT`` for the example; one letter for a one-word name; ``?`` for an empty name.
    """
    words = name.split()
    return "".join(word[0] for word in words[:MAX_INITIALS]).upper() or "?"


def tone_of(key: str) -> Tone:
    """Return the tint of a person or a team, the same every time for the same key.

    Args:
        key: A person's name or a team's name; case does not matter.

    Returns:
        One of ``PERSON_TONES``.
    """
    return PERSON_TONES[zlib.crc32(key.strip().casefold().encode()) % len(PERSON_TONES)]


def read_people(raw: dict[str, object], read: Reader) -> dict[str, dict[str, object]]:
    """Read the optional ``people`` object that pins the initials or the tint of a person.

    Args:
        raw: The spec.
        read: The reader that collects problems.

    Returns:
        Name to its settings; empty when the spec has none.
    """
    found = raw.get(PEOPLE_KEY, {})
    if not isinstance(found, dict):
        read.report(PEOPLE_KEY, "must be an object of names")
        return {}
    for name, settings in found.items():
        where = f"{PEOPLE_KEY}.{name}"
        if not isinstance(settings, dict):
            read.report(where, "must be an object")
            continue
        read.check_keys(settings, PERSON_KEYS, where)
        read.enum(Tone, settings, "tone", where)
    return {name: settings for name, settings in found.items() if isinstance(settings, dict)}


def person_of(name: str, pinned: dict[str, dict[str, object]], team: str = "") -> Person:
    """Build the person of a name, taking what the spec pinned and the rest from the name.

    Args:
        name: The name written in the spec.
        pinned: The result of ``read_people``.
        team: The team of the person, whose name decides the tint when the person has none.

    Returns:
        The person.
    """
    settings = pinned.get(name, {})
    tone = settings.get("tone")
    initials = settings.get("initials")
    return Person(
        name=name,
        initials=initials if isinstance(initials, str) else initials_of(name),
        tone=Tone(tone) if isinstance(tone, str) else tone_of(team or name),
    )
