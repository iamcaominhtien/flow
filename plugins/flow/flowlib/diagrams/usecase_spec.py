"""Read and check the spec of a UML use case diagram.

The JSON format::

    {"type": "usecase", "title": "...", "desc": "...", "style": "plain|illustrated",
     "system": "Delivery app",
     "actors": [{"id", "label", "tone", "icon", "external": true}],
     "usecases": [{"id", "label", "tone"}],
     "links": [{"from", "to", "style": "association|include|extend|generalizes", "label"}]}

An ``include`` link runs from the base use case to the one it includes; an ``extend`` link runs
from the extension to the base. The older form with ``items`` (each with a ``kind`` of ``actor``
or ``usecase``) and ``zones`` (the first is the system) is still read.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..model import Tone
from ..reader import Reader, SpecError, suggestion
from ..theme import icon_names

SPEC_KEYS = {
    "type", "title", "desc", "theme", "style", "system", "actors", "usecases", "links",
    "items", "zones",
}  # fmt: skip
ACTOR_KEYS = {"id", "label", "tone", "icon", "external", "kind"}
USE_CASE_KEYS = {"id", "label", "tone", "kind", "zone", "detail"}
LINK_KEYS = {"from", "to", "style", "label"}
ACTOR_KIND = "actor"
EXTERNAL_TAG = "«external system»"


class LinkStyle(StrEnum):
    """What a link between two elements of a use case diagram means."""

    ASSOCIATION = "association"
    INCLUDE = "include"
    EXTEND = "extend"
    GENERALIZES = "generalizes"


@dataclass(frozen=True)
class Actor:
    """A person or an external system outside the system."""

    id: str
    name: str
    tone: Tone | None
    icon: str | None
    is_external: bool


@dataclass(frozen=True)
class UseCase:
    """A goal of an actor, written as a verb phrase."""

    id: str
    name: str
    tone: Tone | None


@dataclass(frozen=True)
class Link:
    """A line between two elements."""

    source: str
    target: str
    style: LinkStyle
    label: str


@dataclass(frozen=True)
class UseCaseSpec:
    """A checked use case diagram."""

    title: str | None
    description: str | None
    system: str
    actors: tuple[Actor, ...]
    use_cases: tuple[UseCase, ...]
    links: tuple[Link, ...]
    is_illustrated: bool


def read_spec(raw: object) -> UseCaseSpec:
    """Check a use case spec.

    Args:
        raw: The result of ``json.loads`` on a ``usecase`` spec.

    Returns:
        The checked spec.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    actor_rows, case_rows, system = _rows(raw)
    actors = [_actor(item, f"actors[{i}]", read) for i, item in enumerate(actor_rows)]
    cases = [_use_case(item, f"usecases[{i}]", read) for i, item in enumerate(case_rows)]
    found = {each.id: each for each in (*actors, *cases) if each is not None}
    if not any(isinstance(each, UseCase) for each in found.values()):
        read.report("spec", "'usecases' must list at least one use case")
    rows = raw.get("links", [])
    links = [
        _link(item, f"links[{i}]", read, found)
        for i, item in enumerate(rows if isinstance(rows, list) else [])
    ]
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    illustrated = read.illustrated(raw, "spec")
    if read.problems:
        raise SpecError(read.problems)
    return UseCaseSpec(
        title=title,
        description=description,
        system=system,
        actors=tuple(each for each in actors if each),
        use_cases=tuple(each for each in cases if each),
        links=tuple(each for each in links if each),
        is_illustrated=illustrated,
    )


def _list(raw: dict[str, Any], key: str) -> list[Any]:
    """Return a field that should be a list, or an empty list when it is not one."""
    value = raw.get(key, [])
    return value if isinstance(value, list) else []


def _rows(raw: dict[str, Any]) -> tuple[list[Any], list[Any], str]:
    """Return the actor rows, the use case rows and the system name, reading both forms."""
    items = _list(raw, "items")
    zones = _list(raw, "zones")
    system = raw.get("system")
    if not isinstance(system, str):
        first = zones[0] if zones and isinstance(zones[0], dict) else {}
        system = first.get("label", "") if isinstance(first.get("label", ""), str) else ""
    legacy_actors = [i for i in items if isinstance(i, dict) and i.get("kind") == ACTOR_KIND]
    legacy_cases = [i for i in items if i not in legacy_actors]
    return (
        [*_list(raw, "actors"), *legacy_actors],
        [*_list(raw, "usecases"), *legacy_cases],
        system,
    )


def _actor(raw: object, where: str, read: Reader) -> Actor | None:
    """Build one actor, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ACTOR_KEYS, where)
    icon = raw.get("icon")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'; use one of: {', '.join(sorted(icon_names()))}")
    identifier = read.identifier(raw, where)
    return Actor(
        id=identifier,
        name=read.text(raw, "label", where) or identifier,
        tone=read.enum(Tone, raw, "tone", where),
        icon=icon,
        is_external=raw.get("external") is True,
    )


def _use_case(raw: object, where: str, read: Reader) -> UseCase | None:
    """Build one use case, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, USE_CASE_KEYS, where)
    identifier = read.identifier(raw, where)
    return UseCase(
        id=identifier,
        name=read.text(raw, "label", where) or identifier,
        tone=read.enum(Tone, raw, "tone", where),
    )


def _link(raw: object, where: str, read: Reader, found: dict[str, Actor | UseCase]) -> Link | None:
    """Build one link, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, LINK_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in found:
            read.report(
                where, f"'{key}' names '{name}', which is not an item{suggestion(name, found)}"
            )
        ends.append(name if name in found else "")
    return Link(
        source=ends[0],
        target=ends[1],
        style=read.enum(LinkStyle, raw, "style", where) or LinkStyle.ASSOCIATION,
        label=read.text(raw, "label", where) or "",
    )
