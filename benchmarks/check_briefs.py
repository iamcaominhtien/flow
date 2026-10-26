#!/usr/bin/env python3
"""Check the benchmark briefs: the format, the index, and how the claimed sizes compare to the text.

Errors are things that break the format (a missing section, an id that does not match its file, a
brief that is not in the index). Warnings are soft: a claimed element count far from the number of
names the text contains, a brief outside its word range, a feature the tool cannot draw.

    python3 benchmarks/check_briefs.py            print the report
    python3 benchmarks/check_briefs.py --errors   print only errors; exit code 1 if there are any
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

BRIEFS_DIR = Path(__file__).resolve().parent / "briefs"
TYPES = ("flowchart", "sequence", "er", "architecture", "bpmn", "state", "orgchart", "gantt")
LEVELS = ("A", "B", "C")
SECTIONS = ("Brief", "Must show", "Traps", "Sources", "Uncertain")
STRUCTURE = "Structure"  # optional: the exact elements and connections, checked against the text
FIELDS = ("type", "level", "elements", "connections", "groups")
ELEMENT_RANGE = {"A": (8, 12), "B": (20, 30), "C": (40, 60)}
WORD_MIN, WORD_MAX = 80, 250
WORD_MAX_LEVEL_C = 700  # a level C brief names dozens of elements and needs more words
NAME_TOLERANCE = 0.25  # a measured name count more than this fraction off the claim is flagged
FAN_OUT_MINIMUM = 3  # a level C brief with a structure needs a node with at least this many exits
BACK_EDGE_MINIMUM = 2  # a level C brief of a type with loops must state at least this many
LOOP_TYPES = ("flowchart", "sequence", "architecture", "bpmn", "state")
UNSUPPORTED = (
    "boundary event",
    "data object",
    "logo",
    "event sub-process",
    "event subprocess",
    "device frame",
)
NAME_PATTERN = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+\b")
BACK_PATTERN = re.compile(r"\b(?:loops? back|returns? to|routes? back|back to|re-enters?)\b", re.I)
HEADING_PATTERN = re.compile(r"^## (?P<id>[a-z]+-[ABC]-\d\d) — (?P<title>.+)$", re.M)
FIELD_PATTERN = re.compile(r"^\* \*\*(?P<key>[a-z]+):\*\* ?(?P<value>.*)$", re.M)
DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
ELEMENT_LINE = re.compile(r"^- (?P<group>[^:]+): (?P<names>.+)$", re.M)
CONNECTION_LINE = re.compile(r"^- (?P<source>\w+) -> (?P<target>\w+)(?: \((?P<label>.*)\))?$", re.M)
PLACEMENT = re.compile(r"^(?P<name>\w+)@(?P<start>\d+)\+(?P<length>\d+)$")
GLUED_NUMBER = re.compile(r"[a-z]\d{2}[.,;]?(?:\s|$)")  # a two-digit mark; names end in 1-9


@dataclass
class Brief:
    """One brief as read from a file."""

    identifier: str
    title: str
    path: Path
    fields: dict[str, str] = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def kind(self) -> str:
        """Return the diagram type in the id."""
        return self.identifier.rsplit("-", 2)[0]

    @property
    def level(self) -> str:
        """Return the level letter in the id."""
        return self.identifier.rsplit("-", 2)[1]

    def claimed(self, key: str) -> int | None:
        """Return a claimed number (``elements`` or ``connections``), or None if it is not one."""
        value = self.fields.get(key, "")
        return int(value) if value.isdigit() else None

    @property
    def names(self) -> set[str]:
        """Return the distinct CamelCase names in the brief text."""
        return set(NAME_PATTERN.findall(self.sections.get("Brief", "")))

    @property
    def structure(self) -> "Structure | None":
        """Return the parsed Structure section, or None when the brief has none."""
        text = self.sections.get(STRUCTURE)
        return parse_structure(text) if text else None

    @property
    def words(self) -> int:
        """Return the number of words in the brief text."""
        return len(self.sections.get("Brief", "").split())


@dataclass
class Structure:
    """The exact content of a brief: its elements by group, and its connections."""

    groups: dict[str, list[str]]
    placements: dict[str, tuple[int, int]]
    connections: list[tuple[str, str]]
    labels: set[str]  # single-word labels of connections, such as the name of a message

    @property
    def elements(self) -> list[str]:
        """Return every element name, in the order written."""
        return [name for names in self.groups.values() for name in names]


@dataclass
class Report:
    """What the checks found."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_structure(text: str) -> Structure:
    """Read the Structure section of a brief.

    Args:
        text: The text under the ``Structure`` heading.

    Returns:
        The groups with their element names, the start and length of timed elements, and the
        connections as (source, target) pairs.
    """
    elements_text, _, connections_text = text.partition("**Connections**")
    groups: dict[str, list[str]] = {}
    placements: dict[str, tuple[int, int]] = {}
    for line in ELEMENT_LINE.finditer(elements_text):
        names = []
        for token in line["names"].split(", "):
            placed = PLACEMENT.match(token.strip())
            name = placed["name"] if placed else token.strip()
            if placed:
                placements[name] = (int(placed["start"]), int(placed["length"]))
            names.append(name)
        groups[line["group"].strip()] = names
    found = list(CONNECTION_LINE.finditer(connections_text))
    connections = [(m["source"], m["target"]) for m in found]
    labels = {m["label"] for m in found if m["label"] and NAME_PATTERN.fullmatch(m["label"])}
    return Structure(groups, placements, connections, labels)


def _split_sections(text: str) -> dict[str, str]:
    """Split the body of a brief at its ``###`` headings."""
    parts = re.split(r"^### (.+)$", text, flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def read_briefs(directory: Path = BRIEFS_DIR) -> list[Brief]:
    """Read every brief of every type file in a folder.

    Args:
        directory: The folder that holds ``<type>.md`` files.

    Returns:
        The briefs, in file order and then in the order written.
    """
    briefs = []
    for kind in TYPES:
        path = directory / f"{kind}.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        matches = list(HEADING_PATTERN.finditer(text))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[match.end() : end].split("\n---")[0]
            fields = {m["key"]: m["value"].strip() for m in FIELD_PATTERN.finditer(body)}
            brief = Brief(match["id"], match["title"].strip(), path, fields, _split_sections(body))
            briefs.append(brief)
    return briefs


def _check_format(brief: Brief, report: Report) -> None:
    """Report a missing field or section, and an id, number or source that does not fit."""
    where = brief.identifier
    if brief.kind not in TYPES or brief.level not in LEVELS:
        report.errors.append(f"{where}: the id must be <type>-<A|B|C>-<nn> with a known type")
    if brief.path.stem != brief.kind:
        report.errors.append(f"{where}: is in {brief.path.name}, expected {brief.kind}.md")
    report.errors.extend(
        f"{where}: field '{key}' is missing or empty" for key in FIELDS if not brief.fields.get(key)
    )
    report.errors.extend(
        f"{where}: section '{name}' is missing or empty"
        for name in SECTIONS
        if not brief.sections.get(name)
    )
    _check_numbers(brief, report)
    if "http" not in brief.sections.get("Sources", ""):
        report.warnings.append(f"{where}: Sources holds no URL (a book or standard only)")


def _check_numbers(brief: Brief, report: Report) -> None:
    """Report counts that are not numbers and a type or level that differs from the id."""
    where = brief.identifier
    for key in ("elements", "connections"):
        if brief.claimed(key) is None:
            report.errors.append(f"{where}: '{key}' must be a number")
    kind = brief.fields.get("type", "").replace(" ", "")
    if kind != brief.kind or brief.fields.get("level") != brief.level:
        report.errors.append(f"{where}: the type and level fields do not match the id")


def _check_size(brief: Brief, report: Report) -> None:
    """Warn when the claimed size, the word count or the names in the text do not fit the level."""
    where = brief.identifier
    elements = brief.claimed("elements")
    if elements is None or brief.level not in ELEMENT_RANGE:
        return
    low, high = ELEMENT_RANGE[brief.level]
    if brief.kind == "sequence" and brief.structure is not None:
        elements = brief.claimed("connections") or 0  # a sequence is sized by its messages
    if not low <= elements <= high:
        report.warnings.append(
            f"{where}: claims {elements} elements, level {brief.level} is {low}-{high}"
        )
    word_max = WORD_MAX_LEVEL_C if brief.level == "C" else WORD_MAX
    if not WORD_MIN <= brief.words <= word_max:
        report.warnings.append(
            f"{where}: the brief has {brief.words} words, the range is {WORD_MIN}-{word_max}"
        )
    measured = len(brief.names)
    if brief.structure is None and abs(measured - elements) > NAME_TOLERANCE * elements:
        report.warnings.append(
            f"{where}: claims {elements} elements, the text names {measured} CamelCase identifiers"
        )


def _check_content(brief: Brief, report: Report) -> None:
    """Warn about unsupported features, dates, leftover citation numbers and too few returns."""
    where = brief.identifier
    text = brief.sections.get("Brief", "")
    lowered = text.lower()
    for word in UNSUPPORTED:
        if word in lowered:
            report.warnings.append(f"{where}: mentions '{word}', which the tool cannot draw")
    if DATE_PATTERN.search(text):
        report.warnings.append(f"{where}: holds a calendar date, which the tool cannot read")
    if GLUED_NUMBER.search(text):
        report.warnings.append(
            f"{where}: a number is glued to a word, perhaps a leftover citation mark"
        )
    returns = len(BACK_PATTERN.findall(text))
    needs_returns = brief.level == "C" and brief.kind in LOOP_TYPES and brief.structure is None
    if needs_returns and returns < BACK_EDGE_MINIMUM:
        report.warnings.append(
            f"{where}: level C but only {returns} phrases about a return or loop"
        )


def _check_counts(brief: Brief, structure: Structure, report: Report) -> None:
    """Report claimed counts that differ from the Structure, and connections to unknown elements."""
    where = brief.identifier
    elements = structure.elements
    if len(elements) != brief.claimed("elements") or len(set(elements)) != len(elements):
        report.errors.append(
            f"{where}: Structure lists {len(elements)} elements, "
            f"the field says {brief.fields.get('elements')}"
        )
    if len(structure.connections) != brief.claimed("connections"):
        report.errors.append(
            f"{where}: Structure lists {len(structure.connections)} connections, "
            f"the field says {brief.fields.get('connections')}"
        )
    known = set(elements)
    for source, target in structure.connections:
        if source not in known or target not in known:
            report.errors.append(
                f"{where}: the connection {source} -> {target} names an unknown element"
            )


def _check_names(brief: Brief, structure: Structure, report: Report) -> None:
    """Report Structure names that the Brief does not use, and Brief names the Structure lacks."""
    where = brief.identifier
    text = brief.sections.get("Brief", "")
    missing = [name for name in (*structure.elements, *structure.labels) if name not in text]
    if missing:
        report.errors.append(f"{where}: names not used in the Brief: {', '.join(missing[:5])}")
    extra = sorted(brief.names - set(structure.elements) - structure.labels)
    if extra:
        report.warnings.append(
            f"{where}: the Brief names identifiers not in Structure: {', '.join(extra[:5])}"
        )


def _check_structure(brief: Brief, report: Report) -> None:
    """Check a Structure section against the claimed counts, the text and the level."""
    structure = brief.structure
    if structure is None:
        return
    _check_counts(brief, structure, report)
    _check_names(brief, structure, report)
    _check_level_rules(brief, structure, report)


def _check_timing(brief: Brief, structure: Structure, report: Report) -> None:
    """Report a timed element that starts before one of its predecessors ends."""
    for source, target in structure.connections:
        if source in structure.placements and target in structure.placements:
            start, length = structure.placements[source]
            if structure.placements[target][0] < start + length:
                report.errors.append(f"{brief.identifier}: {target} starts before {source} ends")


def _check_level_rules(brief: Brief, structure: Structure, report: Report) -> None:
    """Check the level C rules that can be measured on a structure: fan-out and crossings."""
    _check_timing(brief, structure, report)
    if brief.level != "C":
        return
    where = brief.identifier
    exits: dict[str, int] = {}
    for source, _ in structure.connections:
        exits[source] = exits.get(source, 0) + 1
    if max(exits.values(), default=0) < FAN_OUT_MINIMUM:
        report.warnings.append(
            f"{where}: level C but no element has {FAN_OUT_MINIMUM} or more exits"
        )
    group_of = {name: group for group, names in structure.groups.items() for name in names}
    if not any(group_of.get(s) != group_of.get(t) for s, t in structure.connections):
        report.warnings.append(f"{where}: level C but no connection crosses between groups")


def _check_index(briefs: list[Brief], directory: Path, report: Report) -> None:
    """Report a brief that the index does not list, or lists with other numbers."""
    index = directory / "index.md"
    listed = {}
    for line in index.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(("id", "type", "level", "subject", "elements", "connections")):
            listed[cells[0]] = cells
    for brief in briefs:
        row = listed.get(brief.identifier)
        if row is None:
            report.errors.append(f"{brief.identifier}: is not in index.md")
        elif (row[4], row[5]) != (brief.fields.get("elements"), brief.fields.get("connections")):
            report.errors.append(f"{brief.identifier}: the counts in index.md differ from the file")
    known = {brief.identifier for brief in briefs}
    for name in listed.keys() - known - {"id", ":----"}:
        if not name.startswith(":"):
            report.errors.append(f"{name}: is in index.md but in no type file")


def check(directory: Path = BRIEFS_DIR) -> tuple[list[Brief], Report]:
    """Run every check on the briefs in a folder.

    Args:
        directory: The folder that holds the type files and ``index.md``.

    Returns:
        The briefs and the report.
    """
    briefs = read_briefs(directory)
    report = Report()
    for brief in briefs:
        _check_format(brief, report)
        _check_size(brief, report)
        _check_content(brief, report)
        _check_structure(brief, report)
    _check_index(briefs, directory, report)
    seen = [brief.identifier for brief in briefs]
    for name in {name for name in seen if seen.count(name) > 1}:
        report.errors.append(f"{name}: appears more than once")
    return briefs, report


def format_report(briefs: list[Brief], report: Report) -> str:
    """Write the report as Markdown: a table of measurements, then errors and warnings.

    Args:
        briefs: The briefs that were checked.
        report: The result of ``check``.

    Returns:
        The report text.
    """
    lines = [
        "| id | claimed elements | names in text | words | claimed connections |",
        "| --- | --- | --- | --- | --- |",
    ]
    for brief in briefs:
        lines.append(
            f"| {brief.identifier} | {brief.fields.get('elements')} | {len(brief.names)} "
            f"| {brief.words} | {brief.fields.get('connections')} |"
        )
    lines += ["", f"Errors: {len(report.errors)}", *[f"- {item}" for item in report.errors]]
    lines += ["", f"Warnings: {len(report.warnings)}", *[f"- {item}" for item in report.warnings]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the command line.

    Args:
        argv: The arguments after the program name; ``sys.argv`` is used when None.

    Returns:
        1 when ``--errors`` was given and an error was found, else 0.
    """
    parser = argparse.ArgumentParser(description="Check the benchmark briefs.")
    parser.add_argument("--errors", action="store_true", help="fail on errors only")
    arguments = parser.parse_args(argv)
    briefs, report = check()
    print(format_report(briefs, report))
    return 1 if arguments.errors and report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
