"""The screen flow: device frames at four fidelity levels, joined by ``trigger [guard] / effect``.

A spec that uses the keys of design 02 (see ``screen_spec``) is laid out on a grid of rows and
columns, in dashed tinted zones, with entry points at the left, a tab bar drawn once as a bus and
a table for conditions that are written as codes. A spec that uses none of them is drawn as plain
boxes, as in earlier versions.
"""

from dataclasses import dataclass, replace

from ..canvas import fit_canvas
from ..check import chip_rect
from ..model import (
    Edge,
    Frame,
    Head,
    Node,
    Point,
    Role,
    Scene,
    Tone,
)
from ..theme import Theme, load_theme
from . import catalog, graph
from .screen_chips import Crowd, blocks_of, choose_spot, lines_of
from .screen_geometry import Geometry, Sizing, compute_geometry
from .screen_items import assign_cells, build_nodes, densify
from .screen_labels import Caption, assign_codes, caption_of, trigger_label
from .screen_plan import (
    ENTRY_STACK_GAP_PX,
    ENTRY_ZONE_ID,
    Grid,
    Plan,
    RouteType,
    ZoneExtent,
    channel_counts,
    lane_counts,
    make_grid,
    plan_routes,
    sides_of,
    split_bands,
    strip_counts,
    zig_counts,
    zone_extents,
)
from .screen_routes import (
    BACK_KINDS,
    End,
    collect_uses,
    place_chips,
    port_offsets,
    port_point,
    route_points,
)
from .screen_spec import (
    Bus,
    FlowSpec,
    Item,
    ItemKind,
    Transition,
    TransitionKind,
    parse_flow,
    uses_screen_features,
)
from .screen_table import CodedArrow, condition_row, conditions_table

ENTRY_ZONE_LABEL = "Entry points"
BUS_CHIP_RISE_PX = 18


@dataclass(frozen=True)
class Build:
    """Everything the final steps of a layout share."""

    spec: FlowSpec
    theme: Theme
    grid: Grid
    plans: list[Plan]
    captions: dict[int, Caption]
    geometry: Geometry


def layout_raw(raw: object) -> Scene:
    """Lay out a screen flow from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on the spec.

    Returns:
        The scene. A spec without the keys of design 02 is drawn as plain boxes.

    Raises:
        SpecError: If the spec is not valid.
    """
    if not uses_screen_features(raw):
        return graph.layout_with(catalog.SCREEN)(raw)
    return build_scene(parse_flow(raw))


def build_scene(spec: FlowSpec) -> Scene:
    """Place the screens, route the arrows and draw the zones of a screen flow.

    Args:
        spec: The parsed spec.

    Returns:
        The scene, with its canvas sized.
    """
    theme = load_theme()
    nodes = build_nodes(spec, theme)
    cells, rows, columns = densify(assign_cells(spec))
    grid = make_grid(cells, rows, columns)
    plans = plan_routes(spec, grid)
    codes = assign_codes(spec.transitions, spec.conditions)
    captions = {i: caption_of(t, codes.get(i)) for i, t in enumerate(spec.transitions)}
    sizing = _sizing(spec, theme, (nodes, grid), (plans, captions))
    build = Build(spec, theme, grid, plans, captions, compute_geometry(sizing))
    placed = _place_nodes(nodes, build)
    frames = _zone_frames(placed, build)
    routes, placed = _routes(placed, build)
    edges = _labelled(routes, _bus_edges(placed, build), (placed, frames), build)
    table = _conditions_table(placed, frames, build, codes)
    scene = Scene(
        0, 0, spec.title, spec.description, tuple(frames), (*placed.values(), *table), tuple(edges)
    )
    return fit_canvas(scene)


def _sizing(
    spec: FlowSpec,
    theme: Theme,
    layout: tuple[dict[str, Node], Grid],
    routes: tuple[list[Plan], dict[int, Caption]],
) -> Sizing:
    """Gather what the geometry needs: sizes, plans, zones, channels, bands and the origin."""
    nodes, grid = layout
    plans, captions = routes
    rules = theme.screen
    zones = zone_extents(spec, grid)
    bus_gaps = [grid.cells[bus.targets[0]][0] for bus in spec.buses]
    extra = {gap: bus_gaps.count(gap) for gap in set(bus_gaps)}
    channels = channel_counts(plans, grid.rows, {})
    strips = strip_counts(plans, grid.rows, extra)
    left = theme.layout.margin + (rules.zone_pad_x if _begins_at_first_column(zones) else 0)
    top = theme.layout.margin + (theme.layout.title_block_height if spec.title else 0)
    bands = split_bands(spec, grid)
    zigs = zig_counts(plans, grid.rows)
    lanes = lane_counts(plans)
    return Sizing(
        nodes, grid, plans, captions, zones, rules, channels, zigs, strips, bands, lanes, top, left
    )


def _begins_at_first_column(zones: dict[str, ZoneExtent]) -> bool:
    """Tell whether a zone starts at the first column, which then needs room for its border."""
    return any(extent.first_column == 0 for extent in zones.values())


def _place_nodes(nodes: dict[str, Node], build: Build) -> dict[str, Node]:
    """Set the position of every node: centred on its column, and on the centre line of its row."""
    geometry = build.geometry
    placed: dict[str, Node] = {}
    for cell, ids in build.grid.occupied.items():
        row, column = cell
        stack = sum(nodes[i].height for i in ids) + (len(ids) - 1) * ENTRY_STACK_GAP_PX
        cursor = geometry.row_centre(row) - stack / 2
        for item_id in ids:
            node = nodes[item_id]
            x = geometry.column_centre(row, column) - node.width / 2
            placed[item_id] = replace(node, x=x, y=cursor)
            cursor += node.height + ENTRY_STACK_GAP_PX
    return {item_id: placed[item_id] for item_id in nodes}


def _role_of(transition: Transition) -> Role:
    """Pick the line role: main blue, failure rose, back and retry dashed, a guard green."""
    if transition.kind is TransitionKind.MAIN:
        return Role.MAIN
    if transition.kind is TransitionKind.FAILURE:
        return Role.NO
    if transition.kind in BACK_KINDS:
        return Role.BACK
    return Role.YES if transition.guard else Role.NEXT


def _routes(
    nodes: dict[str, Node], build: Build
) -> tuple[list[tuple[Plan, tuple[Point, ...]]], dict[str, Node]]:
    """Route every transition; returns the routes and the nodes with their id chips placed."""
    uses = collect_uses(build.plans, build.grid.cells)
    offsets = port_offsets(uses, nodes, build.theme)
    nodes, offsets = place_chips(nodes, uses, offsets, build.theme)
    return [(plan, _points(plan, (nodes, offsets), build)) for plan in build.plans], nodes


def _points(
    plan: Plan,
    placed: tuple[dict[str, Node], dict[tuple[int, End], float]],
    build: Build,
) -> tuple[Point, ...]:
    """Route one transition between the sides of its two frames."""
    nodes, offsets = placed
    transition = plan.transition
    cells = build.grid.cells
    sides = sides_of(plan, (cells[transition.source], cells[transition.target]))
    ends = tuple(
        port_point(nodes[node_id], side, offsets[(plan.index, end)])
        for node_id, side, end in (
            (transition.source, sides[0], End.SOURCE),
            (transition.target, sides[1], End.TARGET),
        )
    )
    return route_points(plan, ends, build.geometry)


def _labelled(
    routes: list[tuple[Plan, tuple[Point, ...]]],
    buses: list[Edge],
    around: tuple[dict[str, Node], list[Frame]],
    build: Build,
) -> list[Edge]:
    """Place the words of every arrow clear of frames, chips and other lines; returns the edges."""
    nodes, frames = around
    rules = build.theme.layout
    crowd = Crowd(blocks_of(nodes, frames, build.theme))
    crowd.blocks.extend(chip_rect(bus.label, rules) for bus in buses if bus.label)
    crowd.lines = lines_of([points for _, points in routes] + [bus.points for bus in buses])
    edges: list[Edge] = []
    seen: set[str] = set()
    for number, (plan, points) in enumerate(routes):
        caption = build.captions[plan.index]
        spot = choose_spot(number, points, caption, (crowd, build.theme))
        crowd.blocks.extend(spot.rects)
        transition = plan.transition
        edge_id = _unique_id(f"{transition.source}>{transition.target}", seen)
        edges.append(
            Edge(
                id=edge_id,
                role=_role_of(transition),
                points=points,
                label=spot.chip,
                source=transition.source,
                target=transition.target,
                head=Head.FILLED,
                dashed=_is_undecided(nodes[transition.target]),
                extras=spot.texts,
            )
        )
    return edges + buses


def _unique_id(wanted: str, seen: set[str]) -> str:
    """Return an edge id that has not been used, adding a number when it has."""
    edge_id, number = wanted, 1
    while edge_id in seen:
        number += 1
        edge_id = f"{wanted}#{number}"
    seen.add(edge_id)
    return edge_id


def _is_undecided(node: Node) -> bool:
    """Tell whether a node is an undecided screen, which is entered by a dashed arrow."""
    return node.screen is not None and node.screen.is_undecided


def _bus_edges(nodes: dict[str, Node], build: Build) -> list[Edge]:
    """Draw each tab bar once: one line above the tabs, with an arrow down into each."""
    edges: list[Edge] = []
    used: dict[int, int] = {}
    for number, bus in enumerate(build.spec.buses):
        tabs = [nodes[target] for target in bus.targets]
        gap = build.grid.cells[bus.targets[0]][0]
        taken = sum(1 for p in build.plans if p.route is RouteType.STRIP and p.gap == gap)
        slot = taken + used.get(gap, 0)
        used[gap] = used.get(gap, 0) + 1
        edges.extend(_one_bus(number, bus, tabs, build.geometry.strip_y(gap, slot)))
    return edges


def _one_bus(number: int, bus: Bus, tabs: list[Node], level: float) -> list[Edge]:
    """Build the line, its chip and the arrow into each tab of one bus."""
    centres = [tab.x + tab.width / 2 for tab in tabs]
    middle = (min(centres) + max(centres)) / 2
    caption = Caption(bus.trigger, None, None, None, False)
    label = trigger_label(caption, (middle, level - BUS_CHIP_RISE_PX))
    line = Edge(
        id=f"bus{number}",
        role=Role.NEXT,
        points=((min(centres), level), (max(centres), level)),
        label=label,
        source=None,
        target=None,
        head=Head.NONE,
    )
    drops = [
        Edge(
            id=f"bus{number}>{tab.id}",
            role=Role.NEXT,
            points=((x, level), (x, tab.y)),
            label=None,
            source=None,
            target=tab.id,
        )
        for tab, x in zip(tabs, centres, strict=True)
    ]
    return [line, *drops]


def _zone_frames(nodes: dict[str, Node], build: Build) -> list[Frame]:
    """Draw each zone as a dashed tinted frame with a pill label around its members."""
    rules = build.theme.screen
    members: dict[str, list[Node]] = {}
    for item in build.spec.items:
        zone = ENTRY_ZONE_ID if item.kind is ItemKind.ENTRY else item.zone
        if zone:
            members.setdefault(zone, []).append(nodes[item.id])
    labels = {z.id: (z.label, z.tone) for z in build.spec.zones}
    labels[ENTRY_ZONE_ID] = (ENTRY_ZONE_LABEL, Tone.GREEN)
    frames = []
    for zone_id, group in members.items():
        left = min(n.x for n in group) - rules.zone_pad_x
        first_row = min(build.grid.cells[n.id][0] for n in group)
        strips = build.geometry.strips[first_row] * rules.channel_pitch
        top = min(n.y for n in group) - rules.zone_pad_top - strips
        right = max(n.x + n.width for n in group) + rules.zone_pad_x
        bottom = max(n.y + n.height for n in group) + rules.zone_pad_bottom
        label, tone = labels[zone_id]
        frames.append(Frame(f"zone-{zone_id}", left, top, right - left, bottom - top, label, tone))
    return frames


def _name_of(item: Item) -> str:
    """Return how a table row names an item: a screen by its code, anything else by its name."""
    if item.view is not None:
        return item.view.code
    return item.name


def _conditions_table(
    nodes: dict[str, Node], frames: list[Frame], build: Build, codes: dict[int, str]
) -> list[Node]:
    """Make the table of coded conditions, below the diagram; none when no arrow is coded."""
    if not codes:
        return []
    rules = build.theme.layout
    items = {item.id: item for item in build.spec.items}
    rows = tuple(
        condition_row(_coded_arrow(build.spec.transitions[index], code, items))
        for index, code in codes.items()
    )
    bottoms = [n.y + n.height for n in nodes.values()] + [f.y + f.height for f in frames]
    rights = [n.x + n.width for n in nodes.values()] + [f.x + f.width for f in frames]
    top = max(bottoms) + build.theme.screen.table_gap
    return [conditions_table(rows, (rules.margin, top), max(rights) - rules.margin, rules)]


def _coded_arrow(transition: Transition, code: str, items: dict[str, Item]) -> CodedArrow:
    """Describe a coded transition for its row of the conditions table."""
    return CodedArrow(
        code=code,
        source=_name_of(items[transition.source]),
        target=_name_of(items[transition.target]),
        trigger=transition.trigger.text if transition.trigger else "",
        guard=transition.guard,
        effect=transition.effect,
    )
