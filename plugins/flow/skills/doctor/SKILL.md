---
description: Check that the Flow plugin is installed correctly. Use when the user asks whether Flow works, or after installing or updating it.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py)
---

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py` and report its output to the user as it is. If a line starts with `FAIL`, say what it means and how to fix it; do not guess beyond what the output says.
