"""Content rules of a wireframe (design 10): one primary action, real words, notes off the text.

The one rule that is an error is the first: a screen has one primary button (a modal has its own,
because it covers the screen). The others are warnings, because an author may break them on
purpose: a badge over a word, blocks that overlap, a screen that is taller than its device, words
such as ``Button`` where real words belong, a note that needs more than two lines, and a state
that does not show what its page says (design 10 section 4).
"""

from .check import Code, Finding, Rect, Severity
from .model import (
    BlockAnchor,
    BlockKind,
    CellKind,
    ElementStyle,
    Node,
    Scene,
    ScreenView,
    WireBlock,
    WireState,
)
from .screen_part import Align, PartKind
from .sizing import estimate_text_width
from .theme import Theme, load_theme
from .wire_blocks import OVERLAY_KINDS
from .wire_kit import WireContext
from .wire_layout import WirePlan, plan_screen
from .wire_note import note_lines

PLACEHOLDER_WORDS = (
    "lorem ipsum",
    "label",
    "text",
    "title",
    "button",
    "click here",
    "placeholder",
    "heading",
    "xxx",
)  # words that stand for words, which a wireframe must not have on a button or a label
TEXT_TOP_FRACTION = 0.15  # of a text box: where the letters of a line start
TEXT_BOTTOM_FRACTION = 0.85
OVERLAP_PX = 2  # blocks closer than this inside one another are not an overlap
SECOND_PRIMARY = 2
ACTION_KINDS = (BlockKind.EMPTY, BlockKind.ERROR)
STATE_BLOCKS: dict[WireState, BlockKind | None] = {
    WireState.NORMAL: None,
    WireState.LOADING: BlockKind.LOADING,
    WireState.EMPTY: BlockKind.EMPTY,
    WireState.ERROR: BlockKind.ERROR,
}


def lint_wire_screens(scene: Scene) -> list[Finding]:
    """Check every screen with blocks: one primary action, words, badges, overlaps and height.

    Args:
        scene: A scene with screens that have blocks (a wireframe, or a screen flow at L3).

    Returns:
        The findings; the second primary action is an error, the rest are warnings.
    """
    theme = load_theme()
    findings: list[Finding] = []
    for node in _wire_screens(scene):
        view = node.screen
        findings += _primary_findings(node, view)
        findings += _word_findings(node, view)
        plan = plan_screen(view, theme, (node.width / view.scale, node.height / view.scale))
        findings += _badge_findings(node, view, plan, theme)
        findings += _overlap_findings(node, view, plan)
    return findings


def lint_wireframe(scene: Scene) -> list[Finding]:
    """Check a wireframe: the rules of its screens, its notes, its state set and its widths.

    Args:
        scene: A scene drawn from a wireframe spec.

    Returns:
        The findings.
    """
    findings = lint_wire_screens(scene)
    findings += _note_findings(scene)
    findings += _state_findings(scene)
    findings += _responsive_findings(scene)
    return findings


def _wire_screens(scene: Scene) -> list[Node]:
    """Return the nodes that are screens drawn with blocks, not the notes."""
    return [
        node
        for node in scene.nodes
        if node.screen is not None and node.screen.blocks and not node.screen.is_bare
    ]


def primary_count(block: WireBlock) -> int:
    """Count the primary actions of a block, and of the blocks inside it."""
    count = sum(primary_count(child) for child in block.children)
    if block.kind is BlockKind.BUTTON:
        return count + int(block.style in (None, ElementStyle.PRIMARY))
    if block.kind is BlockKind.NAVBAR or block.kind in ACTION_KINDS:
        return count + int(bool(block.action))
    if block.kind is BlockKind.TABLE:
        return count + _primary_cells(block)
    return count


def _primary_cells(block: WireBlock) -> int:
    """Count the cells of a table that are a primary button."""
    kinds = [column.kind for column in block.columns]
    return sum(
        1
        for row in block.cells
        for kind, cell in zip(kinds, row, strict=False)
        if kind is CellKind.BUTTON and cell.style == ElementStyle.PRIMARY.value
    )


def _primary_findings(node: Node, view: ScreenView) -> list[Finding]:
    """Report a screen, or the overlay on it, that has more than one primary action."""
    layers = {
        "screen": [block for block in view.blocks if block.kind not in OVERLAY_KINDS],
        "overlay": [block for block in view.blocks if block.kind in OVERLAY_KINDS],
    }
    findings = []
    for name, blocks in layers.items():
        count = sum(primary_count(block) for block in blocks)
        if name == "overlay" and blocks:
            count = 1 if any(block.kind is not BlockKind.TOAST for block in blocks) else 0
        if count >= SECOND_PRIMARY:
            findings.append(
                Finding(
                    Severity.ERROR,
                    Code.WIREFRAME_TWO_PRIMARY,
                    f"'{node.id}' has {count} primary actions on its {name}; keep one, "
                    "and draw the others as outlined (secondary) buttons",
                    (node.id,),
                )
            )
    return findings


def _word_findings(node: Node, view: ScreenView) -> list[Finding]:
    """Warn about a button or a label that holds a stand-in word instead of real words."""
    found = []
    for block in view.blocks:
        if block.kind in (BlockKind.BUTTON, BlockKind.FORM_FIELD, BlockKind.LIST_ITEM):
            words = (block.text or block.detail).strip().lower()
            if words in PLACEHOLDER_WORDS:
                found.append(
                    _warn(
                        Code.WIREFRAME_PLACEHOLDER,
                        f"'{node.id}' has a {block.kind.value} that says '{words}'; "
                        "use the real words a person would read",
                        node,
                    )
                )
    return found


def _text_rects(plan: WirePlan, theme: Theme) -> list[tuple[str, Rect]]:
    """Return the area each line of text of the content really covers, with the text."""
    rects = []
    for part in plan.parts[: plan.content_count]:
        if part.kind is not PartKind.TEXT or not part.text:
            continue
        x, y, width, height = part.bounds
        reach = min(width, estimate_text_width(part.text, theme.layout, part.font_size))
        left = {
            Align.LEFT: x,
            Align.CENTER: x + (width - reach) / 2,
            Align.RIGHT: x + width - reach,
        }
        top = y + height * TEXT_TOP_FRACTION
        bottom = y + height * TEXT_BOTTOM_FRACTION
        rects.append((part.text, Rect(left[part.align], top, left[part.align] + reach, bottom)))
    return rects


def _badge_findings(node: Node, view: ScreenView, plan: WirePlan, theme: Theme) -> list[Finding]:
    """Warn about a numbered badge that lies over a word: it belongs on a corner."""
    rects = _text_rects(plan, theme)
    found = []
    size = theme.wire.badge_size
    for part in plan.parts[plan.content_count :]:
        if part.kind is not PartKind.CIRCLE:
            continue
        x, y, _, _ = part.bounds
        badge = Rect(x, y, x + size, y + size)
        covered = [text for text, rect in rects if rect.overlaps(_inner(badge, theme))]
        if covered:
            found.append(
                _warn(
                    Code.WIREFRAME_BADGE_ON_TEXT,
                    f"a badge on '{node.id}' covers the text '{covered[0]}'; "
                    "move it to another corner of the part",
                    node,
                )
            )
    return found


def _inner(badge: Rect, theme: Theme) -> Rect:
    """Shrink a badge to the circle's core, so that a text that only brushes it is not reported."""
    gap = theme.wire.badge_size * (1 - 0.7) / 2
    return Rect(badge.left + gap, badge.top + gap, badge.right - gap, badge.bottom - gap)


def _overlap_findings(node: Node, view: ScreenView, plan: WirePlan) -> list[Finding]:
    """Warn about blocks that overlap and about blocks that run below the foot of the screen."""
    gridded = [
        (index, block)
        for index, block in enumerate(view.blocks)
        if block.kind not in OVERLAY_KINDS
        and block.kind not in (BlockKind.NAVBAR, BlockKind.SIDEBAR, BlockKind.BOTTOM_NAV)
    ]
    found = []
    for position, (index, block) in enumerate(gridded):
        box = plan.boxes[index]
        if block.anchor is BlockAnchor.GRID and box[1] + box[3] > plan.floor + OVERLAP_PX:
            found.append(
                _warn(
                    Code.WIREFRAME_TOO_TALL,
                    f"'{node.id}' has a {block.kind.value} that runs below the foot of the "
                    "screen; drop a block or move it to another screen",
                    node,
                )
            )
        found += _pair_overlaps(node, gridded[position + 1 :], plan, (index, box))
    return found[:MAX_OVERLAP_FINDINGS]


MAX_OVERLAP_FINDINGS = 3  # more than this many findings about one screen say the same thing


def _pair_overlaps(
    node: Node,
    others: list[tuple[int, WireBlock]],
    plan: WirePlan,
    first: tuple[int, tuple[float, float, float, float]],
) -> list[Finding]:
    """Report the blocks after a block that cover part of it."""
    _, box = first
    own = Rect(box[0], box[1], box[0] + box[2], box[1] + box[3])
    found = []
    for index, block in others:
        other = plan.boxes[index]
        rect = Rect(other[0], other[1], other[0] + other[2], other[1] + other[3])
        if rect.overlaps(own, -OVERLAP_PX):
            found.append(
                _warn(
                    Code.WIREFRAME_OVERLAP,
                    f"two blocks of '{node.id}' overlap (a {block.kind.value} and another); "
                    "give them different rows or columns",
                    node,
                )
            )
    return found


def _note_findings(scene: Scene) -> list[Finding]:
    """Warn about a note whose line needs more than the two lines a column gives it."""
    theme = load_theme()
    ctx = WireContext(theme, natural_view().device)
    found = []
    for node in scene.nodes:
        view = node.screen
        if view is None or not view.is_bare:
            continue
        block = view.blocks[0]
        if len(note_lines(block, node.width, ctx)) > theme.wire.notes.max_lines:
            found.append(
                _warn(
                    Code.WIREFRAME_NOTE_LONG,
                    f"the note '{block.text}' takes more than {theme.wire.notes.max_lines} lines; "
                    "a note is a bold title and one line",
                    node,
                )
            )
    return found


def natural_view() -> ScreenView:
    """Return an empty screen view, to give a context a device."""
    return ScreenView(code="")


def _state_findings(scene: Scene) -> list[Finding]:
    """Warn when a screen that says which state it shows does not draw what that state needs."""
    found = []
    for node in _wire_screens(scene):
        view = node.screen
        if view.state is None:
            continue
        wanted = STATE_BLOCKS[view.state]
        kinds = [block.kind for block in view.blocks]
        if wanted is not None and wanted not in kinds:
            found.append(
                _warn(
                    Code.WIREFRAME_STATE,
                    f"'{node.id}' is the {view.state.value} state but has no {wanted.value} block",
                    node,
                )
            )
        found += _state_action_findings(node, view)
    return found


def _state_action_findings(node: Node, view: ScreenView) -> list[Finding]:
    """Check the one action of an empty state and the retry of an error."""
    found = []
    for block in view.blocks:
        if block.kind is BlockKind.EMPTY and (not block.action or block.items):
            found.append(
                _warn(
                    Code.WIREFRAME_STATE,
                    f"the empty state of '{node.id}' should offer exactly one action",
                    node,
                )
            )
        if block.kind is BlockKind.ERROR and not block.action:
            found.append(
                _warn(
                    Code.WIREFRAME_STATE,
                    f"the error state of '{node.id}' should put a retry first",
                    node,
                )
            )
    return found


def _responsive_findings(scene: Scene) -> list[Finding]:
    """Warn when a responsive set has no note saying what changes between the widths."""
    screens = _wire_screens(scene)
    is_responsive = all(node.screen.is_plain for node in screens) and len(screens) > 1
    has_notes = any(node.screen.badges for node in screens)
    if is_responsive and not has_notes:
        return [
            Finding(
                Severity.WARNING,
                Code.WIREFRAME_NO_NOTES,
                "a responsive set should say in a short note what changes between the widths "
                "(columns, filters, links)",
                (),
            )
        ]
    return []


def _warn(code: Code, message: str, node: Node) -> Finding:
    """Build a warning about a screen."""
    return Finding(Severity.WARNING, code, message, (node.id,))
