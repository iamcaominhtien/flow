"""The table of wireframe blocks: for each kind, how tall it is and how it is drawn."""

from collections.abc import Callable
from dataclasses import dataclass

from .model import BlockKind, WireBlock
from .screen_part import Bounds
from .wire_basic import (
    button_height,
    checklist_height,
    chip_height,
    draw_button,
    draw_checklist,
    draw_chip,
    draw_field,
    draw_image,
    draw_rows,
    draw_stepper,
    draw_text,
    field_height,
    image_height,
    rows_height,
    stepper_height,
    text_height,
)
from .wire_cards import (
    card_height,
    chart_height,
    draw_card,
    draw_chart,
    draw_figure,
    draw_item,
    draw_table,
    figure_height,
    item_height,
    table_height,
)
from .wire_chrome import (
    bottom_nav_height,
    draw_bottom_nav,
    draw_navbar,
    draw_search,
    draw_sidebar,
    draw_tabs,
    navbar_height,
    search_height,
    sidebar_height,
    tabs_height,
)
from .wire_kit import Drawn, Ink, WireContext, card_box, label
from .wire_note import draw_note, note_height
from .wire_state import draw_state, state_height

HeightOf = Callable[[WireBlock, float, WireContext], float]
DrawBlock = Callable[[WireBlock, Bounds, WireContext], Drawn]
OVERLAY_KINDS = (BlockKind.MODAL, BlockKind.SHEET, BlockKind.TOAST)
STRETCH_KINDS = (
    BlockKind.CARD,
    BlockKind.PANEL,
    BlockKind.CHART,
    BlockKind.TABLE,
    BlockKind.CHECKLIST,
    BlockKind.FIGURE,
)  # the blocks that grow to the height of the row they share with a taller block


@dataclass(frozen=True)
class BlockType:
    """How tall a kind of block is at a width, and how it is drawn in a box."""

    height: HeightOf
    draw: DrawBlock


def block_type(kind: BlockKind) -> BlockType:
    """Return the height and the drawer of a kind of block.

    Args:
        kind: A kind that sits in the grid or on a screen edge, not an overlay.

    Returns:
        The two functions of the kind.
    """
    return TYPES[kind]


def panel_height(block: WireBlock, width: float, ctx: WireContext) -> float:
    """Return the height of a panel: its title and the blocks it holds, one below the other."""
    rules = ctx.rules
    inner = width - 2 * rules.card_pad
    heights = [block_type(child.kind).height(child, inner, ctx) for child in block.children]
    title = rules.table_title if block.text else 0
    stack = sum(heights) + ctx.gap * max(len(heights) - 1, 0)
    return block.height or 2 * rules.card_pad + title + stack


def draw_panel(block: WireBlock, box: Bounds, ctx: WireContext) -> Drawn:
    """Draw a titled card that holds other blocks, for instance a list of items to look at."""
    rules, colors = ctx.rules, ctx.colors
    x, y, width, _ = box
    drawn = Drawn([card_box(box, ctx)], {})
    left, top = x + rules.card_pad, y + rules.card_pad
    inner = width - 2 * rules.card_pad
    if block.text:
        title = (left, top, inner, rules.table_title)
        drawn.parts.append(
            label(title, block.text, Ink(rules.font_label, colors.ink, is_bold=True))
        )
        top += rules.table_title
    for index, child in enumerate(block.children):
        kind = block_type(child.kind)
        place = (left, top, inner, kind.height(child, inner, ctx))
        inside = kind.draw(child, place, ctx)
        drawn.parts.extend(inside.parts)
        drawn.anchors[f"child-{index}"] = place
        drawn.anchors.update({f"child-{index}.{name}": box for name, box in inside.anchors.items()})
        top += place[3] + ctx.gap
    return drawn


TYPES: dict[BlockKind, BlockType] = {
    BlockKind.NAVBAR: BlockType(navbar_height, draw_navbar),
    BlockKind.SIDEBAR: BlockType(sidebar_height, draw_sidebar),
    BlockKind.CARD: BlockType(card_height, draw_card),
    BlockKind.PANEL: BlockType(panel_height, draw_panel),
    BlockKind.LIST_ITEM: BlockType(item_height, draw_item),
    BlockKind.FORM_FIELD: BlockType(field_height, draw_field),
    BlockKind.BUTTON: BlockType(button_height, draw_button),
    BlockKind.IMAGE: BlockType(image_height, draw_image),
    BlockKind.TAB_BAR: BlockType(tabs_height, draw_tabs),
    BlockKind.BOTTOM_NAV: BlockType(bottom_nav_height, draw_bottom_nav),
    BlockKind.SEARCH_BAR: BlockType(search_height, draw_search),
    BlockKind.TABLE: BlockType(table_height, draw_table),
    BlockKind.CHART: BlockType(chart_height, draw_chart),
    BlockKind.LOADING: BlockType(state_height, draw_state),
    BlockKind.EMPTY: BlockType(state_height, draw_state),
    BlockKind.ERROR: BlockType(state_height, draw_state),
    BlockKind.SUCCESS: BlockType(state_height, draw_state),
    BlockKind.CHIP: BlockType(chip_height, draw_chip),
    BlockKind.STEPPER: BlockType(stepper_height, draw_stepper),
    BlockKind.FIGURE: BlockType(figure_height, draw_figure),
    BlockKind.TEXT: BlockType(text_height, draw_text),
    BlockKind.ROWS: BlockType(rows_height, draw_rows),
    BlockKind.CHECKLIST: BlockType(checklist_height, draw_checklist),
    BlockKind.NOTE: BlockType(note_height, draw_note),
}
