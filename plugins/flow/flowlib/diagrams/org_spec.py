"""Read and check the spec of an org chart.

The JSON format::

    {"type": "org", "title": "...", "desc": "...", "style": "plain|illustrated",
     "root": {"id", "name", "role", "team", "tone", "initials", "open": true, "icon",
              "children": [ ...the same... ]},
     "links": [{"from": "id", "to": "id", "label": "works with"}],
     "people": {"Ava Lopez": {"initials": "AL", "tone": "blue"}}}

A person is a card with a name and a role (a noun phrase, such as ``Mobile developer``). An
open role has no name: its card shows the title and the words *Open role*. The tint of a card
comes from ``tone``, else from the ``team`` (which the people below inherit), else, for a head
that reports to the top, from the name; people below a head keep the tint of the head. The
older form, with ``label`` for the name and ``detail`` for the role, is still read.
"""

from dataclasses import dataclass
from typing import Any

from ..model import Tone
from ..reader import Reader, SpecError, suggestion
from ..theme import icon_names
from .people import Person, person_of, read_people, tone_of

SPEC_KEYS = {"type", "title", "desc", "theme", "style", "root", "links", "people"}
ITEM_KEYS = {
    "id", "name", "role", "team", "tone", "initials", "open", "icon", "children", "label", "detail",
}  # fmt: skip
LINK_KEYS = {"from", "to", "label"}
MAX_DEPTH = 8
WORKS_WITH_LABEL = "works with"
OPEN_ROLE_INITIALS = "?"
MAX_ROLE_WORDS = 6  # a role longer than this is a sentence, not a noun phrase


@dataclass(frozen=True)
class Member:
    """One card of the chart and where it hangs."""

    id: str
    name: str  # for an open role, the title of the role
    role: str  # for an open role, the words ``Open role``
    person: Person
    parent: str | None
    depth: int
    is_open: bool
    icon: str | None


@dataclass(frozen=True)
class Link:
    """A working relationship between two people with no reporting line."""

    source: str
    target: str
    label: str


@dataclass(frozen=True)
class OrgSpec:
    """A checked org chart; the members are in the order written."""

    title: str | None
    description: str | None
    is_illustrated: bool
    members: tuple[Member, ...]
    links: tuple[Link, ...]


def read_spec(raw: object) -> OrgSpec:
    """Check an org chart spec and turn it into the description the layout works on.

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
    pinned = read_people(raw, read)
    members: list[Member] = []
    if "root" not in raw:
        read.report("spec", "'root' is required")
    else:
        _read_item(raw["root"], members, ("root", read), (pinned, None))
    links = _links(raw, members, read)
    illustrated = read.illustrated(raw, "spec")
    if read.problems:
        raise SpecError(read.problems)
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    return OrgSpec(title, description, illustrated, tuple(members), tuple(links))


def _read_item(
    raw: object,
    members: list[Member],
    place: tuple[str, Reader],
    context: tuple[dict[str, dict[str, object]], Member | None],
) -> None:
    """Read one item and everything below it, adding the members in the order written."""
    where, read = place
    pinned, parent = context
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return
    read.check_keys(raw, ITEM_KEYS, where)
    member = _member(raw, f"n{len(members)}", place, (pinned, parent))
    members.append(member)
    children = raw.get("children", [])
    if not isinstance(children, list):
        read.report(where, "'children' must be a list")
        return
    if member.depth >= MAX_DEPTH:
        read.report(where, f"is nested deeper than {MAX_DEPTH} levels")
        return
    for index, child in enumerate(children):
        _read_item(child, members, (f"{where}.children[{index}]", read), (pinned, member))


def _member(
    raw: dict[str, Any],
    default_id: str,
    place: tuple[str, Reader],
    context: tuple[dict[str, dict[str, object]], Member | None],
) -> Member:
    """Read the fields of one item."""
    where, read = place
    pinned, parent = context
    identifier = read.identifier(raw, where) if "id" in raw else default_id
    name = read.text(raw, "name", where) or read.text(raw, "label", where) or ""
    role = read.text(raw, "role", where) or read.text(raw, "detail", where) or ""
    is_open = raw.get("open") is True
    if not (name or is_open):
        read.report(where, "needs a 'name' (or 'open': true with a 'role')")
    icon = raw.get("icon")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    person = _person(raw, name or role, (pinned, parent), (where, read))
    return Member(
        id=identifier,
        name=role if is_open else name,
        role="Open role" if is_open else role,
        person=person,
        parent=parent.id if parent else None,
        depth=parent.depth + 1 if parent else 0,
        is_open=is_open,
        icon=icon,
    )


def _person(
    raw: dict[str, Any],
    name: str,
    context: tuple[dict[str, dict[str, object]], Member | None],
    place: tuple[str, Reader],
) -> Person:
    """Build the circle of a person: initials, and a tint from the tone, the team or the head."""
    pinned, parent = context
    where, read = place
    team = read.text(raw, "team", where) or ""
    tone = read.enum(Tone, raw, "tone", where)
    given = person_of(name, pinned, team)
    initials = raw.get("initials")
    if tone is None and not team and parent is not None and parent.parent is not None:
        tone = parent.person.tone
    if raw.get("open") is True:
        return Person(name, initials or OPEN_ROLE_INITIALS, tone or Tone.GRAY)
    return Person(
        name=name,
        initials=initials if isinstance(initials, str) else given.initials,
        tone=tone or (tone_of(team) if team else given.tone),
    )


def _links(raw: dict[str, Any], members: list[Member], read: Reader) -> list[Link]:
    """Read the working links; each must join two people on the same level."""
    items = raw.get("links", [])
    if not isinstance(items, list):
        read.report("spec", "'links' must be a list")
        return []
    by_id = {member.id: member for member in members}
    found = []
    for index, item in enumerate(items):
        where = f"links[{index}]"
        if not isinstance(item, dict):
            read.report(where, "must be an object")
            continue
        read.check_keys(item, LINK_KEYS, where)
        ends = [item.get("from"), item.get("to")]
        known = [end for end in ends if end in by_id]
        for end in ends:
            if end not in by_id:
                read.report(where, f"'{end}' is not the id of a person{suggestion(end, by_id)}")
        if len(known) == len(ends) and by_id[known[0]].depth != by_id[known[1]].depth:
            read.report(where, "joins two people on different levels; use two on the same level")
        elif len(known) == len(ends):
            found.append(
                Link(known[0], known[1], read.text(item, "label", where) or WORKS_WITH_LABEL)
            )
    return found
