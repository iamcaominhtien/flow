---
description: Draw a mind map (a central idea with branches and sub-branches, radial) as an HTML page and a draw.io file. Use when the user asks for a mind map or a topic breakdown.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Mind map

You write a short **spec**: a nested tree. A script lays it out around the topic (branches on both sides, three to a side), draws the curved coloured lines, checks the result and writes the files. Never write coordinates or HTML yourself. Nothing in a mind map animates, and no order is implied.

## Steps

1. Find the topic, the areas of work (the branches) and a few short ideas on each. For a large subject add groups, ideas and details, and say what is first (P1), done, owned, or linked.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "mindmap",
  "style": "illustrated",
  "title": "Mind map: launching the delivery app",
  "desc": "One topic, three areas of work and a few ideas on each.",
  "root": {
    "label": "Launch the delivery app",
    "goal": "first orders in May",
    "icon": "launch",
    "children": [
      {
        "label": "Product",
        "icon": "idea",
        "children": [
          {
            "label": "Menu and photos",
            "icon": "store"
          },
          {
            "label": "Checkout flow",
            "icon": "cart"
          },
          {
            "label": "Order tracking",
            "icon": "pin"
          }
        ]
      },
      {
        "label": "Engineering",
        "icon": "server",
        "children": [
          {
            "label": "Backend API",
            "icon": "doc"
          },
          {
            "label": "Mobile apps",
            "icon": "phone"
          },
          {
            "label": "Payments",
            "icon": "card"
          }
        ]
      },
      {
        "label": "Marketing",
        "icon": "flag",
        "children": [
          {
            "label": "Launch offer",
            "icon": "star"
          },
          {
            "label": "Restaurant sign-ups",
            "icon": "store"
          },
          {
            "label": "Social media",
            "icon": "bell"
          }
        ]
      }
    ]
  }
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- `style`: `illustrated` (the topic is a card with a large icon and a goal line; a branch is a solid colour pill with a round icon; a leaf is a white card with a colour bar and a small icon) or `plain` (default: a dark topic pill, tinted branch pills, leaves as phrases on a coloured underline).
- **Root**: `label`, `goal` (the line under the topic, written as `Goal: ...`), `icon`. **Item**: `label` (at most four words; the build warns above that), `icon`, `tone`, `children`.
- **Branches and tones**: the first half of the branches go on the right, the rest on the left; `side` (`left` or `right`) moves one. The branches take the tones blue, violet, amber, teal, green, red, gray in turn, and pass them on to everything below; `tone` sets one. Six branches fit best, three on each side, 300 px apart.
- **Levels**: branch, then leaf. When some branch goes deeper, the levels are branch, group, idea, detail (at most four), drawn smaller: groups are tinted pills, ideas white cards, details tinted boxes. Leaves have the icon of their branch unless they have their own.
- **Marks on an idea** (`P1`/`P2` pills, a check, an owner circle, `+N`): `priority` (`P1` do first, `P2` do next), `done: true`, `owner` (a name; the circle shows the initials and the tint of that name), `hidden` (how many ideas below are left out). A key at the top lists the marks the map uses.
- **Links**: `links`: `[{"from": id, "to": id, "label": "needs"}]` joins two ideas (give them an `id`) on the same side, as a dashed violet arc with a pill. Use only a few: the build warns above four.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`; detailed ones for the round icon of a branch and the topic include `idea launch courier money team flag server cloud`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).
- Items are numbered in the order written, so without an `id` the ids in the scene file are `n0`, `n1`, ...: use them in an overrides file.

A deeper item looks like this (a map with four levels, a priority, a done idea, hidden ideas and a link):

```json
{"label": "Engineering", "icon": "server", "side": "right", "children": [{"label": "Platform", "children": [{"label": "Backend API", "done": true, "children": [{"label": "Orders"}, {"label": "Couriers"}]}, {"label": "Event bus", "id": "bus", "priority": "P1"}, {"label": "Data store", "hidden": 4}]}]}
```

## Limits to tell the user

- A link joins two ideas on the same side; it is drawn outside the leaves, so it can cross the lines of other branches.
- A map of three or four levels is drawn at one size; a very large map is wide. Split it by branch when it passes about seven branches.
- Seven branches or more take the gray tone for the seventh; set `tone` to choose.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor; the curves are drawn as smooth lines through points.

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`, `red`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
