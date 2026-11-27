"""Read back the brief an agent writes beside a diagram, and say when there is none.

The working method (``skills/WORKING.md``) asks for ``<name>.brief.md`` before a diagram is
drawn: the question, the reader, the medium, the sources read, what was left out and what is
unknown. The tools do not judge it; they print the main lines with the check report, so that
what the diagram rests on is in front of the agent and, through it, the person.
"""

from pathlib import Path

from .check import Code, Finding, Severity

BRIEF_SUFFIX = ".brief.md"
FIELDS = ("Question", "Reader", "Medium", "Sources read", "Left out", "Unknowns")
PRINTED_FIELDS = ("Question", "Medium", "Sources read", "Left out")
MARKUP = "-*_ "  # list bullets and bold or italic marks around a field name


def brief_path(folder: Path, name: str) -> Path:
    """Return where the brief of a diagram is expected.

    Args:
        folder: The folder of the spec, or the output folder on the author path.
        name: The diagram's name without a suffix.

    Returns:
        ``<folder>/<name>.brief.md``.
    """
    return folder / f"{name}{BRIEF_SUFFIX}"


def read_fields(text: str) -> dict[str, str]:
    """Read the ``Field: value`` lines of a brief, ignoring Markdown marks around the names.

    Args:
        text: The content of a brief file.

    Returns:
        Field name to value, for the fields of ``FIELDS`` that are present and not empty.
    """
    fields: dict[str, str] = {}
    for line in text.splitlines():
        name, separator, value = line.partition(":")
        name = name.strip(MARKUP)
        if separator and name in FIELDS and value.strip(MARKUP):
            fields[name] = value.strip(MARKUP)
    return fields


def report_brief(path: Path) -> list[Finding]:
    """Print the main lines of a brief, or return a warning when there is no brief.

    Args:
        path: Where the brief is expected (see ``brief_path``).

    Returns:
        An empty list when the brief exists (its lines are printed), or one ``no-brief``
        warning.
    """
    if not path.is_file():
        message = (
            f"no brief at {path}; write it first, as the working method in skills/WORKING.md "
            "says (question, reader, medium, sources read, left out, unknowns)"
        )
        return [Finding(Severity.WARNING, Code.NO_BRIEF, message, ())]
    fields = read_fields(path.read_text(encoding="utf-8"))
    for name in PRINTED_FIELDS:
        print(f"brief {name}: {fields.get(name, '(missing)')}")
    return []
