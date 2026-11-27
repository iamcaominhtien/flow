"""Tests for reading back the brief written beside a diagram."""

import json
import subprocess
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "flow"
SKILLS_DIR = PLUGIN_DIR / "skills"
FLOW_CLI = PLUGIN_DIR / "scripts" / "flow.py"
TESTS_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(PLUGIN_DIR))
sys.path.insert(0, str(TESTS_DIR))

from flowlib.author import Canvas, NodeOptions  # noqa: E402
from flowlib.brief import FIELDS, brief_path, check_brief, read_fields  # noqa: E402
from flowlib.check import Code  # noqa: E402
from flowlib.model import Shape  # noqa: E402
from test_er_tables import DOMAIN_SPEC  # noqa: E402

NOT_DRAWING: tuple[str, ...] = (
    "doctor",
    "edit-drawio",
    "import-drawio",
)  # skills that start from a file
WORKING_BLOCK: str = (
    "Before step 1, follow the working method in `${CLAUDE_PLUGIN_ROOT}/skills/WORKING.md`: "
    "know the question, the reader and the medium; read the source as deep as the question "
    "needs; choose what is in and what is left out; and write the brief, one line each for "
    "`Question:`, `Reader:`, `Medium:`, `Sources read:`, `Left out:` and `Unknowns:`, as "
    "`<name>.brief.md` in the folder of the spec, with the spec's name (on the author path, "
    "in the folder and with the name you pass to `canvas.write`). `flow.py build` and "
    "`canvas.write` print it back with the check report. Before you deliver, look at the "
    "picture at the medium's size (step 8), and tell the user the sources you read and what "
    "you left out."
)  # the same text opens the steps of every drawing skill


def test_fields_are_read_through_markdown_marks() -> None:
    """Marks around a name are ignored, case does not matter, and values are kept whole."""
    text = (
        "# Brief\n- **Question:** why?\n## medium: phone\nSources read: __init__.py, _private_\n"
        "Colour: blue\nLeft out:\n"
    )
    assert read_fields(text) == {
        "Question": "why?",
        "Medium": "phone",
        "Sources read": "__init__.py, _private_",
    }


def test_a_missing_brief_is_a_warning(tmp_path: Path) -> None:
    """No brief file gives one no-brief warning that points to the working method."""
    said = check_brief(brief_path(tmp_path, "order"))
    assert said.lines == ()
    assert [finding.code for finding in said.findings] == [Code.NO_BRIEF]
    assert "WORKING.md" in said.findings[0].message


def test_a_brief_is_read_back_and_its_missing_lines_are_named(tmp_path: Path) -> None:
    """Every field is printed; the ones without a line are named in one warning."""
    brief_path(tmp_path, "order").write_text("Question: how is an order paid?\nMedium: phone\n")
    said = check_brief(brief_path(tmp_path, "order"))
    assert len(said.lines) == len(FIELDS)
    assert "brief Question: how is an order paid?" in said.lines
    assert "brief Sources read: (missing)" in said.lines
    assert "Reader, Sources read, Left out, Unknowns" in said.findings[0].message


def test_an_empty_brief_is_not_enough(tmp_path: Path) -> None:
    """An empty file still gets a warning, so it cannot silence the check."""
    brief_path(tmp_path, "order").write_text("")
    assert [finding.code for finding in check_brief(brief_path(tmp_path, "order")).findings] == [
        Code.NO_BRIEF
    ]


def test_the_author_kit_reads_the_brief_in_its_output_folder(tmp_path: Path) -> None:
    """Canvas.write warns when the brief is missing and not when it is complete."""
    canvas = Canvas("Order", "One step")
    canvas.node("pay", Shape.PROCESS, "Pay order", NodeOptions((200, 200)))
    assert Code.NO_BRIEF in [finding.code for finding in canvas.write(tmp_path, "order")]
    brief_path(tmp_path, "order").write_text("".join(f"{name}: x\n" for name in FIELDS))
    assert Code.NO_BRIEF not in [finding.code for finding in canvas.write(tmp_path, "order")]


def test_every_drawing_skill_starts_with_the_working_method() -> None:
    """Every skill that draws from an input points to the shared working method first."""
    for skill in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        if skill.parent.name in NOT_DRAWING:
            continue
        steps = skill.read_text(encoding="utf-8").split("## Steps", 1)[1]
        assert steps.lstrip().startswith(WORKING_BLOCK), skill.parent.name


def test_split_warns_once_for_a_missing_brief_and_prints_one_report_per_page(
    tmp_path: Path,
) -> None:
    """The brief of the whole spec is reported with the first page, and no extra report."""
    spec_path = tmp_path / "shop.spec.json"
    spec_path.write_text(json.dumps(DOMAIN_SPEC))
    run = subprocess.run(
        [sys.executable, str(FLOW_CLI), "split", str(spec_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.stdout.count("no-brief") == 1
    reports = [line for line in run.stdout.splitlines() if line.startswith("check:")]
    assert len(reports) == run.stdout.count("wrote ") // 2
