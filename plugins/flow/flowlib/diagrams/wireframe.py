"""The wireframe: screens of blocks on a grid, annotated, in a state set or a responsive set.

See ``wireframe_spec`` for the spec format. Screens stand side by side with their name above;
the notes sit below them in columns, numbered like the badges on the screens (design 10).
Nothing animates: a wireframe is a still.
"""

from math import ceil

from ..canvas import fit_canvas
from ..model import BlockKind, Device, Fidelity, Node, Scene, ScreenView, Shape, WireBlock
from ..reader import SpecError
from ..theme import Theme, load_theme
from ..wire_blocks import block_type
from ..wire_kit import WireContext
from ..wire_layout import plan_screen
from .wireframe_spec import Note, SetKind, WireSpec, read_spec

DEFAULT_FONT_SIZE = 12.0
MIN_SCREENS_PER_ROW_OF_NOTES = 2  # one screen alone has its notes in three columns


def layout_raw(raw: object) -> Scene:
    """Lay out a wireframe from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``wireframe`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: With every problem found, including a badge that points at a part that its
            block does not have.
    """
    return layout(read_spec(raw))


def layout(spec: WireSpec) -> Scene:
    """Place the screens and the notes of a checked spec.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with the canvas sized to hold it.
    """
    theme = load_theme()
    rules = theme.layout
    sizes = [_size_of(view, spec.kind, theme) for view in spec.screens]
    _check_parts(spec, sizes, theme)
    top = (
        rules.margin + (rules.title_block_height if spec.title else 0) + _caption_room(spec, theme)
    )
    screens = _screen_nodes(spec, sizes, (theme.wire.notes.screens_left, top), theme)
    notes = _note_nodes(spec, screens, theme)
    return fit_canvas(Scene(0, 0, spec.title, spec.description, (), (*screens, *notes), ()))


def _size_of(view: ScreenView, kind: SetKind | None, theme: Theme) -> tuple[float, float]:
    """Return the size of a screen: the width of its device, or of its width in a responsive set."""
    wire = theme.wire
    if kind is SetKind.RESPONSIVE:
        return wire.responsive[view.device.value]
    return wire.device[view.device.value]


def _caption_room(spec: WireSpec, theme: Theme) -> float:
    """Return the room above the frames for the name of the screen and its small line."""
    rules = theme.wire
    has_note = any(view.caption_note for view in spec.screens)
    if not any(view.title or view.code or view.caption_note for view in spec.screens):
        return 0
    return rules.caption_gap + rules.caption_height + (rules.caption_note_height if has_note else 0)


def _check_parts(spec: WireSpec, sizes: list[tuple[float, float]], theme: Theme) -> None:
    """Check that every badge points at a part its block has; raise with all that do not."""
    problems = []
    for number, (view, size) in enumerate(zip(spec.screens, sizes, strict=True)):
        plan = plan_screen(view, theme, size)
        for badge in view.badges:
            drawn = plan.drawn.get(badge.block)
            if badge.part and drawn is not None and badge.part not in drawn.anchors:
                names = ", ".join(sorted(drawn.anchors)) or "none"
                problems.append(
                    f"screens[{number}]: block {badge.block} has no part '{badge.part}'; "
                    f"its parts are: {names}"
                )
    if problems:
        raise SpecError(problems)


def _gap_of(spec: WireSpec, theme: Theme) -> float:
    """Return the gap between two screens: tight in a responsive set, wide for a flow of screens."""
    notes = theme.wire.notes
    if spec.kind is SetKind.RESPONSIVE:
        return notes.responsive_gap
    return notes.states_gap if spec.kind is SetKind.STATES else notes.screen_gap


def _screen_nodes(
    spec: WireSpec, sizes: list[tuple[float, float]], origin: tuple[float, float], theme: Theme
) -> list[Node]:
    """Put the screens side by side, top aligned."""
    left, top = origin
    nodes = []
    for index, (view, (width, height)) in enumerate(zip(spec.screens, sizes, strict=True)):
        nodes.append(_node(f"screen-{index}", (left, top, width, height), view))
        left += width + _gap_of(spec, theme)
    return nodes


def _node(name: str, box: tuple[float, float, float, float], view: ScreenView) -> Node:
    """Make the scene node of a screen or a note."""
    x, y, width, height = box
    return Node(
        name,
        Shape.SCREEN,
        x,
        y,
        width,
        height,
        (view.title,) if view.title else (),
        None,
        None,
        None,
        DEFAULT_FONT_SIZE,
        screen=view,
    )


def _note_nodes(spec: WireSpec, screens: list[Node], theme: Theme) -> list[Node]:
    """Put the notes below the screens, in columns."""
    notes = theme.wire.notes
    if not spec.notes:
        return []
    columns = _columns(spec, theme)
    base = max(node.y + node.height for node in screens) + notes.notes_top
    ctx = WireContext(theme, Device.PHONE)
    nodes = []
    for column, members in enumerate(columns):
        left, width = _column_box(column, spec, screens, theme)
        for row, note in enumerate(members):
            block = WireBlock(BlockKind.NOTE, text=note.title, detail=note.text, value=note.number)
            height = block_type(BlockKind.NOTE).height(block, width, ctx)
            view = ScreenView(
                code="", fidelity=Fidelity.L3, blocks=(block,), is_bare=True, scale=1.0
            )
            nodes.append(
                _node(f"note-{note.number}", (left, base + row * notes.pitch, width, height), view)
            )
    return nodes


def _column_count(spec: WireSpec, theme: Theme) -> int | None:
    """Return how many columns the notes make, or None when each sits under its own screen."""
    if spec.kind is SetKind.STATES:
        return len(spec.screens)
    if spec.kind is None and _is_per_screen(spec):
        return None
    return theme.wire.notes.columns


def _columns(spec: WireSpec, theme: Theme) -> list[list[Note]]:
    """Split the notes into columns: one under each screen, or a few that read down."""
    count = _column_count(spec, theme)
    if count is None:
        return _notes_by_screen(spec)
    each = max(ceil(len(spec.notes) / count), 1)
    return [list(spec.notes[start : start + each]) for start in range(0, len(spec.notes), each)]


def _is_per_screen(spec: WireSpec) -> bool:
    """Tell whether each note belongs to one screen, so that it can sit under it."""
    if len(spec.screens) < MIN_SCREENS_PER_ROW_OF_NOTES:
        return False
    owners: dict[str, int] = {}
    for index, view in enumerate(spec.screens):
        for badge in view.badges:
            if owners.setdefault(badge.number, index) != index:
                return False
    return True


def _notes_by_screen(spec: WireSpec) -> list[list[Note]]:
    """Return the notes of each screen, in the order of their numbers."""
    by_number = {note.number: note for note in spec.notes}
    columns: list[list[Note]] = []
    for view in spec.screens:
        numbers = sorted({badge.number for badge in view.badges}, key=int)
        columns.append([by_number[number] for number in numbers])
    return columns


def _column_box(
    column: int, spec: WireSpec, screens: list[Node], theme: Theme
) -> tuple[float, float]:
    """Return the left edge and the width of a column of notes."""
    notes = theme.wire.notes
    count = _column_count(spec, theme)
    if count is None:
        node = screens[column]
        return node.x, node.width + notes.screen_gap - notes.column_gap
    left = screens[0].x
    span = screens[-1].x + screens[-1].width - left
    pitch = (span + _gap_of(spec, theme)) / count
    return left + column * pitch, pitch - notes.column_gap
