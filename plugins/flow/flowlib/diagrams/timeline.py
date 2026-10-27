"""The roadmap: items packed in lanes over named periods. The Gantt chart is in ``gantt``.

The JSON format::

    {"type": "roadmap", "title": "...", "desc": "...", "periods": ["Q1", "Q2", "Q3", "Q4"],
     "lanes": [{"label", "tone", "items": [{"label", "start": 0, "length": 2, "detail", "tone"}]}]}

``start`` counts periods from 0 and ``length`` is a number of periods. Dates are not read: name
the periods yourself.
"""

from dataclasses import dataclass, field
from typing import Any

from ..canvas import fit_canvas
from ..model import DEFAULT_FONT_SIZE_PX, Frame, Node, Scene, Shape, Tone
from ..reader import Reader, SpecError
from ..sizing import estimate_text_width
from ..theme import LayoutRules, load_theme

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
SPEC_KEYS = {"type", "title", "desc", "periods", "lanes"}
LANE_KEYS = {"label", "tone", "items"}
ITEM_KEYS = {"id", "label", "start", "length", "detail", "tone"}


@dataclass
class _Bar:
    """One bar on the timeline, before it has a position."""

    id: str
    label: str
    start: int
    length: int
    tone: Tone | None
    detail: str = ""


@dataclass
class _Band:
    """A lane: the bars drawn in one frame."""

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
    """Build one bar from an item, checking that it fits the periods."""
    if not isinstance(raw, dict):
        read.report(where, "must be an object")
        return None
    read.check_keys(raw, ITEM_KEYS, where)
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
    )


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
        y += BAR_HEIGHT_PX + ROW_GAP_PX
    bottom = y - ROW_GAP_PX + (FRAME_BOTTOM_PX if framed else 0)
    if framed:
        frame = Frame(
            f"band-{len(state.frames)}", state.left, top, width, bottom - top, band.label, band.tone
        )
        state.frames.append(frame)
    state.top = bottom + (FRAME_GAP_PX if framed else ROW_GAP_PX)


def layout_roadmap(raw: object) -> Scene:
    """Lay out a roadmap.

    Args:
        raw: The result of ``json.loads`` on a roadmap spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    names = _periods(raw, read)
    bands = _roadmap_bands(raw, len(names), read)
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    if read.problems:
        raise SpecError(read.problems)
    rules = load_theme().layout
    top = rules.margin + (rules.title_block_height if title else 0)
    state = _Layout(rules, _scale(bands, rules), rules.margin, top)
    _header(names, state)
    width = state.period_px * len(names)
    for band in bands:
        _place_band(band, _pack(band.bars), state, width)
    scene = Scene(0, 0, title, description, tuple(state.frames), tuple(state.nodes), ())
    return fit_canvas(scene)
