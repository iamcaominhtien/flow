#!/usr/bin/env python3
"""Print the state of the Flow plugin install. Standard library only."""

import json
import os
import sys
from pathlib import Path

DRAWIO_HINT = (
    "INFO exporting .drawio files to PNG, SVG or PDF needs the optional `drawio@drawio` plugin;\n"
    "     check with `claude plugin list`"
)
PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)


def installed_skills(plugin_root: Path) -> list[str]:
    """Return the names of the skills the plugin ships, in alphabetical order.

    Args:
        plugin_root: The folder that holds ``skills/``.

    Returns:
        One name per ``skills/<name>/SKILL.md`` file.
    """
    return sorted(path.parent.name for path in (plugin_root / "skills").glob("*/SKILL.md"))


def main() -> None:
    """Print one line per check: version, Python, skills, and a hint about draw.io."""
    manifest = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())
    print(f"OK   flow {manifest.get('version', '?')} at {PLUGIN_ROOT}")
    print(f"OK   python {sys.version.split()[0]}")
    print(f"OK   skills: {', '.join(installed_skills(PLUGIN_ROOT))}")
    print(DRAWIO_HINT)


if __name__ == "__main__":
    main()
