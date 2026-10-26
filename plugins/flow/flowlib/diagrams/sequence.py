"""The sequence diagram: lay out lifelines, activation bars, messages, fragments and notes.

Time runs down. Items are placed in rows in the order they are written; the x of a lifeline
comes from the order of the participants. Activation bars are derived from pairs of a call and
its return; fragments wrap the rows they hold.
"""

from dataclasses import dataclass, field

from .. import canvas
from ..model import (
    DEFAULT_FONT_SIZE_PX,
    Divider,
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
    Side,
    Tone,
)
from ..sizing import estimate_text_width, wrap_text
from ..theme import Theme, load_theme
from . import sequence_spec as spec_io
from .sequence_spec import (
    Destroy,
    Fragment,
    Item,
    Message,
    MessageKind,
    MessageRole,
    Note,
    SequenceSpec,
)

ROLE_OF_MESSAGE = {
    MessageRole.NEXT: Role.NEXT,
    MessageRole.MAIN: Role.MAIN,
    MessageRole.FAIL: Role.NO,
    MessageRole.EVENT: Role.DATA,
}
HEAD_OF_KIND = {
    MessageKind.SYNC: Head.FILLED,
    MessageKind.RETURN: Head.OPEN,
    MessageKind.ASYNC: Head.OPEN,
    MessageKind.SELF: Head.FILLED,
    MessageKind.LOST: Head.DOT,
    MessageKind.FOUND: Head.FILLED,
    MessageKind.CREATE: Head.OPEN,
}
DASHED_KINDS = (MessageKind.RETURN, MessageKind.CREATE)
LABEL_ABOVE_LINE_PX = 30  # room a message row needs above its line, for the label
ROW_BELOW_LINE_PX = 22  # room a message row needs below its line
PARTICIPANT_TEXT_EXTRA_PX = 24
PARTICIPANT_ICON_EXTRA_PX = 30
LABEL_PADDING_PX = 16
LABEL_GAP_PX = 10
NOTE_FONT_SIZE_PX = 11


@dataclass
class _Bar:
    """An activation bar of one participant, between two y positions."""

    participant: str
    top: float
    bottom: float
    call_id: int
    depth: int = 0


@dataclass
class _Call:
    """A call that has not been answered yet."""

    callee: str
    caller: str
    y: float
    ident: int


@dataclass
class _Row:
    """A message and the y of its line."""

    message: Message
    y: float


@dataclass
class _FragmentRecord:
    """A fragment frame while it is being built."""

    fragment: Fragment
    top: float
    touched: set[str] = field(default_factory=set)
    dividers: list[Divider] = field(default_factory=list)
    children: list[Frame] = field(default_factory=list)
    bottom: float = 0.0
    order: int = 0


class _Builder:
    """Walks the items of a spec once, recording rows, bars, fragments and notes."""

    def __init__(self, spec: SequenceSpec, theme: Theme) -> None:
        """Compute the position of each lifeline and the y of the first message.

        Args:
            spec: The sequence description.
            theme: The design tokens.
        """
        self.spec = spec
        self.theme = theme
        self.rules = theme.sequence
        self.box_width = {
            each.id: self._box_width(each.label, each.icon) for each in spec.participants
        }
        self.x = self._lifeline_positions()
        title = theme.layout.title_block_height if spec.title else 0
        self.box_top = theme.layout.margin + title
        self.cursor = self.box_top + self.rules.participant_height + self.rules.first_message_gap
        self.rows: list[_Row] = []
        self.bars: list[_Bar] = []
        self.calls: list[_Call] = []
        self.frames: list[Frame] = []
        self.notes: list[tuple[Note, float]] = []
        self.closed: set[int] = set()
        self._call_count = 0
        self.destroyed: dict[str, float] = {}
        self.created: dict[str, float] = {}
        self._frame_count = 0

    def _box_width(self, label: str, icon: str | None) -> float:
        """Return the width of a participant box: the standard width, or more for a long label."""
        layout = self.theme.layout
        text = estimate_text_width(label, layout, DEFAULT_FONT_SIZE_PX)
        extra = PARTICIPANT_TEXT_EXTRA_PX + (PARTICIPANT_ICON_EXTRA_PX if icon else 0)
        return max(self.rules.participant_width, text + extra)

    def _lifeline_positions(self) -> dict[str, float]:
        """Return the x of each lifeline, left to right, spaced so that boxes never touch."""
        positions: dict[str, float] = {}
        previous: tuple[float, float] | None = None
        for each in self.spec.participants:
            half = self.box_width[each.id] / 2
            if previous is None:
                center = self.theme.layout.margin + half
            else:
                gap = previous[1] + half + self.rules.min_gap_between_boxes
                center = previous[0] + max(self.rules.pitch, gap)
            positions[each.id] = center
            previous = (center, half)
        return positions

    def walk(
        self, items: tuple[Item, ...], touched: set[str], frame: _FragmentRecord | None
    ) -> None:
        """Place every item in order, recursing into fragments.

        Args:
            items: The items to place.
            touched: Participants used by these items, filled in for the enclosing fragment.
            frame: The fragment being built, or None at the top level.
        """
        for item in items:
            if isinstance(item, Message):
                self._message(item)
                touched.update({item.source, item.target})
            elif isinstance(item, Note):
                self.notes.append((item, self.cursor - LABEL_ABOVE_LINE_PX))
                touched.add(item.over)
            elif isinstance(item, Destroy):
                self.destroyed[item.target] = self.cursor - self.rules.row_height / 2
            else:
                self._fragment(item, touched, frame)

    def _message(self, message: Message) -> None:
        """Place one message on its row and track the calls that make activation bars."""
        y = self.cursor
        self.rows.append(_Row(message, y))
        self.cursor += self.rules.row_height
        if message.kind is MessageKind.SELF:
            self.cursor += self.rules.self_row_extra
        if message.kind is MessageKind.CREATE:
            self.created[message.target] = y
        if message.kind in (MessageKind.SYNC, MessageKind.CREATE):
            self._call_count += 1
            self.calls.append(_Call(message.target, message.source, y, self._call_count))
        elif message.kind is MessageKind.RETURN:
            self._answer(message, y)

    def _answer(self, message: Message, y: float) -> None:
        """Close the latest open call that this return answers, making an activation bar."""
        for index in range(len(self.calls) - 1, -1, -1):
            call = self.calls[index]
            if call.callee == message.source and call.caller == message.target:
                over = self.rules.bar_overshoot
                self.bars.append(_Bar(call.callee, call.y - over, y + over, call.ident))
                self.closed.add(call.ident)
                del self.calls[index]
                return

    def _fragment(
        self, fragment: Fragment, touched: set[str], parent: _FragmentRecord | None
    ) -> None:
        """Place a fragment: its sections, dividers and frame."""
        rules = self.rules
        self._frame_count += 1
        record = _FragmentRecord(
            fragment,
            top=self.cursor - ROW_BELOW_LINE_PX - rules.fragment_enter / 3,
            order=self._frame_count,
        )
        self.cursor += rules.fragment_enter
        open_before, closed_before = list(self.calls), set(self.closed)
        for index, section in enumerate(fragment.sections):
            self.calls = list(open_before)
            if index > 0:
                divider_y = self.cursor - rules.divider_gap + ROW_BELOW_LINE_PX / 2
                record.dividers.append(Divider(y=divider_y, guard=section.guard or ""))
                self.cursor += rules.divider_gap
            self.walk(section.items, record.touched, record)
        answered = self.closed - closed_before
        self.calls = [call for call in open_before if call.ident not in answered]
        record.bottom = self.cursor - ROW_BELOW_LINE_PX
        self.cursor += rules.fragment_exit
        touched.update(record.touched)
        frame = self._close(record)
        if parent is not None:
            parent.children.append(frame)

    def _close(self, record: _FragmentRecord) -> Frame:
        """Turn a finished fragment record into a frame, wide enough for what it holds."""
        rules = self.rules
        columns = [self.x[name] for name in record.touched] or [
            self.x[self.spec.participants[0].id]
        ]
        left = min(columns) - rules.fragment_pad_x
        right = max(columns) + rules.fragment_pad_x
        for child in record.children:
            left = min(left, child.x - rules.fragment_inset_x)
            right = max(right, child.x + child.width + rules.fragment_inset_x)
        first = record.fragment.sections[0]
        frame = Frame(
            id=f"fragment-{record.order}",
            x=left,
            y=record.top,
            width=right - left,
            height=record.bottom - record.top,
            label=record.fragment.kind.value,
            tone=Tone.AMBER,
            variant=FrameVariant.FRAGMENT,
            guard=first.guard,
            dividers=tuple(record.dividers),
        )
        self.frames.append(frame)
        self.frames.sort(key=lambda each: int(each.id.rsplit("-", 1)[1]))
        return frame

    def finish_bars(self) -> None:
        """Merge the bars of one call across alternative sections, and stack overlapping bars.

        A call answered in several sections of a fragment (alt and else) is one bar that lasts
        until the last of the answers. A call that is never answered makes no bar.
        """
        merged: dict[int, _Bar] = {}
        for bar in self.bars:
            known = merged.get(bar.call_id)
            if known is None:
                merged[bar.call_id] = bar
            else:
                known.bottom = max(known.bottom, bar.bottom)
        self.bars = sorted(merged.values(), key=lambda each: each.top)
        placed: list[_Bar] = []
        for bar in self.bars:
            bar.depth = sum(
                1
                for other in placed
                if other.participant == bar.participant and other.bottom > bar.top
            )
            placed.append(bar)

    def bar_edge(self, participant: str, y: float, toward: float) -> float:
        """Return the x where a line at height ``y`` meets a lifeline, on the side of ``toward``.

        Args:
            participant: The lifeline.
            y: The height of the line.
            toward: The x of the other end of the line.

        Returns:
            The edge of the outermost activation bar that covers ``y`` on that side, or the
            lifeline itself when no bar covers it.
        """
        center = self.x[participant]
        half = self.rules.bar_width / 2
        edges = [
            center + bar.depth * self.rules.bar_step + (half if toward > center else -half)
            for bar in self.bars
            if bar.participant == participant and bar.top <= y <= bar.bottom
        ]
        if not edges:
            return center
        return max(edges) if toward > center else min(edges)


def _label(message: Message, at: Point) -> EdgeLabel | None:
    """Build the label of a message, or None when it has no text and no number."""
    if not message.label and not message.number:
        return None
    kind = LabelKind.TEXT_FAIL if message.role is MessageRole.FAIL else LabelKind.TEXT
    return EdgeLabel(text=message.label, at=at, kind=kind, number=message.number)


def _message_points(builder: _Builder, row: _Row) -> list[Point]:
    """Return the route of a message: straight, a loop for a self call, or to a free end."""
    message, y = row.message, row.y
    rules = builder.rules
    source_x, target_x = builder.x[message.source], builder.x[message.target]
    if message.kind is MessageKind.SELF:
        start = builder.bar_edge(message.source, y, source_x + 1)
        out = start + rules.self_width
        return [(start, y), (out, y), (out, y + rules.self_height), (start, y + rules.self_height)]
    if message.kind in (MessageKind.LOST, MessageKind.FOUND):
        is_last = source_x >= max(builder.x.values())
        far = source_x + (-1 if is_last else 1) * rules.lost_length
        near = builder.bar_edge(message.source, y, far)
        return [(near, y), (far, y)] if message.kind is MessageKind.LOST else [(far, y), (near, y)]
    start = builder.bar_edge(message.source, y, target_x)
    if message.kind is MessageKind.CREATE:
        half = builder.box_width[message.target] / 2
        end = target_x - half if target_x > source_x else target_x + half
    else:
        end = builder.bar_edge(message.target, y, source_x)
    return [(start, y), (end, y)]


def _message_edge(builder: _Builder, row: _Row, index: int) -> Edge:
    """Build the scene edge of one message."""
    message = row.message
    points = _message_points(builder, row)
    rules = builder.rules
    if message.kind is MessageKind.SELF:
        loop_width = estimate_text_width(
            message.label, builder.theme.layout, builder.theme.layout.chip_font_size
        )
        at = (
            points[1][0] + LABEL_GAP_PX + (loop_width + LABEL_PADDING_PX) / 2,
            row.y + rules.self_height / 2,
        )
    else:
        at = ((points[0][0] + points[-1][0]) / 2, row.y - rules.label_rise)
    head = HEAD_OF_KIND[message.kind]
    tail = Head.DOT if message.kind is MessageKind.FOUND else Head.NONE
    return Edge(
        id=f"m{index}",
        role=ROLE_OF_MESSAGE[message.role],
        points=tuple(points),
        label=_label(message, at),
        source=None,
        target=None,
        head=head,
        tail=tail,
        dashed=message.kind in DASHED_KINDS,
    )


def _participant_nodes(builder: _Builder) -> list[Node]:
    """Build the header box of each participant; a created one sits at its create message."""
    rules = builder.rules
    nodes = []
    for each in builder.spec.participants:
        top = builder.box_top
        if each.id in builder.created:
            top = builder.created[each.id] - rules.participant_height / 2
        width = builder.box_width[each.id]
        nodes.append(
            Node(
                id=each.id,
                shape=Shape.PROCESS,
                x=builder.x[each.id] - width / 2,
                y=top,
                width=width,
                height=rules.participant_height,
                text=(each.label,),
                icon=each.icon,
                tone=each.tone,
                number=None,
                font_size=DEFAULT_FONT_SIZE_PX,
            )
        )
    return nodes


def _lifelines(builder: _Builder, nodes: list[Node], end_y: float) -> tuple[list[Edge], list[Node]]:
    """Build the dashed lifeline of each participant, and the cross of each destroyed one."""
    rules = builder.rules
    lines: list[Edge] = []
    crosses: list[Node] = []
    for node in nodes:
        stop = builder.destroyed.get(node.id, end_y)
        x = builder.x[node.id]
        if node.id in builder.destroyed:
            half = rules.destroy_size / 2
            crosses.append(
                Node(
                    f"destroy-{node.id}",
                    Shape.CROSS,
                    x - half,
                    stop - half,
                    rules.destroy_size,
                    rules.destroy_size,
                    (),
                    None,
                    None,
                    None,
                    DEFAULT_FONT_SIZE_PX,
                )
            )
            stop -= half
        lines.append(
            Edge(
                id=f"life-{node.id}",
                role=Role.LIFELINE,
                points=((x, node.y + node.height), (x, stop)),
                label=None,
                source=None,
                target=None,
                head=Head.NONE,
            )
        )
    return lines, crosses


def _bar_nodes(builder: _Builder) -> list[Node]:
    """Build the activation bars as thin tone-filled rectangles on their lifelines."""
    rules = builder.rules
    tone_of = {each.id: each.tone for each in builder.spec.participants}
    return [
        Node(
            id=f"bar-{index}",
            shape=Shape.BAR,
            x=builder.x[bar.participant] + bar.depth * rules.bar_step - rules.bar_width / 2,
            y=bar.top,
            width=rules.bar_width,
            height=bar.bottom - bar.top,
            text=(),
            icon=None,
            tone=tone_of[bar.participant],
            number=None,
            font_size=DEFAULT_FONT_SIZE_PX,
        )
        for index, bar in enumerate(builder.bars, start=1)
    ]


def _note_nodes(builder: _Builder) -> list[Node]:
    """Build each note as a folded-corner box beside its lifeline."""
    rules = builder.rules
    layout = builder.theme.layout
    nodes = []
    for index, (note, top) in enumerate(builder.notes, start=1):
        lines = wrap_text(
            note.text, layout, rules.note_width - rules.note_padding, NOTE_FONT_SIZE_PX
        )
        height = len(lines) * rules.note_line_height + rules.note_padding
        center = builder.x[note.over]
        offset = rules.note_offset + rules.bar_width / 2
        left = center + offset if note.side is Side.RIGHT else center - offset - rules.note_width
        nodes.append(
            Node(
                f"note-{index}",
                Shape.NOTE,
                left,
                top,
                rules.note_width,
                height,
                tuple(lines),
                None,
                None,
                None,
                NOTE_FONT_SIZE_PX,
            )
        )
    return nodes


def layout(spec: SequenceSpec) -> Scene:
    """Lay out a sequence diagram.

    Args:
        spec: The sequence description.

    Returns:
        The scene: participant boxes, lifelines, activation bars, messages, notes and fragments.
    """
    builder = _Builder(spec, load_theme())
    builder.walk(spec.items, set(), None)
    builder.finish_bars()
    end_y = builder.cursor + builder.rules.bottom_gap
    participants = _participant_nodes(builder)
    lifelines, crosses = _lifelines(builder, participants, end_y)
    messages = [
        _message_edge(builder, row, index) for index, row in enumerate(builder.rows, start=1)
    ]
    scene = Scene(
        width=0,
        height=0,
        title=spec.title,
        description=spec.description,
        frames=tuple(builder.frames),
        nodes=tuple(participants + _bar_nodes(builder) + _note_nodes(builder) + crosses),
        edges=tuple(lifelines + messages),
    )
    return canvas.fit_canvas(scene)


def layout_raw(raw: object) -> Scene:
    """Lay out a sequence diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a sequence spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(spec_io.parse(raw))
