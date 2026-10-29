"""Compare a screen flow with the code of the app it draws, and say where they differ.

Each screen of the spec is tied to a page of the code by its address: the ``path`` key of the
screen (``"/settings"``) or the address its L4 screenshot was taken at. Then:

- a tap from a screen whose page has no link to the tap's target is ``tap-not-in-code``: the
  code no longer leads there, or the diagram is wrong;
- a link in a page's own view files to a page the diagram has, with no tap for it, is
  ``link-not-drawn`` (a service's or a store's links are left out: they follow actions many
  pages share, such as signing out); a link in the files every page shows (the top bar)
  needs one arrow anywhere into the page;
- a guarded page that no decision leads to is ``guard-not-drawn``;
- a page of the code with no screen is ``page-not-drawn``, once for all of them.

A tap into a decision is checked against the pages the decision leads to. A tap between two
screens of one page (Sign in and Sign in with an error) is a change of state, not checked. A tap
from a tab of a top bar is checked against the links every page shows.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .check import Code, Finding, Severity
from .code_map import CodeMap, Link, Route, matches, route_of
from .code_scan import links_of
from .diagrams.screen_manifest import MANIFEST_KEY
from .diagrams.screen_spec import ItemKind

MAX_DECISION_DEPTH = 4  # decisions in a row that a tap is followed through
NOT_DRAWN_MARKERS = ("service", "store", "api", "guard", "interceptor", "util")  # not a view


@dataclass(frozen=True)
class _Flow:
    """The parts of a spec the comparison reads: items by id, taps, and each screen's page."""

    kinds: dict[str, str]
    taps: tuple[tuple[str, str], ...]
    pages: dict[str, Route]  # screen id to its page in the code
    unplaced: tuple[str, ...]  # screens with an address that no page matches


def find_drift(raw: dict, folder: Path, code: CodeMap) -> tuple[list[Finding], str]:
    """Compare a screen flow spec with a code map.

    Args:
        raw: The spec, as ``json.loads`` returns it.
        folder: The folder of the spec, where its capture manifest is found.
        code: The map of the app's code.

    Returns:
        The findings, and a line that says how many taps were checked and how many were not.
    """
    flow = _read_flow(raw, folder, code)
    checked, findings = _tap_findings(flow, code)
    findings.extend(_link_findings(flow, code))
    findings.extend(_guard_findings(flow, code))
    findings.extend(_page_findings(flow, code))
    summary = (
        f"drift: {checked} of {len(flow.taps)} taps checked against the code; "
        f"{len(flow.pages)} screens tied to a page"
    )
    if flow.unplaced:
        summary += f"; no page matches the address of {', '.join(flow.unplaced)}"
    return findings, summary


def _read_flow(raw: dict, folder: Path, code: CodeMap) -> _Flow:
    """Read the items, the taps and the page of every screen that has an address."""
    screens = [item for item in raw.get("screens", []) if isinstance(item, dict)]
    addresses = _manifest_addresses(raw, folder)
    kinds = {str(item["id"]): str(item.get("kind", ItemKind.SCREEN.value)) for item in screens}
    pages: dict[str, Route] = {}
    unplaced: list[str] = []
    for item in screens:
        address = item.get("path") or addresses.get(str(item.get("capture", "")))
        if not address:
            continue
        page = route_of(code, address)
        if page is None:
            unplaced.append(str(item["id"]))
            continue
        pages[str(item["id"])] = page
    taps = tuple(
        (str(tap["from"]), str(tap["to"]))
        for tap in raw.get("taps", [])
        if isinstance(tap, dict) and "from" in tap and "to" in tap
    )
    return _Flow(kinds, taps, pages, tuple(unplaced))


def _manifest_addresses(raw: dict, folder: Path) -> dict[str, str]:
    """Return the path each capture code of the spec's manifest was taken at."""
    reference = raw.get(MANIFEST_KEY)
    if not isinstance(reference, str) or not (folder / reference).is_file():
        return {}
    manifest = json.loads((folder / reference).read_text(encoding="utf-8"))
    return {
        code: urlparse(entry.get("url", "")).path or "/"
        for code, entry in manifest.get("screens", {}).items()
        if isinstance(entry, dict) and entry.get("url")
    }


def _reached(flow: _Flow, item: str, depth: int = 0) -> set[str]:
    """Return the page paths a tap into an item ends at, through decisions."""
    if item in flow.pages:
        return {flow.pages[item].path}
    if flow.kinds.get(item) != ItemKind.DECISION.value or depth >= MAX_DECISION_DEPTH:
        return set()
    reached: set[str] = set()
    for source, target in flow.taps:
        if source == item:
            reached |= _reached(flow, target, depth + 1)
    return reached


def _links_from(flow: _Flow, item: str, code: CodeMap) -> list[Link] | None:
    """Return the links a tap from an item may follow; None when the item has no page."""
    shared = [link for link in code.links if link.file in code.shared]
    if flow.kinds.get(item) == ItemKind.TAB.value:
        return shared
    page = flow.pages.get(item)
    if page is None:
        return None
    return links_of(code, page.files) + shared


def _tap_findings(flow: _Flow, code: CodeMap) -> tuple[int, list[Finding]]:
    """Report each tap that no link of its source's page leads to; count the taps checked."""
    checked, findings = 0, []
    for source, target in flow.taps:
        links = _links_from(flow, source, code)
        ends = _reached(flow, target)
        own = flow.pages.get(source)
        if links is None or not ends or (own is not None and own.path in ends):
            continue
        checked += 1
        if any(matches(end, link.target) for end in ends for link in links):
            continue
        findings.append(
            Finding(
                Severity.WARNING,
                Code.TAP_NOT_IN_CODE,
                f"the tap '{source}' to '{target}' leads to {', '.join(sorted(ends))}, but no "
                f"link in the code of {_place(flow, source)} goes there; take the tap out, or "
                "check the code",
                (source, target),
            )
        )
    return checked, findings


def _place(flow: _Flow, item: str) -> str:
    """Name the page of an item for a message: its path, or the top bar for a tab."""
    page = flow.pages.get(item)
    return page.path if page is not None else "the parts every page shows"


def _link_findings(flow: _Flow, code: CodeMap) -> list[Finding]:
    """Report each link in a page's own files to a drawn page with no tap for it."""
    drawn = {page.path for page in flow.pages.values()}
    findings: list[Finding] = []
    for screen, page in flow.pages.items():
        tapped = set().union(*(_reached(flow, t) for s, t in flow.taps if s == screen))
        reported: set[str] = set()
        for link in links_of(code, page.files):
            if _is_logic(link.file):
                continue
            missing = _missed_page(link, (page.path, drawn, tapped | reported))
            if missing is not None:
                reported.add(missing)
                findings.append(_link_finding(screen, link, missing))
    return findings + _shared_link_findings(flow, code, drawn)


def _is_logic(file: str) -> bool:
    """Tell a file of logic (a service, a store) from a view.

    The links of a service follow an action many pages share, such as signing out, so they are
    not asked of each page.
    """
    name = Path(file).name.lower()
    return any(marker in name for marker in NOT_DRAWN_MARKERS)


def _missed_page(link: Link, known: tuple[str, set[str], set[str]]) -> str | None:
    """Return the drawn page a link leads to when no tap covers it, else None."""
    own, drawn, covered = known
    targets = [path for path in drawn if matches(path, link.target) and path != own]
    if not targets or any(path in covered for path in targets):
        return None
    return targets[0]


def _link_finding(screen: str, link: Link, page: str) -> Finding:
    """Write the finding for a link of the code that the diagram does not draw."""
    words = f" ('{link.text}')" if link.text else ""
    return Finding(
        Severity.WARNING,
        Code.LINK_NOT_DRAWN,
        f"{link.file}:{link.line} links '{screen}' to {page}{words}, and no tap from "
        f"'{screen}' leads there; draw it, or say in desc why it is left out",
        (screen,),
    )


def _shared_link_findings(flow: _Flow, code: CodeMap, drawn: set[str]) -> list[Finding]:
    """Report each page the top bar links to that no tap of the diagram leads to."""
    entered = set().union(*(_reached(flow, target) for _, target in flow.taps))
    findings: list[Finding] = []
    for link in (link for link in code.links if link.file in code.shared):
        missing = _missed_page(link, ("", drawn, entered))
        if missing is not None:
            entered.add(missing)
            findings.append(_link_finding("every page", link, missing))
    return findings


def _guard_findings(flow: _Flow, code: CodeMap) -> list[Finding]:
    """Report each guarded page that is drawn but that no decision leads to."""
    decided = set().union(
        *(_reached(flow, target) for source, target in flow.taps if _is_decision(flow, source))
    )
    findings: list[Finding] = []
    drawn = {page.path: screen for screen, page in flow.pages.items()}
    for route in code.routes:
        if not route.guards or route.path not in drawn or route.path in decided:
            continue
        sends = f", and sends the user to {', '.join(route.denied)} instead" if route.denied else ""
        findings.append(
            Finding(
                Severity.WARNING,
                Code.GUARD_NOT_DRAWN,
                f"the code guards {route.path} ({', '.join(route.guards)}){sends}; no decision "
                f"leads to '{drawn[route.path]}', so the diagram does not show it",
                (drawn[route.path],),
            )
        )
    return findings


def _is_decision(flow: _Flow, item: str) -> bool:
    """Tell whether an item is a decision."""
    return flow.kinds.get(item) == ItemKind.DECISION.value


def _page_findings(flow: _Flow, code: CodeMap) -> list[Finding]:
    """Report, once, the pages of the code that no screen draws."""
    drawn = {page.path for page in flow.pages.values()}
    missing = [route.path for route in code.routes if route.path not in drawn]
    if not missing:
        return []
    return [
        Finding(
            Severity.WARNING,
            Code.PAGE_NOT_DRAWN,
            f"pages of the code with no screen: {', '.join(missing)}; draw them, or say in desc "
            "why they are left out",
            (),
        )
    ]


def format_drift(findings: list[Finding], summary: str) -> str:
    """Write the drift findings and the summary as lines of text.

    Args:
        findings: The result of ``find_drift``.
        summary: Its summary line.

    Returns:
        One line per finding, then the summary.
    """
    lines = [f"{f.severity.value.upper()} {f.code.value}: {f.message}" for f in findings]
    return "\n".join([*lines, summary])
