"""Split a large ER spec by domain: an overview and one page per domain.

The design splits a schema of more than about ten tables by domain. The overview has one box
per domain and one line per foreign key that crosses a domain border, named after the column.
A domain page draws the tables of its domain in full; a table of another domain that they
point at, or that points at them, appears once as a grey dashed copy that shows only its key
and a tag ("See Orders page").

Tables name their domain with ``"domain"``. The result is a set of ER specs, which are built
like any other.
"""

import math
import re
from typing import Any

OVERVIEW = "overview"
GRAY = "gray"
OVERVIEW_ROWS_FROM = 4  # an overview with more domains than this uses two rows
SEE_TAG = "See {domain} page"
NEIGHBOUR_STEPS = (
    (0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1), (0, 2), (0, -2),
)  # fmt: skip
DEFAULT_COLUMNS = 3

Cell = tuple[int, int]


class SplitError(ValueError):
    """The spec cannot be split: a table has no domain."""


def slug(name: str) -> str:
    """Return a name as lower case words joined by hyphens, for ids and file names.

    Args:
        name: A domain name.

    Returns:
        The slug, or ``domain`` for a name with no letters or digits.
    """
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "domain"


def split_by_domain(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Split an ER spec into an overview and one spec per domain.

    Args:
        raw: A parsed ER spec in which every table has a ``domain``.

    Returns:
        The specs by name: ``overview``, then the slug of each domain.

    Raises:
        SplitError: If a table has no domain, or there is only one domain.
    """
    tables = {table["id"]: table for table in raw.get("tables", [])}
    missing = [name for name, table in tables.items() if not table.get("domain")]
    if missing:
        raise SplitError(f"these tables have no 'domain': {', '.join(missing)}")
    domains = list(dict.fromkeys(table["domain"] for table in tables.values()))
    if len(domains) < 2:  # noqa: PLR2004
        raise SplitError("there is only one domain; nothing to split")
    pages = {OVERVIEW: _overview(raw, tables, domains)}
    for domain in domains:
        pages[slug(domain)] = _domain_page(raw, tables, domain)
    return pages


def _overview(
    raw: dict[str, Any], tables: dict[str, dict[str, Any]], domains: list[str]
) -> dict[str, Any]:
    """Build the overview: a header-only box per domain and a line per crossing foreign key."""
    first = {
        domain: next(t for t in tables.values() if t["domain"] == domain) for domain in domains
    }
    columns = math.ceil(len(domains) / 2) if len(domains) > OVERVIEW_ROWS_FROM else len(domains)
    boxes = []
    for index, domain in enumerate(domains):
        box = {
            "id": slug(domain),
            "name": domain,
            "tone": first[domain].get("tone", GRAY),
            "columns": [],
            "at": [index // columns, index % columns],
        }
        if first[domain].get("icon"):
            box["icon"] = first[domain]["icon"]
        boxes.append(box)
    joined: dict[tuple[str, str], dict[str, Any]] = {}
    for relation in raw.get("relations", []):
        start, end = tables[relation["from"]]["domain"], tables[relation["to"]]["domain"]
        if start == end:
            continue
        label = relation.get("to_column") or relation.get("from_column") or relation.get("label")
        crossing = {k: v for k, v in relation.items() if k not in COLUMN_KEYS}
        line = joined.setdefault((start, end), {**crossing, "from": slug(start), "to": slug(end)})
        names = [line["label"], label] if line.get("label") else [label]
        line["label"] = ", ".join(dict.fromkeys(name for name in names if name))
    relations = list(joined.values())
    return {**_header(raw, f"{raw.get('title', 'Schema')}: overview"), "tables": boxes,
            "relations": relations}  # fmt: skip


COLUMN_KEYS = ("from_column", "to_column", "label")


def _header(raw: dict[str, Any], title: str) -> dict[str, Any]:
    """Return the keys every page shares: type, style, title and description."""
    header = {"type": raw.get("type", "er"), "title": title, "desc": raw.get("desc", "")}
    if "style" in raw:
        header["style"] = raw["style"]
    return header


def _domain_page(
    raw: dict[str, Any], tables: dict[str, dict[str, Any]], domain: str
) -> dict[str, Any]:
    """Build the page of one domain: its tables in full and grey copies of the foreign ones."""
    own = [table for table in tables.values() if table["domain"] == domain]
    own_ids = {table["id"] for table in own}
    relations = [r for r in raw.get("relations", []) if r["from"] in own_ids or r["to"] in own_ids]
    foreign_ids = list(
        dict.fromkeys(end for r in relations for end in (r["from"], r["to"]) if end not in own_ids)
    )
    cells = _cells(own)
    pages = [{**table, "at": list(cells[table["id"]])} for table in own]
    for name in foreign_ids:
        copy = _copy(tables[name])
        copy["at"] = list(_free_cell(name, cells, relations, own_ids))
        cells[name] = (copy["at"][0], copy["at"][1])
        pages.append(copy)
    for page in pages:
        page.pop("domain", None)
    kept = {page["id"]: {c["name"] for c in page["columns"]} for page in pages}
    drawn = [_relation_on_page(r, kept) for r in relations]
    _compact(pages)
    return {**_header(raw, f"{raw.get('title', 'Schema')}: {domain}"), "tables": pages,
            "relations": drawn}  # fmt: skip


def _copy(table: dict[str, Any]) -> dict[str, Any]:
    """Return the grey dashed copy of a foreign table: its key columns and a tag."""
    keys = [c for c in table["columns"] if "pk" in c.get("flags", [])] or table["columns"][:1]
    copy = {
        "id": table["id"],
        "name": table["name"],
        "tone": GRAY,
        "columns": keys,
        "see": SEE_TAG.format(domain=table["domain"]),
    }
    if table.get("icon"):
        copy["icon"] = table["icon"]
    return copy


def _relation_on_page(relation: dict[str, Any], kept: dict[str, set[str]]) -> dict[str, Any]:
    """Return a relation with the column names dropped that a copy does not show."""
    drawn = dict(relation)
    for end, key in (("from", "from_column"), ("to", "to_column")):
        if drawn.get(key) not in kept[drawn[end]]:
            drawn.pop(key, None)
    return drawn


def _cells(own: list[dict[str, Any]]) -> dict[str, Cell]:
    """Return the grid cell of each table of a domain: its own ``at``, or row after row."""
    if all("at" in table for table in own):
        return {table["id"]: (table["at"][0], table["at"][1]) for table in own}
    return {
        table["id"]: (index // DEFAULT_COLUMNS, index % DEFAULT_COLUMNS)
        for index, table in enumerate(own)
    }


def _free_cell(
    name: str, cells: dict[str, Cell], relations: list[dict[str, Any]], own_ids: set[str]
) -> Cell:
    """Find a free cell for a copy, next to the table of its domain that it is joined to."""
    neighbour = next(
        end for r in relations for end in (r["from"], r["to"])
        if name in (r["from"], r["to"]) and end != name and end in own_ids
    )  # fmt: skip
    row, column = cells[neighbour]
    taken = set(cells.values())
    for step_row, step_column in NEIGHBOUR_STEPS:
        cell = (row + step_row, column + step_column)
        if cell not in taken:
            return cell
    return (row + 2, column)


def _compact(pages: list[dict[str, Any]]) -> None:
    """Rewrite the cells so that rows and columns are numbered from 0 without gaps."""
    rows = sorted({page["at"][0] for page in pages})
    columns = sorted({page["at"][1] for page in pages})
    for page in pages:
        page["at"] = [rows.index(page["at"][0]), columns.index(page["at"][1])]
