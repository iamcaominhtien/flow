"""How much room a node shape leaves for its text. Shared by the renderer and the layout."""

from .model import Shape

DECISION_TEXT_WIDTH_FRACTION = 0.64  # a diamond only has room for the middle of its width
PLAIN_TEXT_INSET_PX = 20  # total horizontal padding of text in an upright shape
SLANTED_TEXT_INSET_PX = 36  # total horizontal padding in shapes with slanted sides
ICON_TEXT_RESERVE_PX = 24  # text width given up to make room for an icon
SLANTED_SHAPES = (Shape.IO, Shape.PREPARATION, Shape.SUBPROCESS)


def text_area_width(shape: Shape, width: float, has_icon: bool) -> float:
    """Return how wide the text of a node may be.

    Args:
        shape: The node shape.
        width: The node width in pixels.
        has_icon: Whether the node shows an icon, which takes room from the text.

    Returns:
        The width available to text, in pixels.
    """
    if shape in (Shape.DECISION, Shape.ELLIPSE, Shape.USE_CASE):
        available = width * DECISION_TEXT_WIDTH_FRACTION
    elif shape in SLANTED_SHAPES:
        available = width - SLANTED_TEXT_INSET_PX
    else:
        available = width - PLAIN_TEXT_INSET_PX
    return available - (ICON_TEXT_RESERVE_PX if has_icon else 0)
