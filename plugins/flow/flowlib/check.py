"""Check a scene for the problems the design rules forbid, without drawing it.

Each check returns findings that name the items involved, so that the author can change the
spec (a hint, shorter text) and build again.
"""

import math
from dataclasses import dataclass, replace
from enum import StrEnum
from itertools import combinations, pairwise

from .explain_parts import is_explain_node
from .html_board import board_text_room, is_board_node
from .html_nodes import CAPTION_FONT_SIZE_PX, CAPTION_GAP_PX, CAPTION_WIDTH_PX
from .html_plan import is_plan_node, plan_text_room
from .model import Edge, EdgeLabel, Frame, LabelKind, Node, Point, Role, Scene, Shape
from .sizing import LINE_HEIGHT_FACTOR, estimate_text_width
from .text_area import text_area_width
from .theme import LayoutRules, Theme, load_theme

REFERENCE_ROLES = (Role.LIFELINE, Role.GRID, Role.TODAY)  # lines that are not content
CAPTION_TEXT_PAD_PX = 8  # a caption rectangle is this much wider than its text
BORDER_TOLERANCE_PX = 1.0  # a part this close to a frame's border counts as inside or outside
NODE_CLEARANCE_PX = 4.0  # nodes closer than this count as touching
LINE_CLEARANCE_PX = 2.0
MIN_CROSSING_EDGES = 2
MIN_OVERLAP_PX = 32.0  # a shorter shared stretch is a junction at a node, not an overlap
INLINE_LABEL_MAX_CHARS = 20  # design 02: longer words go in a table, under a code
WORDS_KINDS = (
    LabelKind.USER,
    LabelKind.SYSTEM,
    LabelKind.GUARD_OK,
    LabelKind.GUARD_FAIL,
    LabelKind.EFFECT,
)  # the kinds that carry the words of a screen flow transition
WRAPPING_CHARS = 2  # the brackets of a guard, or the slash and space of an effect
MIN_SHARED_BUS_PX = 240.0  # lines of one kind that leave one node may share a bus this long


class Severity(StrEnum):
    """How serious a finding is."""

    ERROR = "error"
    WARNING = "warning"


class Code(StrEnum):
    """The kind of problem a finding reports."""

    NODES_OVERLAP = "nodes-overlap"
    LINE_THROUGH_NODE = "line-through-node"
    LABEL_COVERS = "label-covers"
    OUTSIDE_CANVAS = "outside-canvas"
    TEXT_MAY_NOT_FIT = "text-may-not-fit"
    LINES_CROSS = "lines-cross"
    LINES_OVERLAP = "lines-overlap"
    CAPTION_COVERED = "caption-covered"
    CROSSES_BORDER = "crosses-border"
    ON_DIVIDER = "on-divider"
    LABEL_TOO_LONG = "label-too-long"
    TEXT_TOO_LONG = "text-too-long"
    DECISION_NOT_QUESTION = "decision-not-question"
    DECISION_FEW_EXITS = "decision-few-exits"
    DECISION_NO_ELSE = "decision-no-else"
    CHART_TOO_BIG = "chart-too-big"
    START_PLACEMENT = "start-placement"
    END_PLACEMENT = "end-placement"
    SEQUENCE_LABEL_LONG = "sequence-label-long"
    DFD_PROCESS_COUNT = "dfd-process-count"
    DFD_STORE_ONE_WAY = "dfd-store-one-way"
    BPMN_TOO_MANY_ELEMENTS = "bpmn-too-many-elements"
    BPMN_ROUTE_BENDS = "bpmn-route-bends"
    BPMN_MAIN_PATH = "bpmn-main-path"
    GANTT_TOO_MANY_ROWS = "gantt-too-many-rows"
    ORG_TOO_MANY_LEVELS = "org-too-many-levels"
    ORG_ROLE_SENTENCE = "org-role-sentence"
    MIND_PHRASE_LONG = "mindmap-phrase-long"
    MIND_TOO_MANY_LINKS = "mindmap-too-many-links"
    KANBAN_OVER_LIMIT = "kanban-over-limit"
    KANBAN_CARD_FULL = "kanban-card-full"
    ROADMAP_EXACT_DATE = "roadmap-exact-date"
    ROADMAP_DEPENDENCIES = "roadmap-dependencies"
    EXPLAINER_TOO_MANY_CARDS = "explainer-too-many-cards"
    EXPLAINER_TEXT_LONG = "explainer-text-long"
    EXPLAINER_JARGON = "explainer-jargon"
    EXPLAINER_NO_TITLE = "explainer-no-title"
    WIREFRAME_TWO_PRIMARY = "wireframe-two-primary"
    WIREFRAME_BADGE_ON_TEXT = "wireframe-badge-on-text"
    WIREFRAME_PLACEHOLDER = "wireframe-placeholder-words"
    WIREFRAME_STATE = "wireframe-state"
    WIREFRAME_NOTE_LONG = "wireframe-note-long"
    WIREFRAME_TOO_TALL = "wireframe-too-tall"
    WIREFRAME_OVERLAP = "wireframe-blocks-overlap"
    WIREFRAME_NO_NOTES = "wireframe-no-notes"


@dataclass(frozen=True)
class Finding:
    """One problem found in a scene."""

    severity: Severity
    code: Code
    message: str
    items: tuple[str, ...]


@dataclass(frozen=True)
class Rect:
    """An axis-aligned rectangle."""

    left: float
    top: float
    right: float
    bottom: float

    def overlaps(self, other: "Rect", margin: float = 0.0) -> bool:
        """Tell whether two rectangles share area, or come closer than ``margin``."""
        return (
            self.left < other.right + margin
            and self.right > other.left - margin
            and self.top < other.bottom + margin
            and self.bottom > other.top - margin
        )


def node_rect(node: Node) -> Rect:
    """Return the rectangle a node covers."""
    return Rect(node.x, node.y, node.x + node.width, node.y + node.height)


def _segment_rect(start: Point, end: Point) -> Rect:
    """Return the thin rectangle that covers a horizontal or vertical segment."""
    return Rect(
        min(start[0], end[0]), min(start[1], end[1]), max(start[0], end[0]), max(start[1], end[1])
    )


def _segment_hits(start: Point, end: Point, rect: Rect) -> bool:
    """Tell whether a segment, straight or slanted, passes through a rectangle.

    The rectangle is shrunk by the line clearance. A horizontal or vertical segment is its own
    bounding box; a slanted one is clipped against the
    rectangle, so that it does not count as covering the corner its box would.
    """
    inner = Rect(
        rect.left + LINE_CLEARANCE_PX,
        rect.top + LINE_CLEARANCE_PX,
        rect.right - LINE_CLEARANCE_PX,
        rect.bottom - LINE_CLEARANCE_PX,
    )
    if not _segment_rect(start, end).overlaps(inner):
        return False
    delta_x, delta_y = end[0] - start[0], end[1] - start[1]
    if abs(delta_x) < LINE_CLEARANCE_PX or abs(delta_y) < LINE_CLEARANCE_PX:
        return True
    low, high = 0.0, 1.0
    for step, distance in (
        (-delta_x, start[0] - inner.left),
        (delta_x, inner.right - start[0]),
        (-delta_y, start[1] - inner.top),
        (delta_y, inner.bottom - start[1]),
    ):
        if step == 0:
            continue
        ratio = distance / step
        low, high = (max(low, ratio), high) if step < 0 else (low, min(high, ratio))
    return low <= high


def chip_rect(label: EdgeLabel, rules: LayoutRules) -> Rect:
    """Return the rectangle a label chip covers, estimated from its text."""
    width = estimate_text_width(label.text, rules, rules.chip_font_size) + rules.chip_padding_x
    half_width, half_height = width / 2, rules.chip_height / 2
    at_x, at_y = label.at
    return Rect(at_x - half_width, at_y - half_height, at_x + half_width, at_y + half_height)


def label_rect(edge: Edge, rules: LayoutRules) -> Rect | None:
    """Return the rectangle a label chip covers, estimated from its text, or None."""
    if edge.label is None:
        return None
    return chip_rect(edge.label, rules)


def caption_rect(node: Node, rules: LayoutRules) -> Rect | None:
    """Return the rectangle the caption of a node covers, or None without a caption.

    The caption hangs under the node, or above it when ``caption_above`` is set. It is as wide
    as its text, up to the width of the caption box.
    """
    if not node.caption:
        return None
    widths = [
        estimate_text_width(line, rules, CAPTION_FONT_SIZE_PX) for line in node.caption.split("\n")
    ]
    text_width = max(widths)
    lines = sum(max(1, math.ceil(width / CAPTION_WIDTH_PX)) for width in widths)
    height = lines * CAPTION_FONT_SIZE_PX * LINE_HEIGHT_FACTOR
    half = min(text_width + CAPTION_TEXT_PAD_PX, CAPTION_WIDTH_PX) / 2
    centre = node.x + node.width / 2
    if node.caption_above:
        bottom = node.y - CAPTION_GAP_PX
        return Rect(centre - half, bottom - height, centre + half, bottom)
    top = node.y + node.height + CAPTION_GAP_PX
    return Rect(centre - half, top, centre + half, top + height)


def _is_content(edge: Edge) -> bool:
    """Tell a line that carries meaning from a reference line or a curve, which are not checked."""
    return edge.role not in REFERENCE_ROLES and not edge.is_curved


def _may_cross(edge: Edge, node: Node) -> bool:
    """Tell a line that may pass a node: a dependency runs down the date line of a milestone."""
    return node.shape is Shape.MILESTONE and edge.role in (Role.NEXT, Role.MAIN)


def check_nodes_overlap(scene: Scene) -> list[Finding]:
    """Report every pair of nodes that touch or overlap."""
    findings = []
    for first, second in combinations(scene.nodes, 2):
        if first.id in (second.host,) or second.id == first.host:
            continue
        if node_rect(first).overlaps(node_rect(second), NODE_CLEARANCE_PX):
            findings.append(
                Finding(
                    Severity.ERROR,
                    Code.NODES_OVERLAP,
                    f"'{first.id}' and '{second.id}' touch or overlap",
                    (first.id, second.id),
                )
            )
    return findings


def check_lines_through_nodes(scene: Scene) -> list[Finding]:
    """Report every line that passes through a node it does not start or end at."""
    findings = []
    for edge in scene.edges:
        if edge.role in REFERENCE_ROLES or edge.is_curved:
            continue
        for node in scene.nodes:
            if node.id in (edge.source, edge.target) or _may_cross(edge, node):
                continue
            rect = node_rect(node)
            if any(_segment_hits(start, end, rect) for start, end in pairwise(edge.points)):
                findings.append(
                    Finding(
                        Severity.ERROR,
                        Code.LINE_THROUGH_NODE,
                        f"line '{edge.id}' passes through '{node.id}'",
                        (edge.id, node.id),
                    )
                )
    return findings


def check_labels(scene: Scene, rules: LayoutRules) -> list[Finding]:
    """Report label chips that sit on a node or on another chip."""
    chips = [(edge.id, rect) for edge in scene.edges if (rect := label_rect(edge, rules))]
    findings = []
    for edge_id, rect in chips:
        for node in scene.nodes:
            if rect.overlaps(node_rect(node)):
                findings.append(
                    Finding(
                        Severity.ERROR,
                        Code.LABEL_COVERS,
                        f"the label of '{edge_id}' covers '{node.id}'",
                        (edge_id, node.id),
                    )
                )
    for (first_id, first), (second_id, second) in combinations(chips, 2):
        if first.overlaps(second):
            findings.append(
                Finding(
                    Severity.ERROR,
                    Code.LABEL_COVERS,
                    f"the labels of '{first_id}' and '{second_id}' overlap",
                    (first_id, second_id),
                )
            )
    return findings


def check_captions(scene: Scene, rules: LayoutRules) -> list[Finding]:
    """Report lines and label chips that sit on the caption under an event or an actor."""
    findings = []
    chips = [(edge.id, rect) for edge in scene.edges if (rect := label_rect(edge, rules))]
    for node in scene.nodes:
        caption = caption_rect(node, rules)
        if caption is None:
            continue
        for edge in scene.edges:
            if edge.role is Role.LIFELINE:
                continue
            if any(_segment_hits(start, end, caption) for start, end in pairwise(edge.points)):
                findings.append(
                    Finding(
                        Severity.ERROR,
                        Code.CAPTION_COVERED,
                        f"line '{edge.id}' runs over the caption of '{node.id}'",
                        (edge.id, node.id),
                    )
                )
        findings.extend(
            Finding(
                Severity.ERROR,
                Code.CAPTION_COVERED,
                f"the label of '{edge_id}' covers the caption of '{node.id}'",
                (edge_id, node.id),
            )
            for edge_id, chip in chips
            if chip.overlaps(caption)
        )
    return findings


def check_canvas(scene: Scene, rules: LayoutRules) -> list[Finding]:
    """Report nodes, lines and labels that reach outside the canvas."""
    canvas = Rect(0, 0, scene.width, scene.height)
    findings = []
    for node in scene.nodes:
        rect = node_rect(node)
        if not (
            rect.left >= 0
            and rect.top >= 0
            and rect.right <= canvas.right
            and rect.bottom <= canvas.bottom
        ):
            findings.append(
                Finding(
                    Severity.ERROR,
                    Code.OUTSIDE_CANVAS,
                    f"'{node.id}' is outside the canvas",
                    (node.id,),
                )
            )
    for edge in scene.edges:
        label = label_rect(edge, rules)
        points_out = any(
            not (0 <= x <= canvas.right and 0 <= y <= canvas.bottom) for x, y in edge.points
        )
        label_out = label is not None and (label.left < 0 or label.right > canvas.right)
        if points_out or label_out:
            findings.append(
                Finding(
                    Severity.ERROR,
                    Code.OUTSIDE_CANVAS,
                    f"'{edge.id}' is outside the canvas",
                    (edge.id,),
                )
            )
    return findings


def check_text_fit(scene: Scene, rules: LayoutRules) -> list[Finding]:
    """Report nodes whose text probably does not fit, judging by the estimated text width."""
    findings = []
    theme = load_theme(scene.theme)
    for node in scene.nodes:
        if not node.text or node.screen is not None:
            continue
        room = _text_room(node, rules, theme)
        if room is None:
            continue
        widest = max(
            (estimate_text_width(line, rules, node.font_size) for line in node.text), default=0
        )
        height = len(node.text) * node.font_size * LINE_HEIGHT_FACTOR
        if widest > room or height > node.height:
            findings.append(
                Finding(
                    Severity.WARNING,
                    Code.TEXT_MAY_NOT_FIT,
                    f"the text of '{node.id}' may not fit",
                    (node.id,),
                )
            )
    return findings


def _text_room(node: Node, rules: LayoutRules, theme: Theme) -> float | None:
    """Return how wide the text of a node may be, or None for a node whose text is not checked."""
    if is_explain_node(node):
        return None
    if is_plan_node(node):
        return plan_text_room(node, theme)
    if is_board_node(node):
        return board_text_room(node, theme)
    if node.card:
        return node.width - 2 * (rules.card_padding + rules.card_pill_padding)
    return text_area_width(node.shape, node.width, node.icon is not None)


def check_label_length(scene: Scene) -> list[Finding]:
    """Report words on an arrow that are longer than a screen flow allows inline.

    Design 02 writes a condition on the arrow while it stays under about 20 characters; a longer
    one, or one shared by several arrows, becomes a code with a row in a table.
    """
    findings = []
    for edge in scene.edges:
        for label in (*([edge.label] if edge.label else []), *edge.extras):
            if label.kind not in WORDS_KINDS or _words_length(label) <= INLINE_LABEL_MAX_CHARS:
                continue
            findings.append(
                Finding(
                    Severity.WARNING,
                    Code.LABEL_TOO_LONG,
                    f"the words on '{edge.id}' are longer than {INLINE_LABEL_MAX_CHARS} "
                    "characters; use conditions: coded",
                    (edge.id,),
                )
            )
    return findings


def _words_length(label: EdgeLabel) -> int:
    """Return how many characters of a label are the author's words, without its brackets."""
    is_wrapped = label.kind in (LabelKind.GUARD_OK, LabelKind.GUARD_FAIL, LabelKind.EFFECT)
    return len(label.text) - (WRAPPING_CHARS if is_wrapped else 0)


def _crosses(first: tuple[Point, Point], second: tuple[Point, Point]) -> bool:
    """Tell whether a horizontal and a vertical segment cross in the middle of both."""
    a_start, a_end = first
    b_start, b_end = second
    a_horizontal = abs(a_start[1] - a_end[1]) < LINE_CLEARANCE_PX
    b_horizontal = abs(b_start[1] - b_end[1]) < LINE_CLEARANCE_PX
    if a_horizontal == b_horizontal:
        return False
    horizontal, vertical = (first, second) if a_horizontal else (second, first)
    row, column = horizontal[0][1], vertical[0][0]
    left, right = sorted((horizontal[0][0], horizontal[1][0]))
    top, bottom = sorted((vertical[0][1], vertical[1][1]))
    return left < column < right and top < row < bottom


def check_crossings(scene: Scene) -> list[Finding]:
    """Report every pair of lines that cross each other."""
    findings = []
    drawn = [edge for edge in scene.edges if _is_content(edge)]
    for first, second in combinations(drawn, 2):
        crossing = any(
            _crosses(a, b) for a in pairwise(first.points) for b in pairwise(second.points)
        )
        if crossing:
            findings.append(
                Finding(
                    Severity.WARNING,
                    Code.LINES_CROSS,
                    f"lines '{first.id}' and '{second.id}' cross",
                    (first.id, second.id),
                )
            )
    return findings


def _shared_length(first: tuple[Point, Point], second: tuple[Point, Point]) -> float:
    """Return how far two parallel segments run on top of each other, else 0."""
    for axis in (0, 1):
        other = 1 - axis
        flat = all(
            abs(segment[0][axis] - segment[1][axis]) < LINE_CLEARANCE_PX
            for segment in (first, second)
        )
        if flat and abs(first[0][axis] - second[0][axis]) < LINE_CLEARANCE_PX:
            low = max(
                min(first[0][other], first[1][other]), min(second[0][other], second[1][other])
            )
            high = min(
                max(first[0][other], first[1][other]), max(second[0][other], second[1][other])
            )
            return max(0.0, high - low)
    return 0.0


def _longest_shared(first: Edge, second: Edge) -> float:
    """Return the longest stretch two lines share."""
    return max(
        (_shared_length(a, b) for a in pairwise(first.points) for b in pairwise(second.points)),
        default=0.0,
    )


def _share_a_node(first: Edge, second: Edge) -> bool:
    """Tell whether two lines start or end at the same node."""
    ends = {first.source, first.target} - {None}
    return bool(ends & {second.source, second.target})


def check_overlaps(scene: Scene) -> list[Finding]:
    """Report lines that run on top of each other, so one cannot be told from the other.

    Lines that leave or reach the same node may share a short trunk; lines of different
    kinds (solid and dashed) may not share more than a junction.
    """
    findings = []
    drawn = [edge for edge in scene.edges if _is_content(edge) and edge.role is not Role.REPORTS]
    for first, second in combinations(drawn, 2):
        shared = _longest_shared(first, second)
        limit = MIN_OVERLAP_PX
        if first.dashed == second.dashed and _share_a_node(first, second):
            limit = MIN_SHARED_BUS_PX
        if shared >= limit:
            findings.append(
                Finding(
                    Severity.WARNING,
                    Code.LINES_OVERLAP,
                    f"lines '{first.id}' and '{second.id}' run on top of each other",
                    (first.id, second.id),
                )
            )
    return findings


def frame_rect(frame: Frame) -> Rect:
    """Return the rectangle a frame covers."""
    return Rect(frame.x, frame.y, frame.x + frame.width, frame.y + frame.height)


def _straddles(part: Rect, frame: Rect) -> bool:
    """Tell whether a part lies partly inside a frame and partly outside it.

    A part that holds the whole frame (a big box over a small frame) is not a straddle.
    """
    tolerance = BORDER_TOLERANCE_PX
    if not part.overlaps(frame, -tolerance):
        return False
    inside = (
        part.left >= frame.left - tolerance
        and part.right <= frame.right + tolerance
        and part.top >= frame.top - tolerance
        and part.bottom <= frame.bottom + tolerance
    )
    holds = (
        part.left <= frame.left + tolerance
        and part.right >= frame.right - tolerance
        and part.top <= frame.top + tolerance
        and part.bottom >= frame.bottom - tolerance
    )
    return not inside and not holds


def _parts(scene: Scene, rules: LayoutRules) -> list[tuple[str, Rect]]:
    """Return what a frame border or a divider must not cut: nodes and the chips of lines.

    An activation bar and the bar of a split are left out: they are long on purpose.
    """
    parts = [
        (node.id, node_rect(node))
        for node in scene.nodes
        if node.shape not in (Shape.BAR, Shape.FORK)
    ]
    for edge in scene.edges:
        rect = label_rect(edge, rules)
        if rect is not None:
            parts.append((edge.id, rect))
    return parts


def check_borders(scene: Scene, rules: LayoutRules) -> list[Finding]:
    """Report a node or a label that straddles a frame border or sits on a divider.

    A part belongs inside a frame or outside it (design 01 section 10, check 3). The frame
    borders are those of zones, pools, lanes and fragments; the dividers are the dashed lines
    across a fragment. Both are warnings, since a long box may cross a frame on purpose.
    """
    findings = []
    for part_id, rect in _parts(scene, rules):
        for frame in scene.frames:
            frame_box = frame_rect(frame)
            if _straddles(rect, frame_box):
                findings.append(_border_finding(part_id, frame, Code.CROSSES_BORDER))
            if any(_on_divider(rect, frame_box, divider.y) for divider in frame.dividers):
                findings.append(_border_finding(part_id, frame, Code.ON_DIVIDER))
    return findings


def _on_divider(part: Rect, frame: Rect, y: float) -> bool:
    """Tell whether a part inside a frame's width is cut by the divider at height ``y``."""
    if not part.overlaps(frame, -BORDER_TOLERANCE_PX):
        return False
    return part.top + BORDER_TOLERANCE_PX < y < part.bottom - BORDER_TOLERANCE_PX


def _border_finding(part_id: str, frame: Frame, code: Code) -> Finding:
    """Build the warning for a part that is cut by a frame border or a divider."""
    where = "straddles the border of" if code is Code.CROSSES_BORDER else "sits on a divider of"
    return Finding(
        Severity.WARNING,
        code,
        f"'{part_id}' {where} the frame '{frame.id}'; move it inside or outside",
        (part_id, frame.id),
    )


def check_scene(scene: Scene) -> list[Finding]:
    """Run every check on a scene.

    Args:
        scene: The scene to check.

    Returns:
        All findings, errors first.
    """
    from .check_notation import check_notation
    from .lint import lint_scene

    rules = load_theme().layout
    findings = [
        *lint_scene(scene),
        *check_nodes_overlap(scene),
        *check_lines_through_nodes(scene),
        *check_labels(scene, rules),
        *check_captions(scene, rules),
        *check_canvas(scene, rules),
        *check_text_fit(scene, rules),
        *check_crossings(scene),
        *check_overlaps(scene),
        *check_borders(scene, rules),
        *check_label_length(scene),
        *check_notation(scene),
    ]
    named = [_with_names(finding, scene) for finding in findings]
    return sorted(named, key=lambda finding: finding.severity is not Severity.ERROR)


def _title_of(node: Node) -> str:
    """Return the words a person sees on a node: its text, else its caption."""
    return " ".join(node.text) or node.caption or ""


def _with_names(finding: Finding, scene: Scene) -> Finding:
    """Add to each quoted id in a message what it is: a node's label, or a line's two ends.

    Args:
        finding: A finding whose message quotes node and line ids.
        scene: The scene the ids belong to.

    Returns:
        The finding with a short description after each id, so that a person can find the item
        without reading the scene file.
    """
    nodes = {node.id: node for node in scene.nodes}
    message = finding.message
    for node in nodes.values():
        if f"'{node.id}'" in message and _title_of(node):
            message = message.replace(f"'{node.id}'", f"'{node.id}' ({_title_of(node)})")
    for edge in scene.edges:
        if f"'{edge.id}'" not in message or edge.source not in nodes or edge.target not in nodes:
            continue
        start, end = _title_of(nodes[edge.source]), _title_of(nodes[edge.target])
        if start and end:
            message = message.replace(f"'{edge.id}'", f"'{edge.id}' ({start} to {end})")
    return replace(finding, message=message)


def format_report(findings: list[Finding]) -> str:
    """Write the findings as lines of text for a person or for Claude to read.

    Args:
        findings: The result of ``check_scene``.

    Returns:
        One line per finding, or a single line saying that nothing was found.
    """
    if not findings:
        return "check: no problems found"
    return "\n".join(
        f"{finding.severity.value.upper()} {finding.code.value}: {finding.message}"
        for finding in findings
    )
