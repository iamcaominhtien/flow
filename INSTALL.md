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

## Google Antigravity: not tested

Antigravity has its own plugins. Its [plugin documentation](https://antigravity.google/docs/plugins/) says a plugin is a folder with a `plugin.json` at its root (only `name` and `description`) and optional `skills/<name>/SKILL.md`, `agents/`, `rules/`, `mcp_config.json` and `hooks.json`. Flow's plugin folder has that shape: `plugins/flow/` now holds a `plugin.json` next to its `skills/` and `scripts/`. Whether Antigravity accepts it has **not been tried**.

To try it (Antigravity CLI):

1. Clone the repository: `git clone https://github.com/iamcaominhtien/flow`.
2. Install from the local folder: `agy plugin install /path/to/flow/plugins/flow`, or in the interactive CLI `/plugin install` and give the same path. In the desktop app or the IDE, copy `plugins/flow` into `.agents/plugins/` of your project, or into `~/.gemini/config/plugins/` for all projects.
3. Installing from the repository address (`agy plugin install https://github.com/iamcaominhtien/flow`) may not find the plugin, because it sits in the `plugins/flow` subfolder and the repository root is a Claude Code marketplace. Not known.

What may not work, because the documentation does not say:

- Flow's skills run their scripts through `${CLAUDE_PLUGIN_ROOT}`, a variable Claude Code sets. The Antigravity page lists no variable for a plugin's own folder. If the agent cannot find the scripts, tell it the real path of `plugins/flow` and ask it to use that wherever a skill says `${CLAUDE_PLUGIN_ROOT}`.
- The `allowed-tools` line in each skill is a Claude Code permission rule; the page does not mention it, so the agent may ask before running a command.
- The page does not say how a skill is started (a slash command or from its description). In Claude Code it is `/flow:<skill>`.
- Plugins can be listed in the official marketplace only through Google's interest form; there is no way found to add this repository as a marketplace.

The scripts (`scripts/flow.py`, `scripts/doctor.py`, the `flowlib` package) are plain Python and do not depend on any tool. You can check them by hand: `python3 /path/to/flow/plugins/flow/scripts/doctor.py`.

If you try it, please say what happened (installed or refused, skills found or not, scripts found or not), and this section will be corrected.

## Developing Flow

`pip install ruff pytest`, then `ruff format .`, `ruff check .` and `python3 -m pytest` from the repository root.
