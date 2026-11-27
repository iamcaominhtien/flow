# Held-out briefs: raw input to a diagram

Seven requests on raw input of different kinds, written on 2026-11-27 **before** the working-method change (`docs/plugin/working-method.md`) was built (h7 was added after the design review, still before the build), to test whether a change to the plugin generalises. Do not tune the plugin on these: if a run fails here, find the general gap, fix it, and test the fix on new briefs too.

Unlike `briefs/`, these do not list what to draw. The agent has to work out the purpose, read the source, choose the scope and, in two of them, the type.

| id | input | request (`request.md`) | medium |
| :-- | :-- | :-- | :-- |
| h1-rebase | none, one sentence (Vietnamese) | flowchart of git rebase with conflicts | phone |
| h2-redirect | `request.py` from CPython 3.13.18 | flowchart of how urllib follows a redirect | phone |
| h3-threadpool | `thread.py` from CPython 3.13.18 | a diagram of a task's life in a thread pool; type not given | screen |
| h4-meeting | a meeting transcript written for this set | a process diagram for the support team | slide |
| h5-tickets | a CSV of 650 ticket status changes (generated, seed 7) | how a ticket moves through statuses | phone |
| h6-deploy | a small repo: CI workflow, Makefile, two scripts, Dockerfile | "draw our deployment"; deliberately vague | screen |
| h7-httpstates | `client.py` from CPython 3.13.18, whose docstring holds its own ASCII state diagram | the states of an HTTPConnection | phone |

## How to run one

1. Copy `<id>/input/` (if any) to an empty folder outside this repo and start a fresh session there with the plugin loaded (`claude -p --plugin-dir plugins/flow`), giving it only the text of `<id>/request.md`.
2. Never show it `ANSWERS.md`, this README, `briefs/`, `examples/`, `docs/`, the tests or the git history.
3. Grade the PNG it returns, outside the plugin's own check:
   - A separate model answers the five questions of `ANSWERS.md` for that id twice: once with no picture (the control: what it knows already) and once with the PNG resized to the medium's width (phone 390 css px at 3x = 1170 px, screen 1440 px, slide 1280 px). Score one point per answer that matches; the result is the gain over the control. The questions follow from the one-line request, so a different but valid scope still answers them.
   - Five drawn elements, picked by the grader, are checked against the source: correct, wrong, or invented.
   - The smallest text, measured at the medium's width (phone 390 px, screen 1440 px, slide 1280 px).
   - Whether the source has decisions that the picture leaves out.
4. Record the run in `results/<date>-heldout-<id>.md`.

## Decision rule (fixed before any run)

Two runs per brief and plugin version, Sonnet, the old version being 0.17.0 (`main`, aeef609). The new version is better if, over the two runs, its mean gain over the control is higher on at least 5 of the 7 briefs, and its count of wrong or invented elements (of the five checked per run) is no higher in total. Otherwise it is not better, whatever else it does. The size of the smallest text is recorded but does not decide: no diagram in `examples/` is readable on a phone at fit-to-width (smallest node text 1.3 to 6.6 px at 390 px, `benchmarks/measure_text_size.py`), so it would only measure a format the plugin does not have yet.

### Amendment (2026-11-27, after the controls and before any run was graded)

The no-picture control scored 5/5 on h1-rebase, 5/5 on h2-redirect and 4/5 on h7-httpstates (the model already knows git and CPython), 0/5 on the other four. On those three the gain over the control cannot show a difference, so the gain criterion uses only the briefs where the control scored 3 or less (h3, h4, h5, h6): the new version must have the higher mean gain on at least 3 of these 4. The fidelity criterion (wrong or invented elements no higher in total) still covers all seven. h7's request is also no longer fully blind: the working method written after it names a docstring diagram as a summary to check against the source; that example was removed again before any run of the new version. A tie on a brief counts against the new version.
