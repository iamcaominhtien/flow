---
description: Draw an org chart (who reports to whom) as an animated HTML page and a draw.io file. Use when the user asks for an org chart or a reporting structure.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Org chart

You write a short **spec**: a nested tree of people. A script places the cards (top to bottom), draws the bus lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. Write the tree: the top person, then the people who report to them, level by level. Note who works with whom without reporting, and any open role.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "org",
  "title": "Org chart: the delivery team, plain",
  "desc": "Lines run from a manager down to the people who report to them. A dashed line is a working relationship without reporting. A dashed card is an open role.",
  "root": {
    "id": "dana",
    "name": "Dana Reed",
    "role": "CEO",
    "tone": "violet",
    "children": [
      {
        "id": "minh",
        "name": "Minh Tran",
        "role": "Head of Product",
        "team": "Product",
        "tone": "blue",
        "children": [
          {
            "id": "noah",
            "name": "Noah Kim",
            "role": "Product analyst"
          },
          {
            "id": "ava",
            "name": "Ava Lopez",
            "role": "Designer"
          }
        ]
      },
      {
        "id": "sam",
        "name": "Sam Ortiz",
        "role": "Head of Engineering",
        "team": "Engineering",
        "tone": "green",
        "children": [
          {
            "id": "lia",
            "name": "Lia Chen",
            "role": "Mobile developer"
          },
          {
            "id": "kai",
            "name": "Kai Novak",
            "role": "Backend developer"
          },
          {
            "id": "qa",
            "role": "QA engineer",
            "open": true
          }
        ]
      },
      {
        "id": "lena",
        "name": "Lena Park",
        "role": "Head of Operations",
        "team": "Courier operations",
        "tone": "teal",
        "children": [
          {
            "id": "joy",
            "name": "Joy Adams",
            "role": "Support lead"
          },
          {
            "id": "max",
            "name": "Max Rossi",
            "role": "Courier operations"
          }
        ]
      }
    ]
  },
  "links": [
    {
      "from": "ava",
      "to": "lia",
      "label": "works with"
    }
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- `style`: `plain` (default: a card with a circle of initials, the name and the role) or `illustrated` (a name pill, the role and a person icon).
- **Person**: `name`, `role` (a noun phrase such as `Mobile developer`, not a sentence; the build warns on a long one), optional `id` (needed by `links`), `team`, `tone`, `initials`, `icon` (illustrated style), `children`.
- **Tint**: `tone` if given, else the tone of the `team`, else, for someone who reports to the top, the tone of the name; the people below keep the tint of their head. The tint comes from the name or team, so a person has the same tint in every diagram. `people` (`{"Ava Lopez": {"initials": "AL", "tone": "blue"}}`) pins initials or a tint.
- **Open role**: `"open": true` with a `role` and no name. A dashed card, with the title and the words *Open role* (faded in the illustrated style).
- **Working link**: `links`: `[{"from": id, "to": id, "label": "works with"}]`: a dashed line with a pill between two people on the same level.
- The older form with `label` (name) and `detail` (role) is still read.
- Cards are 210 x 78 (plain) or 232 x 110 (illustrated), 250 px apart in a row, one level every 240 to 270 px; a manager stands over its middle report.
- Items are numbered in the order written, so without an `id` the ids in the scene file are `n0`, `n1`, ...: use them in an overrides file.

## Limits to tell the user

- Four levels fit a page; the build warns above that. Draw one chart per department.
- A working link joins two people on the same level; the line runs between the facing sides, so put the two side by side.
- Only one top person.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`, `red`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
