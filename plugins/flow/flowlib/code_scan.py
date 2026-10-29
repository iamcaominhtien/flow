"""Read a web app's source folder into a code map: its routes, its links and its imports.

Every source file is read once. Its links come from ``code_links`` and its routes from
``code_routes``; the routes of a file that another file loads with ``loadChildren`` are put
under that route's path. A file's static imports (and an Angular ``templateUrl``) say which
files draw a page: the components of a route and all they import.

Files that the start of the app imports (``main.ts``, the root component) but no route does are
the parts every page shows, such as the top bar and the footer: their links are ``shared``.
"""

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .code_links import find_links
from .code_map import CodeMap, Link, Route, closure
from .code_routes import RawRoute, read_routes

SOURCE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".vue", ".svelte", ".html")
SKIPPED_FOLDERS = frozenset({"node_modules", "dist", "build", ".git", ".angular", "coverage"})
TEST_MARKERS = (".spec.", ".test.", ".stories.")
ENTRY_STEMS = frozenset({"main", "index", "app", "app.component", "app.config", "router"})
STATIC_IMPORT = re.compile(
    r"""(?:^|\n)\s*(?:import|export)\s[^'";]*?from\s+['"](?P<module>\.{1,2}/[^'"]+)['"]"""
    r"""|(?:^|\n)\s*import\s+['"](?P<bare>\.{1,2}/[^'"]+)['"]"""
)
TEMPLATE_URL = re.compile(r"""\btemplateUrl\s*:\s*['"](?P<module>[^'"]+)['"]""")
INDEX_STEM = "index"
ENTRY_DEPTH = 2  # an entry sits in the source folder or one folder below (src/app/app.ts)


@dataclass(frozen=True)
class _Source:
    """The files of the app, read once: path relative to the root, and text."""

    root: Path
    texts: dict[str, str]


def scan(root: Path) -> CodeMap:
    """Read the source folder of a web app.

    Args:
        root: The folder to read, usually the app's ``src``.

    Returns:
        The map of its routes, links, static imports and shared files.
    """
    source = _Source(root, _read_files(root))
    imports = {file: tuple(_imports_of(file, source)) for file in source.texts}
    links = tuple(link for file, text in source.texts.items() for link in find_links(file, text))
    routes = tuple(_routes(source))
    code = CodeMap(routes, links, imports)
    return CodeMap(routes, links, imports, tuple(sorted(_shared(code, source))))


def _read_files(root: Path) -> dict[str, str]:
    """Read every source file under a folder, leaving out tests and built output."""
    texts: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in SKIPPED_FOLDERS for part in relative.parts):
            continue
        if path.suffix not in SOURCE_SUFFIXES or any(m in path.name for m in TEST_MARKERS):
            continue
        if path.is_file():
            texts[relative.as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    return texts


def _imports_of(file: str, source: _Source) -> list[str]:
    """Return the files a file imports statically, and its Angular template."""
    text = source.texts[file]
    modules = [
        match.group("module") or match.group("bare") for match in STATIC_IMPORT.finditer(text)
    ]
    modules.extend(match.group("module") for match in TEMPLATE_URL.finditer(text))
    found = (_resolved(file, module, source) for module in modules)
    return [path for path in found if path is not None]


def _resolved(file: str, module: str, source: _Source) -> str | None:
    """Return the file a relative module name points to, trying the usual suffixes."""
    base = PurePosixPath(file).parent / module
    clean = _clean(base)
    candidates = [clean, *(f"{clean}{suffix}" for suffix in SOURCE_SUFFIXES)]
    candidates.extend(f"{clean}/{INDEX_STEM}{suffix}" for suffix in SOURCE_SUFFIXES)
    return next((candidate for candidate in candidates if candidate in source.texts), None)


def _clean(path: PurePosixPath) -> str:
    """Resolve ``.`` and ``..`` in a relative path without touching the disk."""
    parts: list[str] = []
    for part in path.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)
    return "/".join(parts)


def _routes(source: _Source) -> list[Route]:
    """Return every page route of the app, with its full path and the files that draw it."""
    raw = {file: read_routes(text) for file, text in source.texts.items() if _may_route(text)}
    raw = {file: routes for file, routes in raw.items() if routes}
    loaded = {
        _resolved(file, route.children_module, source)
        for file, routes in raw.items()
        for route in routes
        if route.children_module
    }
    pages: list[Route] = []
    for file in raw:
        if file not in loaded:
            pages.extend(_expanded(file, ("", (), ()), raw, source))
    return list({route.path: route for route in pages}.values())


def _may_route(text: str) -> bool:
    """Tell whether a file may hold routes, before it is read for them."""
    return "path" in text and ("Route" in text or "route" in text)


def _expanded(
    file: str,
    above: tuple[str, tuple[str, ...], tuple[str, ...]],
    raw: dict[str, list[RawRoute]],
    source: _Source,
) -> list[Route]:
    """Return the page routes of one file under the path, files and guards above it."""
    prefix, files, guards = above
    pages: list[Route] = []
    routes = raw.get(file, [])
    for route in routes:
        path, chain_files, chain_guards, denied = _chain(file, route, routes, source)
        full_files = tuple(dict.fromkeys((*files, *chain_files)))
        full = (_joined(prefix, path), full_files, tuple(dict.fromkeys((*guards, *chain_guards))))
        if route.children_module:
            child = _resolved(file, route.children_module, source)
            if child is not None:
                pages.extend(_expanded(child, full, raw, source))
            continue
        if not route.has_children:
            pages.append(Route(*full, denied))
    return pages


def _chain(
    file: str, route: RawRoute, routes: list[RawRoute], source: _Source
) -> tuple[str, list[str], tuple[str, ...], tuple[str, ...]]:
    """Return a route's path, files, guards and denials, with those of its parents in the file."""
    path, files, guards, denied = "", [], [], []
    current: RawRoute | None = route
    while current is not None:
        path = _joined(current.path, path)
        resolved = (_resolved(file, module, source) for module in current.components)
        files[:0] = [found for found in resolved if found is not None]
        guards[:0] = current.guards
        denied[:0] = current.denied
        current = routes[current.parent] if current.parent is not None else None
    return path, files, tuple(dict.fromkeys(guards)), tuple(dict.fromkeys(denied))


def _joined(first: str, second: str) -> str:
    """Join two route paths with one slash; the result starts with ``/``."""
    parts = [part for part in f"{first}/{second}".split("/") if part]
    return "/" + "/".join(parts)


def _shared(code: CodeMap, source: _Source) -> set[str]:
    """Return the files with links that the start of the app reaches and no route's files do.

    A file that declares routes is left out: its links are the redirects of its guards.
    """
    starts = tuple(file for file in source.texts if _is_entry(file))
    pages: set[str] = set()
    for route in code.routes:
        pages |= closure(code, route.files)
    routing = {file for file, text in source.texts.items() if read_routes(text)}
    with_links = {link.file for link in code.links}
    return (closure(code, starts) - pages - routing) & with_links


def _is_entry(file: str) -> bool:
    """Tell whether a file is where the app starts: ``main.ts`` or the root component."""
    path = PurePosixPath(file)
    stem = path.name.rsplit(".", 1)[0]
    return stem.lower() in ENTRY_STEMS and len(path.parts) <= ENTRY_DEPTH


def links_of(code: CodeMap, files: tuple[str, ...]) -> list[Link]:
    """Return the links in some files and in everything they import.

    Args:
        code: The map.
        files: The files of a page.

    Returns:
        The links found there, in the order of the map.
    """
    reached = closure(code, files)
    return [link for link in code.links if link.file in reached]
