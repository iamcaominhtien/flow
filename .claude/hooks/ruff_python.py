#!/usr/bin/env python3
"""PostToolUse hook: format and lint a Python file right after Claude edits it.

Reads the hook JSON on stdin. Formats and auto-fixes the file with ruff, then reports any
lint error left over to Claude (exit code 2) so that it fixes the error. Only files of this
repository are touched: a scratch script elsewhere (a benchmark run in a temporary folder) is
left as its author wrote it, and the excludes of ``pyproject.toml`` (``docs/``) are kept.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_REPORT_TO_CLAUDE = 2


def run_ruff(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run ruff with the given arguments and capture its output.

    Args:
        *arguments: The ruff command line after the program name.

    Returns:
        The finished process, whether or not ruff found problems.
    """
    return subprocess.run(["ruff", *arguments], capture_output=True, text=True, check=False)


def main() -> int:
    """Fix the edited file if it is Python, and report what ruff cannot fix.

    Returns:
        0 when there is nothing to report, 2 when lint errors remain.
    """
    path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
    if not path.endswith(".py") or not Path(path).is_file() or not _is_in_project(path):
        return EXIT_OK
    try:
        run_ruff("format", "--force-exclude", path)
        run_ruff("check", "--force-exclude", "--fix", "--quiet", path)
        remaining = run_ruff("check", "--force-exclude", "--output-format=concise", path)
    except FileNotFoundError:
        print("ruff is not installed; run `pip install ruff`.", file=sys.stderr)
        return EXIT_OK
    if remaining.returncode != 0:
        print(f"ruff found problems in {path}:\n{remaining.stdout}", file=sys.stderr)
        return EXIT_REPORT_TO_CLAUDE
    return EXIT_OK


def _is_in_project(path: str) -> bool:
    """Tell whether a file lies inside the project the hook runs for.

    Args:
        path: The file Claude edited.

    Returns:
        True when the file is under ``CLAUDE_PROJECT_DIR`` (or the current folder when the
        variable is not set).
    """
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    return Path(path).resolve().is_relative_to(project)


if __name__ == "__main__":
    sys.exit(main())
