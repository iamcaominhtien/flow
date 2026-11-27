"""Tests for reading back the brief written beside a diagram."""

import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"
SKILLS_DIR = PLUGIN_DIR / "skills"

sys.path.insert(0, str(PLUGIN_DIR))

import pytest  # noqa: E402
from flowlib.author import Canvas, NodeOptions  # noqa: E402
from flowlib.brief import brief_path, read_fields, report_brief  # noqa: E402
from flowlib.check import Code  # noqa: E402
from flowlib.model import Shape  # noqa: E402

NOT_DRAWING = ("doctor", "edit-drawio", "import-drawio")  # skills that start from a file
WORKING_BLOCK = (
    "Before step 1, follow the working method in `${CLAUDE_PLUGIN_ROOT}/skills/WORKING.md`: "
    "know the question, the reader and the medium; read the source as deep as the question "
    "needs; choose what is in and what is left out; and write `<name>.brief.md` beside the "
    "spec (on the author path, in the output folder) with the lines `Question:`, `Reader:`, "
    "`Medium:`, `Sources read:`, `Left out:` and `Unknowns:`. The build prints it back. When "
    "you deliver, tell the user the sources you read and what you left out."
)  # the same text opens the steps of every drawing skill


def test_fields_are_read_through_markdown_marks() -> None:
    """Bullets and bold around a field name are ignored; unknown and empty fields are not kept."""
    text = "# Brief\n- **Question:** why?\nMedium: phone\nColour: blue\nLeft out:\n"
    assert read_fields(text) == {"Question": "why?", "Medium": "phone"}


def test_a_missing_brief_is_a_warning(tmp_path: Path) -> None:
    """No brief file gives one no-brief warning that points to the working method."""
    findings = report_brief(brief_path(tmp_path, "order"))
    assert [finding.code for finding in findings] == [Code.NO_BRIEF]
    assert "WORKING.md" in findings[0].message


def test_a_brief_is_printed_and_gives_no_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The main lines are printed, a missing one is said to be missing."""
    brief_path(tmp_path, "order").write_text("Question: how is an order paid?\nMedium: phone\n")
    assert report_brief(brief_path(tmp_path, "order")) == []
    printed = capsys.readouterr().out
    assert "brief Question: how is an order paid?" in printed
    assert "brief Sources read: (missing)" in printed


def test_the_author_kit_reads_the_brief_in_its_output_folder(tmp_path: Path) -> None:
    """Canvas.write warns when the brief is missing and not when it is there."""
    canvas = Canvas("Order", "One step")
    canvas.node("pay", Shape.PROCESS, "Pay order", NodeOptions((200, 200)))
    assert Code.NO_BRIEF in [finding.code for finding in canvas.write(tmp_path, "order")]
    brief_path(tmp_path, "order").write_text("Question: how is an order paid?\n")
    assert Code.NO_BRIEF not in [finding.code for finding in canvas.write(tmp_path, "order")]


def test_every_drawing_skill_starts_with_the_working_method() -> None:
    """Every skill that draws from an input points to the shared working method first."""
    for skill in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        if skill.parent.name in NOT_DRAWING:
            continue
        steps = skill.read_text(encoding="utf-8").split("## Steps", 1)[1]
        assert steps.lstrip().startswith(WORKING_BLOCK), skill.parent.name
