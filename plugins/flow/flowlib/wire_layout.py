"""Place the blocks of a wireframe screen on its grid and draw the device around them.

A block is placed by a row, a column and a span of a 12 column grid, never by coordinates
(design 10 section 8). A row is as tall as its tallest block; a block that spans several rows
takes their height. The navbar, the sidebar and the bottom navigation sit on the edges of the
screen, blocks that say ``bottom`` are pinned above its foot, and overlays lie on top.
"""

import re
from dataclasses import dataclass, field, replace

from .model import BlockAnchor, BlockKind, Corner, Device, ScreenView, WireBadge, WireBlock
from .screen_part import Align, Bounds, Part
from .theme import Theme
from .wire_blocks import OVERLAY_KINDS, STRETCH_KINDS, block_type
from .wire_kit import HALF, Drawn, Ink, Line, WireContext, circle, label, pill, rect
from .wire_state import draw_overlay, scrim_part

FULL_SPAN = 12
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
SIDE_OUTWARD = {Corner.LEFT: -1, Corner.RIGHT: 1}  # a side badge sits wholly outside its part
STATUS_TIME = "10:24"
LABEL_FLAG = "label"
CORNER_POINTS: dict[Corner, tuple[float, float]] = {
    Corner.TOP_LEFT: (0, 0),
    Corner.TOP_RIGHT: (1, 0),
    Corner.BOTTOM_LEFT: (0, 1),
    Corner.BOTTOM_RIGHT: (1, 1),
    Corner.LEFT: (0, 0.5),
    Corner.RIGHT: (1, 0.5),
    Corner.TOP: (0.5, 0),
    Corner.BOTTOM: (0.5, 1),
}  # as fractions of the width and the height of the part a badge sits on


@dataclass
class WirePlan:
    """The parts of a drawn screen, and where each block and its named parts ended up."""

    parts: list[Part] = field(default_factory=list)
    drawn: dict[int, Drawn] = field(default_factory=dict)
    boxes: dict[int, Bounds] = field(default_factory=dict)
    content_count: int = 0  # the parts before the badges: what a badge must not cover
    floor: float = 0  # the lowest y the blocks of the grid may reach


@dataclass(frozen=True)
class Slot:
    """Where a block sits on the grid: its index in the screen, its row, column and spans."""

    index: int
    row: int
    col: int
    span: int
    rows: int


@dataclass
class Screen:
    """The screen being drawn: its view, its context, its size and what is left to fill."""

    view: ScreenView
    ctx: WireContext
    width: float
    height: float
    plan: WirePlan
    top: float = 0
    left: float = 0
    floor: float = 0

    @property
    def margin(self) -> float:
        """Return the margin around the content on this device."""
        return self.ctx.rules.margin[self.view.device.value]

    @property
    def inner_left(self) -> float:
        """Return the x where the device border ends."""
        return self.ctx.rules.border

    @property
    def inner_width(self) -> float:
        """Return the width inside the device border."""
        return self.width - 2 * self.ctx.rules.border


def natural_size(view: ScreenView, theme: Theme) -> tuple[float, float]:
    """Return the width and height of a wireframe screen at real size, from its device.

    Args:
        view: What the screen shows.
        theme: The design tokens.

    Returns:
        The size of the frame in pixels, before it is shrunk by ``view.scale``.
    """
    return theme.wire.device[view.device.value]


def plan_screen(
    view: ScreenView, theme: Theme, size: tuple[float, float] | None = None
) -> WirePlan:
    """Lay out a wireframe screen and list its parts, back to front, at real size.

    Args:
        view: A screen with blocks.
        theme: The design tokens.
        size: The frame size in pixels when it is not the size of the device, as for a
            responsive page.

    Returns:
        The plan: the parts to draw and the boxes of the blocks, for the badges and the checks.
    """
    ctx = WireContext(theme, view.device, view.is_plain)
    width, height = size or natural_size(view, theme)
    plan = WirePlan()
    screen = Screen(view, ctx, width, height, plan)
    if view.is_bare:
        return _plan_bare(screen)
    plan.parts.extend(_device_parts(screen))
    groups = _split(view.blocks)
    _place_edges(screen, groups[0])
    _place_grid(screen, groups[1])
    _place_pinned(screen, groups[2])
    _place_overlays(screen, groups[3])
    plan.content_count = len(plan.parts)
    plan.floor = screen.floor
    _add_badges(screen)
    plan.parts.append(_frame_border(screen))
    plan.parts.extend(_caption_parts(screen))
    return plan


def _plan_bare(screen: Screen) -> WirePlan:
    """Draw blocks with no device around them: each fills the node, which has no border."""
    box = (0, 0, screen.width, screen.height)
    screen.plan.parts.append(rect(box, None))
    for index, block in enumerate(screen.view.blocks):
        _put(screen, index, block, box)
    return screen.plan


def scale_parts(parts: list[Part], factor: float) -> list[Part]:
    """Shrink every part of a drawing by a factor, for a screen drawn small in a flow.

    Args:
        parts: The parts at real size.
        factor: The scale; 1 returns the parts as they are.

    Returns:
        New parts with the box, the font, the border, the corners and the path scaled.
    """
    if factor == 1:
        return parts
    return [_scaled(part, factor) for part in parts]


def _scaled(part: Part, factor: float) -> Part:
    """Scale one part."""
    path = NUMBER.sub(lambda found: f"{float(found.group()) * factor:g}", part.path)
    return replace(
        part,
        bounds=tuple(value * factor for value in part.bounds),
        stroke_width=part.stroke_width * factor,
        radius=part.radius * factor,
        font_size=part.font_size * factor,
        path=path,
    )


def _split(
    blocks: tuple[WireBlock, ...],
) -> tuple[list[tuple[int, WireBlock]], ...]:
    """Sort the blocks into edge, grid, pinned and overlay blocks, keeping their indices."""
    edges, flowing, pinned, overlays = [], [], [], []
    for index, block in enumerate(blocks):
        if block.kind in OVERLAY_KINDS:
            overlays.append((index, block))
        elif block.kind in (BlockKind.NAVBAR, BlockKind.SIDEBAR, BlockKind.BOTTOM_NAV):
            edges.append((index, block))
        elif block.anchor is BlockAnchor.BOTTOM:
            pinned.append((index, block))
        else:
            flowing.append((index, block))
    return edges, flowing, pinned, overlays


def _put(screen: Screen, index: int, block: WireBlock, box: Bounds) -> None:
    """Draw a block in a box and remember where it went."""
    drawn = block_type(block.kind).draw(block, box, screen.ctx)
    screen.plan.parts.extend(drawn.parts)
    screen.plan.drawn[index] = drawn
    screen.plan.boxes[index] = box


def _height_of(screen: Screen, block: WireBlock, width: float) -> float:
    """Return how tall a block is at a width."""
    return block_type(block.kind).height(block, width, screen.ctx)


def _place_edges(screen: Screen, blocks: list[tuple[int, WireBlock]]) -> None:
    """Place the navbar at the top, the sidebar at the left and the bottom nav at the foot."""
    rules = screen.ctx.rules
    is_wide = screen.view.device is Device.DESKTOP or screen.view.is_plain
    screen.top = rules.browser_bar if is_wide else rules.status_height
    if screen.view.is_plain:
        screen.top = screen.inner_left
    screen.floor = screen.height - (screen.inner_left if is_wide else rules.foot)
    by_kind = {block.kind: (index, block) for index, block in blocks}
    if BlockKind.NAVBAR in by_kind:
        _place_navbar(screen, *by_kind[BlockKind.NAVBAR])
    if BlockKind.BOTTOM_NAV in by_kind:
        _place_bottom_nav(screen, *by_kind[BlockKind.BOTTOM_NAV])
    if BlockKind.SIDEBAR in by_kind:
        _place_sidebar(screen, *by_kind[BlockKind.SIDEBAR])


def _place_navbar(screen: Screen, index: int, block: WireBlock) -> None:
    """Place the navbar under the status bar: in the margins on a phone, full width on a desktop."""
    is_phone = screen.ctx.is_phone
    left = screen.margin if is_phone else screen.inner_left
    width = screen.width - 2 * left
    height = _height_of(screen, block, width)
    _put(screen, index, block, (left, screen.top, width, height))
    screen.top += height


def _place_bottom_nav(screen: Screen, index: int, block: WireBlock) -> None:
    """Place the bottom navigation at the foot of the screen."""
    height = _height_of(screen, block, screen.inner_width)
    screen.floor -= height
    _put(screen, index, block, (screen.inner_left, screen.floor, screen.inner_width, height))


def _place_sidebar(screen: Screen, index: int, block: WireBlock) -> None:
    """Place the sidebar at the left, from the navbar to the foot of the screen."""
    rules = screen.ctx.rules
    height = screen.height - screen.inner_left - screen.top
    _put(screen, index, block, (screen.inner_left, screen.top, rules.sidebar_width, height))
    screen.left = rules.sidebar_width


def _assign_slots(blocks: list[tuple[int, WireBlock]]) -> list[Slot]:
    """Give every block a row, a column and a span.

    A block with no row goes in a new row below the last; with a column after the first and no
    row, it goes in the row of the block before it.
    """
    slots: list[Slot] = []
    last_row = 0
    for index, block in blocks:
        continues = block.row == 0 and block.col > 1 and bool(slots)
        row = block.row or (slots[-1].row if continues else last_row + 1)
        col = block.col or 1
        span = block.span or FULL_SPAN - col + 1
        slots.append(Slot(index, row, col, span, block.rows))
        last_row = max(last_row, row + block.rows - 1)
    return slots


def _place_grid(screen: Screen, blocks: list[tuple[int, WireBlock]]) -> None:
    """Place the blocks of the grid row by row below the navbar."""
    if not blocks:
        return
    by_index = dict(blocks)
    slots = _assign_slots(blocks)
    left = screen.left + screen.margin
    width = screen.width - left - screen.margin
    gap = screen.ctx.gap
    column = (width - (FULL_SPAN - 1) * gap) / FULL_SPAN
    heights = _row_heights(screen, slots, (by_index, column, gap))
    tops = _row_tops(screen, slots, by_index, heights)
    for slot in slots:
        block = by_index[slot.index]
        box_width = slot.span * column + (slot.span - 1) * gap
        box_left = left + (slot.col - 1) * (column + gap)
        natural = _height_of(screen, block, box_width)
        spanned = _spanned_height(slot, heights, tops)
        height = max(spanned, natural) if block.kind in STRETCH_KINDS else natural
        _put(screen, slot.index, block, (box_left, tops[slot.row], box_width, height))


def _row_heights(
    screen: Screen, slots: list[Slot], metrics: tuple[dict[int, WireBlock], float, float]
) -> dict[int, float]:
    """Return the height of each row: its tallest block; tall blocks add what is missing below."""
    by_index, column, gap = metrics
    last = max(slot.row + slot.rows - 1 for slot in slots)
    heights = dict.fromkeys(range(1, last + 1), 0.0)
    ordered = sorted(slots, key=lambda slot: slot.rows)
    for slot in ordered:
        width = slot.span * column + (slot.span - 1) * gap
        natural = _height_of(screen, by_index[slot.index], width)
        end = slot.row + slot.rows - 1
        have = sum(heights[row] for row in range(slot.row, end + 1)) + gap * (slot.rows - 1)
        heights[end] = max(heights[end], heights[end] + natural - have)
    return heights


def _row_gap(screen: Screen, above: list[WireBlock], below: list[WireBlock]) -> float:
    """Return the gap between two rows: tight under a section label, wider before one."""
    rules = screen.ctx.rules
    device = screen.view.device.value
    if above and all(LABEL_FLAG in block.flags for block in above):
        return rules.label_gap_below
    if below and all(LABEL_FLAG in block.flags for block in below):
        return rules.section_gap[device]
    return screen.ctx.gap


def _row_tops(
    screen: Screen,
    slots: list[Slot],
    by_index: dict[int, WireBlock],
    heights: dict[int, float],
) -> dict[int, float]:
    """Return the y of the top of each row."""
    rules = screen.ctx.rules
    members: dict[int, list[WireBlock]] = {row: [] for row in heights}
    for slot in slots:
        members[slot.row].append(by_index[slot.index])
    tops: dict[int, float] = {}
    y = screen.top + rules.content_top[screen.view.device.value]
    for row in sorted(heights):
        tops[row] = y
        following = members.get(row + 1, [])
        y += heights[row] + _row_gap(screen, members[row], following)
    return tops


def _spanned_height(slot: Slot, heights: dict[int, float], tops: dict[int, float]) -> float:
    """Return the height of the rows a block spans, with the gaps between them."""
    end = slot.row + slot.rows - 1
    return tops[end] + heights[end] - tops[slot.row]


def _place_pinned(screen: Screen, blocks: list[tuple[int, WireBlock]]) -> None:
    """Pin blocks above the foot of the screen, in the order written, as one stack."""
    if not blocks:
        return
    rules = screen.ctx.rules
    width = screen.width - 2 * screen.margin - screen.left
    heights = [_height_of(screen, block, width) for _, block in blocks]
    has_nav = any(block.kind is BlockKind.BOTTOM_NAV for block in screen.view.blocks)
    pad = rules.anchor_pad_nav if has_nav else rules.anchor_pad
    total = sum(heights) + rules.anchor_gap * (len(blocks) - 1)
    top = screen.floor - pad - total
    for (index, block), height in zip(blocks, heights, strict=True):
        _put(screen, index, block, (screen.left + screen.margin, top, width, height))
        top += height + rules.anchor_gap


def _place_overlays(screen: Screen, blocks: list[tuple[int, WireBlock]]) -> None:
    """Draw modals, sheets and toasts over the screen; a modal and a sheet dim what is under."""
    rules = screen.ctx.rules
    whole = (0, 0, screen.width, screen.height)
    radius = rules.radius[screen.view.device.value]
    for index, block in blocks:
        if block.kind is not BlockKind.TOAST:
            screen.plan.parts.append(scrim_part(whole, radius, screen.ctx))
        drawn = draw_overlay(block, whole, screen.ctx)
        screen.plan.parts.extend(drawn.parts)
        screen.plan.drawn[index] = drawn
        screen.plan.boxes[index] = next(iter(drawn.anchors.values()), whole)


def _badge_target(screen: Screen, badge: WireBadge) -> Bounds | None:
    """Return the box a badge sits on: a named part of its block, or the block."""
    drawn = screen.plan.drawn.get(badge.block)
    box = screen.plan.boxes.get(badge.block)
    if drawn is None or box is None:
        return None
    return drawn.anchors.get(badge.part, box) if badge.part else box


def badge_parts(number: str, target: Bounds, corner: Corner, ctx: WireContext) -> list[Part]:
    """Draw a numbered badge centred on a corner of a part: a dark circle with teal digits.

    Args:
        number: The digits of the badge.
        target: The box of the part that is explained.
        corner: Which corner or side of it the badge sits on.
        ctx: The drawing context.

    Returns:
        The circle and its number.
    """
    rules, badge = ctx.rules, ctx.theme.badge
    across, down = CORNER_POINTS[corner]
    size = rules.badge_size
    outward = SIDE_OUTWARD.get(corner, 0) * (size / HALF + rules.badge_gap)
    box = (
        target[0] + target[2] * across - size / HALF + outward,
        target[1] + target[3] * down - size / HALF,
        size,
        size,
    )
    ink = Ink(rules.font_badge, badge.foreground, is_bold=True, align=Align.CENTER, is_mono=True)
    return [
        circle(box, badge.background, Line(ctx.colors.paper, rules.badge_ring)),
        label(box, number, ink),
    ]


def _add_badges(screen: Screen) -> None:
    """Draw the badges of the screen over everything else."""
    for badge in screen.view.badges:
        target = _badge_target(screen, badge)
        if target is not None:
            screen.plan.parts.extend(badge_parts(badge.number, target, badge.corner, screen.ctx))


def _device_parts(screen: Screen) -> list[Part]:
    """Draw the device behind the blocks: the screen, the status bar or the browser bar."""
    rules, colors = screen.ctx.rules, screen.ctx.colors
    device = screen.view.device
    frame = rect(
        (0, 0, screen.width, screen.height),
        colors.screen,
        Line(colors.ink, rules.border),
        rules.radius[device.value],
    )
    if screen.view.is_plain:
        return [frame]
    if device is Device.DESKTOP:
        return [frame, *_browser_parts(screen)]
    time = (rules.time_left, rules.time_top, rules.time_width, rules.font_time * rules.line_factor)
    ink = Ink(rules.font_time, colors.ink, is_bold=True)
    home = (
        (screen.width - rules.home_width) / HALF,
        screen.height - rules.home_bottom - rules.home_height,
        rules.home_width,
        rules.home_height,
    )
    return [frame, label(time, STATUS_TIME, ink), pill(home, colors.ink)]


def _browser_parts(screen: Screen) -> list[Part]:
    """Draw the bar of a desktop browser: three dots and an address field."""
    rules, colors = screen.ctx.rules, screen.ctx.colors
    inset = rules.border
    bar = (inset, inset, screen.width - 2 * inset, rules.browser_bar - inset)
    parts = [rect(bar, colors.chrome, None, rules.radius[Device.DESKTOP.value] - inset)]
    middle = inset + bar[3] / HALF
    for index, color in enumerate((rules.dot_red, rules.dot_amber, rules.dot_green)):
        size = rules.browser_dot
        left = rules.dot_left + index * rules.dot_step
        parts.append(circle((left, middle - size / HALF, size, size), color))
    address = (
        rules.address_left,
        middle - rules.address_height / HALF,
        rules.address_width,
        rules.address_height,
    )
    parts.append(pill(address, colors.paper))
    words = (address[0] + rules.address_pad, address[1], address[2] - rules.address_pad, address[3])
    parts.append(label(words, screen.view.address, Ink(rules.font_small + 0.5, colors.text)))
    return parts


def _frame_border(screen: Screen) -> Part:
    """Draw the border of the device again over the content, so that no block pokes out."""
    rules, colors = screen.ctx.rules, screen.ctx.colors
    box = (0, 0, screen.width, screen.height)
    return rect(box, None, Line(colors.ink, rules.border), rules.radius[screen.view.device.value])


def _caption_parts(screen: Screen) -> list[Part]:
    """Draw the name above the frame, as ``S12 · Cart``, and the small line under the name."""
    view, rules, colors = screen.view, screen.ctx.rules, screen.ctx.colors
    if not view.is_captioned:
        return []
    name = " · ".join(text for text in (view.code, view.title) if text)
    if not name and not view.caption_note:
        return []
    note_room = rules.caption_note_height if view.caption_note else 0
    top = -(rules.caption_gap + note_room + rules.caption_height)
    box = (0, top, screen.width, rules.caption_height)
    ink = Ink(rules.font_caption, colors.ink, is_bold=True, align=Align.CENTER)
    parts = [label(box, name, ink)]
    if view.caption_note:
        note = (0, -(rules.caption_gap + note_room), screen.width, note_room)
        ink = Ink(rules.font_small + 1, colors.muted, align=Align.CENTER)
        parts.append(label(note, view.caption_note, ink))
    return parts
