"""The map of an app's code that a screen flow is checked against: routes, links and imports.

``code_scan`` writes it from the source of a web app; ``code_drift`` compares a screen flow
spec with it and ``code_draft`` makes a first spec from it. It is kept as JSON so an agent can
read it, correct it, and keep it next to the spec.

Paths in the map are relative to the source folder and use ``/``. A route path is written as in
the router (``/article/:slug``); a link target has ``*`` for each part that the code computes
(``/profile/*``).
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

ANY_PART = "*"  # a part of a link target that the code computes
PARAM_PREFIX = ":"  # a part of a route path that takes any value
REST = "**"  # a route part that takes the rest of the path
JSON_INDENT = 2


class CodeMapError(ValueError):
    """Raised when a code map file cannot be read."""


@dataclass(frozen=True)
class Route:
    """A page of the app: its path, the files that draw it, and what guards it."""

    path: str
    files: tuple[str, ...]  # the components of the route and of the routes around it
    guards: tuple[str, ...] = ()  # the names of the guards, or "inline guard"
    denied: tuple[str, ...] = ()  # where a guard sends the user instead, when the code says


@dataclass(frozen=True)
class Link:
    """A place in the code that leads to a path: a link, a button's navigation, a redirect."""

    file: str
    line: int
    target: str
    text: str = ""  # the words of the link, when the code shows them


@dataclass(frozen=True)
class CodeMap:
    """Everything read from the code of one app."""

    routes: tuple[Route, ...]
    links: tuple[Link, ...]
    imports: dict[str, tuple[str, ...]] = field(default_factory=dict)  # static, file to files
    shared: tuple[str, ...] = ()  # files on every page, such as the top bar


def dump(code: CodeMap, path: Path) -> None:
    """Write a code map as JSON.

    Args:
        code: The map.
        path: The file to write.
    """
    path.write_text(json.dumps(asdict(code), indent=JSON_INDENT) + "\n", encoding="utf-8")


def load(path: Path) -> CodeMap:
    """Read a code map written by ``dump``.

    Args:
        path: The JSON file.

    Returns:
        The map.

    Raises:
        CodeMapError: When the file is not a code map.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return CodeMap(
            routes=tuple(_route(item) for item in raw["routes"]),
            links=tuple(Link(**item) for item in raw["links"]),
            imports={key: tuple(value) for key, value in raw.get("imports", {}).items()},
            shared=tuple(raw.get("shared", ())),
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise CodeMapError(f"{path} is not a code map: {error}") from error


def _route(raw: dict) -> Route:
    """Build a route from its JSON object."""
    return Route(
        path=raw["path"],
        files=tuple(raw["files"]),
        guards=tuple(raw.get("guards", ())),
        denied=tuple(raw.get("denied", ())),
    )


def matches(route_path: str, target: str) -> bool:
    """Tell whether a link target, or the path of an address, leads to a route.

    Args:
        route_path: The route, as the router writes it (``/article/:slug``).
        target: A link target (``/article/*``) or a concrete path (``/article/hello``).

    Returns:
        True when every part agrees: a parameter or a computed part matches any one part.
    """
    route_parts = _parts(route_path)
    target_parts = _parts(target)
    if route_parts and route_parts[-1] == REST:
        prefix = route_parts[:-1]
        return len(target_parts) >= len(prefix) and _agree(prefix, target_parts[: len(prefix)])
    return len(route_parts) == len(target_parts) and _agree(route_parts, target_parts)


def specificity(route_path: str) -> int:
    """Return how many fixed parts a route has: of two routes that match, the more fixed wins."""
    return sum(1 for part in _parts(route_path) if not part.startswith(PARAM_PREFIX))


def route_of(code: CodeMap, path: str) -> Route | None:
    """Return the route a concrete path is drawn by: the most specific one that matches."""
    found = [route for route in code.routes if matches(route.path, path)]
    return max(found, key=lambda route: specificity(route.path), default=None)


def closure(code: CodeMap, files: tuple[str, ...]) -> set[str]:
    """Return the files and every file they import, directly or not.

    Args:
        code: The map, with its static imports.
        files: Where to start.

    Returns:
        The files reached, the starting ones included.
    """
    reached: set[str] = set()
    waiting = list(files)
    while waiting:
        current = waiting.pop()
        if current in reached:
            continue
        reached.add(current)
        waiting.extend(code.imports.get(current, ()))
    return reached


def _parts(path: str) -> list[str]:
    """Split a path into its parts, without empty ones."""
    return [part for part in path.split("/") if part]


def _agree(route_parts: list[str], target_parts: list[str]) -> bool:
    """Tell whether two lists of parts of the same length agree part by part."""
    return all(
        one == two or one.startswith(PARAM_PREFIX) or two == ANY_PART
        for one, two in zip(route_parts, target_parts, strict=True)
    )
