"""The draw.io cells of the frames of cloud and architecture diagrams: a container and a pill."""

import xml.etree.ElementTree as ET

from .drawio_common import FLOW_FRAME_KEY, FONT_BOLD, add_geometry, add_vertex, style_string
from .html_zones import pill_width
from .markup import esc
from .model import Frame, FrameVariant
from .theme import Theme

ARC_PERCENT = 6
PILL_ARC_PERCENT = 50
DASH_PATTERN = "4 3"
OPACITY_PERCENT = 100  # draw.io writes ``fillOpacity`` as a percentage


def add_zone_frame(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add a cloud frame or an architecture layer, and its name in a pill on the top edge.

    Args:
        root: The ``root`` element of the diagram.
        frame: A frame whose variant is ``NETWORK`` or ``LAYER``.
        theme: The design tokens.
    """
    tone = theme.tones[frame.tone]
    rules = theme.cloud
    pairs: dict[str, object] = {
        FLOW_FRAME_KEY: frame.variant.value,
        "rounded": 1,
        "arcSize": ARC_PERCENT,
        "dashed": 0 if frame.is_solid else 1,
        "container": 1,
        "collapsible": 0,
        "html": 1,
        "fillColor": tone.stroke,
        "fillOpacity": round(rules.tint_alpha * OPACITY_PERCENT),
        "strokeColor": tone.stroke,
        "strokeWidth": rules.border_width,
    }
    if not frame.is_solid:
        pairs["dashPattern"] = DASH_PATTERN
    cell = add_vertex(root, f"frame-{frame.id}", "", style_string(pairs))
    add_geometry(cell, (frame.x, frame.y, frame.width, frame.height))
    if frame.label:
        _add_pill(root, frame, theme)


def _add_pill(root: ET.Element, frame: Frame, theme: Theme) -> None:
    """Add the pill with the name of a frame, centred on its top edge."""
    rules = theme.cloud
    fill = theme.ink if frame.variant is FrameVariant.LAYER else theme.tones[frame.tone].accent
    style = style_string(
        {
            "rounded": 1,
            "arcSize": PILL_ARC_PERCENT,
            "html": 1,
            "fillColor": fill,
            "strokeColor": "none",
            "fontColor": theme.on_accent,
            "fontStyle": FONT_BOLD,
            "fontSize": theme.type_scale.pill.size,
            "fontFamily": theme.fonts.sans,
            "spacingLeft": 0,
            "spacingRight": 0,
        }
    )
    label = frame.label or ""
    cell = add_vertex(root, f"label-frame-{frame.id}", esc(label), style)
    left, top = frame.x + rules.pill_inset, frame.y - rules.pill_height / 2
    add_geometry(cell, (left, top, pill_width(label, theme), rules.pill_height))
