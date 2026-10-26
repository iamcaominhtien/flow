"""Checks of the notation rules of a data flow diagram and of a BPMN diagram.

They run on the finished scene, so they also hold for a diagram that was imported or edited.
"""

from collections import Counter

from .check import Code, Finding, Rect, Severity, frame_rect, node_rect
from .model import Frame, FrameVariant, Role, Scene, Shape

CONTEXT_NUMBER = "0"
TOP_PROCESSES = (4, 7)  # a level 1 diagram opens its process into this many (design 14)
OPENED_PROCESSES = (3, 6)  # a level 2 diagram opens one of them into this many
DFD = "dfd"
BPMN = "bpmn"
MAX_ELEMENTS = 25  # design 11: longer than this, use sub-processes
MAX_BENDS = 2


def check_notation(scene: Scene) -> list[Finding]:
    """Run the checks that belong to the type of diagram a scene was drawn from.

    Args:
        scene: The scene to check.

    Returns:
        The findings; empty for a type that has no notation checks.
    """
    if scene.diagram == DFD:
        return [*_check_process_count(scene), *_check_stores(scene)]
    if scene.diagram == BPMN:
        return [*_check_size(scene), *_check_bends(scene), *_check_main_path(scene)]
    return []


def _opened_frame(scene: Scene) -> Frame | None:
    """Return the dashed frame of an opened process, or None on a diagram that has none."""
    return next((f for f in scene.frames if f.variant is FrameVariant.OPENED), None)


def _check_process_count(scene: Scene) -> list[Finding]:
    """Warn when a level has fewer or more processes than the design allows."""
    processes = [node for node in scene.nodes if node.shape is Shape.DFD_PROCESS]
    if any(node.number == CONTEXT_NUMBER for node in processes):
        return []
    low, high = OPENED_PROCESSES if _opened_frame(scene) else TOP_PROCESSES
    if low <= len(processes) <= high:
        return []
    level = 2 if _opened_frame(scene) else 1
    message = (
        f"level {level} has {len(processes)} processes; the design asks for {low} to {high}"
        " (open or merge processes to fit)"
    )
    return [Finding(Severity.WARNING, Code.DFD_PROCESS_COUNT, message, ())]


def _check_stores(scene: Scene) -> list[Finding]:
    """Warn about a store that is only written or only read: data stored but never used."""
    reads = Counter(edge.source for edge in scene.edges)
    writes = Counter(edge.target for edge in scene.edges)
    findings = []
    for node in scene.nodes:
        if node.shape is not Shape.DFD_STORE:
            continue
        name = " ".join(node.text)
        if not writes[node.id] and not reads[node.id]:
            message = f"store '{node.id}' ({name}) has no flow at all"
        elif not reads[node.id]:
            message = f"store '{node.id}' ({name}) is written but never read: stored, never used"
        elif not writes[node.id]:
            message = f"store '{node.id}' ({name}) is read but never written: used, never stored"
        else:
            continue
        findings.append(Finding(Severity.WARNING, Code.DFD_STORE_ONE_WAY, message, (node.id,)))
    return findings


def _check_size(scene: Scene) -> list[Finding]:
    """Warn when a BPMN diagram has more elements than one page should hold."""
    count = len([node for node in scene.nodes if node.host is None])
    if count <= MAX_ELEMENTS:
        return []
    message = f"the diagram has {count} elements; about {MAX_ELEMENTS} is the most one page holds"
    return [
        Finding(Severity.WARNING, Code.BPMN_TOO_MANY_ELEMENTS, message + ": use sub-processes", ())
    ]


def _check_bends(scene: Scene) -> list[Finding]:
    """Warn about a BPMN route with more than two bends."""
    return [
        Finding(
            Severity.WARNING,
            Code.BPMN_ROUTE_BENDS,
            f"line '{edge.id}' has {len(edge.points) - 2} bends; "
            f"BPMN routes have at most {MAX_BENDS}",
            (edge.id,),
        )
        for edge in scene.edges
        if len(edge.points) - 2 > MAX_BENDS
    ]


def _pools(scene: Scene) -> list[Rect]:
    """Return the rectangle of each pool: the outermost pool frames and the black-box bars."""
    rects = [
        frame_rect(frame)
        for frame in scene.frames
        if frame.variant in (FrameVariant.POOL, FrameVariant.BLACK_BOX)
    ]
    return [r for r in rects if not any(o is not r and _contains(o, r) for o in rects)]


def _contains(outer: Rect, inner: Rect) -> bool:
    """Tell whether a rectangle lies inside another."""
    return (
        outer.left <= inner.left
        and outer.top <= inner.top
        and outer.right >= inner.right
        and outer.bottom >= inner.bottom
        and outer != inner
    )


def _check_main_path(scene: Scene) -> list[Finding]:
    """Warn when the blue main path is drawn in more than one pool: one per diagram."""
    nodes = {node.id: node for node in scene.nodes}
    pools = _pools(scene)
    found: set[int] = set()
    for edge in scene.edges:
        node = nodes.get(edge.source or "")
        if edge.role is not Role.MAIN or node is None:
            continue
        middle = node_rect(node)
        found.update(index for index, pool in enumerate(pools) if _contains(pool, middle))
    if len(found) <= 1:
        return []
    message = "the main path (blue) is in more than one pool: mark one path, not one per pool"
    return [Finding(Severity.WARNING, Code.BPMN_MAIN_PATH, message, ())]
