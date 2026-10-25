---
description: Draw a Kanban board or a side-by-side comparison (columns of cards) as an animated HTML page and a draw.io file. Use when the user asks for a Kanban board, a status board or a comparison of options.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Kanban board and comparison

You write a short **spec**: columns, each with cards. A script sizes the cards, stacks them and frames each column. Never write coordinates or HTML yourself.

## Steps

1. List the columns (statuses, or the options to compare) and the cards in each.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "kanban",
  "title": "Kanban: this sprint",
  "desc": "Cards by status; the finished column is green.",
  "columns": [
    {
      "label": "To do",
      "tone": "gray",
      "cards": [
        {
          "label": "Write the release notes"
        },
        {
          "label": "Add dark mode",
          "detail": "Design is ready"
        }
      ]
    },
    {
      "label": "Doing",
      "tone": "blue",
      "cards": [
        {
          "label": "Fix the login timeout",
          "icon": "bug"
        }
      ]
    },
    {
      "label": "Done",
      "tone": "green",
      "cards": [
        {
          "label": "Upgrade the database",
          "icon": "database"
        },
        {
          "label": "Set up monitoring"
        }
      ]
    }
  ]
}
```

- **Column**: `label`, optional `tone`, `cards`.
- **Card**: `label`, optional `detail` (a small second line), `icon`, `tone`.
- For a comparison, make each option a column and each point a card.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Limits to tell the user

- Cards cannot be dragged or edited as a board in draw.io; they are plain boxes.
- There are no counts, limits, assignees or dates.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
