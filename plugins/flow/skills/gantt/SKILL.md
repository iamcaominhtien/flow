---
description: Draw a Gantt chart (tasks on a time axis, grouped in phases, with owners, progress and dependencies) as an animated HTML page and a draw.io file. Use when the user asks for a Gantt chart, a project schedule or a timeline of tasks.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Gantt chart

You write a short **spec**: the tasks with their dates, owners and status. A script puts them on a week grid, draws the month header, the phases, the dependency lines and the critical path, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the tasks with their start and end dates (or week numbers), who owns each one, how far each is, and which task must finish before which.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "gantt",
  "title": "Gantt: launching the delivery app",
  "desc": "Three phases over fourteen weeks.",
  "today": "2026-04-20",
  "tasks": [
    {
      "id": "research",
      "label": "Research",
      "owner": "Noah Kim",
      "group": "Discover",
      "start": "2026-03-02",
      "end": "2026-03-15",
      "status": "done"
    },
    {
      "id": "spec",
      "label": "Write the spec",
      "owner": "Ava Lopez",
      "group": "Discover",
      "start": "2026-03-16",
      "end": "2026-03-22",
      "status": "done",
      "after": "research"
    },
    {
      "id": "design",
      "label": "Design",
      "owner": "Ava Lopez",
      "group": "Build",
      "start": "2026-03-23",
      "end": "2026-04-05",
      "status": "done",
      "after": "spec"
    },
    {
      "id": "mobile",
      "label": "Mobile app",
      "owner": "Lia Chen",
      "group": "Build",
      "start": "2026-04-06",
      "end": "2026-05-10",
      "status": "in_progress",
      "progress": 0.3,
      "after": "design"
    },
    {
      "id": "beta",
      "label": "Beta test",
      "owner": "Max Rossi",
      "group": "Launch",
      "start": "2026-05-11",
      "end": "2026-05-24",
      "status": "planned",
      "after": [
        "mobile"
      ]
    }
  ],
  "milestones": [
    {
      "id": "approved",
      "label": "Spec approved",
      "date": "2026-03-23",
      "group": "Discover"
    }
  ],
  "people": {
    "Noah Kim": {
      "tone": "blue"
    },
    "Ava Lopez": {
      "tone": "blue"
    },
    "Lia Chen": {
      "tone": "green"
    },
    "Kai Novak": {
      "tone": "green"
    },
    "Max Rossi": {
      "tone": "teal"
    }
  }
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- **Time** is read in one of three ways, never mixed. *Dates*: `start` and `end` are ISO dates and `end` is the last day; the first column is the Monday on or before the first date (or `axis_start`), and a month header is drawn above the weeks. *Weeks*: `start` and `end` are week numbers from 1, `end` included (or `length` in weeks instead of `end`); the columns are `W1`, `W2`. *Periods* (older form): `periods` names the columns, `start` counts from 0 and `length` is a number of periods.
- **Task**: `id`, `label`, `owner` (a name; the circle shows the initials), `group` (the phase: a grey band with its name, in the order first used), `status` (`done` green with a check, `in_progress` blue filled to `progress` from 0 to 1, `planned` grey, `blocked` rose with a dashed outline and a short `reason`, which is required), `after` (an id or a list of ids that must finish first: a thin finish-to-start arrow), `critical: true` to mark the critical path yourself. Without `status` it is worked out from `progress`: none is planned, all is done.
- **Milestone** (`milestones`): `id`, `label`, and where it falls: `date`, or `at` (a position counted in columns from the left edge: 3 is between W3 and W4), or `after` (the end of a task; an arrow runs into the diamond). `group` puts it in a phase; by default it follows the task it comes after.
- `today`: a date, or a position in columns. A red dashed line with a red pill.
- `people`: optional `{"Ava Lopez": {"initials": "AL", "tone": "blue"}}` to pin the initials or the tint. The tint is chosen from the name, so the same name has the same tint in a Gantt chart, an org chart and a mind map; give the team to the org chart to match it.
- **Critical path**: the one blue, thick, animated chain. When no task is marked `critical`, it is the chain that ends last: the last item to finish, then the predecessor that finishes last at each step (the first written when two finish together).
- A task must fit the columns, and one with `after` must start no earlier than that one ends: the build refuses anything else with the reason. `tone` is accepted and ignored: the status is the colour.
- Weeks are 88 px wide, the name column 300 px, rows 52 px, bars 26 px.
- Icons are not used in a Gantt chart.

## Limits to tell the user

- About 15 rows fit a page; the build warns above that. Draw one Gantt per phase.
- Weeks start on Monday; there are no weekends, holidays or half days. A date inside a week is drawn at its place in the week.
- A dependency runs only from the end of one item to the start of another (finish to start).
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
