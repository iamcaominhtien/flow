"""Check a scene for the problems the design rules forbid, without drawing it.

Each check returns findings that name the items involved, so that the author can change the
spec (a hint, shorter text) and build again.
"""

import math
from dataclasses import dataclass, replace
from enum import StrEnum
from itertools import combinations, pairwise

from .html_nodes import CAPTION_FONT_SIZE_PX, CAPTION_GAP_PX, CAPTION_WIDTH_PX
from .model import Edge, Frame, Node, Point, Role, Scene, Shape
from .sizing import LINE_HEIGHT_FACTOR, estimate_text_width
from .text_area import text_area_width
from .theme import LayoutRules, load_theme

BORDER_TOLERANCE_PX = 1.0  # a part this close to a frame's border counts as inside or outside
NODE_CLEARANCE_PX = 4.0  # nodes closer than this count as touching
LINE_CLEARANCE_PX = 2.0
MIN_CROSSING_EDGES = 2
MIN_OVERLAP_PX = 32.0  # a shorter shared stretch is a junction at a node, not an overlap
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


def label_rect(edge: Edge, rules: LayoutRules) -> Rect | None:
    """Return the rectangle a label chip covers, estimated from its text, or None."""
    if edge.label is None:
        return None
    width = estimate_text_width(edge.label.text, rules, rules.chip_font_size) + rules.chip_padding_x
    half_width, half_height = width / 2, rules.chip_height / 2
    at_x, at_y = edge.label.at
    return Rect(at_x - half_width, at_y - half_height, at_x + half_width, at_y + half_height)


def caption_rect(node: Node, rules: LayoutRules) -> Rect | None:
    """Return the rectangle the caption under a node covers, or None without a caption."""
    if not node.caption:
        return None
    text_width = estimate_text_width(node.caption, rules, CAPTION_FONT_SIZE_PX)
    lines = max(1, math.ceil(text_width / CAPTION_WIDTH_PX))
    height = lines * CAPTION_FONT_SIZE_PX * LINE_HEIGHT_FACTOR
    centre = node.x + node.width / 2
    top = node.y + node.height + CAPTION_GAP_PX
    return Rect(centre - CAPTION_WIDTH_PX / 2, top, centre + CAPTION_WIDTH_PX / 2, top + height)


def check_nodes_overlap(scene: Scene) -> list[Finding]:
    """Report every pair of nodes that touch or overlap."""
    findings = []
    for first, second in combinations(scene.nodes, 2):
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
        if edge.role is Role.LIFELINE:
            continue
        for node in scene.nodes:
            if node.id in (edge.source, edge.target):
                continue
            rect = node_rect(node)
            if any(
                _segment_rect(start, end).overlaps(rect, -LINE_CLEARANCE_PX)
                for start, end in pairwise(edge.points)
            ):
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
            if any(
                _segment_rect(start, end).overlaps(caption, -LINE_CLEARANCE_PX)
                for start, end in pairwise(edge.points)
            ):
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
    for node in scene.nodes:
        if not node.text:
            continue
        room = text_area_width(node.shape, node.width, node.icon is not None)
        if node.card:
            room = node.width - 2 * (rules.card_padding + rules.card_pill_padding)
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
    drawn = [edge for edge in scene.edges if edge.role is not Role.LIFELINE]
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
    drawn = [edge for edge in scene.edges if edge.role is not Role.LIFELINE]
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

    An activation bar is left out: it is long on purpose and may run past a fragment.
    """
    parts = [(node.id, node_rect(node)) for node in scene.nodes if node.shape is not Shape.BAR]
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
    rules = load_theme().layout
    findings = [
        *check_nodes_overlap(scene),
        *check_lines_through_nodes(scene),
        *check_labels(scene, rules),
        *check_captions(scene, rules),
        *check_canvas(scene, rules),
        *check_text_fit(scene, rules),
        *check_crossings(scene),
        *check_overlaps(scene),
        *check_borders(scene, rules),
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
