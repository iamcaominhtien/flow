"""The key of a mind map: a sample of each mark the map uses, and what it means."""

from dataclasses import replace

from ..model import (
    DEFAULT_FONT_SIZE_PX,
    Edge,
    Head,
    MindLevel,
    Node,
    PlanView,
    Point,
    Role,
    Shape,
    Status,
    Tone,
)
from ..sizing import estimate_text_width
from ..theme import Theme
from .mindmap_spec import MindSpec

FIRST_PRIORITY = 1  # P1
SECOND_PRIORITY = 2  # P2
KEY_HEIGHT_PX = 40  # the room the key takes above the map
KEY_FONT_PX = 11
SAMPLE_GAP_PX = 10  # between a sample and its words
ENTRY_GAP_PX = 36
LINE_SAMPLE_PX = 34
MARK_ROW_PX = 16
TEXT_SLACK_PX = 6
SAMPLE_WIDTHS = {"p1": 24.0, "p2": 24.0, "done": 16.0, "more": 30.0, "owner": 18.0}
HIDDEN_SAMPLE = 4  # the ``+4`` of the sample, as in the design
OWNER_SAMPLE = "K"


def has_key(spec: MindSpec) -> bool:
    """Tell whether a map uses a mark or a link, and so needs a key."""
    return bool(_entries(spec))


def _entries(spec: MindSpec) -> list[tuple[str, str]]:
    """Return the samples the map needs as ``(sample, words)``, in a fixed order."""
    found = []
    ideas = spec.ideas
    if any(idea.priority == FIRST_PRIORITY for idea in ideas):
        found.append(("p1", "Do first"))
    if any(idea.priority == SECOND_PRIORITY for idea in ideas):
        found.append(("p2", "Do next"))
    if any(idea.is_done for idea in ideas):
        found.append(("done", "Done"))
    if any(idea.hidden for idea in ideas):
        found.append(("more", "More ideas hidden"))
    if any(idea.owner for idea in ideas):
        found.append(("owner", "Owner"))
    if spec.links:
        found.append(("link", "Link between branches"))
    return found


def key_parts(spec: MindSpec, origin: Point, theme: Theme) -> tuple[list[Node], list[Edge]]:
    """Draw the key: each sample, then its words.

    Args:
        spec: The checked spec.
        origin: The left end and the vertical middle of the key.
        theme: The design tokens.

    Returns:
        The samples and words, and the sample of the dashed link.
    """
    x, middle = origin
    nodes: list[Node] = []
    edges: list[Edge] = []
    for index, (sample, words) in enumerate(_entries(spec)):
        if sample == "link":
            ends = ((x, middle), (x + LINE_SAMPLE_PX, middle))
            edges.append(Edge("key-link", Role.LINK, ends, None, None, None, Head.NONE))
            width = LINE_SAMPLE_PX
        else:
            width = SAMPLE_WIDTHS[sample]
            nodes.append(_sample(sample, index, (x, middle - MARK_ROW_PX / 2, width)))
        text_x = x + width + SAMPLE_GAP_PX
        room = estimate_text_width(words, theme.layout, KEY_FONT_PX) + TEXT_SLACK_PX
        nodes.append(_words(index, words, (text_x, middle, room)))
        x = text_x + room + ENTRY_GAP_PX
    return nodes, edges


def _sample(sample: str, index: int, box: tuple[float, float, float]) -> Node:
    """Build the node that shows one mark."""
    x, y, width = box
    views = {
        "p1": PlanView(level=MindLevel.KEY, priority=FIRST_PRIORITY),
        "p2": PlanView(level=MindLevel.KEY, priority=SECOND_PRIORITY),
        "done": PlanView(level=MindLevel.KEY, status=Status.DONE),
        "more": PlanView(level=MindLevel.KEY, hidden=HIDDEN_SAMPLE),
        "owner": PlanView(level=MindLevel.KEY, initials=OWNER_SAMPLE, person_tone=Tone.GREEN),
    }
    return Node(
        f"key-sample-{index}", Shape.LEAF, x, y, width, MARK_ROW_PX, (), None, None, None,
        DEFAULT_FONT_SIZE_PX, plan=views[sample],
    )  # fmt: skip


def _words(index: int, words: str, box: tuple[float, float, float]) -> Node:
    """Build the node that holds the words of one entry."""
    x, middle, width = box
    node = Node(
        f"key-text-{index}", Shape.LABEL, x, middle - MARK_ROW_PX, width, 2 * MARK_ROW_PX,
        (words,), None, None, None, KEY_FONT_PX, plan=PlanView(),
    )  # fmt: skip
    return replace(node, font_size=KEY_FONT_PX)
