"""Helpers for an author who lays a diagram out by hand, in a script of their own.

``Canvas`` keeps the design's rules in one place (the size of each shape, how a node is
widened to hold its text, where a line attaches to a diamond or a pill, the colour of each
line role) and leaves every decision about position to the author: where a node goes, which
way a line runs, how groups are arranged. A script calls ``node``, ``edge``, ``lane`` and
``zone`` and then ``write``, which draws the HTML and draw.io files and runs the checks.
"""

from dataclasses import dataclass, field, replace
from enum import StrEnum
from itertools import pairwise
from pathlib import Path

from . import check, render_drawio, render_html, scene
from .canvas import fit_canvas
from .labels import place_labels
from .model import (
    DEFAULT_FONT_SIZE_PX,
    Edge,
    EdgeLabel,
    Frame,
    FrameVariant,
    Head,
    LabelKind,
    Node,
    Point,
    Role,
    Scene,
    Shape,
    Tone,
)
from .sizing import NodeContent, estimate_text_width, fit_card, fit_node, wrap_text
from .text_area import text_area_width
from .theme import load_theme

CAPTIONED_SHAPES = {Shape.START, Shape.END, Shape.INTERMEDIATE, Shape.ACTOR}  # the text goes under
LABEL_KIND_OF_ROLE = {Role.YES: LabelKind.YES, Role.NO: LabelKind.NO, Role.BACK: LabelKind.BACK}
MIDDLE = 0.5
GATEWAY_ICONS = {"x", "plus"}  # a diamond with one of these marks is a BPMN gateway
TEXT_SLACK_PX = 48  # room added to the estimated width of free text, so it stays on one line
TEXT_HEIGHT_PX = 24
LEGEND_ROW_PX = 28  # the height of one legend line
LEGEND_SAMPLE_PX = 50  # the length of the sample line
LEGEND_TEXT_OFFSET_PX = 90  # where the words start, to the right of the sample line
LEGEND_WORDS = {
    Role.MAIN: "Main path, animated fast: the route a normal case takes",
    Role.DATA: "Message between pools, or a data stream: dashed, animated slowly",
    Role.YES: "Yes exit of a decision",
    Role.NO: "No exit, or a failure",
    Role.BACK: "Retry or return",
    Role.NEXT: "Next step",
}


class Side(StrEnum):
    """A side of a node: ``top``, ``bottom``, ``left`` or ``right``."""

    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class Box:
    """A node that has been placed, with the points where a line can attach to it."""

    node: Node

    def port(self, side: str, along: float = 0.5) -> Point:
        """Return where a line attaches to one side of the node.

        Args:
            side: ``top``, ``bottom``, ``left`` or ``right``.
            along: How far along the side the point is, from 0 (the left end of a top or bottom
                side, the top end of a left or right side) to 1. The middle, 0.5, is the default.
                Use other values to spread several lines over a wide node or a bar. A diamond
                has a point only at its tips, so it takes the middle only.

        Returns:
            The point on the outline of the node.

        Raises:
            ValueError: If the side is not one of the four, ``along`` is outside 0 to 1, or a
                diamond is given a point other than a tip.
        """
        node = self.node
        if side not in tuple(Side):
            raise ValueError(f"unknown side '{side}'; use top, bottom, left or right")
        if not 0.0 <= along <= 1.0:
            raise ValueError("'along' must be between 0 and 1")
        if node.shape is Shape.DECISION and along != MIDDLE:
            raise ValueError("a decision has a point only at its four tips (along=0.5)")
        across_x, across_y = node.x + node.width * along, node.y + node.height * along
        ports = {
            Side.TOP: (across_x, node.y),
            Side.BOTTOM: (across_x, node.y + node.height),
            Side.LEFT: (node.x, across_y),
            Side.RIGHT: (node.x + node.width, across_y),
        }
        return ports[Side(side)]

    @property
    def centre(self) -> Point:
        """The middle of the node."""
        return self.node.x + self.node.width / 2, self.node.y + self.node.height / 2


@dataclass
class Canvas:
    """A diagram being built by hand: frames, nodes and lines at positions the author chooses."""

    title: str | None = None
    description: str | None = None
    boxes: dict[str, Box] = field(default_factory=dict)
    frames: list[Frame] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def lane(
        self, name: str, label: str, tone: Tone, bounds: tuple[float, float, float, float]
    ) -> None:
        """Add a swimlane: a lightly tinted band with its name on a dark tab.

        Args:
            name: The id of the lane.
            label: The name shown on the tab.
            tone: The colour group of the lane.
            bounds: Left, top, width and height of the band, tab included. The tab takes
                ``lane_tab`` pixels at the left of a wide lane, or at the top of a tall one.
        """
        self.frames.append(_frame(f"lane-{name}", (label, tone), bounds, FrameVariant.LANE))

    def zone(
        self, name: str, label: str, tone: Tone, bounds: tuple[float, float, float, float]
    ) -> None:
        """Add a group area: a tinted, dashed area with a name pill in its corner.

        Args:
            name: The id of the zone.
            label: The name shown on the pill.
            tone: The colour group of the zone.
            bounds: Left, top, width and height of the area.
        """
        self.frames.append(_frame(f"zone-{name}", (label, tone), bounds, FrameVariant.AREA))

    def node(self, name: str, shape: Shape, text: str, options: "NodeOptions") -> Box:
        """Add a node centred on a point, sized by the design's rules to hold its text.

        Args:
            name: The id of the node.
            shape: The outline: a terminator, a process, a decision and so on.
            text: The words in the node. Write them in sentence case; a decision is a question.
            options: Where the middle of the node goes, and optionally an icon, a tone, a number
                chip, a detail line, or a size to force.

        Returns:
            The placed box, for attaching lines to.

        Raises:
            ValueError: If the id is already used.
        """
        if name in self.boxes:
            raise ValueError(f"the id '{name}' is used twice")
        rules = load_theme().layout
        content = NodeContent(text, options.detail or "", options.icon is not None)
        fitted = fit_card(content, rules) if options.card else fit_node(shape, content, rules)
        width = options.width or fitted.width
        height = options.height or fitted.height
        if options.width:
            area = text_area_width(shape, width, options.icon is not None)
            fitted = replace(
                fitted, lines=tuple(wrap_text(text, rules, area, DEFAULT_FONT_SIZE_PX))
            )
        is_gateway = shape is Shape.DECISION and options.icon in GATEWAY_ICONS
        captioned = shape in CAPTIONED_SHAPES or is_gateway
        placed = Node(
            id=name,
            shape=shape,
            x=options.centre[0] - width / 2,
            y=options.centre[1] - height / 2,
            width=width,
            height=height,
            text=() if captioned else fitted.lines,
            icon=options.icon,
            tone=options.tone,
            number=options.number,
            font_size=DEFAULT_FONT_SIZE_PX,
            detail=fitted.detail,
            caption=text if captioned else None,
            card=options.card,
        )
        box = Box(placed)
        self.boxes[name] = box
        return box

    def text(self, name: str, words: str, anchor: Point) -> Box:
        """Add free text with no outline, for a heading, a note or a legend line.

        Args:
            name: The id of the text.
            words: The text.
            anchor: Where the left end of the text goes, at the middle of its height.

        Returns:
            The placed box.
        """
        rules = load_theme().layout
        width = estimate_text_width(words, rules, DEFAULT_FONT_SIZE_PX) + TEXT_SLACK_PX
        centre = (anchor[0] + width / 2, anchor[1])
        return self.node(
            name, Shape.TEXT, words, NodeOptions(centre, width=width, height=TEXT_HEIGHT_PX)
        )

    def legend(self, corner: Point, roles: tuple[Role, ...]) -> None:
        """Add a "Reading the chart" legend: a heading, then a sample line and words per role.

        Args:
            corner: The top-left corner of the legend.
            roles: The line roles the diagram uses, in the order to list them.
        """
        left, top = corner
        self.text("legend-title", "Reading the chart", (left, top))
        for index, role in enumerate(roles):
            row = top + LEGEND_ROW_PX * (index + 1)
            style = Route(role=role, dashed=role is Role.BACK)
            sample = [(left, row), (left + LEGEND_SAMPLE_PX, row)]
            self.edges.append(_sample_edge(f"legend-line-{index}", sample, style))
            anchor = (left + LEGEND_TEXT_OFFSET_PX, row)
            self.text(f"legend-text-{index}", LEGEND_WORDS[role], anchor)

    def edge(
        self,
        source: str,
        target: str,
        route: "Route | None" = None,
    ) -> Edge:
        """Add a line between two nodes, drawn with right angles.

        Args:
            source: The id of the node it leaves.
            target: The id of the node it enters.
            route: Which sides it uses, the points it passes, its role and its label. Without
                it the line leaves and enters the sides that face each other.

        Returns:
            The line that was added.
        """
        route = route or Route()
        first, second = self.boxes[source], self.boxes[target]
        leave = route.leave or _facing_side(first, second)
        arrive = route.arrive or _facing_side(second, first)
        corners = [
            first.port(leave, route.leave_along),
            *route.via,
            second.port(arrive, route.arrive_along),
        ]
        points = _right_angled(corners)
        label = None
        if route.label:
            label = EdgeLabel(
                route.label, _middle(points), LABEL_KIND_OF_ROLE.get(route.role) or LabelKind.PLAIN
            )
        line = Edge(
            id=f"e{len(self.edges) + 1}",
            role=route.role,
            points=tuple(points),
            label=label,
            source=source,
            target=target,
            head=route.head,
            tail=route.tail,
            dashed=route.dashed,
        )
        self.edges.append(line)
        return line

    def scene(self) -> Scene:
        """Return the finished scene: labels moved off boxes, canvas sized to hold everything."""
        done = Scene(
            width=0,
            height=0,
            title=self.title,
            description=self.description,
            frames=tuple(self.frames),
            nodes=tuple(box.node for box in self.boxes.values()),
            edges=tuple(self.edges),
        )
        return fit_canvas(place_labels(done))

    def write(self, folder: str | Path, name: str) -> list[check.Finding]:
        """Write ``<name>.scene.json``, ``.html`` and ``.drawio`` and check the scene.

        Args:
            folder: Where to write; it is created when missing.
            name: The file name without a suffix.

        Returns:
            The findings of the check, errors first. Print them with ``check.format_report``.
        """
        final = self.scene()
        target = Path(folder)
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{name}.scene.json").write_text(scene.dumps(final, indent=2), encoding="utf-8")
        (target / f"{name}.html").write_text(render_html.render(final), encoding="utf-8")
        (target / f"{name}.drawio").write_text(render_drawio.render(final), encoding="utf-8")
        return check.check_scene(final)


@dataclass(frozen=True)
class NodeOptions:
    """Where a node goes, and what can be set on it besides its shape and words."""

    centre: Point
    icon: str | None = None
    tone: Tone | None = None
    number: str | None = None
    detail: str | None = None
    card: bool = False
    width: float | None = None
    height: float | None = None


@dataclass(frozen=True)
class Route:
    """How a line runs: its sides, the points it passes, and how it is drawn."""

    leave: str | None = None
    arrive: str | None = None
    leave_along: float = MIDDLE
    arrive_along: float = MIDDLE
    via: tuple[Point, ...] = ()
    role: Role = Role.NEXT
    label: str | None = None
    dashed: bool = False
    head: Head = Head.FILLED
    tail: Head = Head.NONE


def sentence_case(text: str) -> str:
    """Return text with only its first word and acronyms capitalised, as the design asks.

    Args:
        text: Words, for example ``"Soft Reconfig Store"``.

    Returns:
        The same words in sentence case, for example ``"Soft reconfig store"``. A word that is
        with capitals inside (``"RIB"``, ``"Adj-RIB-In"``) is kept as it is.
    """
    words = text.split()
    kept = [
        word if _is_name(word) else word.lower() if index else word.capitalize()
        for index, word in enumerate(words)
    ]
    return " ".join(kept)


def _is_name(word: str) -> bool:
    """Tell whether a word has capitals inside it (``RIB``, ``Adj-RIB-In``) and must be kept."""
    letters = [char for char in word if char.isalpha()]
    inner = sum(1 for char in letters[1:] if char.isupper())
    return len(letters) > 1 and inner > 0


def _frame(
    name: str,
    words: tuple[str, Tone],
    bounds: tuple[float, float, float, float],
    variant: FrameVariant,
) -> Frame:
    """Build a frame from its id, its label and tone, its bounds and its variant."""
    left, top, width, height = bounds
    return Frame(name, left, top, width, height, words[0], words[1], variant)


def _sample_edge(name: str, points: list[Point], route: Route) -> Edge:
    """Build a short line that belongs to no node, for the legend."""
    return Edge(
        id=name,
        role=route.role,
        points=tuple(points),
        label=None,
        source=None,
        target=None,
        head=route.head,
        dashed=route.dashed,
    )


def _facing_side(box: Box, other: Box) -> str:
    """Return the side of a box that looks towards another box."""
    delta_x = other.centre[0] - box.centre[0]
    delta_y = other.centre[1] - box.centre[1]
    if abs(delta_x) >= abs(delta_y):
        return Side.RIGHT if delta_x > 0 else Side.LEFT
    return Side.BOTTOM if delta_y > 0 else Side.TOP


def _right_angled(corners: list[Point]) -> list[Point]:
    """Join points with right angles, adding a corner where two points differ in x and in y."""
    points = [corners[0]]
    for start, end in pairwise(corners):
        if start[0] != end[0] and start[1] != end[1]:
            points.append((end[0], start[1]))
        points.append(end)
    return points


def _middle(points: list[Point]) -> Point:
    """Return the middle of the longest segment of a line."""
    start, end = max(
        pairwise(points),
        key=lambda pair: abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1]),
    )
    return (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
