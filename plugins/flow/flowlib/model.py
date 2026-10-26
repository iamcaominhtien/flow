"""The vocabulary of a scene: closed sets of values and the dataclasses that hold a scene.

A scene is plain geometry in pixels. ``x`` and ``y`` are the top-left corner of a node or
frame; an edge carries its own routed points and the position of its label.
"""

from dataclasses import dataclass
from enum import StrEnum

Point = tuple[float, float]

DEFAULT_FONT_SIZE_PX = 13.0


class Shape(StrEnum):
    """The outline of a flowchart node."""

    TERMINATOR = "terminator"
    FAIL = "fail"
    PROCESS = "process"
    SUBPROCESS = "subprocess"
    DECISION = "decision"
    IO = "io"
    DOCUMENT = "document"
    PREPARATION = "preparation"
    CONNECTOR = "connector"
    BAR = "bar"
    NOTE = "note"
    CROSS = "cross"
    TABLE = "table"
    CYLINDER = "cylinder"
    ENTITY = "entity"
    STORE = "store"
    START = "start"
    END = "end"
    INTERMEDIATE = "intermediate"
    ACTOR = "actor"
    ELLIPSE = "ellipse"


class Role(StrEnum):
    """What a line means; decides its colour, weight, dash and animation."""

    NEXT = "next"
    YES = "yes"
    NO = "no"
    BACK = "back"
    MAIN = "main"
    DATA = "data"
    LIFELINE = "lifeline"


class LabelKind(StrEnum):
    """The colour family of a label chip on a line."""

    PLAIN = "plain"
    YES = "yes"
    NO = "no"
    BACK = "back"
    TEXT = "text"
    TEXT_FAIL = "text_fail"


class Tone(StrEnum):
    """A colour group that marks a domain or an owner, never a meaning by itself."""

    BLUE = "blue"
    VIOLET = "violet"
    AMBER = "amber"
    GREEN = "green"
    TEAL = "teal"
    GRAY = "gray"


class Head(StrEnum):
    """What a line has at one end."""

    NONE = "none"
    FILLED = "filled"
    OPEN = "open"
    DOT = "dot"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    DIAMOND_FILLED = "diamond_filled"
    ONE = "one"
    MANY = "many"
    ONE_ONLY = "one_only"
    ZERO_ONE = "zero_one"
    ZERO_MANY = "zero_many"
    ONE_MANY = "one_many"


SYMBOL_HEADS = (
    Head.TRIANGLE,
    Head.DIAMOND,
    Head.DIAMOND_FILLED,
    Head.ONE,
    Head.MANY,
    Head.ONE_ONLY,
    Head.ZERO_ONE,
    Head.ZERO_MANY,
    Head.ONE_MANY,
)  # heads that need room of their own where several lines meet a node


class FrameVariant(StrEnum):
    """How a frame is drawn: a tinted area (zone), a lane with a tab, or a fragment with a tag."""

    AREA = "area"
    LANE = "lane"
    FRAGMENT = "fragment"


class Side(StrEnum):
    """Which side of the main flow a branch is placed on."""

    LEFT = "left"
    RIGHT = "right"


class Direction(StrEnum):
    """Which way a flow runs: top to bottom, or left to right."""

    DOWN = "down"
    RIGHT = "right"


class Animation(StrEnum):
    """The animated tiers; the value is the CSS class and keyframes name."""

    FLOW = "flow"
    FLOW_SLOW = "flow2"


@dataclass(frozen=True)
class Divider:
    """A dashed line across a fragment frame, with the guard of the part below it."""

    y: float
    guard: str


@dataclass(frozen=True)
class Frame:
    """An area that groups nodes: a lane or zone, or a labelled fragment around some rows."""

    id: str
    x: float
    y: float
    width: float
    height: float
    label: str | None
    tone: Tone
    variant: FrameVariant = FrameVariant.AREA
    guard: str | None = None
    dividers: tuple[Divider, ...] = ()


@dataclass(frozen=True)
class Row:
    """One row of a table node: a name on the left and, optionally, a note on the right."""

    left: str
    right: str = ""


@dataclass(frozen=True)
class Node:
    """One box of the diagram."""

    id: str
    shape: Shape
    x: float
    y: float
    width: float
    height: float
    text: tuple[str, ...]
    icon: str | None
    tone: Tone | None
    number: str | None
    font_size: float
    detail: tuple[str, ...] = ()
    caption: str | None = None
    sections: tuple[tuple[Row, ...], ...] = ()
    card: bool = False  # drawn as an illustrated card: a large icon, a name pill, a detail line


@dataclass(frozen=True)
class EdgeLabel:
    """A chip that sits on a line, centred on ``at``."""

    text: str
    at: Point
    kind: LabelKind
    number: str | None = None


@dataclass(frozen=True)
class Edge:
    """A routed line, optionally linked to the nodes it joins."""

    id: str
    role: Role
    points: tuple[Point, ...]
    label: EdgeLabel | None
    source: str | None
    target: str | None
    head: Head = Head.FILLED
    tail: Head = Head.NONE
    dashed: bool = False
    extras: tuple[EdgeLabel, ...] = ()


@dataclass(frozen=True)
class Scene:
    """A whole diagram, ready to draw."""

    width: float
    height: float
    title: str | None
    description: str | None
    frames: tuple[Frame, ...]
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
