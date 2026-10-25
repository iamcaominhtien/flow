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


class Role(StrEnum):
    """What a line means; decides its colour, weight, dash and animation."""

    NEXT = "next"
    YES = "yes"
    NO = "no"
    BACK = "back"
    MAIN = "main"
    DATA = "data"


class LabelKind(StrEnum):
    """The colour family of a label chip on a line."""

    PLAIN = "plain"
    YES = "yes"
    NO = "no"
    BACK = "back"


class Tone(StrEnum):
    """A colour group that marks a domain or an owner, never a meaning by itself."""

    BLUE = "blue"
    VIOLET = "violet"
    AMBER = "amber"
    GREEN = "green"
    TEAL = "teal"
    GRAY = "gray"


class ArrowEnd(StrEnum):
    """Whether a line ends in an arrowhead."""

    END = "end"
    NONE = "none"


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
class Frame:
    """A tinted, dashed area that groups nodes (a lane, a zone)."""

    id: str
    x: float
    y: float
    width: float
    height: float
    label: str | None
    tone: Tone


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


@dataclass(frozen=True)
class EdgeLabel:
    """A chip that sits on a line, centred on ``at``."""

    text: str
    at: Point
    kind: LabelKind


@dataclass(frozen=True)
class Edge:
    """A routed line, optionally linked to the nodes it joins."""

    id: str
    role: Role
    points: tuple[Point, ...]
    arrow: ArrowEnd
    label: EdgeLabel | None
    source: str | None
    target: str | None


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
