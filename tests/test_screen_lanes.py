"""Tests for the free lanes of a screen flow, the chips off frames, and the automatic grid."""

import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib.check import Code, Severity, check_scene, chip_rect, node_rect  # noqa: E402
from flowlib.diagrams import layout  # noqa: E402
from flowlib.diagrams.screen_items import assign_cells  # noqa: E402
from flowlib.diagrams.screen_lanes import LanePath, PortSide, Run, assign_slots  # noqa: E402
from flowlib.diagrams.screen_spec import parse_flow  # noqa: E402
from flowlib.model import Scene  # noqa: E402
from flowlib.theme import load_theme  # noqa: E402

TALL_COLUMN = 5
LARGE_FLOW_WARNING_LIMIT = 45


def column_of(count: int, **keys: object) -> list[dict[str, object]]:
    """Make ``count`` screens one above the other in column 0."""
    return [
        {"id": f"s{row}", "label": f"S{row}", "at": [row, 0], "size": "mini", **keys}
        for row in range(count)
    ]


def flow(screens: list[dict[str, object]], taps: list[dict[str, object]], **top: object) -> Scene:
    """Lay out a small screen flow."""
    return layout({"type": "screen", "screens": screens, "taps": taps, **top})


def codes_of(scene: Scene, severity: Severity) -> list[Code]:
    """Return the codes of the findings of one severity."""
    return [f.code for f in check_scene(scene) if f.severity is severity]


def test_a_return_across_three_frames_goes_around_them() -> None:
    """A back arrow from the fifth screen to the first leaves the column and crosses no frame."""
    taps = [{"from": f"s{row}", "to": f"s{row + 1}"} for row in range(TALL_COLUMN - 1)]
    taps.append({"from": "s4", "to": "s0", "kind": "back", "trigger": "tap Back"})
    scene = flow(column_of(TALL_COLUMN), taps)
    back = scene.edges[-1]
    nodes = scene.nodes
    assert Code.LINE_THROUGH_NODE not in codes_of(scene, Severity.ERROR)
    left = min(n.x for n in nodes)
    right = max(n.x + n.width for n in nodes)
    assert any(x < left or x > right for x, _ in back.points)


def test_two_parallel_returns_do_not_overlap() -> None:
    """Two returns over the same frames run in lanes of their own."""
    taps = [{"from": f"s{row}", "to": f"s{row + 1}"} for row in range(TALL_COLUMN - 1)]
    taps.append({"from": "s4", "to": "s0", "kind": "back", "trigger": "tap Back"})
    taps.append({"from": "s3", "to": "s1", "kind": "back", "trigger": "tap Undo"})
    scene = flow(column_of(TALL_COLUMN), taps)
    verticals = []
    for edge in scene.edges[-2:]:
        longest = max(
            zip(edge.points, edge.points[1:], strict=False), key=lambda s: abs(s[0][1] - s[1][1])
        )
        verticals.append(longest[0][0])
    assert abs(verticals[0] - verticals[1]) >= 1
    assert Code.LINES_OVERLAP not in codes_of(scene, Severity.WARNING)
    assert Code.LINE_THROUGH_NODE not in codes_of(scene, Severity.ERROR)


def test_runs_that_overlap_take_different_slots_and_others_share() -> None:
    """Slots are given by first fit: runs that do not meet may take the same one."""

    def path(low: float, high: float, bias: int = 0) -> LanePath:
        run = Run(is_horizontal=True, lane=1, band=0, low=low, high=high, bias=bias)
        return LanePath(PortSide.NORTH, PortSide.NORTH, (run,), (0, 0), (0, 0))

    slotted = assign_slots({0: path(0, 3), 1: path(1, 2), 2: path(5, 6)}, {})
    slots = {index: p.runs[0].slot for index, p in slotted.items()}
    assert slots[0] != slots[1]
    assert slots[2] == slots[0]


def test_a_run_fed_from_above_takes_a_slot_above_one_fed_from_below() -> None:
    """The legs at the ends of a route do not cross the lanes of other routes."""

    def path(bias: int) -> LanePath:
        run = Run(is_horizontal=True, lane=1, band=0, low=0, high=2, bias=bias)
        return LanePath(PortSide.NORTH, PortSide.NORTH, (run,), (0, 0), (0, 0))

    slotted = assign_slots({0: path(1), 1: path(-1)}, {1: 2})
    assert slotted[1].runs[0].slot < slotted[0].runs[0].slot
    assert slotted[1].runs[0].slot >= 2


def test_words_stay_off_the_frames_and_off_each_other() -> None:
    """A chip never covers a frame or another chip, even where a line is long."""
    taps = [{"from": f"s{row}", "to": f"s{row + 1}", "trigger": f"tap {row}"} for row in range(4)]
    taps.append({"from": "s4", "to": "s0", "kind": "back", "trigger": "tap Back"})
    scene = flow(column_of(TALL_COLUMN), taps)
    rules = load_theme().layout
    chips = [chip_rect(edge.label, rules) for edge in scene.edges if edge.label]
    for chip in chips:
        assert not any(chip.overlaps(node_rect(node)) for node in scene.nodes)
    for number, first in enumerate(chips):
        assert not any(first.overlaps(second) for second in chips[number + 1 :])


def _zone_spec(count: int) -> dict[str, object]:
    """Make a zone of ``count`` screens in a chain, with no ``at``."""
    screens = [{"id": f"s{n}", "label": f"S{n}", "zone": "z", "size": "mini"} for n in range(count)]
    taps = [{"from": f"s{n}", "to": f"s{n + 1}"} for n in range(count - 1)]
    return {
        "type": "screen",
        "zones": [{"id": "z", "label": "Zone"}],
        "screens": screens,
        "taps": taps,
    }


def test_a_zone_reads_left_to_right_and_wraps_in_whole_rows() -> None:
    """Seven screens of one zone fill two rows of four and three, each row from the left."""
    cells = assign_cells(parse_flow(_zone_spec(7)))
    assert [cells[f"s{n}"] for n in range(7)] == [
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 0),
        (1, 1),
        (1, 2),
    ]


def test_zones_without_at_are_blocks_that_start_at_the_left_of_their_shelf() -> None:
    """A second zone never starts in the middle of the first one's rows."""
    raw = _zone_spec(6)
    raw["zones"].append({"id": "y", "label": "Other"})
    for number in range(6, 12):
        raw["screens"].append({"id": f"s{number}", "label": f"S{number}", "zone": "y"})
        raw["taps"].append({"from": f"s{number - 1}", "to": f"s{number}"})
    cells = assign_cells(parse_flow(raw))
    first = {cells[f"s{n}"] for n in range(6)}
    second = {cells[f"s{n}"] for n in range(6, 12)}
    assert not first & second
    assert min(row for row, _ in second) >= 0
    assert len({cells[f"s{n}"][0] for n in range(6, 12)}) >= 2


def test_the_large_example_has_no_error_with_or_without_at() -> None:
    """The 52-screen ride-hailing flow: no line through a frame, no chip on a frame."""
    raw = json.loads((EXAMPLES / "ride-screen-flow.spec.json").read_text())
    with_at = layout(json.loads(json.dumps(raw)))
    assert codes_of(with_at, Severity.ERROR) == []
    assert len(codes_of(with_at, Severity.WARNING)) < LARGE_FLOW_WARNING_LIMIT
    for screen_item in raw["screens"]:
        screen_item.pop("at", None)
    without_at = layout(raw)
    assert codes_of(without_at, Severity.ERROR) == []
