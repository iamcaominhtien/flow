"""Tests for the benchmark briefs: their format, and the checker that guards it."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))

import check_briefs  # noqa: E402

EXPECTED_TYPES = 8
LEVELS_PER_TYPE = 3
EXTRA_BRIEFS = 1  # a second level C brief for BPMN


def test_the_briefs_have_no_format_errors() -> None:
    """Every brief has its fields and sections, matches its file and is in the index."""
    briefs, report = check_briefs.check()
    assert report.errors == []
    assert len(briefs) == EXPECTED_TYPES * LEVELS_PER_TYPE + EXTRA_BRIEFS


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


def test_level_c_briefs_have_a_structure_that_matches_their_counts() -> None:
    """Every level C brief lists its elements and connections, and the counts are exact."""
    briefs, report = check_briefs.check()
    level_c = [brief for brief in briefs if brief.level == "C"]
    assert all(brief.structure is not None for brief in level_c)
    for brief in level_c:
        structure = brief.structure
        assert structure is not None
        assert len(structure.elements) == brief.claimed("elements")
        assert len(structure.connections) == brief.claimed("connections")
    assert not [e for e in report.errors if "Structure" in e]


def test_checker_catches_a_wrong_count_and_a_timing_error(tmp_path: Path) -> None:
    """A Structure whose count is wrong, or whose task starts before its predecessor ends, fails."""
    folder = tmp_path / "briefs"
    folder.mkdir()
    text = (
        "## gantt-C-01 — T\n\n* **type:** gantt\n* **level:** C\n* **elements:** 3\n"
        "* **connections:** 1\n* **groups:** G\n\n### Brief\n\nTaskOne then TaskTwo.\n\n"
        "### Must show\n\n* x\n\n### Traps\n\n* x\n\n### Structure\n\n**Elements**\n\n"
        "- G: TaskOne@0+3, TaskTwo@2+1\n\n**Connections**\n\n- TaskOne -> TaskTwo\n\n"
        "### Sources\n\n* https://example.com\n\n### Uncertain\n\n* none\n"
    )
    (folder / "gantt.md").write_text(text)
    (folder / "index.md").write_text(
        "| id | type | level | subject | elements | connections |\n"
        "| gantt-C-01 | gantt | C | T | 3 | 1 |\n"
    )
    _, report = check_briefs.check(folder)
    assert any("lists 2 elements" in error for error in report.errors)
    assert any("starts before TaskOne ends" in error for error in report.errors)
