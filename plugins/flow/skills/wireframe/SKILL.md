---
description: Draw a low-fidelity wireframe (screens made of headers, text, inputs, buttons, images and lists) as an animated HTML page and a draw.io file. Use when the user asks for a wireframe or a rough screen layout.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Wireframe

You write a short **spec**: screens, each with its elements from top to bottom. A script stacks the elements in a phone-width frame and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the screens and, for each, its elements in order.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "wireframe",
  "title": "Wireframe: sign in",
  "desc": "Two screens: the sign-in form and the home screen after it.",
  "screens": [
    {
      "label": "Sign in",
      "elements": [
        {
          "kind": "header",
          "label": "My app"
        },
        {
          "kind": "image",
          "label": "logo"
        },
        {
          "kind": "input",
          "label": "Email"
        },
        {
          "kind": "input",
          "label": "Password"
        },
        {
          "kind": "button",
          "label": "Sign in"
        },
        {
          "kind": "text",
          "label": "Forgot your password?"
        }
      ]
    },
    {
      "label": "Home",
      "elements": [
        {
          "kind": "header",
          "label": "Home"
        },
        {
          "kind": "list",
          "items": [
            "Orders",
            "Messages",
            "Settings"
          ]
        },
        {
          "kind": "button",
          "label": "New order"
        }
      ]
    }
  ]
}
```

- `theme` (optional): `pastel` (default), `technical` or `midnight`; see the flowchart skill.
- **Screen**: `label`, `elements`.
- **Element**: `kind` is `header`, `text`, `input`, `button`, `image` or `list`; `label` is its text. A `list` takes `items`, a list of strings, one row each.
- Screens sit side by side, in the order written.

## Limits to tell the user

- It is a stack of boxes in one column: no side-by-side elements, no tabs, no desktop layout, no annotations or arrows between screens (use the screen flow skill for that).
- Elements are boxes with text, not drawn controls.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.

For a large or dense diagram (more than about 15 elements, many groups, or a hub with many lines) the automatic layout gives long pages and bundled lines; use the `author` skill (`/flow:author`) instead, which lays the diagram out by hand and looks at the result.
