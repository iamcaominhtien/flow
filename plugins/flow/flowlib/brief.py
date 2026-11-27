"""Read back the brief an agent writes beside a diagram, and say what is missing from it.

The working method (``skills/WORKING.md``) asks for ``<name>.brief.md`` before a diagram is
drawn: the question, the reader, the medium, the sources read, what was left out and what is
unknown. The tools do not judge it; they print it with the check report, so that what the
diagram rests on is in front of the agent and, through it, the person, and they warn when the
file or one of its lines is missing.
"""

from dataclasses import dataclass
from pathlib import Path

from .check import Code, Finding, Severity

BRIEF_SUFFIX: str = ".brief.md"
FIELDS: tuple[str, ...] = ("Question", "Reader", "Medium", "Sources read", "Left out", "Unknowns")
NAME_MARKS: str = "-*#> \t"  # bullets, bold, heading and quote marks around a field name
VALUE_MARKS: str = "* \t"  # bold marks and spaces around a value; underscores belong to names
MISSING: str = "(missing)"


@dataclass(frozen=True)
class BriefReport:
    """What the tools say about a brief: lines to print and findings to add to the report."""

    lines: tuple[str, ...]
    findings: tuple[Finding, ...]


def brief_path(folder: Path, name: str) -> Path:
    """Return where the brief of a diagram is expected.

    Args:
        folder: The folder of the spec, or the folder passed to ``Canvas.write``.
        name: The diagram's name without a suffix, the same as its spec's or outputs'.

    Returns:
        ``<folder>/<name>.brief.md``.
    """
    return folder / f"{name}{BRIEF_SUFFIX}"


def read_fields(text: str) -> dict[str, str]:
    """Read the ``Field: value`` lines of a brief, one line per field.

    Field names are matched without regard to case and to Markdown marks around them.

    Args:
        text: The content of a brief file.

    Returns:
        Field name, as written in ``FIELDS``, to value, for the fields present and not empty.
    """
    by_lower = {name.lower(): name for name in FIELDS}
    fields: dict[str, str] = {}
    for line in text.splitlines():
        label, separator, value = line.partition(":")
        name = by_lower.get(label.strip(NAME_MARKS).lower())
        value = value.strip(VALUE_MARKS)
        if separator and name and value:
            fields[name] = value
    return fields


def check_brief(path: Path) -> BriefReport:
    """Read a brief back: its lines to print, and a warning if it or one of its lines is missing.

    Args:
        path: Where the brief is expected (see ``brief_path``).

    Returns:
        The lines ``brief <Field>: <value>`` for every field, and at most one ``no-brief``
        warning naming the file or the missing fields.
    """
    if not path.is_file():
        message = (
            f"no brief at {path}; write it first, as the working method in skills/WORKING.md "
            f"says, one line each: {', '.join(FIELDS)}"
        )
        return BriefReport((), (Finding(Severity.WARNING, Code.NO_BRIEF, message, ()),))
    fields = read_fields(path.read_text(encoding="utf-8"))
    lines = tuple(f"brief {name}: {fields.get(name, MISSING)}" for name in FIELDS)
    missing = [name for name in FIELDS if name not in fields]
    if not missing:
        return BriefReport(lines, ())
    message = f"the brief at {path} has no line for: {', '.join(missing)}"
    return BriefReport(lines, (Finding(Severity.WARNING, Code.NO_BRIEF, message, ()),))
