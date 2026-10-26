---
description: Draw a roadmap (what each team ships in each quarter or month, in lanes) as an animated HTML page and a draw.io file. Use when the user asks for a roadmap or a plan by theme or team.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Roadmap

You write a short **spec**: the periods and the lanes with their items. A script scales the items, stacks the ones that overlap in time and writes the files. Never write coordinates or HTML yourself.

## Steps

1. Choose the periods (quarters, months) and the lanes (teams or themes), then list each lane's items with the period they start in and how many periods they last.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "roadmap",
  "title": "Roadmap: 2026",
  "desc": "What each team plans to ship in each quarter.",
  "periods": [
    "Q1",
    "Q2",
    "Q3",
    "Q4"
  ],
  "lanes": [
    {
      "label": "Product",
      "tone": "blue",
      "items": [
        {
          "label": "Onboarding",
          "start": 0,
          "length": 1
        },
        {
          "label": "Search",
          "start": 1,
          "length": 2
        },
        {
          "label": "Mobile app",
          "start": 2,
          "length": 2
        }
      ]
    },
    {
      "label": "Platform",
      "tone": "violet",
      "items": [
        {
          "label": "Move to the new database",
          "start": 0,
          "length": 2
        },
        {
          "label": "Faster builds",
          "start": 2,
          "length": 1
        }
      ]
    }
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- `periods`: the names of the columns, such as `["Q1", "Q2", "Q3", "Q4"]`.
- **Lane**: `label`, optional `tone`, `items`.
- **Item**: `label`, `start` (period number from 0), `length` (number of periods), optional `tone`. Items of a lane that overlap in time are stacked in extra rows.
- An item must fit inside the periods; the build refuses one that does not.

## Limits to tell the user

- Time is in whole periods; there are no dates, dependencies or progress marks.
- A long item label makes the periods wide.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
