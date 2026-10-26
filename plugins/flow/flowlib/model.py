"""The vocabulary of a scene: closed sets of values and the dataclasses that hold a scene.

A scene is plain geometry in pixels. ``x`` and ``y`` are the top-left corner of a node or
frame; an edge carries its own routed points and the position of its label.
"""

from dataclasses import dataclass
from enum import StrEnum

Point = tuple[float, float]

DEFAULT_FONT_SIZE_PX = 12.0
REF_FRAGMENT = "ref"  # the label of a frame that points to another diagram, whose name it shows
DEFAULT_THEME = "pastel"  # the look of every diagram that does not ask for another


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
    HEADER = "header"  # the box or card at the top of a sequence lifeline
    FORK = "fork"  # the thick bar of a parallel split or join
    NOTE = "note"
    TEXT = "text"
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
    SCREEN = "screen"
    FLAG = "flag"
    TASK = "task"  # a BPMN task: a rounded box with an ink outline
    DFD_PROCESS = "dfd_process"  # a rounded box with its number in a header strip (Gane-Sarson)
    DFD_STORE = "dfd_store"  # a box open on the right, with an id cell on the left


class Marker(StrEnum):
    """A small mark inside a BPMN event, task or gateway that names its kind or trigger."""

    MESSAGE = "message"  # an outlined envelope: a message event, or a receive task
    MESSAGE_FILLED = "message_filled"  # a filled envelope: a send task
    TIMER = "timer"
    ERROR = "error"
    SIGNAL = "signal"
    USER = "user"
    SERVICE = "service"
    MANUAL = "manual"
    CROSS = "cross"  # an exclusive gateway
    PLUS = "plus"  # a parallel gateway
    CIRCLE = "circle"  # an inclusive gateway
    EVENT_BASED = "event_based"  # a ringed pentagon
    LOOP = "loop"
    MULTI_INSTANCE = "multi_instance"  # three bars
    SUBPROCESS = "subprocess"  # a small box with a plus at the bottom


class Role(StrEnum):
    """What a line means; decides its colour, weight, dash and animation."""

    NEXT = "next"
    YES = "yes"
    NO = "no"
    BACK = "back"
    MAIN = "main"
    DATA = "data"
    LIFELINE = "lifeline"
    LOGICAL = "logical"
    ASSOCIATION = "association"  # a dotted line from a task to a data store


class LabelKind(StrEnum):
    """The colour family of a label chip on a line."""

    PLAIN = "plain"
    YES = "yes"
    NO = "no"
    BACK = "back"
    TEXT = "text"
    TEXT_FAIL = "text_fail"
    USER = "user"
    SYSTEM = "system"
    CODE = "code"
    GUARD_OK = "guard_ok"
    GUARD_FAIL = "guard_fail"
    EFFECT = "effect"


class Tone(StrEnum):
    """A colour group that marks a domain or an owner, never a meaning by itself."""

    BLUE = "blue"
    VIOLET = "violet"
    AMBER = "amber"
    GREEN = "green"
    TEAL = "teal"
    GRAY = "gray"
    RED = "red"


MONO_LABEL_KINDS = (LabelKind.CODE, LabelKind.GUARD_OK, LabelKind.GUARD_FAIL)  # drawn in mono
KEY_FLAG_TONES: dict[str, Tone] = {"PK": Tone.AMBER, "FK": Tone.BLUE, "UQ": Tone.VIOLET}


class Head(StrEnum):
    """What a line has at one end."""

    NONE = "none"
    FILLED = "filled"
    OPEN = "open"
    DOT = "dot"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    DIAMOND_FILLED = "diamond_filled"
    CIRCLE = "circle"  # a hollow circle: the start of a message flow
    ONE = "one"
    MANY = "many"
    ONE_ONLY = "one_only"
    ZERO_ONE = "zero_one"
    ZERO_MANY = "zero_many"
    ONE_MANY = "one_many"


SYMBOL_HEADS = (
    Head.TRIANGLE,
    Head.CIRCLE,
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
    POOL = "pool"  # a white pool with a coloured band on the left that carries the name
    BLACK_BOX = "black_box"  # a pool drawn only as a filled bar with its name
    OPENED = "opened"  # the dashed frame around a process that a lower-level diagram opens


class Side(StrEnum):
    """Which side of the main flow a branch is placed on."""

    LEFT = "left"
    RIGHT = "right"


class Device(StrEnum):
    """The kind of device a screen is drawn in; the frame is the platform statement."""

    PHONE = "phone"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WATCH = "watch"


class Orientation(StrEnum):
    """Whether a device frame is tall or wide."""

    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class Fidelity(StrEnum):
    """How far the design of a screen has been decided (design 02 section 2.3)."""

    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class Content(StrEnum):
    """What the body of an L2 screen shows besides its named elements."""

    HATCH = "hatch"
    SPLASH = "splash"
    SUCCESS = "success"
    ERROR = "error"
    LOADING = "loading"
    EMPTY = "empty"


class Overlay(StrEnum):
    """A modal, a bottom sheet or a toast drawn on the screen it covers."""

    MODAL = "modal"
    SHEET = "sheet"
    TOAST = "toast"


class ElementStyle(StrEnum):
    """How a named element of a screen looks."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    OUTLINE = "outline"
    DANGER = "danger"
    FIELD = "field"


class Placement(StrEnum):
    """Where a named element sits on its screen."""

    TOP = "top"
    BOTTOM = "bottom"


class ChipPlace(StrEnum):
    """Where the id chip of a screen sits: above its left or right corner, or below it."""

    ABOVE = "above"
    ABOVE_RIGHT = "above_right"
    BELOW = "below"


class Layer(StrEnum):
    """Whether an element belongs to the screen or to the overlay on it."""

    BASE = "base"
    OVERLAY = "overlay"


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
    """One row of a table node: key chips and a name on the left, a note on the right.

    ``flags`` are the short marks drawn as chips before the name, such as ``PK`` or ``FK``.
    """

    left: str
    right: str = ""
    flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class EdgeLabel:
    """A chip that sits on a line, centred on ``at``."""

    text: str
    at: Point
    kind: LabelKind
    number: str | None = None
    icon: str | None = None  # an icon drawn before the text, as on the chip of a system trigger


@dataclass(frozen=True)
class ScreenElement:
    """An element of a screen that causes a transition; a red dot marks the tapped one."""

    text: str
    style: ElementStyle = ElementStyle.PRIMARY
    placement: Placement = Placement.BOTTOM
    layer: Layer = Layer.BASE
    is_hotspot: bool = True


@dataclass(frozen=True)
class ScreenView:
    """What a screen node shows: its device frame, its fidelity level and its named elements."""

    code: str  # the text of the id chip, such as ``S31 · loading``
    title: str = ""  # the name of the screen, drawn at the top of its body
    device: Device = Device.PHONE
    orientation: Orientation = Orientation.PORTRAIT
    is_mini: bool = False
    fidelity: Fidelity = Fidelity.L0
    content: Content = Content.HATCH
    hatch_label: str = ""
    elements: tuple[ScreenElement, ...] = ()
    overlay: Overlay | None = None
    overlay_title: str = ""
    tab_active: int | None = None
    tab_count: int = 0
    is_undecided: bool = False
    chip_place: ChipPlace = ChipPlace.ABOVE  # moved when a line would run through the chip


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
    caption_above: bool = False  # the caption hangs above the node, where a line leaves below
    sections: tuple[tuple[Row, ...], ...] = ()
    card: bool = False  # drawn as an illustrated card: a large icon, a name pill, a detail line
    dashed: bool = False  # a dashed outline: a reference to something drawn elsewhere
    screen: ScreenView | None = None  # what a screen of a screen flow shows
    markers: tuple[Marker, ...] = ()  # BPMN marks: the trigger, the task type, the repeat
    host: str | None = None  # the id of the task a boundary event sits on the edge of
    chip: EdgeLabel | None = None  # a chip on the node; ``at`` is relative to its top-left


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
    theme: str = DEFAULT_THEME
    diagram: str = ""  # the spec type it was drawn from; some checks apply to one type only
