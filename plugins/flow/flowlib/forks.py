"""Stretch the bar of a parallel split or join over the steps it joins, in layout space."""

from dataclasses import replace

from .model import Node, Role, Shape
from .spec import Spec
from .theme import LayoutRules

# A data stream that leaves a bar is a message, not a branch: it does not widen the bar.
NON_BRANCH_ROLES = (Role.DATA, Role.BACK)


def is_inside(node: Node, x: float) -> bool:
    """Tell whether a vertical line at ``x`` meets a bar, that is, lies within its width."""
    return node.x <= x <= node.x + node.width


def span_forks(spec: Spec, nodes: dict[str, Node], rules: LayoutRules) -> dict[str, Node]:
    """Widen each bar so that it reaches every step it splits into or joins, plus an overhang.

    Args:
        spec: The flowchart description, which says what each bar is joined to.
        nodes: The placed nodes, in layout space where the flow runs down.
        rules: The layout rules, which hold the overhang.

    Returns:
        A copy of ``nodes`` in which each bar spans the centres of its neighbours; the bar keeps
        its centre line and its thickness. A bar with no neighbour keeps its size.
    """
    spanned = dict(nodes)
    for node in spec.nodes:
        if node.kind is not Shape.FORK:
            continue
        centres = _neighbour_centres(spec, node.id, nodes)
        if not centres:
            continue
        bar = nodes[node.id]
        left = min(centres) - rules.fork_overhang
        right = max(centres) + rules.fork_overhang
        spanned[node.id] = replace(bar, x=left, width=right - left)
    return spanned


def _neighbour_centres(spec: Spec, bar_id: str, nodes: dict[str, Node]) -> list[float]:
    """Return the centre x of every step on a branch of the bar, before or after it."""
    centres = []
    for edge in spec.edges:
        if edge.role in NON_BRANCH_ROLES:
            continue
        for near, far in ((edge.source, edge.target), (edge.target, edge.source)):
            if near == bar_id and far != bar_id:
                other = nodes[far]
                centres.append(other.x + other.width / 2)
    return centres
