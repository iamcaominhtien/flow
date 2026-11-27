"""Warn when a diagram breaks a writing or placement rule of its type's design page.

These are rules about the words and the shape of a chart, not about its geometry: the checks in
``check`` look at the pictures, these at the content. Each finding is a warning, because an
author may break a rule on purpose. The exception is a flowchart that goes on past an end: it says
the opposite of what the chart means, so it is an error. Which rules apply depends on
``Scene.diagram``.
"""

from collections import Counter

from .check import Code, Finding, Severity
from .lint_board import lint_kanban, lint_roadmap
from .lint_explainer import lint_explainer
from .lint_wire import lint_wire_screens, lint_wireframe
from .model import Edge, FrameVariant, MindLevel, Node, Role, Scene, Shape
from .theme import load_theme

FLOWCHART = "flowchart"
SEQUENCE = "sequence"
MAX_WORDS = 4  # words in a node, as the flowchart page allows
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
MIN_STEPS_FOR_MIX = 8  # a shorter chart may well use one kind of step
MAIN_KIND_SHARE = 0.6  # past this share of one kind, a chart reads as a list drawn in boxes
FEW_KINDS = 2  # a chart this long with this many kinds of step or fewer reads the same way
LONG_RATIO = 4.0  # a chart this many times longer than it is wide is scrolled, not seen
AUTHOR_HINT = "or lay the chart out by hand with /flow:author"
NOTE_ROLES = (Role.LIFELINE,)
MAX_ROLE_WORDS = 6  # a role longer than this is a sentence, not a noun phrase
LEGEND_PREFIXES = ("legend", "key")  # the ids of the samples and the words of a legend


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
    return PLANNING_LINTS.get(scene.diagram, lambda _scene: [])(scene)


def lint_flowchart(scene: Scene) -> list[Finding]:
    """Check the text, the decisions and the start and end of a flowchart."""
    steps = [node for node in scene.nodes if node.shape not in NOT_DRAWN_AS_NODES]
    findings = [_too_long(node) for node in steps if _has_too_many_words(node)]
    findings += _decision_findings(scene)
    findings += [_end_has_exit(scene, node) for node in steps if _goes_on_past_end(scene, node)]
    findings += _few_shapes(steps) + _long_column(scene)
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


def _few_shapes(steps: list[Node]) -> list[Finding]:
    """Suggest more kinds of step when a chart is mostly one kind, so it reads as a list.

    Args:
        steps: The nodes of the flowchart drawn as steps.

    Returns:
        One ``few-shapes`` warning, or nothing.
    """
    middle = [node for node in steps if node.shape is not Shape.TERMINATOR]
    kinds = Counter(node.shape for node in middle)
    if len(middle) < MIN_STEPS_FOR_MIX or not _is_mainly_one_kind(kinds, len(middle)):
        return []
    shape, count = kinds.most_common(1)[0]
    message = (
        f"{count} of {len(middle)} steps are {shape.value} and only {len(kinds)} kinds are used; "
        f"group steps into subprocess steps or lanes, show data with io or document, {AUTHOR_HINT}"
    )
    return [_warn(Code.FEW_SHAPES, message, ())]


def _long_column(scene: Scene) -> list[Finding]:
    """Suggest another arrangement when a chart is one long column or row, scrolled, not seen.

    Args:
        scene: The laid out flowchart.

    Returns:
        One ``long-column`` warning, or nothing.
    """
    long_side, short_side = sorted((scene.width, scene.height), reverse=True)
    if not short_side or long_side / short_side <= LONG_RATIO:
        return []
    message = (
        f"the chart is {long_side:.0f} px long and {short_side:.0f} px across; group steps into "
        f"subprocess steps or lanes, {AUTHOR_HINT}"
    )
    return [_warn(Code.LONG_COLUMN, message, ())]


def _is_mainly_one_kind(kinds: Counter[Shape], step_count: int) -> bool:
    """Tell whether one kind of step dominates, or too few kinds are used.

    Args:
        kinds: How many steps there are of each shape.
        step_count: The number of steps counted.

    Returns:
        True when the chart uses few kinds, or one kind takes more than its share.
    """
    return len(kinds) <= FEW_KINDS or max(kinds.values()) / step_count > MAIN_KIND_SHARE


def _goes_on_past_end(scene: Scene, node: Node) -> bool:
    """Tell whether a line leaves a failed end, or an end that a line reaches.

    A terminator with lines out and none in is the start; one with both is an end the flow
    walks through, so what follows it reads as happening after the flow has stopped.

    Args:
        scene: The laid out flowchart.
        node: The step to look at.

    Returns:
        True when the flow goes on from an end.
    """
    if not _exits(scene, node):
        return False
    if node.shape is Shape.FAIL:
        return True
    return node.shape is Shape.TERMINATOR and any(edge.target == node.id for edge in scene.edges)


def _end_has_exit(scene: Scene, node: Node) -> Finding:
    """Build the error for an end that the flow goes on from.

    Args:
        scene: The laid out flowchart.
        node: The end that a line leaves.

    Returns:
        An ``end-has-exit`` error that names the end and where its lines go.
    """
    targets = ", ".join(f"'{edge.target}'" for edge in _exits(scene, node))
    message = (
        f"'{node.id}' is an end but a line leaves it to {targets}; "
        "end the path there, or make the step a process"
    )
    return Finding(Severity.ERROR, Code.END_HAS_EXIT, message, (node.id,))


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


def lint_gantt(scene: Scene) -> list[Finding]:
    """Warn when a Gantt chart has more rows than a page holds (about 15)."""
    rows = len([f for f in scene.frames if f.variant is FrameVariant.BAND])
    rows += len(
        [
            n
            for n in scene.nodes
            if n.shape in (Shape.PLAN_BAR, Shape.MILESTONE) and not _is_legend(n)
        ]
    )
    limit = load_theme(scene.theme).planning.gantt.max_rows
    if rows <= limit:
        return []
    message = f"the chart has {rows} rows; about {limit} fit a page, so draw one Gantt per phase"
    return [_warn(Code.GANTT_TOO_MANY_ROWS, message, ())]


def lint_org(scene: Scene) -> list[Finding]:
    """Warn when an org chart has more than four levels, or a role that is a sentence."""
    cards = [n for n in scene.nodes if n.shape is Shape.PERSON_CARD and not _is_legend(n)]
    levels = len({round(card.y) for card in cards})
    limit = load_theme(scene.theme).planning.org.max_levels
    findings = []
    if levels > limit:
        message = (
            f"the chart has {levels} levels; {limit} fit a page, so draw one chart per department"
        )
        findings.append(_warn(Code.ORG_TOO_MANY_LEVELS, message, ()))
    for card in cards:
        role = " ".join(card.detail)
        if len(role.split()) > MAX_ROLE_WORDS or role.endswith("."):
            message = (
                f"the role of '{card.id}' is a sentence; write a noun phrase such as "
                "Mobile developer"
            )
            findings.append(_warn(Code.ORG_ROLE_SENTENCE, message, (card.id,)))
    return findings


def lint_mindmap(scene: Scene) -> list[Finding]:
    """Warn about a phrase of more than four words, and about too many links between ideas."""
    rules = load_theme(scene.theme).planning.mind
    findings = []
    for node in scene.nodes:
        is_phrase = node.plan is not None and node.plan.level not in (
            None,
            MindLevel.CENTRE,
            MindLevel.KEY,
        )
        if is_phrase and len(_words(node)) > rules.max_leaf_words:
            message = (
                f"'{node.id}' has {len(_words(node))} words; "
                f"{rules.max_leaf_words} or fewer read at a glance"
            )
            findings.append(_warn(Code.MIND_PHRASE_LONG, message, (node.id,)))
    links = [
        edge for edge in scene.edges if edge.role is Role.LINK and not edge.id.startswith("key")
    ]
    if len(links) > rules.max_links:
        message = (
            f"the map has {len(links)} links; about {rules.max_links} is the most "
            "before it turns into a tangle"
        )
        findings.append(_warn(Code.MIND_TOO_MANY_LINKS, message, ()))
    return findings


def _is_legend(node: Node) -> bool:
    """Tell a sample or the words of a legend from a part of the diagram."""
    return node.id.startswith(LEGEND_PREFIXES)


PLANNING_LINTS = {
    "gantt": lint_gantt,
    "org": lint_org,
    "mindmap": lint_mindmap,
    "kanban": lint_kanban,
    "roadmap": lint_roadmap,
    "explainer": lint_explainer,
    "wireframe": lint_wireframe,
    "screen": lint_wire_screens,
}
