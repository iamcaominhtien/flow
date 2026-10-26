"""The BPMN diagram: pools and lanes, events, tasks and gateways, sequence and message flows.

See ``bpmn_spec`` for the spec format. Time runs left to right. The layout gives each element a
column and a row (``bpmn_grid``), puts them on the page inside pools and lanes
(``bpmn_place``) and routes the flows (``bpmn_routes``).
"""

from ..canvas import fit_canvas
from ..labels import place_labels
from ..model import Scene
from ..theme import load_theme
from .bpmn_grid import build_grid
from .bpmn_place import place
from .bpmn_routes import route_links
from .bpmn_spec import BpmnSpec, read_spec


def layout_raw(raw: object) -> Scene:
    """Lay out a BPMN diagram from a parsed JSON spec.

    Args:
        raw: The result of ``json.loads`` on a ``bpmn`` spec.

    Returns:
        The scene.

    Raises:
        SpecError: If the spec is not valid, or breaks a rule of BPMN.
    """
    return layout(read_spec(raw))


def layout(spec: BpmnSpec) -> Scene:
    """Place the elements of a checked spec and route its flows.

    Args:
        spec: The checked spec.

    Returns:
        The scene, with its canvas fitted.
    """
    theme = load_theme()
    placed = place(spec, build_grid(spec), theme)
    scene = Scene(
        width=0,
        height=0,
        title=spec.title,
        description=spec.description,
        frames=placed.frames,
        nodes=tuple(placed.nodes.values()),
        edges=tuple(route_links(spec, placed, theme)),
    )
    return fit_canvas(place_labels(scene))
