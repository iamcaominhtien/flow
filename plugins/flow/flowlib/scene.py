"""The scene: plain geometry in pixels that every renderer and the checks read.

    {"size": [w, h], "title": "...", "desc": "...",
     "frames": [{"id", "x", "y", "w", "h", "label", "tone"}],
     "nodes":  [{"id", "shape", "x", "y", "w", "h", "text", "icon", "tone", "number"}],
     "edges":  [{"id", "role", "points": [[x, y], ...], "arrow", "label": {"text", "at", "kind"}}]}

x and y are the top-left corner of a node or frame.
"""

import json
from pathlib import Path

from .theme import icons, theme

NODE_KEYS = {"id", "shape", "x", "y", "w", "h", "text", "icon", "tone", "number", "font_size"}
EDGE_KEYS = {"id", "from", "to", "role", "points", "arrow", "label"}
FRAME_KEYS = {"id", "x", "y", "w", "h", "label", "tone"}
SCENE_KEYS = {"size", "title", "desc", "frames", "nodes", "edges"}


class SceneError(ValueError):
    """The scene is not valid. The message lists every problem found."""

    def __init__(self, problems):
        self.problems = problems
        super().__init__("\n".join(problems))


def load(path):
    scene = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(scene)
    return scene


def _number(value):
    return isinstance(value, int | float) and not isinstance(value, bool)


def _check_unknown(item, allowed, where, problems):
    for key in sorted(set(item) - allowed):
        problems.append(f"{where}: unknown field '{key}'")


def _check_box(item, where, problems):
    for key in ("x", "y", "w", "h"):
        if not _number(item.get(key)):
            problems.append(f"{where}: '{key}' must be a number")
    if _number(item.get("w")) and item["w"] <= 0:
        problems.append(f"{where}: 'w' must be positive")
    if _number(item.get("h")) and item["h"] <= 0:
        problems.append(f"{where}: 'h' must be positive")


def validate(scene):
    """Raise SceneError listing every problem, or return None when the scene is fine."""
    problems = []
    t = theme()
    if not isinstance(scene, dict):
        raise SceneError(["the scene must be a JSON object"])
    _check_unknown(scene, SCENE_KEYS, "scene", problems)
    size = scene.get("size")
    if not (isinstance(size, list) and len(size) == 2 and all(_number(v) for v in size)):
        problems.append("scene: 'size' must be [width, height]")

    ids = set()

    def new_id(item, where):
        ident = item.get("id")
        if not isinstance(ident, str) or not ident:
            problems.append(f"{where}: 'id' must be a non-empty string")
        elif ident in ids:
            problems.append(f"{where}: id '{ident}' is used twice")
        else:
            ids.add(ident)

    for i, frame in enumerate(scene.get("frames", [])):
        where = f"frames[{i}]"
        new_id(frame, where)
        _check_unknown(frame, FRAME_KEYS, where, problems)
        _check_box(frame, where, problems)
        if frame.get("tone", "gray") not in t["tones"]:
            problems.append(f"{where}: unknown tone '{frame['tone']}'")

    node_ids = set()
    for i, node in enumerate(scene.get("nodes", [])):
        where = f"nodes[{i}]"
        new_id(node, where)
        node_ids.add(node.get("id"))
        _check_unknown(node, NODE_KEYS, where, problems)
        _check_box(node, where, problems)
        if node.get("shape") not in t["shapes"]:
            problems.append(f"{where}: unknown shape '{node.get('shape')}'")
        if "tone" in node and node["tone"] not in t["tones"]:
            problems.append(f"{where}: unknown tone '{node['tone']}'")
        if "icon" in node and node["icon"] not in icons():
            problems.append(f"{where}: unknown icon '{node['icon']}'")
        text = node.get("text", "")
        if not isinstance(text, str | list):
            problems.append(f"{where}: 'text' must be a string or a list of lines")

    for i, edge in enumerate(scene.get("edges", [])):
        where = f"edges[{i}]"
        new_id(edge, where)
        _check_unknown(edge, EDGE_KEYS, where, problems)
        if edge.get("role", "next") not in t["roles"]:
            problems.append(f"{where}: unknown role '{edge['role']}'")
        points = edge.get("points")
        if not (
            isinstance(points, list)
            and len(points) >= 2
            and all(
                isinstance(p, list) and len(p) == 2 and all(_number(v) for v in p) for p in points
            )
        ):
            problems.append(f"{where}: 'points' must be a list of at least two [x, y] pairs")
        for end in ("from", "to"):
            if end in edge and edge[end] not in node_ids:
                problems.append(f"{where}: '{end}' names '{edge[end]}', which is not a node")
        if edge.get("arrow", "end") not in ("end", "none"):
            problems.append(f"{where}: 'arrow' must be 'end' or 'none'")
        label = edge.get("label")
        if label is not None:
            at = label.get("at") if isinstance(label, dict) else None
            if not (isinstance(label, dict) and isinstance(label.get("text"), str)):
                problems.append(f"{where}: 'label' needs a 'text'")
            elif not (isinstance(at, list) and len(at) == 2 and all(_number(v) for v in at)):
                problems.append(f"{where}: 'label' needs 'at': [x, y]")
            elif label.get("kind", "plain") not in t["chips"]:
                problems.append(f"{where}: unknown label kind '{label['kind']}'")

    if problems:
        raise SceneError(problems)
