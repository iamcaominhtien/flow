"""The flowchart: parse a spec, place the nodes on a grid, route the lines."""

from .. import spec as spec_io
from .. import transpose
from ..canvas import fit_canvas
from ..fold import Folded, fold
from ..labels import place_labels
from ..layered import build_grid
from ..model import Direction, Scene
from ..placement import place_nodes
from ..routing import Port, route_edges
from ..spec import Spec
from ..theme import load_theme


def layout(spec: Spec) -> Scene:
    """Place and route a flowchart, giving a scene ready to draw.

    Args:
        spec: The flowchart description.

    Returns:
        The scene: sized nodes at pixel positions, routed lines, swimlane frames, and a canvas
        that holds them.
    """
    rules = load_theme().layout
    if spec.illustrated:
        spec = spec_io.with_cards(spec)
    grid = build_grid(spec)
    placement = place_nodes(spec, grid, rules)
    nodes = tuple(placement.nodes.values())
    frames = placement.frames
    edges = tuple(route_edges(spec, grid, placement, rules))
    caption_port = Port.RIGHT if spec.direction is Direction.RIGHT else Port.BOTTOM
    folded = fold(Folded(nodes, frames, edges), rules, caption_port)
    nodes, frames, edges = folded.nodes, folded.frames, folded.edges
    if spec.direction is Direction.RIGHT:
        nodes = tuple(transpose.node(node) for node in nodes)
        frames = tuple(transpose.frame(frame) for frame in frames)
        edges = tuple(transpose.edge(edge) for edge in edges)
    scene = Scene(
        width=0,
        height=0,
        title=spec.title,
        description=spec.description,
        frames=frames,
        nodes=nodes,
        edges=edges,
    )
    return fit_canvas(place_labels(scene))


def layout_raw(raw: object) -> Scene:
    """Lay out a flowchart from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a flowchart spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid.
    """
    return layout(spec_io.parse(raw))
