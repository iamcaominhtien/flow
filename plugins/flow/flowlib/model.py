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
    INITIAL = "initial"  # the filled dot that starts a state diagram
    FINAL = "final"  # the ringed dot that ends a state diagram
    INTERMEDIATE = "intermediate"
    ACTOR = "actor"
    ELLIPSE = "ellipse"
    USE_CASE = "use_case"  # an oval of a use case diagram, with an ink outline
    SCREEN = "screen"
    FLAG = "flag"
    TASK = "task"  # a BPMN task: a rounded box with an ink outline
    DFD_PROCESS = "dfd_process"  # a rounded box with its number in a header strip (Gane-Sarson)
    DFD_STORE = "dfd_store"  # a box open on the right, with an id cell on the left
    C4_BOX = "c4_box"  # a C4 system, container or component: icon, name, [Kind: technology], text
    C4_PERSON = "c4_person"  # the same box with rounder corners: a person of a C4 diagram
    WIDE_CARD = "wide_card"  # an illustrated architecture part: name pill, detail, large icon
    PERSON = "person"  # a circle with initials, the tint of a person or a team
    PERSON_CARD = "person_card"  # a card of an org chart: initials, name, role
    PLAN_BAR = "plan_bar"  # a bar of a Gantt chart, coloured and filled by its status
    MILESTONE = "milestone"  # the amber diamond of a Gantt chart
    LABEL = "label"  # plain text with no outline: a row name or a header of a chart
    BRANCH = "branch"  # a pill of a mind map: a branch or a group
    LEAF = "leaf"  # a card or an underlined phrase of a mind map
    KANBAN_CARD = "kanban_card"  # a card of a Kanban board: title, kind tag, owner circle
    ROADMAP_CARD = "roadmap_card"  # a card of a roadmap: title, status tag, owner; dashed if open
    BOARD_PILL = "board_pill"  # a pill in the header of a Kanban column: its name, count or limit
    LANE_HEAD = "lane_head"  # the card at the left of a roadmap row: a large icon and the theme
    PERIOD_HEAD = "period_head"  # the header of a roadmap column: a name and its dates in words
    EXPLAIN_CARD = "explain_card"  # an explainer card: large icon, name pill, two lines of text
    ROW_CARD = "row_card"  # an explainer row: icon at the left, a name and one line of text
    CELL = "cell"  # a tinted box of an explainer comparison, with left-aligned text
    PILL_LABEL = "pill_label"  # a pill with an ink outline: a comparison row name, or ``vs``
    REMARK = "remark"  # bold text with no outline: a remark in a band, a closing line, a note
    SECTION_HEAD = "section_head"  # a dark letter circle and the heading of a section


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
    GRID = "grid"  # a thin line of the grid of a Gantt chart
    TODAY = "today"  # the red dashed line of today
    REPORTS = "reports"  # the solid bus line of an org chart
    WORKS_WITH = "works_with"  # a dashed line between two people without a reporting line
    BRANCH = "branch"  # the thick curve from the centre of a mind map to a branch
    TWIG = "twig"  # a thin curve from a branch to what hangs on it
    LINK = "link"  # the dashed arc between two ideas of a mind map
    KEY = "key"  # a line in a legend: the critical path, blue and dashed but not animated


UNDERLAY_ROLES = (Role.LIFELINE, Role.GRID)  # lines drawn under the nodes


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
    TODAY = "today"  # the red pill of the today line
    LINK = "link"  # the violet pill of a link between two ideas


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
    NETWORK = "network"  # a cloud frame: solid or dashed by kind, with a pill in its own colour
    SYSTEM = "system"  # a use case diagram's system: a white box with its name at the top left
    LAYER = "layer"  # an architecture frame: dashed and tinted, with a dark pill label
    PANEL = "panel"  # a white rounded box with a thin outline, such as the header of a Gantt
    BAND = "band"  # a grey row with its name in bold, such as a phase of a Gantt
    COLUMN = "column"  # a tinted rounded area with no outline: a Kanban column or a roadmap row
    STRIP = "strip"  # an explainer band: a wide tinted strip with a pill label at its top left


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
    L4 = "L4"  # as built: a screenshot of the running app


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
    DISABLED = "disabled"


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


class BlockKind(StrEnum):
    """The wireframe blocks of design 10 section 2: what a screen of a wireframe is made of."""

    NAVBAR = "navbar"
    SIDEBAR = "sidebar"
    CARD = "card"
    PANEL = "panel"
    LIST_ITEM = "list_item"
    FORM_FIELD = "form_field"
    BUTTON = "button"
    IMAGE = "image"
    TAB_BAR = "tab_bar"
    BOTTOM_NAV = "bottom_nav"
    SEARCH_BAR = "search_bar"
    TABLE = "table"
    CHART = "chart"
    MODAL = "modal"
    SHEET = "sheet"
    TOAST = "toast"
    LOADING = "loading"
    EMPTY = "empty"
    ERROR = "error"
    SUCCESS = "success"
    CHIP = "chip"
    STEPPER = "stepper"
    FIGURE = "figure"
    TEXT = "text"
    ROWS = "rows"
    CHECKLIST = "checklist"
    NOTE = "note"  # a note below the screens: a numbered badge, a bold title and one line


class BlockAnchor(StrEnum):
    """Whether a block sits in the grid or is pinned to the foot of the screen."""

    GRID = "grid"
    BOTTOM = "bottom"


class CellKind(StrEnum):
    """How the cells of a table column are drawn."""

    TEXT = "text"
    BOLD = "bold"
    CHIP = "chip"
    BUTTON = "button"


class Corner(StrEnum):
    """The corner or side of a part where an annotation badge sits."""

    TOP_LEFT = "tl"
    TOP_RIGHT = "tr"
    BOTTOM_LEFT = "bl"
    BOTTOM_RIGHT = "br"
    LEFT = "l"
    RIGHT = "r"
    TOP = "t"
    BOTTOM = "b"


class WireState(StrEnum):
    """Which of its four faces a wireframe screen shows (design 10 section 4)."""

    NORMAL = "normal"
    LOADING = "loading"
    EMPTY = "empty"
    ERROR = "error"


class Status(StrEnum):
    """How far a task is. Always drawn as a colour and a second cue (design 08 section 1.1)."""

    DONE = "done"
    IN_PROGRESS = "in_progress"
    PLANNED = "planned"
    BLOCKED = "blocked"


class MindLevel(StrEnum):
    """What an item of a mind map is, which decides how it is drawn."""

    CENTRE = "centre"  # the topic in the middle
    BRANCH = "branch"
    GROUP = "group"  # the second level of a map with four levels
    LEAF = "leaf"  # the second level of a map with two levels
    IDEA = "idea"
    DETAIL = "detail"
    KEY = "key"  # a sample of the marks, in the legend


class PillKind(StrEnum):
    """What a pill of a Kanban column header says, which decides its colours."""

    NAME = "name"  # the name of the column, in the tint of the column
    COUNT = "count"  # how many cards the column holds: dark
    LIMIT = "limit"  # ``2 / 3``: an outline, the column still has room
    FULL = "full"  # ``3 / 3``: red, the column is full and nothing new should be started


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
    is_solid: bool = False  # a solid border, for the frames of a cloud diagram that are not dashed


@dataclass(frozen=True)
class Row:
    """One row of a table node: key chips and a name on the left, a note on the right.

    ``flags`` are the short marks drawn as chips before the name, such as ``PK`` or ``FK``.
    """

    left: str
    right: str = ""
    flags: tuple[str, ...] = ()
    is_mono: bool = False  # the name is code, as a member of a class


@dataclass(frozen=True)
class EdgeLabel:
    """A chip that sits on a line, centred on ``at``."""

    text: str
    at: Point
    kind: LabelKind
    number: str | None = None
    icon: str | None = None  # an icon drawn before the text, as on the chip of a system trigger


@dataclass(frozen=True)
class WireColumn:
    """A column of a wireframe table: its header, its relative width and how its cells look."""

    label: str
    weight: float = 1.0
    kind: CellKind = CellKind.TEXT


@dataclass(frozen=True)
class WireCell:
    """One cell of a wireframe table; ``style`` is the tone of a chip or the style of a button."""

    text: str
    style: str = ""


@dataclass(frozen=True)
class WireBlock:
    """One block of a wireframe screen, placed on a grid by a row, a column and a span.

    Which fields a kind reads is written in ``wire_blocks``; the others stay empty.
    """

    kind: BlockKind
    id: str = ""  # what an annotation points at
    text: str = ""
    detail: str = ""
    value: str = ""
    chip: str = ""
    price: str = ""
    action: str = ""
    hint: str = ""
    stepper: str = ""
    icon: str = ""
    image: str = ""  # ``left`` or ``top`` on a card: where its crossed box sits
    lead: str = ""  # what starts a list item: ``avatar``, ``radio``, ``pin`` or ``thumb``
    trail: str = ""  # the link at the end of a list item
    items: tuple[str, ...] = ()
    icons: tuple[str, ...] = ()
    selected: tuple[int, ...] = ()
    values: tuple[float, ...] = ()
    columns: tuple[WireColumn, ...] = ()
    cells: tuple[tuple[WireCell, ...], ...] = ()
    style: ElementStyle | None = None
    tone: Tone | None = None
    row: int = 0  # 1 based; 0 is the row after the one before
    col: int = 0  # 1 based; 0 is the first column
    span: int = 0  # columns wide; 0 is up to the last column
    rows: int = 1  # rows tall
    height: float = 0  # pixels; 0 is the height of the kind
    bars: int = 0  # grey bars standing for lines of text
    anchor: BlockAnchor = BlockAnchor.GRID
    flags: tuple[str, ...] = ()  # ``back``, ``menu``, ``avatar``, ``bell``, ``bold``, ``tap``...
    children: tuple["WireBlock", ...] = ()  # the blocks a panel holds, one below the other


@dataclass(frozen=True)
class WireBadge:
    """A numbered badge on the corner of a block, or of a part of it."""

    number: str
    block: int  # the index of the block in the screen
    part: str = ""  # the name of a part the block exposes, such as ``stepper``
    corner: Corner = Corner.TOP_RIGHT


@dataclass(frozen=True)
class ScreenElement:
    """An element of a screen that causes a transition; a red dot marks the tapped one."""

    text: str
    style: ElementStyle = ElementStyle.PRIMARY
    placement: Placement = Placement.BOTTOM
    layer: Layer = Layer.BASE
    is_hotspot: bool = True


@dataclass(frozen=True)
class Hotspot:
    """An element of a screenshot that a transition starts from, in the screenshot's pixels."""

    text: str
    box: tuple[float, float, float, float]  # left, top, width, height


@dataclass(frozen=True)
class Capture:
    """The screenshot an L4 screen shows, and the source file that draws the screen."""

    image: str  # the path of a PNG file
    source: str = ""  # the path of the file that draws the screen, for the staleness check
    hotspots: tuple[Hotspot, ...] = ()


@dataclass(frozen=True)
class ScreenView:
    """What a screen node shows: its device frame, its fidelity level and its named elements."""

    code: str  # the text of the id chip, such as ``S31 · loading``
    title: str = ""  # the name of the screen, drawn at the top of its body
    device: Device = Device.PHONE
    orientation: Orientation = Orientation.PORTRAIT
    is_mini: bool = False
    is_large: bool = False  # twice the device size, for an L4 screenshot to be read
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
    blocks: tuple[WireBlock, ...] = ()  # a wireframe: the blocks of an L3 screen
    badges: tuple[WireBadge, ...] = ()
    state: WireState | None = None  # which of the four faces of a state set the screen shows
    scale: float = 1.0  # how much a wireframe is shrunk: 1 is the real size of the device
    caption_note: str = ""  # the small line under the name above a wireframe, such as a width
    is_captioned: bool = False  # the name sits above the frame as ``code · name``, no id chip
    address: str = ""  # the address in the browser bar of a desktop wireframe
    is_bare: bool = False  # no device around the blocks: a note, which is a block on its own
    is_plain: bool = False  # a frame only: no status bar, home bar or browser bar
    capture: Capture | None = None  # the screenshot of an L4 screen


@dataclass(frozen=True)
class PlanView:
    """What a planning node shows besides its text: its status, its person or its mind map level."""

    status: Status | None = None
    progress: float = 0.0  # a bar that is in progress is filled this far, from 0 to 1
    reason: str = ""  # why a blocked task is blocked, written after its bar
    initials: str = ""  # a person, or the owner of an idea
    person_tone: Tone | None = None  # the tint of that person, the same in every diagram
    is_open: bool = False  # an open role: dashed and faded
    is_bold: bool = False  # for a label
    level: MindLevel | None = None
    side: Side | None = None  # which side of the centre a mind map item is on
    priority: int = 0  # 1 or 2 for P1 and P2, 0 for none
    hidden: int = 0  # how many ideas below this one are left out (+N)
    tag: str = ""  # the small tag on a card: its kind on a Kanban, its state on a roadmap
    tag_tone: Tone | None = None  # the tint of that tag
    pill: PillKind | None = None  # what a pill of a Kanban column header says


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
    technology: str = ""  # the mono ``[Kind: technology]`` line of a C4 box
    caption: str | None = None
    caption_above: bool = False  # the caption hangs above the node, where a line leaves below
    sections: tuple[tuple[Row, ...], ...] = ()
    card: bool = False  # drawn as an illustrated card: a large icon, a name pill, a detail line
    dashed: bool = False  # a dashed outline: a reference to something drawn elsewhere
    screen: ScreenView | None = None  # what a screen of a screen flow shows
    markers: tuple[Marker, ...] = ()  # BPMN marks: the trigger, the task type, the repeat
    host: str | None = None  # the id of the task a boundary event sits on the edge of
    chip: EdgeLabel | None = None  # a chip on the node; ``at`` is relative to its top-left
    activities: tuple[str, ...] = ()  # mono grey lines under a state name: ``do / cook``
    stereotype: str = ""  # the small ``«interface»`` line above the name of a class
    is_italic: bool = False  # the name is in italics, as the name of an abstract class
    is_centered: bool = False  # the header text of a table is centred, as in a class box
    plan: PlanView | None = None  # what a planning node shows: status, person, mind map level
    chips: tuple[str, ...] = ()  # the small mono pills at the right of an explainer row
    is_mono: bool = False  # the name of an explainer row is code: a file or a folder


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
    tone: Tone | None = None  # the colour of a mind map curve, taken from its branch
    is_curved: bool = False  # ``points`` are the four points of one cubic Bezier curve


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
