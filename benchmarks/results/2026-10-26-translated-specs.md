# Translated-spec run of the level C briefs (2026-10-26)

**What this is.** The eight level C briefs were turned into plugin specs by a script that reads each brief's `Structure` section, with no agent and no human choices: every element becomes a node, the element name is its label, and every connection becomes a line. The specs were built with `flow.py build` and the check report was counted. This measures the layout engine on a big input. It does **not** measure how well an agent turns a brief into a spec; no agent was run.

**How fair it is.** The labels are the long CamelCase names of the briefs (for example `DedicatedDirectConnectLinkProvisioning`), which cannot wrap. An agent would write short readable labels, so the text-fit warnings and the widths below are worse than a real run would give.

| Brief | Nodes | Lines | Canvas (px) | Errors | Warnings |
| --- | --- | --- | --- | --- | --- |
| flowchart-C-01 | 43 | 51 | 2728 x 4134 | 4 label covers, 1 outside canvas | 4 text may not fit, 3 lines cross |
| sequence-C-01 | 14 | 57 | 3785 x 2600 | none | none |
| er-C-01 | 41 | 50 | 3859 x 1372 | 2 line through node | 62 lines cross |
| architecture-C-01 | 41 | 52 | 2606 x 2158 | 15 label covers, 2 line through node, 1 outside canvas | 23 text may not fit, 38 lines cross |
| bpmn-C-01 | 41 | 48 | 6112 x 1446 | 11 label covers | 29 text may not fit, 2 lines cross |
| state-C-01 | 41 | 51 | 1192 x 4316 | 5 label covers, 1 outside canvas | 30 text may not fit, 16 lines cross |
| orgchart-C-01 | 44 | 43 | 5943 x 732 | none | 28 text may not fit |
| gantt-C-01 | 94 | 43 | 13883 x 2756 | 4 line through node | 1 line crosses |

The Gantt row has 94 nodes because the period header cells are nodes too, and 43 lines instead of 60 (see below).

## What it shows

- **Gantt: a task can follow only one other task.** The `after` field takes one task id. The brief has 60 dependencies; 14 tasks wait for two to four predecessors. The script kept the first predecessor of each, so 17 dependency lines are missing from the picture. This is a plugin limit, not a brief problem.
- **Gantt: long labels make the chart very wide.** The period width grows until the longest label fits inside its bar, so a 2-week task with a 40-character name forces every period to be wide. The chart is 13883 px wide for 50 weeks.
- **Errors at this size are mostly labels covering things** (flowchart, architecture, bpmn, state) and lines that pass through a node (architecture, er, gantt). The check names them. Level B briefs have not been run, so it is not known where the engine starts to fail between the examples (5 to 20 elements) and these (41 to 57).
- **ER with 41 tables and 50 relations has 62 crossing lines.** That may be unavoidable for this schema; it was not compared with a hand layout.
- **Sequence and org chart are clean.** The sequence layout has no ordering problem, so it is not stressed by this input; the org chart only has long labels.

## Not done

- No agent was run on any brief. The `Brief` text has not been tested as a user request.
- The pictures were looked at only for the Gantt chart. The other results are counts from the check report, which does not catch everything (see the BPMN test earlier in the project).
