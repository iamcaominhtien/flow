"""Design tokens read from ``theme.json``, and the icon library read from ``icons.json``."""

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from .model import DEFAULT_THEME, Animation, LabelKind, Role, Shape, Tone

DATA_DIR = Path(__file__).parent
THEMES_KEY = "themes"  # in ``theme.json``: the overrides of each theme other than the default
SHAPE_PAINT_KEY = "shape_paint"  # an override that paints every shape the same way
ICON_STROKE_WIDTH = 2  # line weight of a flat icon, in its 24 px grid


@dataclass(frozen=True)
class Fonts:
    """Font family names."""

    sans: str
    mono: str


@dataclass(frozen=True)
class ShapeColors:
    """Fill and outline colour of a node shape."""

    fill: str
    stroke: str
    dash: str = ""  # an SVG dash pattern, or nothing for a solid outline
    stroke_width: float = 2  # outline weight in pixels, set by the theme
    radius: float = 10  # corner radius of a rounded box in pixels, set by the theme


@dataclass(frozen=True)
class ToneColors:
    """The tints, outline, accent and text colour of a tone."""

    box: str
    pill: str
    stroke: str
    accent: str
    lane: str
    label: str  # text on the pill tint, such as a key chip; the accent where that reads well


@dataclass(frozen=True)
class ChipColors:
    """Background and text colour of a chip."""

    background: str
    foreground: str


@dataclass(frozen=True)
class LineStyle:
    """How one line role is drawn. Sizes are in pixels; the arrowhead scales with ``width``."""

    color: str
    dash: str | None
    width: float
    head_size: float
    gap: float
    animation: Animation | None


@dataclass(frozen=True)
class AnimationSpeed:
    """One animated tier: how far the dashes move per cycle and how long a cycle lasts."""

    dash_offset: float
    seconds: float
    drawio_width: float  # draw.io ``strokeWidth`` of a line in this tier (design 01 section 6.3)
    drawio_duration_ms: int  # draw.io ``flowAnimationDuration`` of a line in this tier


@dataclass(frozen=True)
class StyleRules:
    """The parts of a theme that are not colours."""

    corner_radius: float
    frame_radius: float
    stroke_width: float
    shadow: bool


@dataclass(frozen=True)
class TextStyle:
    """Size in points and weight of one step of the type scale."""

    size: float
    weight: int


@dataclass(frozen=True)
class TypeScale:
    """The type scale of design 01 section 2."""

    title: TextStyle
    pill: TextStyle
    node: TextStyle
    edge: TextStyle
    mono: TextStyle


@dataclass(frozen=True)
class LayoutRules:
    """Sizes and gaps the layout follows. Lengths are in pixels."""

    min_sizes: dict[Shape, tuple[float, float]]
    max_node_width: float
    gap_vertical: float
    gap_vertical_labelled: float
    gap_horizontal: float
    gap_horizontal_labelled: float
    margin: float
    table_header_height: float
    table_row_height: float
    table_section_gap: float
    table_min_width: float
    table_row_gap: float
    table_padding_x: float
    table_bottom_pad: float
    table_extra_width: float
    table_card_header_height: float
    table_chip_width: float
    table_chip_gap: float
    table_key_columns: int
    table_name_font_size: float
    detail_font_size: float
    detail_line_height: float
    caption_height: float
    zone_padding: float
    zone_label_room: float
    lane_padding: float
    lane_tab: float
    fold_extent: float
    band_gap: float
    lane_min_size: float
    min_canvas_width: float
    title_block_height: float
    channel_offset: float
    channel_step: float
    label_offset: float
    char_width_em: float
    line_padding: float
    max_text_lines: int
    chip_font_size: float
    chip_height: float
    chip_padding_x: float
    chip_char_width_em: float
    card_min_width: float
    card_padding: float
    card_disc: float
    card_gap: float
    card_pill_height: float
    card_pill_padding: float
    card_icon_fraction: float


@dataclass(frozen=True)
class SequenceRules:
    """Sizes and gaps of a sequence diagram. Lengths are in pixels."""

    participant_width: float
    participant_height: float
    pitch: float
    min_gap_between_boxes: float
    first_message_gap: float
    row_height: float
    self_row_extra: float
    label_rise: float
    bar_width: float
    bar_overshoot: float
    bar_step: float
    fragment_enter: float
    fragment_exit: float
    fragment_pad_x: float
    fragment_inset_x: float
    divider_gap: float
    max_fragment_depth: int
    note_width: float
    note_offset: float
    note_line_height: float
    note_padding: float
    lost_length: float
    self_width: float
    self_height: float
    destroy_size: float
    tail_gap: float
    bottom_gap: float


@dataclass(frozen=True)
class Theme:
    """Every colour, line style and animation the renderers use."""

    name: str
    fonts: Fonts
    ink: str
    slate: str
    canvas: str
    paper: str  # the surface of a table body or a tag, which stands out from the canvas
    on_accent: str  # text on an accent colour, such as a lane tab
    rule: str  # a divider inside a table
    row_rule: str  # the lighter rule between two rows
    style: StyleRules
    type_scale: TypeScale
    drawio_weights: dict[float, float]  # canvas line width in px to draw.io ``strokeWidth``
    badge: ChipColors
    shapes: dict[Shape, ShapeColors]
    tones: dict[Tone, ToneColors]
    roles: dict[Role, LineStyle]
    animations: dict[Animation, AnimationSpeed]
    chips: dict[LabelKind, ChipColors]
    layout: LayoutRules
    sequence: SequenceRules


def _line_style(raw: dict[str, Any]) -> LineStyle:
    """Build a line style from its JSON object.

    Args:
        raw: The JSON object of one role in ``theme.json``.

    Returns:
        The line style, with ``animation`` set to None for a role that does not move.
    """
    animation = raw.get("animation")
    return LineStyle(
        color=raw["color"],
        dash=raw["dash"],
        width=raw["width"],
        head_size=raw["head_size"],
        gap=raw["gap"],
        animation=Animation(animation) if animation else None,
    )


def _layout_rules(raw: dict[str, Any]) -> LayoutRules:
    """Build the layout rules from their JSON object.

    Args:
        raw: The ``layout`` object of ``theme.json``.

    Returns:
        The rules, with each minimum size as a ``(width, height)`` tuple.
    """
    sizes = {Shape(name): (size[0], size[1]) for name, size in raw["min_sizes"].items()}
    return LayoutRules(**{**raw, "min_sizes": sizes})


def _build_theme(name: str, raw: dict[str, Any]) -> Theme:
    """Build a theme from the parsed ``theme.json``, with a theme's overrides already merged.

    Args:
        name: The theme name.
        raw: The parsed JSON document.

    Returns:
        The theme. A key that is not a member of the matching enum raises ``ValueError``.
    """
    style = StyleRules(**raw["style"])
    paint = {"stroke_width": style.stroke_width, "radius": style.corner_radius}
    return Theme(
        name=name,
        fonts=Fonts(**raw["fonts"]),
        ink=raw["ink"],
        slate=raw["slate"],
        canvas=raw["canvas"],
        paper=raw["paper"],
        on_accent=raw["on_accent"],
        rule=raw["rule"],
        row_rule=raw["row_rule"],
        style=style,
        type_scale=TypeScale(
            **{key: TextStyle(**value) for key, value in raw["type_scale"].items()}
        ),
        drawio_weights={float(key): value for key, value in raw["drawio_weights"].items()},
        badge=ChipColors(**raw["badge"]),
        shapes={
            Shape(shape): ShapeColors(**colors, **paint) for shape, colors in raw["shapes"].items()
        },
        tones={Tone(name): ToneColors(**colors) for name, colors in raw["tones"].items()},
        roles={Role(name): _line_style(style) for name, style in raw["roles"].items()},
        animations={
            Animation(name): AnimationSpeed(**speed) for name, speed in raw["animations"].items()
        },
        chips={LabelKind(name): ChipColors(**colors) for name, colors in raw["chips"].items()},
        layout=_layout_rules(raw["layout"]),
        sequence=SequenceRules(**raw["sequence"]),
    )


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return ``base`` with ``override`` laid over it, going into nested objects.

    Args:
        base: The settings to start from; not changed.
        override: The settings that win. A value that is not an object replaces the one in base.

    Returns:
        A new dict.
    """
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = _merge(base[key], value)
        else:
            merged[key] = value
    return merged


def _paint_every_shape(raw: dict[str, Any], paint: dict[str, Any]) -> dict[str, Any]:
    """Give each shape one fill and outline colour, except the shapes the override names.

    Args:
        raw: The merged settings.
        paint: The ``shape_paint`` override: ``fill``, ``stroke`` and ``except``, a list of shapes.

    Returns:
        The settings with every shape repainted.
    """
    colors = {"fill": paint["fill"], "stroke": paint["stroke"]}
    kept = set(paint.get("except", ()))
    shapes = {name: (old if name in kept else colors) for name, old in raw["shapes"].items()}
    return {**raw, "shapes": shapes}


def theme_names() -> list[str]:
    """Return every theme name a spec may use, the default first."""
    raw = json.loads((DATA_DIR / "theme.json").read_text(encoding="utf-8"))
    return [DEFAULT_THEME, *raw[THEMES_KEY]]


@cache
def load_theme(name: str = DEFAULT_THEME) -> Theme:
    """Return a theme, read once from ``theme.json``.

    Args:
        name: One of ``theme_names()``. Every theme but the default is the default with the
            overrides listed under its name in ``theme.json``.

    Returns:
        The theme.

    Raises:
        KeyError: If the name is not a theme.
    """
    raw = json.loads((DATA_DIR / "theme.json").read_text(encoding="utf-8"))
    overrides = raw.pop(THEMES_KEY)
    if name == DEFAULT_THEME:
        return _build_theme(name, raw)
    override = dict(overrides[name])
    paint = override.pop(SHAPE_PAINT_KEY, None)
    merged = _paint_every_shape(raw, paint) if paint else raw
    return _build_theme(name, _merge(merged, override))


@cache
def _load_builtin_icons() -> dict[str, str]:
    """Return the icons that ship with the plugin."""
    return json.loads((DATA_DIR / "icons.json").read_text(encoding="utf-8"))


_LOCAL_ICONS: dict[str, str] = {}


@cache
def load_detailed_icons() -> dict[str, str]:
    """Return the detailed icons: name to the inner SVG of a 64 x 64 viewBox, with own colours."""
    return json.loads((DATA_DIR / "icons_detailed.json").read_text(encoding="utf-8"))


def icon_names() -> set[str]:
    """Return every icon name a spec may use: flat, custom and detailed."""
    return set(load_icons()) | set(load_detailed_icons())


def has_detailed_icon(name: str) -> bool:
    """Tell whether an icon has a detailed drawing."""
    return name in load_detailed_icons()


def icon_svg(name: str, size: float, stroke: str, attrs: str = "") -> str:
    """Draw an icon as an ``svg`` element, using the flat drawing when there is one.

    Args:
        name: An icon name from ``icon_names``.
        size: The drawn width and height in pixels.
        stroke: The line colour of a flat icon; a detailed icon has its own colours.
        attrs: Extra attributes for the element, such as a ``style`` or ``xmlns``.

    Returns:
        The ``svg`` element.
    """
    flat = load_icons().get(name)
    if flat is None:
        return detailed_icon_svg(name, size, stroke, attrs)
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" {attrs} fill="none" '
        f'stroke="{stroke}" stroke-width="{ICON_STROKE_WIDTH}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{flat}</svg>'
    )


def detailed_icon_svg(name: str, size: float, stroke: str, attrs: str = "") -> str:
    """Draw an icon in its detailed form when it has one, else as the flat drawing.

    Args:
        name: An icon name from ``icon_names``.
        size: The drawn width and height in pixels.
        stroke: The line colour used when only a flat drawing exists.
        attrs: Extra attributes for the element, such as a ``style`` or ``xmlns``.

    Returns:
        The ``svg`` element.
    """
    detailed = load_detailed_icons().get(name)
    if detailed is None:
        return icon_svg(name, size, stroke, attrs)
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" {attrs} '
        f'overflow="visible" aria-hidden="true">{detailed}</svg>'
    )


def register_icons(icons: dict[str, str]) -> None:
    """Add checked custom icons to the library for the rest of the run.

    Args:
        icons: Icon name to inner SVG markup; the caller has validated both.
    """
    _LOCAL_ICONS.update(icons)


def load_icons() -> dict[str, str]:
    """Return the simple line icons: name to the inner SVG of a 24 x 24 viewBox."""
    return {**_load_builtin_icons(), **_LOCAL_ICONS}
