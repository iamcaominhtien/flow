# Flow

AI plugins that draw diagrams as animated HTML/SVG or as draw.io files. The design is in `docs/design/`; the plan for the plugin is in `docs/plugin/design.md`; the work is tracked in GitHub issue #5.

- The plugin lives in `plugins/flow/`. It uses Python 3.10+ and the standard library only: do not add a dependency.
- Code style rules for Python are in `.claude/rules/python.md`. Follow them in every new or edited file.
- Check your work with `ruff format .`, `ruff check .` and `python3 -m pytest`.
- `docs/design/` is a frozen snapshot of the design work. Do not run ruff on it or edit its generators.
- Write in English in code, docs and commits. Keep the repo's tone plain and factual; say what is not verified.
