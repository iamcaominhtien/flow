"""The dependency lines of a Gantt chart, and the critical path that sets the end date.

A line runs from the end of a task to the start of the next one (finish to start). It leaves a
little to the right of the bar, goes down the gap between the two columns and enters the start
of the next bar. The critical path is the one chain of items whose lines are drawn thick, blue
and animated: the items marked ``critical``, or else the longest chain that ends last.
"""

from ..model import Edge, Head, Node, Point, Role, Shape
from .gantt_spec import GanttSpec

Link = tuple[str, str]  # (the item that finishes first, the item that follows)
MIN_ENTRY_RUN_PX = 4  # the last horizontal run into a bar is at least this long


def critical_links(spec: GanttSpec) -> set[Link]:
    """Return the links of the critical path.

    Args:
        spec: The checked spec.

    Returns:
        The marked links when some task is marked ``critical``; otherwise the chain of links that
        ends last, found by taking the last finishing item and walking back through the
        predecessor that finishes last (the first written when two finish together).
    """
    marked = {task.id for task in spec.tasks if task.is_critical}
    links = _links(spec)
    if marked:
        return {link for link in links if link[0] in marked and link[1] in marked}
    return _longest_chain(spec, links)


def _links(spec: GanttSpec) -> list[Link]:
    """Return every ``after`` as a link, in the order written."""
    return [(name, item.id) for item in (*spec.tasks, *spec.milestones) for name in item.after]


def _longest_chain(spec: GanttSpec, links: list[Link]) -> set[Link]:
    """Return the chain of links that ends last; empty when no item follows another."""
    ends = {task.id: task.end for task in spec.tasks}
    ends.update({each.id: each.at for each in spec.milestones})
    followed = {first for first, _ in links}
    depth = {name: _depth(name, links) for name in ends}
    finals = [name for name in ends if name not in followed and depth[name] > 0]
    if not finals:
        return set()
    last = max(finals, key=lambda name: (ends[name], depth[name]))
    chain: set[Link] = set()
    seen = {last}
    while True:
        before = [first for first, second in links if second == last and first not in seen]
        if not before:
            return chain
        latest = max(ends[name] for name in before)
        last_before = next(name for name in before if ends[name] == latest)
        chain.add((last_before, last))
        seen.add(last_before)
        last = last_before


def _depth(name: str, links: list[Link]) -> int:
    """Return how many links lead to an item, following the first one written at each step."""
    depth = 0
    seen = {name}
    while True:
        before = [first for first, second in links if second == name and first not in seen]
        if not before:
            return depth
        name, depth = before[0], depth + 1
        seen.add(name)


def dependency_edges(spec: GanttSpec, nodes: dict[str, Node], gap: float) -> list[Edge]:
    """Draw every dependency, the ordinary ones first so that the critical path lies on top.

    Args:
        spec: The checked spec.
        nodes: The bar or diamond of every task and milestone, by id.
        gap: How far right of a bar its line leaves.

    Returns:
        One edge per dependency.
    """
    critical = critical_links(spec)
    ordered = sorted(_links(spec), key=lambda link: link in critical)
    return [_edge(link, nodes, gap, link in critical) for link in ordered]


def _edge(link: Link, nodes: dict[str, Node], gap: float, is_critical: bool) -> Edge:
    """Build the line of one dependency."""
    before, after = nodes[link[0]], nodes[link[1]]
    start = (before.x + before.width, before.y + before.height / 2)
    return Edge(
        id=f"after-{link[0]}-{link[1]}",
        role=Role.MAIN if is_critical else Role.NEXT,
        points=_route(start, after, gap),
        label=None,
        source=before.id,
        target=after.id,
        head=Head.FILLED,
    )


def _route(start: Point, after: Node, gap: float) -> tuple[Point, ...]:
    """Route a line from the end of an item to a task bar or a milestone."""
    if after.shape is Shape.MILESTONE:
        centre = after.x + after.width / 2
        return (start, (centre, start[1]), (centre, after.y))
    end = (after.x, after.y + after.height / 2)
    down = min(start[0] + gap, (start[0] + end[0]) / 2)
    if end[0] - down < MIN_ENTRY_RUN_PX:
        down = (start[0] + end[0]) / 2
    return (start, (down, start[1]), (down, end[1]), end)
