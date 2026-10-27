"""Content rules of a Kanban board and a roadmap (design 08 sections 5 and 6).

A Kanban column that holds more cards than its limit, and a card whose words do not fit its
100 px, are warned about; so are exact dates and more than one arrow on a roadmap.
"""

import re

from .check import Code, Finding, Severity
from .html_board import card_layout
from .model import Node, PillKind, Role, Scene, Shape
from .theme import Theme, load_theme

# the first three letters of a month, as written before or after a day number
MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
EXACT_DATES = (
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b"),
    re.compile(rf"\b(?:{MONTHS})[a-z]*\.? \d{{1,2}}(?:st|nd|rd|th)?\b", re.IGNORECASE),
    re.compile(rf"\b\d{{1,2}}(?:st|nd|rd|th)? (?:{MONTHS})[a-z]*\b", re.IGNORECASE),
)
LIMIT_SEPARATOR = " / "


def lint_kanban(scene: Scene) -> list[Finding]:
    """Warn about a column over its limit, and about a card whose text does not fit.

    Args:
        scene: A scene drawn from a Kanban spec.

    Returns:
        The findings, all warnings.
    """
    theme = load_theme(scene.theme)
    findings = []
    for node in scene.nodes:
        if node.shape is Shape.BOARD_PILL and _is_over_limit(node):
            message = f"'{node.text[0]}' has more cards than its limit; finish something first"
            findings.append(_warn(Code.KANBAN_OVER_LIMIT, message, (node.id,)))
        if node.shape is Shape.KANBAN_CARD and _overflows(node, theme):
            message = f"the words of '{node.id}' do not fit a card of {node.height:g} px"
            findings.append(_warn(Code.KANBAN_CARD_FULL, message, (node.id,)))
    return findings


def lint_roadmap(scene: Scene) -> list[Finding]:
    """Warn about an exact date in a roadmap, and about more than one arrow.

    Args:
        scene: A scene drawn from a roadmap spec.

    Returns:
        The findings, all warnings.
    """
    findings = []
    for node in scene.nodes:
        text = " ".join((*node.text, *node.detail))
        if node.shape is not Shape.LANE_HEAD and any(date.search(text) for date in EXACT_DATES):
            message = f"'{node.id}' has an exact date; a roadmap has none, dates belong to a Gantt"
            findings.append(_warn(Code.ROADMAP_EXACT_DATE, message, (node.id,)))
    arrows = [edge for edge in scene.edges if edge.role is Role.MAIN]
    if len(arrows) > 1:
        message = (
            f"{len(arrows)} arrows; a roadmap draws only the one dependency that decides the order"
        )
        findings.append(_warn(Code.ROADMAP_DEPENDENCIES, message, ()))
    return findings


def _is_over_limit(pill: Node) -> bool:
    """Tell a ``count / limit`` pill whose count is above its limit."""
    view = pill.plan
    if view is None or view.pill not in (PillKind.FULL, PillKind.LIMIT):
        return False
    count, limit = pill.text[0].split(LIMIT_SEPARATOR)
    return int(count) > int(limit)


def _overflows(card: Node, theme: Theme) -> bool:
    """Tell a Kanban card whose title and detail reach down into the tag."""
    layout = card_layout(card, theme)
    words_bottom = max(
        layout.title[1] + layout.title[3],
        layout.detail[1] + (layout.detail[3] if card.detail else 0),
    )
    return words_bottom > layout.tag[1]


def _warn(code: Code, message: str, items: tuple[str, ...]) -> Finding:
    """Build a warning."""
    return Finding(Severity.WARNING, code, message, items)
