"""Check a scene for the problems the design rules forbid, without drawing it.

Each check returns findings that name the items involved, so that the author can change the
spec (a hint, shorter text) and build again.
"""

from dataclasses import dataclass, replace
from enum import StrEnum
from itertools import combinations, pairwise

from .model import Edge, Node, Point, Role, Scene
from .sizing import LINE_HEIGHT_FACTOR, estimate_text_width
from .text_area import text_area_width
from .theme import LayoutRules, load_theme

NODE_CLEARANCE_PX = 4.0  # nodes closer than this count as touching
LINE_CLEARANCE_PX = 2.0
MIN_CROSSING_EDGES = 2


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


def _node_rect(node: Node) -> Rect:
    """Return the rectangle a node covers."""
    return Rect(node.x, node.y, node.x + node.width, node.y + node.height)


def _segment_rect(start: Point, end: Point) -> Rect:
    """Return the thin rectangle that covers a horizontal or vertical segment."""
    return Rect(
        min(start[0], end[0]), min(start[1], end[1]), max(start[0], end[0]), max(start[1], end[1])
    )


def _label_rect(edge: Edge, rules: LayoutRules) -> Rect | None:
    """Return the rectangle a label chip covers, estimated from its text, or None."""
    if edge.label is None:
        return None
    width = estimate_text_width(edge.label.text, rules, rules.chip_font_size) + rules.chip_padding_x
    half_width, half_height = width / 2, rules.chip_height / 2
    at_x, at_y = edge.label.at
    return Rect(at_x - half_width, at_y - half_height, at_x + half_width, at_y + half_height)


def check_nodes_overlap(scene: Scene) -> list[Finding]:
    """Report every pair of nodes that touch or overlap."""
    findings = []
    for first, second in combinations(scene.nodes, 2):
        if _node_rect(first).overlaps(_node_rect(second), NODE_CLEARANCE_PX):
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
            rect = _node_rect(node)
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
    chips = [(edge.id, rect) for edge in scene.edges if (rect := _label_rect(edge, rules))]
    findings = []
    for edge_id, rect in chips:
        for node in scene.nodes:
            if rect.overlaps(_node_rect(node)):
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


def check_canvas(scene: Scene, rules: LayoutRules) -> list[Finding]:
    """Report nodes, lines and labels that reach outside the canvas."""
    canvas = Rect(0, 0, scene.width, scene.height)
    findings = []
    for node in scene.nodes:
        rect = _node_rect(node)
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
        label = _label_rect(edge, rules)
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
        *check_canvas(scene, rules),
        *check_text_fit(scene, rules),
        *check_crossings(scene),
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
