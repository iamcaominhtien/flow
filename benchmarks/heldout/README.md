# Held-out briefs: raw input to a diagram

Six requests on raw input of different kinds, written on 2026-11-27 **before** the working-method change (`docs/plugin/working-method.md`) was built, to test whether a change to the plugin generalises. Do not tune the plugin on these: if a run fails here, find the general gap, fix it, and test the fix on new briefs too.

Unlike `briefs/`, these do not list what to draw. The agent has to work out the purpose, read the source, choose the scope and, in two of them, the type.

| id | input | request (`request.md`) | medium |
| :-- | :-- | :-- | :-- |
| h1-rebase | none, one sentence (Vietnamese) | flowchart of git rebase with conflicts | phone |
| h2-redirect | `request.py` from CPython 3.13.18 | flowchart of how urllib follows a redirect | phone |
| h3-threadpool | `thread.py` from CPython 3.13.18 | a diagram of a task's life in a thread pool; type not given | screen |
| h4-meeting | a meeting transcript written for this set | a process diagram for the support team | slide |
| h5-tickets | a CSV of 650 ticket status changes (generated, seed 7) | how a ticket moves through statuses | phone |
| h6-deploy | a small repo: CI workflow, Makefile, two scripts, Dockerfile | "draw our deployment"; deliberately vague | screen |

## How to run one

1. Copy `<id>/input/` (if any) to an empty folder outside this repo and start a fresh session there with the plugin loaded (`claude -p --plugin-dir plugins/flow`), giving it only the text of `<id>/request.md`.
2. Never show it `ANSWERS.md`, this README, `briefs/`, `examples/`, `docs/`, the tests or the git history.
3. Grade the PNG it returns, outside the plugin's own check:
   - A separate model, given only the PNG, answers the five questions of `ANSWERS.md` for that id. Score one point per answer that matches.
   - Five drawn elements, picked by the grader, are checked against the source: correct, wrong, or invented.
   - The smallest text, measured at the medium's width (phone 390 px, screen 1440 px, slide 1280 px).
   - Whether the source has decisions that the picture leaves out.
4. Record the run in `results/<date>-heldout-<id>.md`.
