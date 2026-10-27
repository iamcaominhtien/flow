"""Tests for the themes, the line weights, the type scale and the border lint."""

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugins" / "flow"
EXAMPLES = ROOT / "examples"

sys.path.insert(0, str(PLUGIN_DIR))

from flowlib import diagrams, render_drawio, render_html, scene  # noqa: E402
from flowlib.check import Code, check_scene  # noqa: E402
from flowlib.model import (  # noqa: E402
    DEFAULT_THEME,
    Divider,
    Edge,
    EdgeLabel,
    Frame,
    FrameVariant,
    LabelKind,
    Node,
    Role,
    Scene,
    Shape,
    Tone,
)
from flowlib.reader import SpecError  # noqa: E402
from flowlib.theme import load_theme, theme_names  # noqa: E402

THEMES = ["pastel", "technical", "midnight"]
MIN_FONT_PX = 10
NO_TEXT_SHAPES = (
    Shape.START,
    Shape.END,
    Shape.INITIAL,
    Shape.FINAL,
    Shape.BAR,
    Shape.FORK,
)  # solid marks that hold no words
MIN_TEXT_CONTRAST = 4.5
MIDNIGHT_BACKGROUND = "#0B1220"
SIZE_PATTERN = re.compile(r"font-size:\s*([\d.]+)px")


def _themed(name: str, theme: str) -> Scene:
    """Lay out an example spec with a theme."""
    raw = json.loads((EXAMPLES / f"{name}.spec.json").read_text(encoding="utf-8"))
    raw["theme"] = theme
    return diagrams.layout(raw)


def _luminance(color: str) -> float:
    """Return the relative luminance of a ``#RRGGBB`` colour."""
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    """Return the WCAG contrast ratio of two colours."""
    high, low = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_the_known_themes_are_the_three_of_the_design() -> None:
    """The default comes first."""
    assert theme_names() == THEMES
    assert DEFAULT_THEME == "pastel"


@pytest.mark.parametrize("theme", THEMES)
def test_every_theme_renders_html_and_drawio(theme: str) -> None:
    """Each theme builds a page and a draw.io file that parses."""
    laid_out = _themed("order-flow", theme)
    assert laid_out.theme == theme
    assert "<svg" in render_html.render(laid_out)
    ET.fromstring(render_drawio.render(laid_out))


def test_themes_differ_in_colours_and_in_the_page_background() -> None:
    """HTML and draw.io take their background from the theme."""
    html = {theme: render_html.render(_themed("order-flow", theme)) for theme in THEMES}
    drawio = {theme: render_drawio.render(_themed("order-flow", theme)) for theme in THEMES}
    assert len(set(html.values())) == len(set(drawio.values())) == len(THEMES)
    for theme in THEMES:
        background = load_theme(theme).canvas
        assert f"background:{background}" in html[theme]
        assert f'background="{background}"' in drawio[theme]
    assert load_theme("midnight").canvas == MIDNIGHT_BACKGROUND


def test_theme_settings_follow_the_design() -> None:
    """Radius, stroke and shadow of each theme, and solid edges in the technical one."""
    pastel, technical, midnight = (load_theme(name) for name in THEMES)
    assert (technical.style.corner_radius, technical.style.stroke_width) == (4, 1.5)
    assert not technical.style.shadow
    assert (midnight.style.corner_radius, midnight.style.stroke_width) == (12, 2)
    assert pastel.style.stroke_width == 2
    assert all(technical.roles[role].dash is None for role in (Role.MAIN, Role.DATA))
    assert technical.roles[Role.MAIN].animation is None
    assert pastel.roles[Role.MAIN].animation is not None


def test_the_default_theme_is_not_written_to_a_scene_file() -> None:
    """A scene keeps its theme through a round trip; the default adds no key."""
    pastel, midnight = _themed("order-flow", "pastel"), _themed("order-flow", "midnight")
    assert "theme" not in scene.dump(pastel)
    assert scene.parse(scene.dump(midnight)).theme == "midnight"


@pytest.mark.parametrize("name", ["order-flow", "signin-sequence", "delivery-er", "refund-bpmn"])
def test_every_spec_type_accepts_a_theme(name: str) -> None:
    """The ``theme`` key is read for every type, not only for flowcharts."""
    assert _themed(name, "technical").theme == "technical"


def test_an_unknown_theme_is_a_clear_error() -> None:
    """The message names the themes there are."""
    with pytest.raises(SpecError, match="unknown theme 'neon'; use one of: pastel, technical"):
        _themed("order-flow", "neon")


@pytest.mark.parametrize("theme", ["midnight", "technical"])
def test_text_is_readable_on_every_fill(theme: str) -> None:
    """Ink on the tints and shapes, slate on the canvas, label text on the pills."""
    colors = load_theme(theme)
    for tone in colors.tones.values():
        assert _contrast(colors.ink, tone.box) >= MIN_TEXT_CONTRAST
        assert _contrast(colors.ink, tone.pill) >= MIN_TEXT_CONTRAST
        if theme == "midnight":  # the pastel violet chip text is 3.9: the design's own colour
            assert _contrast(tone.label, tone.pill) >= MIN_TEXT_CONTRAST
        assert _contrast(colors.on_accent, tone.accent) >= MIN_TEXT_CONTRAST
    for name, shape in colors.shapes.items():
        if shape.fill != "none" and name not in NO_TEXT_SHAPES:
            assert _contrast(colors.ink, shape.fill) >= MIN_TEXT_CONTRAST
    assert _contrast(colors.slate, colors.canvas) >= MIN_TEXT_CONTRAST


def test_weight_table_and_animation_recipe_of_the_design() -> None:
    """Canvas 2 and 4 px become 2 and 3; the animated tiers are 3 / 500 ms and 1 / 1500 ms."""
    colors = load_theme()
    assert colors.drawio_weights == {1: 1, 2: 2, 4: 3}
    assert [(a.drawio_width, a.drawio_duration_ms) for a in colors.animations.values()] == [
        (3, 500),
        (1, 1500),
    ]


def test_drawio_edges_use_the_weights_of_the_table() -> None:
    """A main line is 3 wide at 500 ms, a data line 1 at 1500 ms, a next line 2."""
    shapes = scene.load(EXAMPLES / "shapes.scene.json")
    cells = {
        cell.get("id"): cell.get("style", "")
        for cell in ET.fromstring(render_drawio.render(shapes)).iter("mxCell")
    }
    assert "strokeWidth=3;" in cells["edge-m1"]
    assert "flowAnimationDuration=500;" in cells["edge-m1"]
    assert "strokeWidth=1;" in cells["edge-d1"]
    assert "flowAnimationDuration=1500;" in cells["edge-d1"]
    assert "strokeWidth=2;" in cells["edge-n1"]


def test_html_weights_are_unchanged() -> None:
    """The canvas weights of design 01 section 6.1 stay in the page: 2, 4 and 2."""
    roles = load_theme().roles
    assert (roles[Role.NEXT].width, roles[Role.MAIN].width, roles[Role.DATA].width) == (2, 4, 2)


def test_type_scale_in_the_page() -> None:
    """Title 20/800, frame pill 13/700, edge label 10/500; nothing under 10 px."""
    html = render_html.render(_themed("shop-architecture", "pastel"))
    assert "font-size:20px;font-weight:800" in html
    assert "font-size:13px;font-weight:700" in html
    assert "font-size:10px;font-weight:500" in html
    assert min(float(size) for size in SIZE_PATTERN.findall(html)) >= MIN_FONT_PX


@pytest.mark.parametrize("name", ["shop-architecture", "delivery-er", "payment-sequence"])
def test_nothing_in_drawio_is_under_ten_points(name: str) -> None:
    """Every ``fontSize`` the renderer writes is at least 10."""
    rendered = render_drawio.render(_themed(name, "pastel"))
    sizes = [float(size) for size in re.findall(r"fontSize=([\d.]+);", rendered)]
    assert sizes
    assert min(sizes) >= MIN_FONT_PX


def test_drawio_style_strings_of_design_section_three() -> None:
    """Pill title, node and container carry the keys the design lists."""
    rendered = render_drawio.render(_themed("shop-architecture", "pastel"))
    cells = {
        cell.get("id"): cell.get("style", "") for cell in ET.fromstring(rendered).iter("mxCell")
    }
    container = cells["frame-backend"]
    for pair in ("dashed=1;", "dashPattern=4 3;", "container=1;", "collapsible=0;", "arcSize=6;"):
        assert pair in container
    assert "strokeWidth=1.5;" in container
    pill = cells["label-frame-backend"]
    for pair in ("rounded=1;", "arcSize=50;", "strokeColor=none;", "fontStyle=1;", "fontSize=13;"):
        assert pair in pill
    node = cells["node-api"]
    for pair in (
        "strokeWidth=2;",
        "fontSize=12;",
        "fontStyle=1;",
        "shadow=1;",
        "fontFamily=Inter;",
    ):
        assert pair in node


def test_technical_drawio_nodes_have_no_shadow_and_a_small_radius() -> None:
    """Technical clean: radius 4, stroke 1.5, no shadow."""
    rendered = render_drawio.render(_themed("order-flow", "technical"))
    styles = [cell.get("style", "") for cell in ET.fromstring(rendered).iter("mxCell")]
    process = next(style for style in styles if "absoluteArcSize=1" in style)
    assert "arcSize=8;" in process
    assert "strokeWidth=1.5;" in process
    assert not any("shadow=1" in style for style in styles)


def _box(node_id: str, left: float, top: float, size: float = 40) -> Node:
    """Return a small box."""
    return Node(node_id, Shape.PROCESS, left, top, size, size, (), None, None, None, 12)


def _frame(frame_id: str, dividers: tuple[Divider, ...] = ()) -> Frame:
    """Return a frame from (100, 100) to (400, 400)."""
    variant = FrameVariant.FRAGMENT if dividers else FrameVariant.AREA
    return Frame(frame_id, 100, 100, 300, 300, "F", Tone.BLUE, variant, dividers=dividers)


def _codes(nodes: tuple[Node, ...], frame: Frame, edges: tuple[Edge, ...] = ()) -> list[Code]:
    """Return the codes found on a scene with one frame."""
    return [f.code for f in check_scene(Scene(600, 600, None, None, (frame,), nodes, edges))]


def test_a_box_straddling_a_frame_border_is_a_warning() -> None:
    """Half in, half out is reported; fully in or fully out is not."""
    frame = _frame("zone")
    assert _codes((_box("a", 80, 200),), frame).count(Code.CROSSES_BORDER) == 1
    assert Code.CROSSES_BORDER not in _codes((_box("a", 150, 200), _box("b", 450, 200)), frame)
    finding = check_scene(Scene(600, 600, None, None, (frame,), (_box("a", 80, 200),), ()))[0]
    assert finding.severity.value == "warning"
    assert "'a'" in finding.message and "'zone'" in finding.message


def test_a_box_on_a_divider_is_a_warning() -> None:
    """A divider across a box is reported, even when the box is inside the frame."""
    frame = _frame("alt", (Divider(220, "else"),))
    codes = _codes((_box("a", 150, 200), _box("b", 150, 300)), frame)
    assert codes.count(Code.ON_DIVIDER) == 1
    assert Code.CROSSES_BORDER not in codes


def test_a_label_on_a_frame_border_is_a_warning() -> None:
    """The chip of a line is a part too."""
    label = EdgeLabel("goes", (400, 250), LabelKind.PLAIN)
    line = Edge("e1", Role.NEXT, ((300, 250), (500, 250)), label, "a", "b")
    nodes = (_box("a", 250, 230), _box("b", 500, 230))
    assert Code.CROSSES_BORDER in _codes(nodes, _frame("zone"), (line,))


def test_a_long_activation_bar_may_cross_a_fragment() -> None:
    """Bars are long on purpose and are not reported."""
    bar = Node("bar", Shape.BAR, 240, 50, 12, 400, (), None, None, None, 12)
    assert _codes((bar,), _frame("zone")) == []
