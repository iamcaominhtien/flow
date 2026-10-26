"""Where the parts of an illustrated card sit: its large icon and its name pill."""

from dataclasses import dataclass

from .model import Node, Shape
from .theme import Theme


@dataclass(frozen=True)
class CardParts:
    """The tops and the height of the parts of a card, in pixels from its top edge."""

    icon_top: float
    pill_top: float
    pill_height: float


def card_parts(node: Node, theme: Theme) -> CardParts:
    """Return where the icon and the pill of a card go.

    A work step has its icon under a padding and its pill under the icon. The header of a
    sequence lifeline is shorter: its pill sits near the bottom edge.

    Args:
        node: The card.
        theme: The design tokens.

    Returns:
        The tops of the icon and the pill, and the height of the pill.
    """
    rules = theme.layout
    if node.shape is Shape.HEADER:
        header = theme.sequence
        pill_top = node.height - header.header_pill_height - header.header_pill_margin
        return CardParts(header.header_icon_top, pill_top, header.header_pill_height)
    pill_top = rules.card_padding + rules.card_disc + rules.card_gap
    return CardParts(rules.card_padding, pill_top, rules.card_pill_height)
