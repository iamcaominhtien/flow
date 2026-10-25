"""Timeline diagrams: a Gantt chart (one row per task) and a roadmap (items packed in lanes).

The JSON format::

    {"type": "gantt", "title": "...", "desc": "...", "periods": ["W1", "W2", "W3"],
     "tasks": [{"id", "label", "start": 0, "length": 2, "group", "tone", "after": "task id"}]}

    {"type": "roadmap", "title": "...", "desc": "...", "periods": ["Q1", "Q2", "Q3", "Q4"],
     "lanes": [{"label", "tone", "items": [{"label", "start": 0, "length": 2, "detail", "tone"}]}]}

``start`` counts periods from 0 and ``length`` is a number of periods. Dates are not read: name
the periods yourself. A Gantt task may follow another with ``after``; the line is drawn from the
end of that task to the start of this one, so it must start no earlier than that task ends.
"""

from dataclasses import dataclass, field
from typing import Any

from ..canvas import fit_canvas
from ..model import DEFAULT_FONT_SIZE_PX, Edge, Frame, Head, Node, Role, Scene, Shape, Tone
from ..reader import Reader, SpecError, suggestion
from ..sizing import estimate_text_width
from ..theme import LayoutRules, load_theme

GANTT = "gantt"
ROADMAP = "roadmap"
PERIOD_PX = 120.0
MIN_PERIOD_PX = 80.0
BAR_HEIGHT_PX = 40.0
HEADER_HEIGHT_PX = 32.0
ROW_GAP_PX = 12.0
BAR_PADDING_PX = 24.0
BAR_INSET_PX = 4.0
FRAME_TOP_PX = 36.0
FRAME_BOTTOM_PX = 12.0
FRAME_GAP_PX = 16.0
DEPENDENCY_ELBOW_PX = 12.0
SPEC_KEYS = {"type", "title", "desc", "periods", "tasks", "lanes"}
TASK_KEYS = {"id", "label", "start", "length", "group", "tone", "after"}
LANE_KEYS = {"label", "tone", "items"}
ITEM_KEYS = {"label", "start", "length", "detail", "tone"}


@dataclass
class _Bar:
    """One bar on the timeline, before it has a position."""

    id: str
    label: str
    start: int
    length: int
    tone: Tone | None
    detail: str = ""
    after: str | None = None


@dataclass
class _Band:
    """A group of bars drawn in one frame (a lane, a task group, or the whole chart)."""

    label: str | None
    tone: Tone
    bars: list[_Bar] = field(default_factory=list)


def _whole(raw: dict[str, Any], key: str, where: str, read: Reader) -> int:
    """Read a whole number field, reporting a problem when it is missing or not whole."""
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        read.report(where, f"'{key}' must be a whole number, 0 or more")
        return 0
    return value


def _bar(raw: object, where: str, periods: int, read: Reader) -> _Bar | None:
    """Build one bar from a task or an item, checking that it fits the periods."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, TASK_KEYS | ITEM_KEYS, where)
    start = _whole(raw, "start", where, read)
    length = _whole(raw, "length", where, read)
    if length < 1:
        read.report(where, "'length' must be at least 1")
    if start + length > periods:
        read.report(where, f"ends in period {start + length}, but there are only {periods}")
    identifier = raw.get("id") or f"bar{len(read.problems)}-{where}"
    return _Bar(
        id=identifier,
        label=read.text(raw, "label", where) or identifier,
        start=start,
        length=max(length, 1),
        tone=read.enum(Tone, raw, "tone", where),
        detail=read.text(raw, "detail", where) or "",
        after=raw.get("after"),
    )


def _gantt_bands(raw: dict[str, Any], periods: int, read: Reader) -> list[_Band]:
    """Read the tasks of a Gantt chart into one band per group, in the order first seen."""
    bands: dict[str | None, _Band] = {}
    tasks = raw.get("tasks", [])
    for index, item in enumerate(tasks if isinstance(tasks, list) else []):
        bar = _bar(item, f"tasks[{index}]", periods, read)
        if bar is None:
            continue
        group = item.get("group") if isinstance(item, dict) else None
        band = bands.setdefault(group, _Band(group, Tone.GRAY))
        band.bars.append(bar)
    if not bands:
        read.report("spec", "'tasks' must list at least one task")
    return list(bands.values())


def _roadmap_bands(raw: dict[str, Any], periods: int, read: Reader) -> list[_Band]:
    """Read the lanes of a roadmap into one band per lane."""
    bands = []
    lanes = raw.get("lanes", [])
    for index, lane in enumerate(lanes if isinstance(lanes, list) else []):
        where = f"lanes[{index}]"
        if not isinstance(lane, dict):
            read.report(where, "must be an object")
            continue
        read.check_keys(lane, LANE_KEYS, where)
        band = _Band(
            read.text(lane, "label", where), read.enum(Tone, lane, "tone", where) or Tone.GRAY
        )
        items = lane.get("items", [])
        for number, item in enumerate(items if isinstance(items, list) else []):
            bar = _bar(item, f"{where}.items[{number}]", periods, read)
            if bar is not None:
                bar.id = f"l{index}i{number}"
                band.bars.append(bar)
        bands.append(band)
    if not bands:
        read.report("spec", "'lanes' must list at least one lane")
    return bands


def _periods(raw: dict[str, Any], read: Reader) -> list[str]:
    """Read the list of period names."""
    periods = raw.get("periods")
    if not (isinstance(periods, list) and periods and all(isinstance(p, str) for p in periods)):
        read.report("spec", "'periods' must be a non-empty list of names such as W1, W2")
        return []
    return periods


def _check_dependencies(bands: list[_Band], read: Reader) -> None:
    """Report an ``after`` that names no task, or a task that starts before the one it follows."""
    bars = {bar.id: bar for band in bands for bar in band.bars}
    for bar in bars.values():
        if bar.after is None:
            continue
        before = bars.get(bar.after)
        if before is None:
            hint = suggestion(bar.after, bars)
            read.report(f"task '{bar.id}'", f"'after' names '{bar.after}', not a task{hint}")
        elif bar.start < before.start + before.length:
            read.report(f"task '{bar.id}'", f"starts before '{bar.after}' ends")


def _pack(bars: list[_Bar]) -> list[list[_Bar]]:
    """Put bars that overlap in time into separate sub-rows, as few as the order allows."""
    rows: list[list[_Bar]] = []
    for bar in sorted(bars, key=lambda each: each.start):
        for row in rows:
            if row[-1].start + row[-1].length <= bar.start:
                row.append(bar)
                break
        else:
            rows.append([bar])
    return rows


@dataclass
class _Layout:
    """The scale and the running position while the chart is built from top to bottom."""

    rules: LayoutRules
    period_px: float
    left: float
    top: float
    nodes: list[Node] = field(default_factory=list)
    frames: list[Frame] = field(default_factory=list)
    positions: dict[str, Node] = field(default_factory=dict)


def _scale(bands: list[_Band], rules: LayoutRules) -> float:
    """Return the width of one period: wide enough that every bar holds its label."""
    scale = PERIOD_PX
    for band in bands:
        for bar in band.bars:
            need = estimate_text_width(bar.label, rules, DEFAULT_FONT_SIZE_PX) + BAR_PADDING_PX
            scale = max(scale, (need + 2 * BAR_INSET_PX) / bar.length)
    return max(scale, MIN_PERIOD_PX)


def _header(names: list[str], state: _Layout) -> None:
    """Add one header cell per period."""
    for index, name in enumerate(names):
        state.nodes.append(
            Node(
                id=f"period-{index}",
                shape=Shape.PROCESS,
                x=state.left + index * state.period_px + BAR_INSET_PX,
                y=state.top,
                width=state.period_px - 2 * BAR_INSET_PX,
                height=HEADER_HEIGHT_PX,
                text=(name,),
                icon=None,
                tone=Tone.GRAY,
                number=None,
                font_size=DEFAULT_FONT_SIZE_PX,
            )
        )
    state.top += HEADER_HEIGHT_PX + FRAME_GAP_PX


def _place_band(band: _Band, rows: list[list[_Bar]], state: _Layout, width: float) -> None:
    """Add the bars of one band, row by row, and the frame around them."""
    framed = band.label is not None
    top = state.top
    y = top + (FRAME_TOP_PX if framed else 0)
    for row in rows:
        for bar in row:
            node = Node(
                id=bar.id,
                shape=Shape.PROCESS,
                x=state.left + bar.start * state.period_px + BAR_INSET_PX,
                y=y,
                width=bar.length * state.period_px - 2 * BAR_INSET_PX,
                height=BAR_HEIGHT_PX,
                text=(bar.label,),
                icon=None,
                tone=bar.tone or band.tone,
                number=None,
                font_size=DEFAULT_FONT_SIZE_PX,
            )
            state.nodes.append(node)
            state.positions[bar.id] = node
        y += BAR_HEIGHT_PX + ROW_GAP_PX
    bottom = y - ROW_GAP_PX + (FRAME_BOTTOM_PX if framed else 0)
    if framed:
        frame = Frame(
            f"band-{len(state.frames)}", state.left, top, width, bottom - top, band.label, band.tone
        )
        state.frames.append(frame)
    state.top = bottom + (FRAME_GAP_PX if framed else ROW_GAP_PX)


def _dependency(bar: _Bar, positions: dict[str, Node]) -> Edge:
    """Build the elbow line from the end of the task a bar follows to the start of the bar."""
    before, after = positions[bar.after or ""], positions[bar.id]
    start = (before.x + before.width, before.y + before.height / 2)
    end = (after.x, after.y + after.height / 2)
    middle = max(
        start[0] + DEPENDENCY_ELBOW_PX / 2,
        min(end[0] - DEPENDENCY_ELBOW_PX / 2, start[0] + DEPENDENCY_ELBOW_PX),
    )
    return Edge(
        id=f"after-{bar.id}",
        role=Role.NEXT,
        points=(start, (middle, start[1]), (middle, end[1]), end),
        label=None,
        source=before.id,
        target=after.id,
        head=Head.FILLED,
    )


def _build(kind: str, raw: object) -> Scene:
    """Check a timeline spec and lay it out as a scene."""
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    names = _periods(raw, read)
    reader = _gantt_bands if kind == GANTT else _roadmap_bands
    bands = reader(raw, len(names), read)
    _check_dependencies(bands, read)
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    if read.problems:
        raise SpecError(read.problems)
    rules = load_theme().layout
    top = rules.margin + (rules.title_block_height if title else 0)
    state = _Layout(rules, _scale(bands, rules), rules.margin, top)
    _header(names, state)
    width = state.period_px * len(names)
    for band in bands:
        rows = _pack(band.bars) if kind == ROADMAP else [[bar] for bar in band.bars]
        _place_band(band, rows, state, width)
    edges = tuple(
        _dependency(bar, state.positions) for band in bands for bar in band.bars if bar.after
    )
    scene = Scene(0, 0, title, description, tuple(state.frames), tuple(state.nodes), edges)
    return fit_canvas(scene)


def layout_gantt(raw: object) -> Scene:
    """Lay out a Gantt chart.

    Args:
        raw: The result of ``json.loads`` on a Gantt spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return _build(GANTT, raw)


def layout_roadmap(raw: object) -> Scene:
    """Lay out a roadmap.

    Args:
        raw: The result of ``json.loads`` on a roadmap spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return _build(ROADMAP, raw)
