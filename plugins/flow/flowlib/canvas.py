"""Size the canvas of a scene to hold everything in it."""

from dataclasses import replace

from .model import Scene
from .theme import load_theme


def fit_canvas(scene: Scene) -> Scene:
    """Size the canvas to hold everything in a scene, with a margin and a minimum width.

    Args:
        scene: A scene whose nodes, frames, lines and labels have their final positions.

    Returns:
        The same scene with ``width`` and ``height`` set.
    """
    rules = load_theme().layout
    xs = [node.x + node.width for node in scene.nodes] + [f.x + f.width for f in scene.frames]
    ys = [node.y + node.height for node in scene.nodes] + [f.y + f.height for f in scene.frames]
    for edge in scene.edges:
        xs += [x for x, _ in edge.points]
        ys += [y for _, y in edge.points]
        if edge.label:
            xs.append(edge.label.at[0] + rules.margin)
            ys.append(edge.label.at[1] + rules.margin)
    return replace(
        scene,
        width=max(rules.min_canvas_width, max(xs)) + rules.margin,
        height=max(ys) + rules.margin,
    )
