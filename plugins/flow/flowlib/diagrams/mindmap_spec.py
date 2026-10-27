"""Read and check the spec of a mind map.

The JSON format::

    {"type": "mindmap", "title": "...", "desc": "...", "style": "plain|illustrated",
     "root": {"label": "Launch the delivery app", "goal": "first orders in May", "icon": "launch",
              "children": [
                {"id", "label", "icon", "tone", "side": "left|right",
                 "children": [{"label": "...", "icon", "priority": "P1", "done": true,
                               "owner": "Kai Novak", "hidden": 4, "children": [ ... ]}]}]},
     "links": [{"from": "id", "to": "id", "label": "needs"}],
     "people": {"Kai Novak": {"initials": "KN", "tone": "green"}}}

Levels are the branch (from the root), then a leaf, or, when some branch goes deeper, a group,
an idea and a detail. A phrase is at most four words. The branches take the right side first,
then the left; ``side`` moves one. A branch gives its tone to what hangs on it. A link joins two
ideas on the same side that are not branches; use only a few.
"""

from dataclasses import dataclass, replace
from typing import Any

from ..model import Side, Tone
from ..reader import Reader, SpecError, suggestion
from ..theme import icon_names
from .people import Person, person_of, read_people

SPEC_KEYS = {"type", "title", "desc", "theme", "style", "root", "links", "people"}
ITEM_KEYS = {
    "id", "label", "detail", "goal", "icon", "tone", "side", "priority", "done", "owner", "hidden",
    "children",
}  # fmt: skip
LINK_KEYS = {"from", "to", "label"}
MAX_DEPTH = 4  # branch, group, idea, detail
FIRST_LINKED_DEPTH = 2  # a link joins ideas, not the topic or a branch
BRANCH_TONES = (Tone.BLUE, Tone.VIOLET, Tone.AMBER, Tone.TEAL, Tone.GREEN, Tone.RED, Tone.GRAY)
ROOT_TONE = Tone.AMBER
BRANCH_ICONS = ("star", "folder", "bolt", "chat", "pin", "gear", "heart")
ROOT_ICON = "idea"
PRIORITIES = {"P1": 1, "P2": 2, 1: 1, 2: 2}


@dataclass(frozen=True)
class Idea:
    """One item of the map: the topic, a branch, or something that hangs on a branch."""

    id: str
    label: str
    detail: str  # the goal of the topic
    icon: str | None
    tone: Tone
    side: Side | None  # None for the topic
    depth: int  # 0 for the topic, 1 for a branch
    parent: str | None
    children: tuple[str, ...]
    priority: int
    is_done: bool
    owner: Person | None
    hidden: int


@dataclass(frozen=True)
class Link:
    """A dashed arc between two ideas of different branches."""

    source: str
    target: str
    label: str


@dataclass(frozen=True)
class MindSpec:
    """A checked mind map; the ideas are in the order written, the topic first."""

    title: str | None
    description: str | None
    is_illustrated: bool
    ideas: tuple[Idea, ...]
    links: tuple[Link, ...]

    @property
    def depth(self) -> int:
        """Return the deepest level of the map: 1 for branches only, up to 4."""
        return max(idea.depth for idea in self.ideas)


def read_spec(raw: object) -> MindSpec:
    """Check a mind map spec and turn it into the description the layout works on.

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
    ideas: list[Idea] = []
    if "root" not in raw:
        read.report("spec", "'root' is required")
    else:
        _read_item(raw["root"], ideas, ("root", read), (pinned, None))
        _give_sides(ideas)
    links = _links(raw, ideas, read)
    illustrated = read.illustrated(raw, "spec")
    if read.problems:
        raise SpecError(read.problems)
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    return MindSpec(title, description, illustrated, tuple(ideas), tuple(links))


def _read_item(
    raw: object,
    ideas: list[Idea],
    place: tuple[str, Reader],
    context: tuple[dict[str, dict[str, object]], Idea | None],
) -> int:
    """Read one item and what hangs on it; return the index of the item in ``ideas``."""
    where, read = place
    pinned, parent = context
    index = len(ideas)
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return index
    read.check_keys(raw, ITEM_KEYS, where)
    idea = _idea(raw, index, place, (pinned, parent, ideas))
    ideas.append(idea)
    children = raw.get("children", [])
    if not isinstance(children, list):
        read.report(where, "'children' must be a list")
        return index
    if idea.depth >= MAX_DEPTH and children:
        read.report(where, f"is nested {MAX_DEPTH + 1} levels deep; the most is {MAX_DEPTH}")
        return index
    kids = [
        ideas[_read_item(child, ideas, (f"{where}.children[{number}]", read), (pinned, idea))].id
        for number, child in enumerate(children)
    ]
    ideas[index] = replace(idea, children=tuple(kids))
    return index


def _idea(
    raw: dict[str, Any],
    index: int,
    place: tuple[str, Reader],
    context: tuple[dict[str, dict[str, object]], Idea | None, list[Idea]],
) -> Idea:
    """Read the fields of one item."""
    where, read = place
    pinned, parent, ideas = context
    depth = parent.depth + 1 if parent else 0
    label = read.text(raw, "label", where)
    if not label:
        read.report(where, "needs a 'label'")
    owner = read.text(raw, "owner", where)
    return Idea(
        id=read.identifier(raw, where) if "id" in raw else f"n{index}",
        label=label or "",
        detail=read.text(raw, "goal", where) or read.text(raw, "detail", where) or "",
        icon=_icon(raw, depth, where, read),
        tone=_tone(raw, (parent, ideas), place),
        side=read.enum(Side, raw, "side", where),
        depth=depth,
        parent=parent.id if parent else None,
        children=(),
        priority=_priority(raw, place),
        is_done=raw.get("done") is True,
        owner=person_of(owner, pinned) if owner else None,
        hidden=_hidden(raw, place),
    )


def _icon(raw: dict[str, Any], depth: int, where: str, read: Reader) -> str | None:
    """Read an icon name, which must be in the icon library; the topic has a default."""
    icon = raw.get("icon")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    return icon or (ROOT_ICON if depth == 0 else None)


def _tone(
    raw: dict[str, Any], context: tuple[Idea | None, list[Idea]], place: tuple[str, Reader]
) -> Tone:
    """Give an item its tone: the one asked for, the next of the palette, or that of its branch."""
    parent, ideas = context
    where, read = place
    asked = read.enum(Tone, raw, "tone", where)
    if asked:
        return asked
    if parent is None:
        return ROOT_TONE
    if parent.depth == 0:
        branches = sum(1 for idea in ideas if idea.depth == 1)
        return BRANCH_TONES[branches % len(BRANCH_TONES)]
    return parent.tone


def _priority(raw: dict[str, Any], place: tuple[str, Reader]) -> int:
    """Read ``priority``: P1 or P2 (or 1 or 2), meaning do first or do next."""
    where, read = place
    if "priority" not in raw:
        return 0
    value = raw["priority"]
    if value not in PRIORITIES:
        read.report(where, "'priority' must be P1 or P2")
        return 0
    return PRIORITIES[value]


def _hidden(raw: dict[str, Any], place: tuple[str, Reader]) -> int:
    """Read ``hidden``: how many ideas below this one are left out."""
    where, read = place
    value = raw.get("hidden", 0)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        read.report(where, "'hidden' must be a whole number, 0 or more")
        return 0
    return value


def _give_sides(ideas: list[Idea]) -> None:
    """Put every branch on a side, the first half on the right, and pass it down."""
    branches = [idea for idea in ideas if idea.depth == 1]
    on_right = (len(branches) + 1) // 2
    sides: dict[str, Side] = {}
    for position, branch in enumerate(branches):
        default = Side.RIGHT if position < on_right else Side.LEFT
        sides[branch.id] = branch.side or default
    for index, idea in enumerate(ideas):
        if idea.depth == 0:
            continue
        ancestor = idea.id if idea.depth == 1 else _branch_of(idea, ideas)
        ideas[index] = replace(idea, side=sides[ancestor])


def _branch_of(idea: Idea, ideas: list[Idea]) -> str:
    """Return the id of the branch an idea hangs on."""
    by_id = {each.id: each for each in ideas}
    while idea.depth > 1:
        idea = by_id[idea.parent or ""]
    return idea.id


def _links(raw: dict[str, Any], ideas: list[Idea], read: Reader) -> list[Link]:
    """Read the links; each joins two ideas that are not branches, on the same side."""
    items = raw.get("links", [])
    if not isinstance(items, list):
        read.report("spec", "'links' must be a list")
        return []
    by_id = {idea.id: idea for idea in ideas}
    found = []
    for index, item in enumerate(items):
        where = f"links[{index}]"
        if not isinstance(item, dict):
            read.report(where, "must be an object")
            continue
        read.check_keys(item, LINK_KEYS, where)
        ends = [item.get("from"), item.get("to")]
        for end in ends:
            if end not in by_id:
                read.report(where, f"'{end}' is not the id of an idea{suggestion(end, by_id)}")
        if all(end in by_id for end in ends) and _link_problem(by_id[ends[0]], by_id[ends[1]]):
            read.report(where, _link_problem(by_id[ends[0]], by_id[ends[1]]))
        elif all(end in by_id for end in ends):
            found.append(Link(ends[0], ends[1], read.text(item, "label", where) or ""))
    return found


def _link_problem(first: Idea, second: Idea) -> str:
    """Say what is wrong with a link between two ideas, or return an empty string."""
    if min(first.depth, second.depth) < FIRST_LINKED_DEPTH:
        return "joins the topic or a branch; link ideas"
    if first.side is not second.side:
        return "joins ideas on different sides; link ideas on the same side"
    if first.id == second.id:
        return "joins an idea to itself"
    return ""
