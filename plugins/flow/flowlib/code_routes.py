"""Read the route table of a web app from its source: which path draws which component.

Two forms are read. Route objects, as Angular, Vue Router and React Router's data routers
write them: ``{ path: 'settings', loadComponent: () => import('./settings'), canActivate:
[requireAuth] }``, nested by ``children`` or by ``loadChildren`` into another file. And JSX
routes: ``<Route path="settings" element={<Settings />} />``, nested by element. Like
``code_links`` this is pattern matching, not a parser; a route table built by code at run time
is not found.
"""

import re
from dataclasses import dataclass, replace

from .code_links import find_links

PATH_KEY = re.compile(r"""\bpath\s*:\s*(['"`])(?P<path>[^'"`]*)\1""")
LOAD = r"""\(\s*\)\s*=>\s*import\(\s*['"](?P<module>[^'"]+)['"]"""
LOAD_COMPONENT = re.compile(rf"\b(?:loadComponent|component)\s*:\s*{LOAD}")
LOAD_CHILDREN = re.compile(rf"\bloadChildren\s*:\s*{LOAD}")
COMPONENT_NAME = re.compile(r"\b(?:component|Component)\s*:\s*(?P<name>[A-Z]\w*)")
ELEMENT_NAME = re.compile(r"\belement\s*[:=]\s*\{?\s*<(?P<name>[A-Z]\w*)")
GUARDS = re.compile(r"\bcan(?:Activate|Match|Load)\w*\s*:\s*\[(?P<guards>[^\]]*)\]")
BEFORE_ENTER = re.compile(r"\bbeforeEnter\s*:\s*(?P<guards>\w+)")
NAME = re.compile(r"^\s*(?P<name>[A-Za-z_]\w*)\s*$")
JSX_TAG = re.compile(r"<(?P<close>/?)Route\b(?P<attributes>[^>]*?)(?P<empty>/?)>", re.S)
JSX_PATH = re.compile(r"""\bpath\s*=\s*\{?\s*['"](?P<path>[^'"]*)['"]""")
INLINE_GUARD = "inline guard"
OPENING, CLOSING = "([{", ")]}"
GUARD_REACH = 1200  # how much of a guard's definition is read for where it sends the user


@dataclass(frozen=True)
class RawRoute:
    """A route as one file writes it, before the paths of the routes around it are added."""

    path: str
    components: tuple[str, ...]  # module names, as the file imports them
    guards: tuple[str, ...]
    denied: tuple[str, ...]
    children_module: str | None  # the module ``loadChildren`` imports
    parent: int | None  # the index of the enclosing route in the same file
    has_children: bool = False


def read_routes(text: str) -> list[RawRoute]:
    """Return the routes a file declares, as route objects or as JSX routes.

    Args:
        text: The file's content.

    Returns:
        The routes in the order of the file; ``components`` and ``children_module`` hold the
        module names the file imports them from, still to be turned into files.
    """
    imports = _imported_names(text)
    routes = _object_routes(text, imports) or _jsx_routes(text, imports)
    parents = {route.parent for route in routes if route.parent is not None}
    return [replace(route, has_children=index in parents) for index, route in enumerate(routes)]


def _imported_names(text: str) -> dict[str, str]:
    """Return each name a file imports and the module it comes from."""
    names: dict[str, str] = {}
    pattern = re.compile(r"""import\s+(?P<what>[^'";]+?)\s+from\s+['"](?P<module>[^'"]+)['"]""")
    for match in pattern.finditer(text):
        for name in re.findall(r"[A-Za-z_]\w*", match.group("what").replace(" as ", " ")):
            names[name] = match.group("module")
    return names


def _object_routes(text: str, imports: dict[str, str]) -> list[RawRoute]:
    """Read the route objects of a file: every ``{...}`` whose own keys hold a ``path``."""
    spans = _brace_spans(text)
    routes: list[RawRoute] = []
    route_of_span: dict[int, int] = {}
    for number, (start, end, outer) in enumerate(spans):
        if end < 0:
            continue
        own = _own_text(text, (start, end), spans)
        found = PATH_KEY.search(own)
        if found is None:
            continue
        parent = _enclosing_route(outer, spans, route_of_span)
        route_of_span[number] = len(routes)
        routes.append(_route_from(own, (found.group("path"), parent), (text, imports)))
    return routes


def _brace_spans(text: str) -> list[tuple[int, int, int | None]]:
    """Return every ``{...}`` as (start, end, index of the enclosing one), in order of start.

    A brace that is never closed keeps an end of -1.
    """
    spans: list[tuple[int, int, int | None]] = []
    stack: list[int] = []
    opened: dict[int, int] = {}
    for position, char in enumerate(text):
        if char == "{":
            opened[position] = len(spans)
            spans.append((position, -1, opened[stack[-1]] if stack else None))
            stack.append(position)
        elif char == "}" and stack:
            start = stack.pop()
            index = opened[start]
            spans[index] = (start, position + 1, spans[index][2])
    return spans


def _own_text(text: str, span: tuple[int, int], spans: list[tuple[int, int, int | None]]) -> str:
    """Return the text of a span without the spans directly inside it."""
    start, end = span
    pieces, cursor = [], start + 1
    for inner_start, inner_end, _ in spans:
        if start < inner_start and 0 < inner_end < end and inner_start >= cursor:
            pieces.append(text[cursor:inner_start])
            cursor = inner_end
    pieces.append(text[cursor : end - 1])
    return "".join(pieces)


def _enclosing_route(
    outer: int | None, spans: list[tuple[int, int, int | None]], route_of_span: dict[int, int]
) -> int | None:
    """Return the index of the nearest enclosing span that is a route, if there is one."""
    while outer is not None:
        if outer in route_of_span:
            return route_of_span[outer]
        outer = spans[outer][2]
    return None


def _route_from(
    own: str, where: tuple[str, int | None], source: tuple[str, dict[str, str]]
) -> RawRoute:
    """Build a route from the own text of its object."""
    path, parent = where
    text, imports = source
    components = [match.group("module") for match in LOAD_COMPONENT.finditer(own)]
    for pattern in (COMPONENT_NAME, ELEMENT_NAME):
        components.extend(
            imports[match.group("name")]
            for match in pattern.finditer(own)
            if match.group("name") in imports
        )
    children = LOAD_CHILDREN.search(own)
    guards, denied = _guards(own, text)
    return RawRoute(
        path=path,
        components=tuple(components),
        guards=guards,
        denied=denied,
        children_module=children.group("module") if children else None,
        parent=parent,
    )


def _guards(own: str, text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the names of a route's guards and where they send the user instead."""
    names: list[str] = []
    denied: list[str] = []
    for match in (*GUARDS.finditer(own), *BEFORE_ENTER.finditer(own)):
        for item in _top_level_items(match.group("guards")):
            name = NAME.match(item)
            names.append(name.group("name") if name else INLINE_GUARD)
            body = _definition(text, name.group("name")) if name else item
            denied.extend(link.target for link in find_links("", body))
    return tuple(dict.fromkeys(names)), tuple(dict.fromkeys(denied))


def _top_level_items(listed: str) -> list[str]:
    """Split a list's text at its commas that are not inside brackets."""
    items, depth, current = [], 0, []
    for char in listed:
        depth += (char in "([{" and 1) or (-1 if char in ")]}" else 0)
        if char == "," and depth == 0:
            items.append("".join(current))
            current = []
            continue
        current.append(char)
    items.append("".join(current))
    return [item for item in items if item.strip()]


def _definition(text: str, name: str) -> str:
    """Return the start of a name's definition in a file: where a guard is written."""
    found = re.search(rf"\b(?:const|let|var|function)\s+{re.escape(name)}\b", text)
    return text[found.start() : found.start() + GUARD_REACH] if found else ""


def _jsx_routes(text: str, imports: dict[str, str]) -> list[RawRoute]:
    """Read the ``<Route>`` elements of a file, nested as they are written."""
    routes: list[RawRoute] = []
    stack: list[int] = []
    for tag in JSX_TAG.finditer(text):
        if tag.group("close"):
            if stack:
                stack.pop()
            continue
        attributes = tag.group("attributes")
        path = JSX_PATH.search(attributes)
        element = ELEMENT_NAME.search(attributes)
        module = imports.get(element.group("name")) if element else None
        routes.append(
            RawRoute(
                path=path.group("path") if path else "",
                components=(module,) if module else (),
                guards=(),
                denied=(),
                children_module=None,
                parent=stack[-1] if stack else None,
            )
        )
        if not tag.group("empty"):
            stack.append(len(routes) - 1)
    return routes
