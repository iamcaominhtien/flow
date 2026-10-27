"""Tests for the mind map: radial layout, levels, marks, curves and links, in all three looks."""

import copy
import json
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib import diagrams, import_drawio, render_drawio, render_html  # noqa: E402
from flowlib import scene as scene_io  # noqa: E402
from flowlib.check import Code, check_scene  # noqa: E402
from flowlib.model import MindLevel, Role, Scene, Shape, Side, Status, Tone  # noqa: E402
from flowlib.reader import SpecError  # noqa: E402

NAMES = ("delivery-mindmap", "delivery-mindmap-plain", "delivery-mindmap-large")


def raw_example(name: str = NAMES[0]) -> dict:
    """Load an example as a fresh dictionary."""
    return copy.deepcopy(json.loads((EXAMPLES / f"{name}.spec.json").read_text()))


def drawn(name: str = NAMES[0]) -> Scene:
    """Lay out an example."""
    return diagrams.layout(raw_example(name))


def nodes_of(scene: Scene) -> dict:
    """Return the nodes of a scene by id."""
    return {node.id: node for node in scene.nodes}


@pytest.mark.parametrize("name", NAMES)
def test_example_has_no_findings_and_draws_in_both_formats(name: str) -> None:
    """Each design example passes every check and renders to HTML and draw.io."""
    scene = drawn(name)
    assert check_scene(scene) == []
    assert "<svg" in render_html.render(scene)
    ET.fromstring(render_drawio.render(scene))
    assert scene_io.parse(scene_io.dump(scene)) == scene


def test_nothing_in_a_mind_map_animates() -> None:
    """No line has an animated role, and no animation class is used on the page."""
    for name in NAMES:
        scene = drawn(name)
        assert not {edge.role for edge in scene.edges} & {Role.MAIN, Role.DATA}
        assert 'class="flow' not in render_html.render(scene)


def test_three_branches_on_each_side_300_px_apart() -> None:
    """The first three branches are on the right, the rest on the left, 300 px apart."""
    nodes = nodes_of(drawn())
    branches = [nodes[f"n{index}"] for index in (1, 6, 11, 16, 21, 26)]
    right, left = branches[:3], branches[3:]
    assert all(node.plan.side is Side.RIGHT for node in right)
    assert all(node.plan.side is Side.LEFT for node in left)
    assert right[1].y - right[0].y == 300 == right[2].y - right[1].y
    centre = nodes["n0"]
    assert right[0].x > centre.x + centre.width and left[0].x + left[0].width < centre.x


def test_leaves_are_cards_with_a_bar_and_a_small_icon() -> None:
    """Four leaves a branch, each 236 x 44 with an icon; branches are 260 x 76."""
    nodes = nodes_of(drawn())
    leaves = [n for n in nodes.values() if n.plan.level is MindLevel.LEAF]
    assert len(leaves) == 24 and all(leaf.icon for leaf in leaves)
    assert (leaves[0].width, leaves[0].height) == (236, 44)
    assert (nodes["n1"].width, nodes["n1"].height) == (260, 76)


def test_lines_are_curves_8_px_at_the_centre_and_4_px_at_the_leaves() -> None:
    """A branch line is a Bezier curve in the colour of its branch; the leaf lines are thinner."""
    scene = drawn()
    curves = [edge for edge in scene.edges if edge.is_curved]
    assert {edge.role for edge in curves} == {Role.BRANCH, Role.TWIG}
    assert all(len(edge.points) == 4 and edge.tone for edge in curves)
    from flowlib.theme import load_theme

    roles = load_theme().roles
    assert (roles[Role.BRANCH].width, roles[Role.TWIG].width) == (8, 4)
    assert '<path data-id="line-n1"' in render_html.render(scene) and " C " in render_html.render(
        scene
    )


def test_plain_style_has_underlined_leaves_and_tinted_pills() -> None:
    """The plain map has no card on a leaf and no solid pill; the rules stay the same."""
    scene = drawn("delivery-mindmap-plain")
    leaf = next(n for n in scene.nodes if n.plan and n.plan.level is MindLevel.LEAF)
    assert not leaf.card
    assert scene.nodes[1].shape is Shape.BRANCH and not scene.nodes[1].card


def test_large_map_has_four_levels_marks_and_links() -> None:
    """Branch, group, idea and detail; priority, check, owner, hidden count and arcs."""
    scene = drawn("delivery-mindmap-large")
    levels = {node.plan.level for node in scene.nodes if node.plan and node.plan.level}
    assert {MindLevel.BRANCH, MindLevel.GROUP, MindLevel.IDEA, MindLevel.DETAIL} <= levels
    nodes = nodes_of(scene)
    assert nodes["cardprovider"].plan.priority == 1
    assert nodes["navigation"].plan.hidden == 3
    assert any(n.plan.status is Status.DONE for n in scene.nodes if n.plan)
    assert any(n.plan.initials for n in scene.nodes if n.plan and n.plan.level is MindLevel.IDEA)
    links = [edge for edge in scene.edges if edge.role is Role.LINK and edge.id.startswith("link")]
    assert len(links) == 3 and all(edge.label and edge.is_curved for edge in links)


def test_no_leaf_overlaps_another_on_the_large_map() -> None:
    """The automatic layout keeps every box clear of every other."""
    assert [
        f for f in check_scene(drawn("delivery-mindmap-large")) if f.code is Code.NODES_OVERLAP
    ] == []


def test_branch_gives_its_tone_to_what_hangs_on_it() -> None:
    """Items take the tone of their branch, and the branches take the palette in turn."""
    nodes = nodes_of(drawn())
    assert nodes["n1"].tone is Tone.BLUE and nodes["n2"].tone is Tone.BLUE
    assert nodes["n6"].tone is Tone.VIOLET


def test_long_phrases_and_too_many_links_are_warnings() -> None:
    """A leaf of more than four words, and more than four links, are reported."""
    raw = raw_example("delivery-mindmap-large")
    raw["root"]["children"][0]["children"][0]["children"][0]["label"] = "one two three four five"
    pairs = [
        ("livemap", "orderevents"),
        ("navigation", "courierevents"),
        ("livemap", "courierevents"),
    ]
    pairs += [("navigation", "orderevents"), ("checkout", "livemap")]
    raw["links"] = [{"from": first, "to": second, "label": "x"} for first, second in pairs]
    codes = {finding.code for finding in check_scene(diagrams.layout(raw))}
    assert {Code.MIND_PHRASE_LONG, Code.MIND_TOO_MANY_LINKS} <= codes


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda raw: raw["links"].append({"from": "livemap", "to": "payouts"}), "different sides"),
        (lambda raw: raw["links"].append({"from": "livemap", "to": "nowhere"}), "not the id"),
        (
            lambda raw: raw["root"]["children"][0]["children"][0]["children"][0]["children"][
                0
            ].update(children=[{"label": "Too deep"}]),
            "deep",
        ),
        (lambda raw: raw["root"]["children"][0]["children"][0].update(priority="P3"), "P1 or P2"),
    ],
)
def test_bad_specs_are_refused_with_the_reason(
    change: Callable[[dict], object], message: str
) -> None:
    """A link across sides, an unknown id, a fifth level or a bad priority is reported."""
    raw = raw_example("delivery-mindmap-large")
    change(raw)
    with pytest.raises(SpecError, match=message):
        diagrams.layout(raw)


def test_the_older_form_without_style_or_icons_still_draws() -> None:
    """A tree of labels with a root and branches is laid out radially in the plain style."""
    raw = {
        "type": "mindmap",
        "root": {
            "label": "Launch",
            "children": [
                {"label": "Product", "children": [{"label": "Tests"}]},
                {"label": "Marketing", "children": [{"label": "Press"}, {"label": "Email"}]},
            ],
        },
    }
    scene = diagrams.layout(raw)
    assert check_scene(scene) == []
    nodes = nodes_of(scene)
    assert (
        nodes["n1"].x > nodes["n0"].x > nodes["n4"].x
        if "n4" in nodes
        else nodes["n1"].x > nodes["n0"].x
    )


def test_drawio_file_is_read_back_with_levels_and_marks() -> None:
    """Shapes, levels, marks and the words of the topic survive the draw.io file."""
    scene = drawn("delivery-mindmap-large")
    path = Path(__file__).parent / "_mind_roundtrip.drawio"
    try:
        path.write_text(render_drawio.render(scene))
        back = import_drawio.convert(path).scene
    finally:
        path.unlink(missing_ok=True)
    by_id = {node.id.removeprefix("node-"): node for node in back.nodes}
    for node in scene.nodes:
        assert by_id[node.id].shape is node.shape and by_id[node.id].plan == node.plan
    assert by_id["n0"].text == scene.nodes[0].text and by_id["n0"].detail == scene.nodes[0].detail
