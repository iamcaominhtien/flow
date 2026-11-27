"""The entry skill routes to every type skill, and only to skills that exist."""

import re
from pathlib import Path

SKILLS: Path = Path(__file__).resolve().parent.parent / "plugins" / "flow" / "skills"
NOT_ROUTED: frozenset[str] = frozenset({"doctor", "draw"})  # skills the table does not send to
TABLE_SKILL: re.Pattern[str] = re.compile(r"`([a-z0-9-]+)`")


def routed_skills() -> set[str]:
    """Return the skill names in the last column of the draw skill's table.

    Returns:
        The names, without the ``flow:`` prefix.
    """
    text = (SKILLS / "draw" / "SKILL.md").read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("| ") and "`" in line]
    return {name for row in rows for name in TABLE_SKILL.findall(row.rsplit("|", 2)[1])}


def test_every_routed_skill_exists() -> None:
    """A name in the table is a skill folder."""
    existing = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert routed_skills() <= existing


def test_every_type_skill_is_routed() -> None:
    """A new skill cannot be missed by the way in."""
    existing = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert existing - NOT_ROUTED <= routed_skills()
