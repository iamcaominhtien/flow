"""Turn routed lines and placed boxes into a finished scene, for the diagrams on a grid."""

from dataclasses import dataclass
from itertools import pairwise

from ..canvas import fit_canvas
from ..labels import place_labels
from ..model import (
    Edge,
    EdgeLabel,
    Frame,
    Head,
    LabelKind,
    Node,
    Point,
    Role,
    Scene,
)

EDGE_ID_PREFIX = "e"


@dataclass(frozen=True)
class Line:
    """One line of a grid diagram: where it goes, what it says and how it looks."""

    source: str
    target: str
    label: str
    role: Role


@dataclass(frozen=True)
class Heading:
    """The title and the description of a diagram."""

    title: str | None
    description: str | None


def build_edges(
    lines: tuple[Line, ...], routes: list[list[Point]], node_ids: set[str]
) -> tuple[Edge, ...]:
    """Build the edge of every line from its route.

    Args:
        lines: The lines, in drawing order.
        routes: One route per line, in the same order.
        node_ids: The ids of the boxes; a line that ends on a frame has no box at that end.

    Returns:
        The edges, each with its label chip in the middle of its longest segment.
    """
    return tuple(
        Edge(
            id=f"{EDGE_ID_PREFIX}{index + 1}",
            role=line.role,
            points=tuple(route),
            label=EdgeLabel(line.label, _middle_of_longest(route), LabelKind.PLAIN)
            if line.label
            else None,
            source=line.source if line.source in node_ids else None,
            target=line.target if line.target in node_ids else None,
            head=Head.FILLED,
        )
        for index, (line, route) in enumerate(zip(lines, routes, strict=True))
    )


def finish_scene(
    heading: Heading, parts: tuple[tuple[Frame, ...], tuple[Node, ...], tuple[Edge, ...]]
) -> Scene:
    """Put the frames, nodes and edges in a scene, move the chips off boxes and fit the canvas.

    Args:
        heading: The title and description.
        parts: The frames (outermost first), the nodes and the edges.

    Returns:
        The scene.
    """
    frames, nodes, edges = parts
    scene = Scene(
        width=0,
        height=0,
        title=heading.title,
        description=heading.description,
        frames=frames,
        nodes=nodes,
        edges=edges,
    )
    return fit_canvas(place_labels(scene))


def _middle_of_longest(route: list[Point]) -> Point:
    """Return the middle of the longest segment of a route, where its label goes."""
    start, end = max(pairwise(route), key=lambda segment: _length(*segment))
    return ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)


def _length(start: Point, end: Point) -> float:
    """Return the length of a horizontal or vertical segment."""
    return abs(end[0] - start[0]) + abs(end[1] - start[1])
