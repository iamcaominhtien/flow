---
description: Draw a Gantt chart (tasks on a time axis, grouped, with dependencies) as an animated HTML page and a draw.io file. Use when the user asks for a Gantt chart, a project schedule or a timeline of tasks.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Gantt chart

You write a short **spec**: the periods and the tasks. A script scales the bars, groups them, draws the dependency lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. Choose the periods (days, weeks, months) and list the tasks with the period each starts in and how many periods it lasts.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "gantt",
  "title": "Gantt: build a website",
  "desc": "Design, build and launch a small website over eight weeks.",
  "periods": [
    "W1",
    "W2",
    "W3",
    "W4",
    "W5",
    "W6",
    "W7",
    "W8"
  ],
  "tasks": [
    {
      "id": "brief",
      "label": "Write the brief",
      "start": 0,
      "length": 1,
      "group": "Plan",
      "tone": "violet"
    },
    {
      "id": "design",
      "label": "Design the pages",
      "start": 1,
      "length": 2,
      "group": "Plan",
      "tone": "violet",
      "after": "brief"
    },
    {
      "id": "build",
      "label": "Build the site",
      "start": 3,
      "length": 3,
      "group": "Build",
      "tone": "blue",
      "after": "design"
    },
    {
      "id": "content",
      "label": "Write the content",
      "start": 2,
      "length": 3,
      "group": "Build",
      "tone": "blue"
    },
    {
      "id": "test",
      "label": "Test and fix",
      "start": 6,
      "length": 1,
      "group": "Launch",
      "tone": "green",
      "after": "build"
    },
    {
      "id": "launch",
      "label": "Launch",
      "start": 7,
      "length": 1,
      "group": "Launch",
      "tone": "green",
      "after": "test"
    }
  ]
}
```

- `periods`: the names of the columns, such as `["W1", "W2"]`. Dates are not read: name the periods yourself.
- **Task**: `id`, `label`, `start` (period number from 0), `length` (number of periods, at least 1), optional `group` (tasks with the same group share a frame), `tone`, `after` (the id of a task that must end first; a line is drawn from its end to this task's start).
- A task must fit inside the periods, and a task with `after` must start at or after the end of that task: the build refuses anything else with the reason.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Limits to tell the user

- Time is in whole periods: no dates, no weekends, no half periods.
- The period width grows so that every task label fits, so a long label makes the chart wide.
- There is no progress marker or milestone shape; a milestone is a task of length 1.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
