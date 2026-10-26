"""Read and check a cloud diagram spec: frames, parts, links and the trust levels.

The JSON format::

    {"type": "cloud", "title": "...", "desc": "...",
     "frames": [{"id", "kind": "region|vpc|zone|public|private|data|onprem|dmz|edge",
                 "label", "range", "parent"}],
     "parts": [{"id", "label", "detail", "icon", "tone", "frame", "at": [row, column]}],
     "links": [{"from", "to", "label", "kind": "call|main|event|copy", "main": true}]}

A frame has the colour and the line of its kind (design 13 section 2). ``range`` is the address
range of a ``vpc`` and goes into its label. A part sits in the smallest frame that holds it; a
part with no ``frame`` is outside the cloud (a user, a remote admin).

Trust levels run from the internet and the edge (0) through a public subnet or a DMZ (1) and a
private subnet (2) to a data subnet (3). The spec is refused when a database sits in a public
subnet, when a line skips two levels, or when the zones of a VPC do not have the same subnets.
"""

from dataclasses import dataclass
from enum import StrEnum

from ..model import Tone
from ..reader import Reader, SpecError, suggestion
from ..theme import icon_names

SPEC_KEYS = {"type", "title", "desc", "frames", "parts", "links", "theme", "style"}
FRAME_KEYS = {"id", "kind", "label", "range", "parent"}
PART_KEYS = {"id", "label", "detail", "icon", "tone", "frame", "at"}
LINK_KEYS = {"from", "to", "label", "kind", "main"}
AT_LENGTH = 2
MAX_SKIPPED_LEVELS = 1  # a line may skip no more than one trust level (design 13 section 3)
INTERNET_LEVEL, PUBLIC_LEVEL, PRIVATE_LEVEL, DATA_LEVEL = range(4)
DATABASE_ICONS = {"database", "sql-database", "nosql-database", "data-warehouse"}


class FrameKind(StrEnum):
    """What a frame is; decides its colour and its line."""

    REGION = "region"
    VPC = "vpc"
    ZONE = "zone"
    PUBLIC = "public"
    PRIVATE = "private"
    DATA = "data"
    ONPREM = "onprem"
    DMZ = "dmz"
    EDGE = "edge"


class LinkKind(StrEnum):
    """What a link is: a plain call, the main route, an event or a copy."""

    CALL = "call"
    MAIN = "main"
    EVENT = "event"
    COPY = "copy"


@dataclass(frozen=True)
class FrameLook:
    """How a kind of frame is drawn."""

    tone: Tone
    is_solid: bool
    name: str  # the label of a frame of this kind that has none
    level: int | None = None  # the trust level of a part that sits in it


LOOKS: dict[FrameKind, FrameLook] = {
    FrameKind.REGION: FrameLook(Tone.BLUE, True, "Region"),
    FrameKind.VPC: FrameLook(Tone.VIOLET, False, "VPC"),
    FrameKind.ZONE: FrameLook(Tone.GRAY, False, "Zone"),
    FrameKind.PUBLIC: FrameLook(Tone.GREEN, False, "Public subnet", PUBLIC_LEVEL),
    FrameKind.PRIVATE: FrameLook(Tone.AMBER, False, "Private subnet", PRIVATE_LEVEL),
    FrameKind.DATA: FrameLook(Tone.TEAL, False, "Data subnet", DATA_LEVEL),
    FrameKind.ONPREM: FrameLook(Tone.GRAY, True, "On premises", INTERNET_LEVEL),
    FrameKind.DMZ: FrameLook(Tone.RED, False, "DMZ subnet", PUBLIC_LEVEL),
    FrameKind.EDGE: FrameLook(Tone.VIOLET, False, "Edge", INTERNET_LEVEL),
}
SUBNET_KINDS = (FrameKind.PUBLIC, FrameKind.DMZ, FrameKind.PRIVATE, FrameKind.DATA)
PUBLIC_KINDS = (FrameKind.PUBLIC, FrameKind.DMZ)
SUBNET_ORDER: dict[FrameKind, int] = {kind: index for index, kind in enumerate(SUBNET_KINDS)}


@dataclass(frozen=True)
class Frame:
    """One frame: its kind, its name and the frame that holds it."""

    id: str
    kind: FrameKind
    label: str
    parent: str | None = None

    @property
    def look(self) -> FrameLook:
        """Return how a frame of this kind is drawn."""
        return LOOKS[self.kind]


@dataclass(frozen=True)
class Part:
    """One part: a server, a gateway, a database, a site device."""

    id: str
    label: str
    detail: str = ""
    icon: str | None = None
    tone: Tone | None = None
    frame: str | None = None
    at: tuple[float, float] | None = None


@dataclass(frozen=True)
class Link:
    """A line from the part that starts the traffic to the part that receives it."""

    source: str
    target: str
    label: str
    kind: LinkKind = LinkKind.CALL


@dataclass(frozen=True)
class CloudSpec:
    """A checked cloud diagram."""

    title: str | None
    description: str | None
    frames: tuple[Frame, ...]
    parts: tuple[Part, ...]
    links: tuple[Link, ...]

    def frame_of(self, part: Part) -> Frame | None:
        """Return the frame a part sits in, or None for a part outside the cloud."""
        return next((frame for frame in self.frames if frame.id == part.frame), None)

    def chain(self, frame_id: str | None) -> list[Frame]:
        """Return a frame and the frames around it, the smallest first."""
        by_id = {frame.id: frame for frame in self.frames}
        found: list[Frame] = []
        while frame_id in by_id:
            found.append(by_id[frame_id])
            frame_id = by_id[frame_id].parent
        return found

    def level_of(self, part: Part) -> int | None:
        """Return the trust level of a part, or None for one that sits in no subnet or site."""
        if part.frame is None:
            return INTERNET_LEVEL
        for frame in self.chain(part.frame):
            if frame.look.level is not None:
                return frame.look.level
        return None


def read_spec(raw: object) -> CloudSpec:
    """Check a cloud spec and turn it into the description the layout uses.

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
    if raw.get("style", "plain") != "plain":
        read.report("spec", "'style' must be 'plain': a cloud diagram has no illustrated style")
    frames = _read_frames(raw.get("frames", []), read)
    by_frame = {frame.id: frame for frame in frames}
    parts = _read_parts(raw.get("parts", []), by_frame, read)
    by_part = {part.id: part for part in parts}
    links = _read_links(raw.get("links", []), by_part, read)
    spec = CloudSpec(
        title=read.text(raw, "title", "spec"),
        description=read.text(raw, "desc", "spec"),
        frames=tuple(frames),
        parts=tuple(parts),
        links=tuple(links),
    )
    problems = [*read.problems, *check_diagram(spec)]
    if problems:
        raise SpecError(problems)
    return spec


def _read_frames(raw: object, read: Reader) -> list[Frame]:
    """Read the frames; an item that is not valid is reported and left out."""
    items = raw if isinstance(raw, list) else []
    built = [_frame(item, f"frames[{index}]", read) for index, item in enumerate(items)]
    frames = [frame for frame in built if frame is not None]
    known = {frame.id: frame for frame in frames}
    for frame in frames:
        _check_parent(frame, known, read)
    return frames


def _frame(raw: object, where: str, read: Reader) -> Frame | None:
    """Build one frame, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, FRAME_KEYS, where)
    kind = read.enum(FrameKind, raw, "kind", where)
    if kind is None:
        read.report(where, "needs a 'kind': " + ", ".join(k.value for k in FrameKind))
        return None
    label = read.text(raw, "label", where) or LOOKS[kind].name
    range_text = read.text(raw, "range", where)
    if range_text:
        label = f"{label} {range_text}"
    return Frame(read.identifier(raw, where), kind, label, raw.get("parent"))


def _check_parent(frame: Frame, known: dict[str, Frame], read: Reader) -> None:
    """Report a frame whose parent is unknown or whose parents make a loop."""
    where = f"frame '{frame.id}'"
    if frame.parent is None:
        return
    if frame.parent not in known:
        hint = suggestion(frame.parent, known)
        read.report(where, f"'parent' names '{frame.parent}', which is not a frame{hint}")
        return
    seen = {frame.id}
    current = known[frame.parent]
    while current.parent in known and current.id not in seen:
        seen.add(current.id)
        current = known[current.parent]
    if current.id in seen:
        read.report(where, "'parent' makes a loop of frames")


def _read_parts(raw: object, frames: dict[str, Frame], read: Reader) -> list[Part]:
    """Read the parts; an item that is not valid is reported and left out."""
    if not isinstance(raw, list) or not raw:
        read.report("spec", "'parts' must list at least one part")
        return []
    built = [_part(item, f"parts[{index}]", frames, read) for index, item in enumerate(raw)]
    return [part for part in built if part is not None]


def _part(raw: object, where: str, frames: dict[str, Frame], read: Reader) -> Part | None:
    """Build one part, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, PART_KEYS, where)
    icon, frame = raw.get("icon"), raw.get("frame")
    if icon is not None and icon not in icon_names():
        read.report(where, f"unknown icon '{icon}'")
    if frame is not None and frame not in frames:
        read.report(
            where, f"'frame' names '{frame}', which is not a frame{suggestion(frame, frames)}"
        )
    at = raw.get("at")
    if at is not None and not (isinstance(at, list) and len(at) == AT_LENGTH):
        read.report(where, "'at' must be [row, column]")
        at = None
    return Part(
        id=read.identifier(raw, where),
        label=read.text(raw, "label", where) or "",
        detail=read.text(raw, "detail", where) or "",
        icon=icon,
        tone=read.enum(Tone, raw, "tone", where),
        frame=frame,
        at=(at[0], at[1]) if at else None,
    )


def _read_links(raw: object, parts: dict[str, Part], read: Reader) -> list[Link]:
    """Read the links; each end must name a part, and each link needs a label."""
    items = raw if isinstance(raw, list) else []
    links = [_link(item, f"links[{index}]", parts, read) for index, item in enumerate(items)]
    return [link for link in links if link is not None]


def _link(raw: object, where: str, parts: dict[str, Part], read: Reader) -> Link | None:
    """Build one link, or report why it cannot be built."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, LINK_KEYS, where)
    ends = []
    for key in ("from", "to"):
        name = raw.get(key)
        if name not in parts:
            read.report(
                where, f"'{key}' names '{name}', which is not a part{suggestion(name, parts)}"
            )
        ends.append(name)
    kind = LinkKind.MAIN if raw.get("main") is True else read.enum(LinkKind, raw, "kind", where)
    label = read.text(raw, "label", where)
    if not label:
        read.report(where, "needs a 'label': a protocol or what travels (HTTPS, SQL, replication)")
    if ends[0] not in parts or ends[1] not in parts or not label:
        return None
    return Link(ends[0], ends[1], label, kind or LinkKind.CALL)


def check_diagram(spec: CloudSpec) -> list[str]:
    """Report every rule a cloud diagram breaks, in plain sentences.

    Args:
        spec: The spec.

    Returns:
        One sentence per problem; empty when the diagram is allowed.
    """
    problems = [_database_in_public(spec, part) for part in spec.parts]
    problems += [_skipped_levels(spec, link) for link in spec.links]
    problems += _unequal_zones(spec)
    return [problem for problem in problems if problem]


def _database_in_public(spec: CloudSpec, part: Part) -> str:
    """Return the problem of a database in a public subnet, or ''."""
    if part.icon not in DATABASE_ICONS:
        return ""
    for frame in spec.chain(part.frame):
        if frame.kind in PUBLIC_KINDS:
            return (
                f"part '{part.id}' is a database in the {frame.look.name.lower()} '{frame.id}': "
                "databases belong in a data subnet, never where the internet can reach"
            )
    return ""


def _skipped_levels(spec: CloudSpec, link: Link) -> str:
    """Return the problem of a line that skips two trust levels, or ''."""
    by_id = {part.id: part for part in spec.parts}
    start, end = spec.level_of(by_id[link.source]), spec.level_of(by_id[link.target])
    if start is None or end is None:
        return ""
    skipped = abs(start - end) - 1
    if skipped <= MAX_SKIPPED_LEVELS:
        return ""
    return (
        f"link '{link.label}' from '{link.source}' to '{link.target}' skips {skipped} trust "
        "levels: a request goes through the layers, so add the part in between"
    )


def _unequal_zones(spec: CloudSpec) -> list[str]:
    """Report zones of one network that do not hold the same subnets in the same order."""
    zones = [frame for frame in spec.frames if frame.kind is FrameKind.ZONE]
    layouts = {zone.id: _subnet_kinds(spec, zone) for zone in zones}
    problems = []
    for parent in {zone.parent for zone in zones}:
        siblings = [zone for zone in zones if zone.parent == parent]
        first = siblings[0]
        problems += [
            f"zone '{zone.id}' has other subnets than zone '{first.id}': draw the same subnets "
            "in the same order in every zone, so a reader can compare them"
            for zone in siblings[1:]
            if layouts[zone.id] != layouts[first.id]
        ]
    return problems


def _subnet_kinds(spec: CloudSpec, zone: Frame) -> list[FrameKind]:
    """Return the kinds of the subnets of a zone, in the order they are drawn."""
    kinds = [
        frame.kind
        for frame in spec.frames
        if frame.parent == zone.id and frame.kind in SUBNET_KINDS
    ]
    return sorted(kinds, key=SUBNET_ORDER.__getitem__)
