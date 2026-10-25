#!/usr/bin/env python3
"""Print the state of the Flow plugin install. Standard library only."""

import json
import os
import sys
from pathlib import Path

root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
manifest = json.loads((root / ".claude-plugin" / "plugin.json").read_text())

print(f"OK   flow {manifest.get('version', '?')} at {root}")
print(f"OK   python {sys.version.split()[0]}")

skills = sorted(p.parent.name for p in (root / "skills").glob("*/SKILL.md"))
print(f"OK   skills: {', '.join(skills)}")

for dep in manifest.get("dependencies", []):
    name = dep["name"] if isinstance(dep, dict) else dep
    print(f"INFO depends on {name}; check with `claude plugin list`")
