# Install Flow

Flow is a plugin for Claude Code. It needs Python 3.11 or newer and nothing else (standard library only).

## Claude Code

```
/plugin marketplace add iamcaominhtien/flow
/plugin install flow@flow
```

Then run `/flow:doctor`. It checks that Python is found and that the scripts run, and says what to fix if not.

Use it:

- `/flow:flowchart how a customer pays and gets an order delivered` (or `/flow:bpmn`, `/flow:sequence`, `/flow:er`, and the other type skills) for a small diagram. Claude writes a short spec, a script lays it out and writes `<name>.html` (animated) and `<name>.drawio` next to the spec.
- `/flow:author` for a large or dense diagram. Claude writes a layout script of its own, builds, looks at the picture and improves it. For it to look, a headless browser has to be available (Chromium with Playwright, for example). Without one, Claude has only the check report and should say so.
- Open the `.html` in any browser. Open the `.drawio` in draw.io (diagrams.net) to keep editing. To export PNG, SVG or PDF, also install the draw.io plugin: `/plugin marketplace add jgraph/drawio-mcp` then `/plugin install drawio@drawio`.

If `python3` is not the right command on your machine (Windows often uses `python` or `py`), `doctor` will tell you; this has not been tested on Windows.

## Other tools (Google Antigravity and similar): not tested

Antigravity reads skills in the same format Flow uses (a folder with a `SKILL.md`, frontmatter with a `description`). So the skills may work there, but this has **not been tried**, and a few things are Claude Code specific:

- Flow's skills call the scripts through `${CLAUDE_PLUGIN_ROOT}`, a variable that only Claude Code sets. In another tool the agent has to be told the real path of the `plugins/flow` folder, and the variable replaced by it.
- The `allowed-tools` line in the frontmatter is a Claude Code permission rule; other tools ignore it or may not run the commands without asking.
- Skill names are `/flow:<skill>` in Claude Code; elsewhere the agent picks a skill from its description.

A manual try, if you want to test it:

1. Clone this repository: `git clone https://github.com/iamcaominhtien/flow`.
2. Copy the folders in `plugins/flow/skills/` into the tool's skills folder (for Antigravity, the guides name `.agents/skills/` in a workspace or `~/.gemini/config/skills/` globally; check Google's documentation, because the guides disagree).
3. Tell the agent where `plugins/flow` is, for example: "The Flow scripts are in /path/to/flow/plugins/flow; wherever a skill says `${CLAUDE_PLUGIN_ROOT}`, use that path."
4. Run `python3 /path/to/flow/plugins/flow/scripts/doctor.py` yourself to check Python and the scripts.
5. Ask for a diagram.

The scripts themselves (`flow.py`, `doctor.py`, the `flowlib` package) are plain Python and do not depend on Claude Code. Only the skill text and the way skills are found do.

## Developing Flow

`pip install ruff pytest`, then `ruff format .`, `ruff check .` and `python3 -m pytest` from the repository root.
