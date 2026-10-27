"""Content rules of an explainer (design 07 sections 1 and 4).

An explainer teaches one idea in plain words: at most eight cards on a shape, at most 14 words on
a card, and no protocol name on a line. Each finding is a warning.
"""

import re

from .check import Code, Finding, Severity
from .explain_parts import is_explain_node
from .model import Node, Scene, Shape

CARD_SHAPES = (Shape.EXPLAIN_CARD, Shape.ROW_CARD)
SECTION_SEPARATOR = "."  # the ids of a section start with its prefix and this mark
MAX_CARDS = 8
MAX_WORDS = 14
PROTOCOLS = ("HTTP", "HTTPS", "TCP", "UDP", "DNS", "TLS", "SSL", "IP", "SMTP", "FTP", "SSH", "REST")
PROTOCOL_WORD = re.compile(rf"\b(?:{'|'.join(PROTOCOLS)})\b")


def lint_explainer(scene: Scene) -> list[Finding]:
    """Warn about too many cards, long text, protocol names on lines and a missing title.

    Args:
        scene: A scene drawn from an explainer spec.

    Returns:
        The findings, all warnings.
    """
    findings = []
    if not scene.title:
        message = "the explainer has no title; it answers one question, so put it in the title"
        findings.append(_warn(Code.EXPLAINER_NO_TITLE, message, ()))
    findings += _too_many_cards(scene)
    findings += [_long_text(node) for node in scene.nodes if _is_long(node)]
    for edge in scene.edges:
        found = PROTOCOL_WORD.search(edge.label.text) if edge.label else None
        if found and edge.label:
            findings.append(_jargon(edge.id, edge.label.text, found.group()))
    return findings


def _group_of(node: Node) -> str:
    """Return the section a node belongs to: the prefix of its id, or none for a single shape."""
    prefix, mark, _rest = node.id.partition(SECTION_SEPARATOR)
    return prefix if mark else ""


def _too_many_cards(scene: Scene) -> list[Finding]:
    """Warn for every section (or the page) that holds more than eight cards."""
    counts: dict[str, list[str]] = {}
    for node in scene.nodes:
        if node.shape in CARD_SHAPES:
            counts.setdefault(_group_of(node), []).append(node.id)
    return [
        _warn(
            Code.EXPLAINER_TOO_MANY_CARDS,
            f"{len(ids)} cards; more than {MAX_CARDS} is too many, so split it in two explainers",
            tuple(ids),
        )
        for ids in counts.values()
        if len(ids) > MAX_CARDS
    ]


def _words(node: Node) -> int:
    """Count the words of the text of a card."""
    return sum(len(line.split()) for line in node.detail)


def _is_long(node: Node) -> bool:
    """Tell a card whose text is longer than 14 words."""
    return is_explain_node(node) and node.shape in CARD_SHAPES and _words(node) > MAX_WORDS


def _long_text(node: Node) -> Finding:
    """Build the warning for a card with too many words."""
    message = f"the text of '{node.id}' has {_words(node)} words; a card holds {MAX_WORDS} at most"
    return _warn(Code.EXPLAINER_TEXT_LONG, message, (node.id,))


def _jargon(edge_id: str, words: str, name: str) -> Finding:
    """Build the warning for a protocol name on a line."""
    message = f"the words on '{edge_id}' use '{name}'; say what happens in everyday words"
    return _warn(Code.EXPLAINER_JARGON, f'{message}: "{words}"', (edge_id,))


def _warn(code: Code, message: str, items: tuple[str, ...]) -> Finding:
    """Build a warning."""
    return Finding(Severity.WARNING, code, message, items)
