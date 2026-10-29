"""Find the places in a source file that lead to another page of the app.

The patterns cover the common routers of the web: Angular (``routerLink``, ``router.navigate``,
``createUrlTree``), React Router (``<Link to>``, ``navigate``, ``<Navigate>``), Vue Router
(``<router-link to>``, ``router.push``) and plain ``href`` links. They are regular expressions,
not a parser: a target that the code builds in an unusual way is missed, and a part the code
computes becomes ``*``. Only targets that start at the root (``/...``) are kept, since a
relative one depends on the page it is on.
"""

import re

from .code_map import ANY_PART, Link

QUOTED = r"""(?P<quote>['"`])(?P<target>/[^'"`]*)(?P=quote)"""
ARRAY = r"\[(?P<array>[^\]]*)\]"
ATTRIBUTES: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        rf"\brouterLink\s*=\s*{QUOTED}",
        rf"\[routerLink\]\s*=\s*\"\s*{ARRAY}",
        rf"\[routerLink\]\s*=\s*\"\s*{QUOTED}",
        rf"(?<!<base )\bhref\s*=\s*{QUOTED}",
        rf"\bto\s*=\s*\{{?\s*{QUOTED}",
    )
)  # an attribute of an element, whose words follow it
CALLS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        rf"\.navigate\(\s*{ARRAY}",
        rf"\b(?:navigate|navigateByUrl|redirect)\(\s*{QUOTED}",
        rf"\brouter\.(?:push|replace)\(\s*{QUOTED}",
        rf"\bcreateUrlTree\(\s*{ARRAY}",
    )
)
TEMPLATE_PART = re.compile(r"\$\{[^}]*\}")
STRING = re.compile(r"""^\s*(['"])(?P<text>[^'"]*)\1\s*$""")
LINK_TEXT = re.compile(r"\s*>(?P<text>[^<>{}]{1,60})<")
QUERY = re.compile(r"[?#].*$")
EXTERNAL_PREFIX = "//"  # a protocol-relative address leaves the app


def find_links(file: str, text: str) -> list[Link]:
    """Return every link of a file, in the order of the file.

    Args:
        file: The file's path, relative to the source folder, as the links record it.
        text: The file's content.

    Returns:
        One link per match, with its line, its target and, for an ``<a>`` element with plain
        words in it, those words.
    """
    found: list[tuple[int, Link]] = []
    for pattern in (*ATTRIBUTES, *CALLS):
        for match in pattern.finditer(text):
            target = _target_of(match)
            if target is None:
                continue
            line = text.count("\n", 0, match.start()) + 1
            words = _words_after(text, match.end()) if pattern in ATTRIBUTES else ""
            found.append((match.start(), Link(file, line, target, words)))
    return [link for _, link in sorted(found, key=lambda pair: pair[0])]


def _target_of(match: re.Match[str]) -> str | None:
    """Return the normalised target of a match, or None when it leaves the app."""
    groups = match.groupdict()
    if groups.get("array") is not None:
        raw = _joined_array(groups["array"])
    else:
        raw = TEMPLATE_PART.sub(ANY_PART, groups["target"])
    if raw is None or raw.startswith(EXTERNAL_PREFIX) or not raw.startswith("/"):
        return None
    return normalised(raw)


def _joined_array(array: str) -> str | None:
    """Join the parts of a route array (``['/profile', user.name]``): a variable becomes ``*``."""
    items = [item for item in array.split(",") if item.strip()]
    if not items:
        return None
    parts = []
    for item in items:
        literal = STRING.match(item)
        parts.append(literal.group("text") if literal else ANY_PART)
    return "/".join(parts)


def normalised(target: str) -> str:
    """Return a target without its query, its fragment, doubled or trailing slashes.

    Args:
        target: A path that starts with ``/``.

    Returns:
        The clean path; ``/`` for the root.
    """
    path = QUERY.sub("", target)
    parts = [part for part in path.split("/") if part]
    return "/" + "/".join(parts)


def _words_after(text: str, end: int) -> str:
    """Return the plain words of the element a link attribute opens, if they follow it."""
    close = text.find(">", end)
    if close < 0:
        return ""
    words = LINK_TEXT.match(text, close)
    return " ".join(words.group("text").split()) if words else ""
