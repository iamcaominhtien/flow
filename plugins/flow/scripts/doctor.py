#!/usr/bin/env python3
"""Print the state of the Flow plugin install. Standard library only."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DRAWIO_HINT = (
    "INFO exporting .drawio files to PNG, SVG or PDF needs the optional `drawio@drawio` plugin;\n"
    "     check with `claude plugin list`"
)
PROBE_TIMEOUT_S = 60  # starting Chromium once can take a while
NO_BROWSER = 3  # view.js's exit code when Playwright or Chromium is missing
PNG_MISSING = (
    "INFO PNG pictures (scripts/view.js) are not available: {reason};\n"
    "     install with `npm install -g playwright && npx playwright install chromium`"
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


def png_status() -> str:
    """Return one line on whether ``view.js`` can write PNG pictures here.

    It runs ``view.js --check``, which loads Playwright and starts Chromium the way a real
    render does, so the check and the use cannot disagree.

    Returns:
        An ``OK`` line, or an ``INFO`` line with what is missing.
    """
    if shutil.which("node") is None:
        return PNG_MISSING.format(reason="Node is not installed")
    view = PLUGIN_ROOT / "scripts" / "view.js"
    try:
        probe = subprocess.run(
            ["node", str(view), "--check"],
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return PNG_MISSING.format(reason="the browser did not start in time")
    if probe.returncode == NO_BROWSER:
        return PNG_MISSING.format(reason=probe.stderr.strip().split(". ")[0])
    if probe.returncode != 0:
        return PNG_MISSING.format(reason=f"view.js failed: {probe.stderr.strip()[:200]}")
    return "OK   PNG pictures: a headless browser starts (scripts/view.js)"


def main() -> None:
    """Print one line per check: version, Python, skills, PNG pictures, and a hint about draw.io."""
    manifest = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())
    print(f"OK   flow {manifest.get('version', '?')} at {PLUGIN_ROOT}")
    print(f"OK   python {sys.version.split()[0]}")
    print(f"OK   skills: {', '.join(installed_skills(PLUGIN_ROOT))}")
    print(png_status())
    print(DRAWIO_HINT)


if __name__ == "__main__":
    main()
