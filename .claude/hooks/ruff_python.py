#!/usr/bin/env python3
"""PostToolUse hook: format and lint a Python file right after Claude edits it.

Reads the hook JSON on stdin. Formats and auto-fixes the file with ruff, then
reports any lint errors left over to Claude (exit 2) so it fixes them.
"""

import json
import subprocess
import sys
from pathlib import Path


def ruff(*args):
    return subprocess.run(["ruff", *args], capture_output=True, text=True)


def main():
    path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
    if not path.endswith(".py") or not Path(path).is_file():
        return 0
    try:
        ruff("format", path)
        ruff("check", "--fix", "--quiet", path)
        left = ruff("check", "--output-format=concise", path)
    except FileNotFoundError:
        print("ruff is not installed; run `pip install ruff`.", file=sys.stderr)
        return 0
    if left.returncode != 0:
        print(f"ruff found problems in {path}:\n{left.stdout}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
