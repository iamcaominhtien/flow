---
description: Draw a UML class diagram (classes with attributes and methods, and how they relate) as an animated HTML page and a draw.io file. Use when the user asks for a class diagram or an object model.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Class diagram

You write a short **spec**. A script places the boxes, routes the lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the classes with their attributes and methods, then the relations (inheritance, composition and so on).
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "class",
  "title": "Class diagram",
  "desc": "Shapes.",
  "classes": [
    {
      "id": "shape",
      "label": "Shape",
      "attributes": [
        "+name: str"
      ],
      "methods": [
        "+area(): float"
      ]
    },
    {
      "id": "circle",
      "label": "Circle",
      "attributes": [
        "-radius: float"
      ],
      "methods": [
        "+area(): float"
      ]
    },
    {
      "id": "canvas",
      "label": "Canvas",
      "attributes": [
        "-shapes: list"
      ],
      "methods": [
        "+draw()"
      ]
    }
  ],
  "relations": [
    {
      "from": "circle",
      "to": "shape",
      "style": "inheritance"
    },
    {
      "from": "canvas",
      "to": "shape",
      "style": "aggregation",
      "to_label": "*"
    }
  ]
}
```

- **Class**: `id`, `label`, `attributes` (list of strings such as `-radius: float`), `methods` (list of strings), `icon`, `tone`.
- **Relation**: `from`, `to`, `label`, `style`: `association` (default), `inheritance` (hollow triangle at `to`, the parent), `implements` (dashed, hollow triangle), `composition` (filled diamond at `from`, the whole), `aggregation` (hollow diamond at `from`), `dependency` (dashed arrow). `from_label` and `to_label` are accepted for multiplicity.
- Top level: `type` (`class`), `title`, `desc`, optional `direction` (`down` default, or `right`).
- Optional `at: [row, column]` on an item places it on an explicit grid cell. Use it only when the automatic placement is wrong.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Limits to tell the user

- Multiplicity labels (`from_label`, `to_label`) are accepted but not drawn yet. Interfaces and abstract classes have no special look: put `«interface»` in the label.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.
