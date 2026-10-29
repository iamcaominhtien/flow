"""Make a first screen flow spec from a code map: one screen per page, one tap per link.

The draft is a start for the author, not a finished diagram: link words are often missing (the
tap then says where it goes), a page drawn in several states (signed in and out) is one screen,
and the arrangement is left to the layout. What it does get right is what the code says: every
page, every link between pages, the top bar drawn once as a bus, and each guard as a decision
before the pages it guards, with the page it sends the user to instead.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from .code_drift import NOT_DRAWN_MARKERS
from .code_map import CodeMap, Link, Route, route_of
from .code_scan import links_of

HOME_ID = "home"
TOP_BAR_TRIGGER = "click a top bar link"
ENTRY_ID = "open"
ID_JUNK = re.compile(r"[^a-z0-9]+")
CAPTURED = "L4"
DRAFTED = "L0"
WEB_DEVICE = "desktop"  # the code read is a web app's
ZONE_TONES = ("blue", "green", "violet", "amber", "teal")
MIN_TABS = 2  # a bus needs two tabs; a single shared link is drawn from no tab


@dataclass(frozen=True)
class _Pages:
    """The pages of the draft: screen id by route path, and the decision before each guard."""

    ids: dict[str, str]
    guards: dict[str, str]  # route path to the id of the decision in front of it


def draft_spec(code: CodeMap, manifest: tuple[str, dict] | None, title: str) -> dict:
    """Write a first screen flow spec from a code map.

    Args:
        code: The map of the app's code.
        manifest: The capture manifest, when there is one, as its path from the spec and its
            content: a page whose address was captured is drawn at L4 with its screenshot.
        title: The title of the diagram.

    Returns:
        The spec, ready for ``json.dumps``.
    """
    pages = _Pages(_screen_ids(code.routes), _guard_ids(code.routes))
    captures = _captures_by_path(code, manifest[1] if manifest else None)
    screens = [_screen(route, pages, captures) for route in code.routes]
    zones = _zones(code, screens)
    screens.extend(_decision(name, ident) for ident, name in _guard_names(code, pages).items())
    taps = _page_taps(code, pages) + _guard_taps(code, pages)
    tabs, top_taps, buses = _top_bar(code, pages)
    entry, entry_taps = _entry(pages)
    spec: dict = {
        "type": "screen",
        "title": title,
        "desc": "Drafted from the code by flow.py code draft: one screen per page, one tap per "
        "link. Check the words of each tap and the states of each page.",
        "screens": [*entry, *screens, *tabs],
        "taps": [*entry_taps, *taps, *top_taps],
    }
    if manifest is not None:
        spec["captures"] = manifest[0]
    if buses:
        spec["buses"] = buses
    if zones:
        spec["zones"] = zones
    return spec


def _screen_ids(routes: tuple[Route, ...]) -> dict[str, str]:
    """Give each page a short id made from its path: ``/editor/:slug`` is ``editor-slug``."""
    ids: dict[str, str] = {}
    for route in routes:
        base = ID_JUNK.sub("-", route.path.lower()).strip("-") or HOME_ID
        ident, number = base, 1
        while ident in ids.values():
            number += 1
            ident = f"{base}-{number}"
        ids[route.path] = ident
    return ids


def _guard_ids(routes: tuple[Route, ...]) -> dict[str, str]:
    """Give each guarded page the id of the decision for its guards."""
    return {
        route.path: "guard-" + ID_JUNK.sub("-", "-".join(route.guards).lower()).strip("-")
        for route in routes
        if route.guards
    }


def _guard_names(code: CodeMap, pages: _Pages) -> dict[str, str]:
    """Return the words of each guard decision, by its id."""
    names: dict[str, str] = {}
    for route in code.routes:
        ident = pages.guards.get(route.path)
        if ident is not None:
            names[ident] = " and ".join(route.guards)
    return names


def _captures_by_path(code: CodeMap, manifest: dict | None) -> dict[str, str]:
    """Return the capture code of each page whose address the manifest holds."""
    if manifest is None:
        return {}
    found: dict[str, str] = {}
    for capture, entry in manifest.get("screens", {}).items():
        route = route_of(code, urlparse(entry.get("url", "")).path or "/")
        if route is not None and route.path not in found:
            found[route.path] = capture
    return found


def _screen(route: Route, pages: _Pages, captures: dict[str, str]) -> dict:
    """Write the screen of one page: at L4 when it was captured, else a card."""
    screen = {
        "id": pages.ids[route.path],
        "label": route.path,
        "path": route.path,
        "device": WEB_DEVICE,
    }
    if route.path in captures:
        screen.update({"fidelity": CAPTURED, "capture": captures[route.path]})
    else:
        screen["fidelity"] = DRAFTED
    return screen


def _zones(code: CodeMap, screens: list[dict]) -> list[dict]:
    """Put the pages with the same guards in one zone, and the open pages in another.

    The screens are given their zone in place. No zone is made when no page is guarded.
    """
    guards = {route.path: " and ".join(route.guards) for route in code.routes}
    if not any(guards.values()):
        return []
    names = list(dict.fromkeys(guards.values()))
    zones = []
    for number, name in enumerate(names):
        ident = f"zone-{number + 1}"
        label = f"Guarded by {name}" if name else "Open to everyone"
        zones.append({"id": ident, "label": label, "tone": ZONE_TONES[number % len(ZONE_TONES)]})
    for screen in screens:
        screen["zone"] = f"zone-{names.index(guards[screen['path']]) + 1}"
    return zones


def _decision(name: str, ident: str) -> dict:
    """Write the decision a guard makes."""
    return {"id": ident, "kind": "decision", "label": f"Passes {name}?"}


def _target_id(path: str, pages: _Pages) -> str:
    """Return where a tap to a page goes: the page, or the decision of its guard."""
    return pages.guards.get(path, pages.ids[path])


def _trigger(link: Link) -> str:
    """Write the trigger of a tap from a link: its words, or where it goes."""
    return f"click {link.text}" if link.text else f"go to {link.target}"


def _page_taps(code: CodeMap, pages: _Pages) -> list[dict]:
    """Write one tap per page and per page its own view files link to."""
    taps: list[dict] = []
    for route in code.routes:
        seen = {route.path}
        for link in links_of(code, route.files):
            target = route_of(code, link.target)
            if target is None or target.path in seen or _is_logic(link.file):
                continue
            seen.add(target.path)
            taps.append(
                {
                    "from": pages.ids[route.path],
                    "to": _target_id(target.path, pages),
                    "trigger": _trigger(link),
                }
            )
    return taps


def _is_logic(file: str) -> bool:
    """Tell a file of logic from a view, as the drift check does."""
    return any(marker in file.rsplit("/", 1)[-1].lower() for marker in NOT_DRAWN_MARKERS)


def _guard_taps(code: CodeMap, pages: _Pages) -> list[dict]:
    """Write the two exits of each guard decision: into the page, or where it sends instead."""
    taps: list[dict] = []
    done: set[tuple[str, str]] = set()
    for route in code.routes:
        decision = pages.guards.get(route.path)
        if decision is None:
            continue
        taps.append({"from": decision, "to": pages.ids[route.path], "guard": "passes"})
        for denied in route.denied:
            target = route_of(code, denied)
            if target is not None and (decision, target.path) not in done:
                done.add((decision, target.path))
                taps.append(
                    {
                        "from": decision,
                        "to": pages.ids[target.path],
                        "guard": "fails",
                        "kind": "failure",
                    }
                )
    return taps


def _top_bar(code: CodeMap, pages: _Pages) -> tuple[list[dict], list[dict], list[dict]]:
    """Write the links every page shows as one tab each, a bus into them, and their taps."""
    tabs: list[dict] = []
    taps: list[dict] = []
    for link in code.links:
        target = route_of(code, link.target) if link.file in code.shared else None
        ident = f"bar-{pages.ids[target.path]}" if target is not None else ""
        if target is None or any(tab["id"] == ident for tab in tabs):
            continue
        tabs.append({"id": ident, "kind": "tab", "label": link.text or target.path})
        taps.append({"from": ident, "to": _target_id(target.path, pages)})
    if len(tabs) < MIN_TABS:
        return [], [], []
    bus = {"trigger": TOP_BAR_TRIGGER, "to": [tab["id"] for tab in tabs]}
    return tabs, taps, [bus]


def _entry(pages: _Pages) -> tuple[list[dict], list[dict]]:
    """Write the entry point of the app, into its root page when it has one."""
    root = pages.ids.get("/")
    if root is None:
        return [], []
    entry = {"id": ENTRY_ID, "kind": "entry", "label": "Open the app", "detail": "address /"}
    return [entry], [{"from": ENTRY_ID, "to": _target_id("/", pages), "trigger": "open"}]
