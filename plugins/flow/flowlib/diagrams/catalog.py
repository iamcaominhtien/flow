"""The graph-family types that are only data: C4, cloud, use case, class, screen flow."""

from typing import Any

from ..model import Head, Shape
from ..reader import Reader
from .graph import GraphType, LineKind, rows_from

FLOW = LineKind()
DASHED = LineKind(dashed=True, head=Head.OPEN)
PLAIN = LineKind(head=Head.NONE)
CALLS = {"call": FLOW, "async": LineKind(dashed=True)}


def _class_sections(raw: dict[str, Any], where: str, read: Reader) -> dict[str, Any]:
    """Return the attribute and method rows of a class as the sections of its table."""
    attributes = rows_from(raw, "attributes", where, read)
    methods = rows_from(raw, "methods", where, read)
    return {"sections": tuple(section for section in (attributes, methods) if section)}


USE_CASE = GraphType(
    name="use case",
    nodes_key="items",
    links_key="links",
    kinds={"actor": Shape.ACTOR, "usecase": Shape.ELLIPSE},
    default_kind="usecase",
    line_kinds={
        "association": PLAIN,
        "include": DASHED,
        "extend": DASHED,
        "generalizes": LineKind(head=Head.TRIANGLE),
    },
    default_line="association",
    has_zones=True,
)
CLASS = GraphType(
    name="class",
    nodes_key="classes",
    links_key="relations",
    kinds={"class": Shape.TABLE},
    default_kind="class",
    line_kinds={
        "association": PLAIN,
        "inheritance": LineKind(head=Head.TRIANGLE),
        "implements": LineKind(dashed=True, head=Head.TRIANGLE),
        "composition": LineKind(head=Head.NONE, tail=Head.DIAMOND_FILLED),
        "aggregation": LineKind(head=Head.NONE, tail=Head.DIAMOND),
        "dependency": DASHED,
    },
    default_line="association",
    extra_node_keys=frozenset({"attributes", "methods"}),
    extra=_class_sections,
)
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
    "usecase": USE_CASE,
    "class": CLASS,
    "screen": SCREEN,
}
