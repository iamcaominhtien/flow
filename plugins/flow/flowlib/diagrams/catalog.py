"""The graph-family types that are only data: screen flow."""

from ..model import Head, Shape
from .graph import GraphType, LineKind

FLOW = LineKind()
DASHED = LineKind(dashed=True, head=Head.OPEN)
PLAIN = LineKind(head=Head.NONE)
CALLS = {"call": FLOW, "async": LineKind(dashed=True)}


SCREEN = GraphType(
    name="screen",
    nodes_key="screens",
    links_key="taps",
    kinds={
        "screen": Shape.PROCESS,
        "dialog": Shape.SUBPROCESS,
        "decision": Shape.DECISION,
        "start": Shape.START,
        "end": Shape.END,
    },
    default_kind="screen",
    line_kinds={"tap": FLOW, "back": LineKind(dashed=True, head=Head.OPEN)},
    default_line="tap",
    unlabelled_kinds=frozenset({"start", "end"}),
)

TYPES: dict[str, GraphType] = {
    "screen": SCREEN,
}
