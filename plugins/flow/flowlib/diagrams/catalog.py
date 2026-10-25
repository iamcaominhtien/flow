"""The graph-family types that are only data: DFD, C4, cloud, use case, BPMN, class, screen flow."""

from typing import Any

from ..model import Head, Role, Shape
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


DFD = GraphType(
    name="DFD",
    nodes_key="elements",
    links_key="flows",
    kinds={"process": Shape.ELLIPSE, "external": Shape.ENTITY, "store": Shape.STORE},
    default_kind="process",
    line_kinds={"flow": FLOW},
    default_line="flow",
    default_role=Role.DATA,
)
C4 = GraphType(
    name="C4",
    nodes_key="elements",
    links_key="relations",
    kinds={
        "person": Shape.ACTOR,
        "system": Shape.PROCESS,
        "external": Shape.SUBPROCESS,
        "container": Shape.PROCESS,
        "component": Shape.PROCESS,
        "database": Shape.CYLINDER,
    },
    default_kind="system",
    line_kinds=CALLS,
    default_line="call",
    has_zones=True,
)
CLOUD = GraphType(
    name="cloud",
    nodes_key="resources",
    links_key="links",
    kinds={
        "service": Shape.PROCESS,
        "client": Shape.TERMINATOR,
        "external": Shape.SUBPROCESS,
        "balancer": Shape.DECISION,
        "database": Shape.CYLINDER,
        "storage": Shape.STORE,
        "queue": Shape.PREPARATION,
    },
    default_kind="service",
    line_kinds=CALLS,
    default_line="call",
    has_zones=True,
)
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
BPMN = GraphType(
    name="BPMN",
    nodes_key="elements",
    links_key="flows",
    kinds={
        "start": Shape.START,
        "end": Shape.END,
        "event": Shape.INTERMEDIATE,
        "timer": Shape.INTERMEDIATE,
        "message": Shape.INTERMEDIATE,
        "error": Shape.INTERMEDIATE,
        "task": Shape.PROCESS,
        "subprocess": Shape.SUBPROCESS,
        "gateway": Shape.DECISION,
        "exclusive": Shape.DECISION,
        "parallel": Shape.DECISION,
        "document": Shape.DOCUMENT,
    },
    default_kind="task",
    line_kinds={"sequence": FLOW, "message": LineKind(dashed=True, head=Head.OPEN, tail=Head.DOT)},
    default_line="sequence",
    unlabelled_kinds=frozenset(
        {"start", "end", "event", "timer", "message", "error", "gateway", "exclusive", "parallel"}
    ),
    has_zones=True,
    zones_are_lanes=True,
    kind_icons={
        "timer": "clock",
        "message": "mail",
        "error": "warn",
        "exclusive": "x",
        "parallel": "plus",
    },
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
    "dfd": DFD,
    "c4": C4,
    "cloud": CLOUD,
    "usecase": USE_CASE,
    "bpmn": BPMN,
    "class": CLASS,
    "screen": SCREEN,
}
