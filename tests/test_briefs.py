"""Tests for the benchmark briefs: their format, and the checker that guards it."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))

import check_briefs  # noqa: E402

EXPECTED_TYPES = 8
LEVELS_PER_TYPE = 3


def test_the_briefs_have_no_format_errors() -> None:
    """Every brief has its fields and sections, matches its file and is in the index."""
    briefs, report = check_briefs.check()
    assert report.errors == []
    assert len(briefs) == EXPECTED_TYPES * LEVELS_PER_TYPE


def test_each_type_has_one_brief_per_level() -> None:
    """A, B and C exist for every type."""
    briefs, _ = check_briefs.check()
    found = {(brief.kind, brief.level) for brief in briefs}
    assert found == {(kind, level) for kind in check_briefs.TYPES for level in check_briefs.LEVELS}


def test_no_citation_number_is_left_glued_to_a_name() -> None:
    """The names in the briefs are clean: no AdjRibIn18 style leftovers."""
    briefs, report = check_briefs.check()
    assert not [w for w in report.warnings if "glued" in w]
    assert all(not name[-2:].isdigit() for brief in briefs for name in brief.names)


def test_checker_flags_a_missing_section(tmp_path: Path) -> None:
    """A brief without a Traps section is an error."""
    folder = tmp_path / "briefs"
    folder.mkdir()
    (folder / "state.md").write_text(
        "## state-A-01 — Test\n\n* **type:** state\n* **level:** A\n* **elements:** 9\n"
        "* **connections:** 9\n* **groups:** none\n\n### Brief\n\ntext\n\n### Must show\n\n* x\n"
    )
    (folder / "index.md").write_text("| id | type | level | subject | elements | connections |\n")
    _, report = check_briefs.check(folder)
    assert any("Traps" in error for error in report.errors)
    assert any("not in index.md" in error for error in report.errors)
