"""Place the ends of every arrow on the frames and draw its route (design 02, Layout).

An arrow leaves the middle of the facing edge of a frame. When several arrows meet one edge they
spread out: two arrows on a side edge take its upper and lower third; on a top or bottom edge the
ones that go straight sit a fixed pitch apart in the middle, and the ones that turn in sit wider
apart beside them, as far as the edge allows. The order is chosen so that
arrows that share a side do not cross each other.
"""

from collections import defaultdict
from dataclasses import dataclass, replace
from enum import StrEnum
from itertools import pairwise

from ..model import ChipPlace, Node, Point, Shape
from ..screen_parts import chip_width, is_card
from ..theme import ScreenRules, Theme
from .screen_geometry import Geometry
from .screen_items import Cell
from .screen_lanes import LanePath, PortSide, Run
from .screen_plan import CHANNEL_ROUTES, Plan, RouteType, sides_of
from .screen_spec import TransitionKind

BACK_KINDS = (TransitionKind.BACK, TransitionKind.RETRY)
CHIP_CLEAR_PX = 4  # between an id chip and an arrow that enters beside it


class End(StrEnum):
    """Which end of an arrow."""

    SOURCE = "source"
    TARGET = "target"


@dataclass(frozen=True)
class Use:
    """One arrow end on one side of one frame."""

    index: int
    end: End
    plan: Plan
    partner: tuple[float, float]  # where the arrow heads from this frame, in cells
    own: Cell


Key = tuple[int, End]


def collect_uses(
    plans: list[Plan], cells: dict[str, Cell]
) -> dict[tuple[str, PortSide], list[Use]]:
    """Group the arrow ends by the frame side they meet."""
    uses: dict[tuple[str, PortSide], list[Use]] = defaultdict(list)
    for plan in plans:
        source, target = plan.transition.source, plan.transition.target
        pair = (cells[source], cells[target])
        side_a, side_b = sides_of(plan, pair)
        toward_target, toward_source = _toward(plan, pair)
        uses[(source, side_a)].append(Use(plan.index, End.SOURCE, plan, toward_target, pair[0]))
        uses[(target, side_b)].append(Use(plan.index, End.TARGET, plan, toward_source, pair[1]))
    return uses


def _toward(plan: Plan, pair: tuple[Cell, Cell]) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return where each end of an arrow heads: the other frame, or the first lane of a route."""
    if plan.lanes is None:
        return pair[1], pair[0]
    return plan.lanes.start_toward, plan.lanes.end_toward


def _is_far_outward(use: Use) -> bool:
    """Tell whether, on a top or bottom edge, the arrow that goes farthest takes the outer port.

    Only the target end of a zig does: there the farther arrow runs in the lower channel, so it
    must enter further out to avoid the nearer arrow's last leg.
    """
    return use.end is End.TARGET and use.plan.route in (RouteType.ZIG, RouteType.BEND)


def _across_offsets(uses: list[Use], width: float, rules: ScreenRules) -> dict[Key, float]:
    """Spread the arrows of a top or bottom edge: straight ones in the middle, others outward."""
    groups: dict[int, list[Use]] = defaultdict(list)
    for use in uses:
        groups[(use.partner[1] > use.own[1]) - (use.partner[1] < use.own[1])].append(use)
    straight = groups.get(0, [])
    base = (len(straight) - 1) / 2 * rules.port_pitch if straight else 0.0
    offsets: dict[Key, float] = {}
    for rank, use in enumerate(_by_kind(straight)):
        offsets[(use.index, use.end)] = (rank - (len(straight) - 1) / 2) * rules.port_pitch
    for sign in (-1, 1):
        ordered = sorted(groups.get(sign, []), key=_outward_key)
        pitch = _fit_pitch(len(ordered), base, width, rules)
        first = min(rules.port_pitch, pitch)  # one arrow alone stays where it always was
        for rank, use in enumerate(ordered):
            offsets[(use.index, use.end)] = sign * (base + first + rank * pitch)
    return offsets


def _outward_key(use: Use) -> tuple[int, int]:
    """Sort key that puts the arrow that takes the inner port first."""
    span = abs(use.partner[1] - use.own[1])
    return (span if _is_far_outward(use) else -span, use.index)


def _by_kind(uses: list[Use]) -> list[Use]:
    """Order arrows between the same two frames: forward first, back and retry after."""
    return sorted(uses, key=lambda use: (use.plan.transition.kind in BACK_KINDS, use.index))


def _fit_pitch(count: int, base: float, width: float, rules: ScreenRules) -> float:
    """Return the distance between ports that turn in: wide apart when the edge has room.

    Arrows that turn into an edge from one direction sit ``port_spread`` apart, so that their
    heads can be told apart; on a short edge the pitch shrinks so every port stays on it.
    """
    room = width / 2 - rules.port_clear - base
    return min(rules.port_spread, room / count) if count else rules.port_pitch


def _along_offsets(uses: list[Use], height: float) -> dict[Key, float]:
    """Spread the arrows of a side edge evenly: the upper and lower third for two."""
    ordered = sorted(
        uses, key=lambda use: (use.partner[0], use.plan.transition.kind in BACK_KINDS, use.index)
    )
    count = len(ordered)
    return {
        (use.index, use.end): height * (rank + 1) / (count + 1) - height / 2
        for rank, use in enumerate(ordered)
    }


def port_offsets(
    uses: dict[tuple[str, PortSide], list[Use]], nodes: dict[str, Node], theme: Theme
) -> dict[Key, float]:
    """Choose where on its side each arrow end sits, as an offset from the middle of the side.

    Args:
        uses: The arrow ends of each frame side.
        nodes: The nodes with their sizes.
        theme: The design tokens.

    Returns:
        ``(arrow index, end)`` to offset in pixels. A decision has only four tips, so its
        offsets are all zero.
    """
    offsets: dict[Key, float] = {}
    for (node_id, side), group in uses.items():
        node = nodes[node_id]
        if node.shape is Shape.DECISION:
            offsets.update({(use.index, use.end): 0.0 for use in group})
        elif side in (PortSide.NORTH, PortSide.SOUTH):
            offsets.update(_across_offsets(group, node.width, theme.screen))
        else:
            offsets.update(_along_offsets(group, node.height))
    return offsets


def place_chips(
    nodes: dict[str, Node],
    uses: dict[tuple[str, PortSide], list[Use]],
    offsets: dict[Key, float],
    theme: Theme,
) -> tuple[dict[str, Node], dict[Key, float]]:
    """Put the id chip of each frame where no arrow runs through it (design 02, Layout).

    The chip stays above the left corner when it can. Otherwise it goes below the frame, or above
    the right corner, and when none of these is free the arrows of the top edge slide to the right
    of the chip.

    Args:
        nodes: The placed nodes.
        uses: The arrow ends of each frame side.
        offsets: Where each arrow end sits on its side.
        theme: The design tokens.

    Returns:
        The nodes with their chip place, and the offsets, moved where the arrows slid.
    """
    placed, moved = dict(nodes), dict(offsets)
    for node_id, node in nodes.items():
        view = node.screen
        if view is None or is_card(view):
            continue
        top = _ports(uses.get((node_id, PortSide.NORTH), []), node, offsets)
        bottom = _ports(uses.get((node_id, PortSide.SOUTH), []), node, offsets)
        reach = chip_width(view.code, theme) + CHIP_CLEAR_PX
        place = _chip_place(top, bottom, (reach, node.width))
        placed[node_id] = replace(node, screen=replace(view, chip_place=place or ChipPlace.ABOVE))
        if place is None:
            moved.update(
                _slid(uses.get((node_id, PortSide.NORTH), []), moved, (reach, node, theme))
            )
    return placed, moved


def _ports(group: list[Use], node: Node, offsets: dict[Key, float]) -> list[float]:
    """Return where along its edge each arrow end of a side sits, from the left corner."""
    return [node.width / 2 + offsets[(use.index, use.end)] for use in group]


def _chip_place(
    top: list[float], bottom: list[float], sizes: tuple[float, float]
) -> ChipPlace | None:
    """Choose where the chip goes: None when every place is crossed by an arrow."""
    reach, width = sizes
    if all(x >= reach for x in top):
        return ChipPlace.ABOVE
    if all(x >= reach for x in bottom):
        return ChipPlace.BELOW
    if all(x <= width - reach for x in top):
        return ChipPlace.ABOVE_RIGHT
    return None


def _slid(
    group: list[Use], offsets: dict[Key, float], context: tuple[float, Node, Theme]
) -> dict[Key, float]:
    """Slide the arrows of a top edge to the right of the chip, when they all fit there."""
    reach, node, theme = context
    ports = _ports(group, node, offsets)
    shift = reach - min(ports, default=reach)
    if shift <= 0 or max(ports) + shift > node.width - theme.screen.port_clear:
        return {}
    return {(use.index, use.end): offsets[(use.index, use.end)] + shift for use in group}


def port_point(node: Node, side: PortSide, offset: float) -> Point:
    """Return the point of a frame side an arrow meets, ``offset`` from the middle of the side."""
    centre_x, centre_y = node.x + node.width / 2, node.y + node.height / 2
    if side is PortSide.NORTH:
        return (centre_x + offset, node.y)
    if side is PortSide.SOUTH:
        return (centre_x + offset, node.y + node.height)
    if side is PortSide.EAST:
        return (node.x + node.width, centre_y + offset)
    return (node.x, centre_y + offset)


def route_points(plan: Plan, ends: tuple[Point, Point], geometry: Geometry) -> tuple[Point, ...]:
    """Return the points of an arrow from its two ends.

    Args:
        plan: The plan, which says the shape and the channel.
        ends: The point on the source and the point on the target.
        geometry: The rows, columns and channels.

    Returns:
        The route, without repeated points.
    """
    start, end = ends
    if plan.route in CHANNEL_ROUTES:
        level = _level(plan, geometry)
        points = [start, (start[0], level), (end[0], level), end]
    elif plan.route is RouteType.BEND:
        points = [start, (end[0], start[1]), end]
    elif plan.route is RouteType.ELBOW:
        points = [start, (start[0], end[1]), end]
    elif plan.lanes is not None:
        points = _lane_points(plan.lanes, ends, geometry)
    elif plan.route is RouteType.VERTICAL and start[0] != end[0]:
        middle = (start[1] + end[1]) / 2
        points = [start, (start[0], middle), (end[0], middle), end]
    elif plan.route is RouteType.HORIZONTAL and start[1] != end[1]:
        middle = (start[0] + end[0]) / 2
        points = [start, (middle, start[1]), (middle, end[1]), end]
    else:
        points = [start, end]
    return _without_repeats(points)


def _lane_points(path: LanePath, ends: tuple[Point, Point], geometry: Geometry) -> list[Point]:
    """Return the points of a route in lanes: the ends, and a corner where two runs meet."""
    start, end = ends
    runs = path.runs
    first, last = runs[0], runs[-1]
    points = [start, _corner(first, start, geometry)]
    for run, following in pairwise(runs):
        points.append(_meeting(run, following, geometry))
    points.extend([_corner(last, end, geometry), end])
    return points


def _corner(run: Run, port: Point, geometry: Geometry) -> Point:
    """Return where the stub from a frame side meets the first or the last run."""
    if run.is_horizontal:
        return (port[0], _line_of(run, geometry))
    return (_line_of(run, geometry), port[1])


def _line_of(run: Run, geometry: Geometry) -> float:
    """Return where a run is: the y of a horizontal one, the x of a vertical one."""
    if run.is_horizontal:
        return geometry.channel_y(run.lane, run.slot)
    return geometry.lane_x(run.band, run.lane, run.slot)


def _meeting(run: Run, following: Run, geometry: Geometry) -> Point:
    """Return the corner where a run turns into the next one."""
    if run.is_horizontal:
        return (_line_of(following, geometry), _line_of(run, geometry))
    return (_line_of(run, geometry), _line_of(following, geometry))


def _level(plan: Plan, geometry: Geometry) -> float:
    """Return the y of the line an arrow runs along: a channel, or a strip above a row."""
    if plan.route is RouteType.STRIP:
        return geometry.strip_y(plan.gap, plan.slot)
    return geometry.channel_y(plan.gap, plan.slot)


def _without_repeats(points: list[Point]) -> tuple[Point, ...]:
    """Drop a point that is the same as the one before it."""
    kept = [points[0]]
    kept.extend(point for point in points[1:] if point != kept[-1])
    return tuple(kept)
