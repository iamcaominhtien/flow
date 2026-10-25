"""Design tokens read from ``theme.json``, and the icon library read from ``icons.json``."""

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from .model import Animation, LabelKind, Role, Shape, Tone

DATA_DIR = Path(__file__).parent


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


@dataclass(frozen=True)
class ToneColors:
    """The box tint, the darker pill tint, and the outline colour of a tone."""

    box: str
    pill: str
    stroke: str


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
    detail_font_size: float
    detail_line_height: float
    caption_height: float
    zone_padding: float
    zone_label_room: float
    lane_padding: float
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

    fonts: Fonts
    ink: str
    slate: str
    canvas: str
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


def _build_theme(raw: dict[str, Any]) -> Theme:
    """Build a theme from the parsed ``theme.json``.

    Args:
        raw: The parsed JSON document.

    Returns:
        The theme. A key that is not a member of the matching enum raises ``ValueError``.
    """
    return Theme(
        fonts=Fonts(**raw["fonts"]),
        ink=raw["ink"],
        slate=raw["slate"],
        canvas=raw["canvas"],
        badge=ChipColors(**raw["badge"]),
        shapes={Shape(name): ShapeColors(**colors) for name, colors in raw["shapes"].items()},
        tones={Tone(name): ToneColors(**colors) for name, colors in raw["tones"].items()},
        roles={Role(name): _line_style(style) for name, style in raw["roles"].items()},
        animations={
            Animation(name): AnimationSpeed(**speed) for name, speed in raw["animations"].items()
        },
        chips={LabelKind(name): ChipColors(**colors) for name, colors in raw["chips"].items()},
        layout=_layout_rules(raw["layout"]),
        sequence=SequenceRules(**raw["sequence"]),
    )


@cache
def load_theme() -> Theme:
    """Return the theme, read once from ``theme.json``."""
    raw = json.loads((DATA_DIR / "theme.json").read_text(encoding="utf-8"))
    return _build_theme(raw)


@cache
def _load_builtin_icons() -> dict[str, str]:
    """Return the icons that ship with the plugin."""
    return json.loads((DATA_DIR / "icons.json").read_text(encoding="utf-8"))


_LOCAL_ICONS: dict[str, str] = {}


def register_icons(icons: dict[str, str]) -> None:
    """Add checked custom icons to the library for the rest of the run.

    Args:
        icons: Icon name to inner SVG markup; the caller has validated both.
    """
    _LOCAL_ICONS.update(icons)


def load_icons() -> dict[str, str]:
    """Return the simple line icons: name to the inner SVG of a 24 x 24 viewBox."""
    return {**_load_builtin_icons(), **_LOCAL_ICONS}
