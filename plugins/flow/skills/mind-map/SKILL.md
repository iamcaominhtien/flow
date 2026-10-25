---
description: Draw a mind map (a central idea with branches and sub-branches) as an animated HTML page and a draw.io file. Use when the user asks for a mind map or a topic breakdown.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Mind map

You write a short **spec**: a nested tree. A script places the boxes (left to right; each main branch gets its own tone, passed to everything below it), draws the lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. Write the tree: the central idea, its main branches, and what hangs off each branch.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "mindmap",
  "title": "Mind map: launch plan",
  "desc": "The main branches of a product launch and what each one needs.",
  "root": {
    "label": "Launch",
    "children": [
      {
        "label": "Product",
        "children": [
          {
            "label": "Final tests"
          },
          {
            "label": "Docs"
          }
        ]
      },
      {
        "label": "Marketing",
        "children": [
          {
            "label": "Landing page"
          },
          {
            "label": "Email"
          },
          {
            "label": "Press"
          }
        ]
      },
      {
        "label": "Support",
        "children": [
          {
            "label": "Help centre"
          },
          {
            "label": "On-call rota"
          }
        ]
      }
    ]
  }
}
```

- `root`: one item. Every item has `label`, and optionally `detail` (a small second line, such as a name), `icon`, `tone` (`blue violet amber green teal gray`) and `children` (a list of items).
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).
- Items are numbered in the order written, so the ids in the scene file are `n0`, `n1`, ...: use them in an overrides file.

## Limits to tell the user

- Each level starts after the tallest or widest item of the level above, and siblings are never packed closer, so a wide tree gets wide. There is no radial mind map layout.
- Only one root. Cross links between branches are not supported.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
