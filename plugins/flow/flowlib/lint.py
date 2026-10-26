"""Warn when a diagram breaks a writing or placement rule of its type's design page.

These are rules about the words and the shape of a chart, not about its geometry: the checks in
``check`` look at the pictures, these at the content. Each finding is a warning, because an
author may break a rule on purpose. Which rules apply depends on ``Scene.diagram``.
"""

from .check import Code, Finding, Severity
from .model import Edge, Node, Role, Scene, Shape

FLOWCHART = "flowchart"
SEQUENCE = "sequence"
MAX_WORDS = 4  # words in a node, as the flowchart page allows
MAX_NODES = 15  # nodes in one chart, past which a split is suggested
MIN_EXITS = 2  # exits of a decision
MULTIWAY_EXITS = 3  # exits from which the last one is called else
ELSE_LABEL = "else"
MAX_LABEL_CHARS = 24  # characters in a message label of a sequence diagram
TEXT_SHAPES = (
    Shape.TERMINATOR,
    Shape.FAIL,
    Shape.PROCESS,
    Shape.SUBPROCESS,
    Shape.IO,
    Shape.DOCUMENT,
    Shape.PREPARATION,
)  # outlines whose text the word limit applies to
NOT_DRAWN_AS_NODES = (Shape.FORK, Shape.CONNECTOR)  # marks that do not count as steps
NOTE_ROLES = (Role.LIFELINE,)


def lint_scene(scene: Scene) -> list[Finding]:
    """Run the content rules of the diagram type that drew the scene.

    Args:
        scene: A scene; its ``diagram`` field says which rules apply.

    Returns:
        Warnings; empty for a type that has no content rules.
    """
    if scene.diagram == FLOWCHART:
        return lint_flowchart(scene)
    if scene.diagram == SEQUENCE:
        return lint_sequence(scene)
    return []


def lint_flowchart(scene: Scene) -> list[Finding]:
    """Check the text, the decisions, the size and the start and end of a flowchart."""
    steps = [node for node in scene.nodes if node.shape not in NOT_DRAWN_AS_NODES]
    findings = [_too_long(node) for node in steps if _has_too_many_words(node)]
    findings += _decision_findings(scene)
    if len(steps) > MAX_NODES:
        findings.append(
            _warn(
                Code.CHART_TOO_BIG,
                f"the chart has {len(steps)} steps; more than about {MAX_NODES} is hard to read, "
                "so split it with a subprocess or an off-page connector",
                (),
            )
        )
    return findings + _placement_findings(scene)


def lint_sequence(scene: Scene) -> list[Finding]:
    """Check that no message label is longer than a header-wide phrase."""
    return [
        _warn(
            Code.SEQUENCE_LABEL_LONG,
            f"the label on '{edge.id}' has {len(edge.label.text)} characters; "
            f"about {MAX_LABEL_CHARS} is the most a message label holds",
            (edge.id,),
        )
        for edge in scene.edges
        if edge.label is not None and len(edge.label.text) > MAX_LABEL_CHARS
    ]


def _warn(code: Code, message: str, items: tuple[str, ...]) -> Finding:
    """Build a warning."""
    return Finding(Severity.WARNING, code, message, items)


def _words(node: Node) -> list[str]:
    """Return the words a person reads on a node."""
    return " ".join(node.text).split()


def _has_too_many_words(node: Node) -> bool:
    """Tell whether a node that holds a name is longer than the page allows."""
    return node.shape in TEXT_SHAPES and len(_words(node)) > MAX_WORDS


def _too_long(node: Node) -> Finding:
    """Build the warning for a node with more than four words."""
    return _warn(
        Code.TEXT_TOO_LONG,
        f"'{node.id}' has {len(_words(node))} words; four or fewer read at a glance",
        (node.id,),
    )


def _exits(scene: Scene, node: Node) -> list[Edge]:
    """Return the lines that leave a node, in the order they were written."""
    return [edge for edge in scene.edges if edge.source == node.id]


def _decision_findings(scene: Scene) -> list[Finding]:
    """Check each decision: a question, at least two exits, and an else last of many."""
    findings = []
    for node in scene.nodes:
        if node.shape is not Shape.DECISION:
            continue
        text = " ".join(node.text)
        if text and not text.endswith("?"):
            findings.append(
                _warn(Code.DECISION_NOT_QUESTION, f"'{node.id}' is not a question", (node.id,))
            )
        exits = _exits(scene, node)
        if len(exits) < MIN_EXITS:
            findings.append(
                _warn(
                    Code.DECISION_FEW_EXITS,
                    f"'{node.id}' has {len(exits)} exit; a decision needs two or more",
                    (node.id,),
                )
            )
        elif len(exits) >= MULTIWAY_EXITS and not _ends_with_else(exits):
            findings.append(
                _warn(
                    Code.DECISION_NO_ELSE,
                    f"the last exit of '{node.id}' should be labelled else",
                    (node.id,),
                )
            )
    return findings


def _ends_with_else(exits: list[Edge]) -> bool:
    """Tell whether the last of the exits is labelled else."""
    label = exits[-1].label
    return label is not None and label.text.strip().lower() == ELSE_LABEL


def _placement_findings(scene: Scene) -> list[Finding]:
    """Check that the flow starts at the top left and ends below or to the right."""
    has_input = {edge.target for edge in scene.edges}
    has_output = {edge.source for edge in scene.edges}
    marks = [node for node in scene.nodes if node.shape is Shape.TERMINATOR]
    starts = [node for node in marks if node.id not in has_input]
    ends = [node for node in marks if node.id not in has_output]
    findings = []
    for start in starts[:1]:
        if any(_is_before(node, start) for node in scene.nodes if node is not start):
            findings.append(
                _warn(
                    Code.START_PLACEMENT,
                    f"the start '{start.id}' is not at the top left: something sits above it",
                    (start.id,),
                )
            )
        findings += [
            _warn(
                Code.END_PLACEMENT,
                f"the end '{end.id}' is above and left of the start; end in the bottom or right",
                (end.id,),
            )
            for end in ends
            if _is_before(end, start)
        ]
    return findings


def _is_before(node: Node, other: Node) -> bool:
    """Tell whether a node lies wholly above, or wholly left of, another."""
    return node.y + node.height <= other.y or node.x + node.width <= other.x
