"""Checks of the notation rules of a data flow diagram and of a BPMN diagram.

They run on the finished scene, so they also hold for a diagram that was imported or edited.
"""

from collections import Counter

from .check import Code, Finding, Severity
from .model import Frame, FrameVariant, Scene, Shape

CONTEXT_NUMBER = "0"
TOP_PROCESSES = (4, 7)  # a level 1 diagram opens its process into this many (design 14)
OPENED_PROCESSES = (3, 6)  # a level 2 diagram opens one of them into this many
DFD = "dfd"


def check_notation(scene: Scene) -> list[Finding]:
    """Run the checks that belong to the type of diagram a scene was drawn from.

    Args:
        scene: The scene to check.

    Returns:
        The findings; empty for a type that has no notation checks.
    """
    if scene.diagram == DFD:
        return [*_check_process_count(scene), *_check_stores(scene)]
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
