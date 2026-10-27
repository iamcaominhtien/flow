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
  "title": "Class diagram: the delivery domain",
  "desc": "One sentence that says what the diagram shows.",
  "classes": [
    {"id": "order", "label": "Order", "tone": "violet", "at": [0, 1],
     "attributes": ["-id: UUID", "-status: OrderStatus"],
     "operations": ["+addItem(d: Dish, n: int)", "+pay(p: Payment)"]},
    {"id": "payment", "label": "Payment", "kind": "abstract", "tone": "amber", "at": [1, 1],
     "operations": ["+authorise(): bool"]},
    {"id": "card", "label": "CardPayment", "tone": "amber", "at": [2, 1],
     "attributes": ["-cardToken: String"], "operations": ["+authorise(): bool"]}
  ],
  "relations": [
    {"from": "order", "to": "payment", "label": "paid by", "from_label": "1", "to_label": "0..*"},
    {"from": "card", "to": "payment", "style": "inheritance"}
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- **Class**: `id`, `label` (a singular noun in PascalCase), `attributes` and `operations` (lists of strings; `methods` is accepted for `operations`), optional `kind` (`class`, `abstract`: the name is italic; `interface`: `«interface»` above the name), `stereotype` (own text such as `«enumeration»`), `tone`, `at: [row, column]`. A compartment with nothing in it is left out. The box is 280 px wide; the header has the class tint (default blue, interface gray).
- **Members** are written as in UML: a visibility mark (`+` public, `-` private, `#` protected), the name, a colon and the type; an operation has its parameters and return type: `+addItem(d: Dish, n: int)`, `+authorise(): bool`. Show the members that explain the relationships, not every field.
- **Relation**: `from`, `to`, optional `label` (a verb: `places`), `from_label` and `to_label` (the multiplicity at each end: `1`, `0..1`, `0..*`, `1..*`; drawn next to the boxes), and `style`:
  - `association` (default): a plain line; `navigable`: an open arrow at `to`;
  - `composition`: a filled diamond at `from`, the whole; `aggregation`: a hollow diamond at `from`;
  - `inheritance`: a hollow triangle at `to`, the parent, so write it from the child; `implements`: the same triangle on a dashed line (the interface is `to`);
  - `dependency`: a dashed open arrow at `to`, a weak, temporary use.
- **Layout (from the design):** boxes sit on a grid 460 px apart sideways and at least 130 px apart downward; a half column is allowed (`[2, 0.5]`) to put two children under a parent. Without `at` the parents go above their children (inheritance and implements), the first class goes top left, the rest follow the relations, four to a row. Lines are orthogonal with at most two bends and do not cross a box. About ten classes fit on a page; past that, one diagram per module.
- Names agree with the ER diagram of the same domain: the class `Order` is the table `orders`.
- Icons: not drawn on classes. The class diagram is plain only.

## Limits to tell the user

- Several lines on one side of a box are spread 60 px apart, so a line can have a small jog. A class that points at itself is a loop at its right side.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).

Tone values: `blue`, `violet`, `amber`, `green`, `teal`, `gray`. Any other value is refused by the build.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
