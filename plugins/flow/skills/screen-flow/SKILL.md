---
description: Draw a screen flow (the screens of an app and how a person moves between them) as an animated HTML page and a draw.io file. Use when the user asks for a user flow, a screen flow or an app navigation map.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Screen flow

You write a short **spec**. A script places the boxes, routes the lines, checks the result and writes the files. Never write coordinates or HTML yourself.

## Steps

1. List the screens, the decisions, the start and end, and what the person taps to go from one to the next.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "screen",
  "title": "Screen flow: sign up",
  "desc": "From the welcome screen a person signs up, confirms an email code and lands on the home screen.",
  "screens": [
    {
      "id": "begin",
      "kind": "start"
    },
    {
      "id": "welcome",
      "label": "Welcome",
      "icon": "phone"
    },
    {
      "id": "form",
      "label": "Sign-up form"
    },
    {
      "id": "code",
      "label": "Enter email code",
      "icon": "mail"
    },
    {
      "id": "home",
      "label": "Home",
      "icon": "home"
    }
  ],
  "taps": [
    {
      "from": "begin",
      "to": "welcome"
    },
    {
      "from": "welcome",
      "to": "form",
      "label": "Sign up",
      "main": true
    },
    {
      "from": "form",
      "to": "code",
      "label": "Continue",
      "main": true
    },
    {
      "from": "code",
      "to": "home",
      "label": "Verify",
      "main": true
    },
    {
      "from": "code",
      "to": "form",
      "label": "Wrong email",
      "style": "back"
    }
  ]
}
```

- **Screen**: `id`, `label`, `kind` (`screen` default, `dialog`, `decision`, `start`, `end`), `detail`, `icon`, `tone`.
- **Tap**: `from`, `to`, `label` (what the person does), `style` (`tap` solid, default; `back` dashed, for going back), `main: true` for the happy path.
- Top level: `type` (`screen`), `title`, `desc`, optional `direction` (`down` default, or `right`).
- Optional `at: [row, column]` on an item places it on an explicit grid cell. Use it only when the automatic placement is wrong.
- Icons: `user phone cart card bell clock pin pot check box bike refund warn star doc store database server cloud lock key mail globe gear chat search file folder link shield truck home calendar bolt heart camera bug code wifi chart`. To draw a missing one, write `icons.local.json` next to the spec (see the flowchart skill).

## Illustrated style

Add `"style": "illustrated"` at the top level to draw each box that has an `icon` as a card: a large icon on a tinted disc, the name in a pill, and the `detail` text under it. Boxes without an icon stay plain. Cards are bigger, so use it for a few boxes (about eight or fewer), give each a `tone` and a short `detail`, and keep names short: the name stays on one line. The default is `"style": "plain"`.

## Limits to tell the user

- Screens are plain boxes: there are no thumbnails or device frames, and no tabs or overlays as in the design.
- Text width is estimated, not measured. The draw.io file was checked in a viewer, not in the draw.io editor.
- Fixes beyond the spec: see the flowchart skill (overrides file).
