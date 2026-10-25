"""Custom icons: read ``icons.local.json`` beside a spec and check that each one is safe SVG.

An icon is the inner markup of a 24 x 24 line icon. It may hold only a few drawing elements with
plain geometry attributes, so a file written by an AI cannot run a script, load a picture or
restyle the page.
"""

import json
import re
from pathlib import Path
from xml.etree import ElementTree

from .reader import SpecError
from .theme import load_icons, register_icons

LOCAL_ICONS_FILE = "icons.local.json"
ALLOWED_ELEMENTS = {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon", "g"}
ALLOWED_ATTRIBUTES = {
    "d", "cx", "cy", "r", "rx", "ry", "x", "y", "width", "height",
    "x1", "y1", "x2", "y2", "points",
}  # fmt: skip
NUMERIC_ATTRIBUTES = ALLOWED_ATTRIBUTES - {"d", "points"}
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
PATH_PATTERN = re.compile(r"^[MmLlHhVvCcSsQqTtAaZz0-9eE.,\s+-]+$")
POINTS_PATTERN = re.compile(r"^[0-9eE.,\s+-]+$")
MAX_MARKUP_LENGTH = 2000
MAX_ELEMENTS = 20
COORDINATE_MIN = -2.0
COORDINATE_MAX = 26.0
SVG_WRAPPER = "<svg>{}</svg>"


def _check_element(element: ElementTree.Element) -> list[str]:
    """Report what is not allowed on one element and the elements inside it."""
    problems = []
    tag = element.tag
    if tag not in ALLOWED_ELEMENTS:
        return [
            f"element <{tag}> is not allowed; use one of: {', '.join(sorted(ALLOWED_ELEMENTS))}"
        ]
    for attribute, value in element.attrib.items():
        problems.extend(_check_attribute(tag, attribute, value))
    for child in element:
        problems.extend(_check_element(child))
    return problems


def _check_attribute(tag: str, attribute: str, value: str) -> list[str]:
    """Report what is not allowed in one attribute."""
    if attribute not in ALLOWED_ATTRIBUTES:
        return [f"<{tag}> attribute '{attribute}' is not allowed"]
    if attribute == "d":
        return (
            [] if PATH_PATTERN.match(value) else [f"<{tag}> has a path 'd' with other characters"]
        )
    if attribute == "points":
        return [] if POINTS_PATTERN.match(value) else [f"<{tag}> 'points' must be numbers"]
    try:
        number = float(value)
    except ValueError:
        return [f"<{tag}> '{attribute}' must be a number, got '{value}'"]
    if not COORDINATE_MIN <= number <= COORDINATE_MAX:
        return [f"<{tag}> '{attribute}' = {value} lies outside the 24 x 24 icon"]
    return []


def validate_icon(markup: object) -> list[str]:
    """Check the inner markup of one icon.

    Args:
        markup: The value written for the icon.

    Returns:
        The problems found; empty when the icon is safe to draw.
    """
    if not isinstance(markup, str) or not markup.strip():
        return ["an icon must be a non-empty string of SVG elements"]
    if len(markup) > MAX_MARKUP_LENGTH:
        return [f"an icon is longer than {MAX_MARKUP_LENGTH} characters"]
    try:
        root = ElementTree.fromstring(SVG_WRAPPER.format(markup))
    except ElementTree.ParseError as error:
        return [f"the markup is not well-formed: {error}"]
    if sum(1 for _ in root.iter()) - 1 > MAX_ELEMENTS:
        return [f"an icon holds more than {MAX_ELEMENTS} elements"]
    problems = []
    for child in root:
        problems.extend(_check_element(child))
    return problems


def use_local_icons(directory: Path) -> int:
    """Add the icons of ``icons.local.json`` in a folder to the library, when the file exists.

    Args:
        directory: The folder of the spec or the scene.

    Returns:
        How many icons were added.

    Raises:
        SpecError: With every problem found; no icon is added in that case.
    """
    path = directory / LOCAL_ICONS_FILE
    if not path.is_file():
        return 0
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SpecError([f"{path}: not valid JSON ({error})"]) from error
    if not isinstance(raw, dict):
        raise SpecError([f"{path}: must be an object of icon name to SVG markup"])
    builtin = load_icons()
    problems = []
    for name, markup in raw.items():
        if not NAME_PATTERN.match(name):
            problems.append(f"icon '{name}': the name must be lowercase letters, digits and '-'")
        if name in builtin:
            problems.append(f"icon '{name}': a built-in icon has this name; pick another")
        problems.extend(f"icon '{name}': {problem}" for problem in validate_icon(markup))
    if problems:
        raise SpecError(problems)
    register_icons(raw)
    return len(raw)
