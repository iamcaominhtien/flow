# Flow

AI plugins that draw diagrams as animated HTML/SVG or as draw.io files. The design is in `docs/design/`; the plan for the plugin is in `docs/plugin/design.md`; the work is tracked in GitHub issue #5.

- The plugin lives in `plugins/flow/`. It uses Python 3.11+ and the standard library only: do not add a dependency.
- Code style rules for Python are in `.claude/rules/python.md`. Follow them in every new or edited file.
- Check your work with `ruff format .`, `ruff check .` and `python3 -m pytest`.
- `docs/design/` is a frozen snapshot of the design work. Do not run ruff on it or edit its generators.
- Write in English in code, docs and commits. Keep the repo's tone plain and factual; say what is not verified.

## How to change the plugin

- The plugin is a tool that should make an AI work well on any input (a sentence, a document, a codebase, a transcript, a table) and any diagram type. Improve how the AI works in general; do not add prompt text, checks or thresholds that only fix the one case that just went wrong.
- When a run goes wrong, find the general gap in the way of working that caused it, and fix that gap in a place every skill shares. Do not change rules on the evidence of a single run: test a change on several held-out briefs of different kinds before keeping it.
- Always work with a second agent that critiques and reviews: spawn one (Opus, high effort) to review your analysis, your plan or your diff independently, give it the files and the evidence rather than your conclusion, and report where it agrees, where it disagrees and what you changed because of it.
