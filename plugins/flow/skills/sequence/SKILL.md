---
description: Draw a sequence diagram (who sends which message to whom, in what order) as an animated HTML page and a draw.io file. Use when the order of messages between people, apps or services is the point: a sign-in, a payment, a checkout across services.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py *)
---

# Sequence diagram

You write a short **spec**: the participants and the messages in order. A script spaces the lifelines, derives the activation bars, wraps fragments around the rows they hold, checks the result and writes the files. Never write coordinates or HTML yourself.

Use it when the *order of messages* is the point. For structure use an architecture diagram; for one actor's steps and decisions use the flowchart skill (neither architecture nor other types are built yet: say so if asked).

## Steps

1. List the participants (a person, an app, a service, a database) and the messages between them, in time order.
2. Write `diagrams/<name>.spec.json` in the current project.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/flow.py build diagrams/<name>.spec.json`. It writes `<name>.scene.json`, `<name>.html` and `<name>.drawio` next to the spec and prints a check report. Exit code 0: no error; 2: errors found (files still written); 1: the spec is invalid and the message lists every problem.
4. Fix errors by changing the spec, at most three rounds. Warnings may stay; mention them. Do not say the diagram "looks good": you have not seen it.
5. Tell the user where the HTML and the `.drawio` file are.

## The spec

```json
{
  "type": "sequence",
  "title": "Sign in",
  "desc": "One sentence that says what the diagram shows.",
  "participants": [
    {"id": "user", "label": "User", "icon": "user", "tone": "gray"},
    {"id": "app", "label": "App", "icon": "phone", "tone": "blue"}
  ],
  "items": [
    {"kind": "sync", "from": "user", "to": "app", "label": "Tap Sign in", "role": "main", "number": "1"},
    {"kind": "return", "from": "app", "to": "user", "label": "Open dashboard", "role": "main", "number": "2"}
  ]
}
```

Items run top to bottom in the order written. An item is one of:

- **A message**: `kind`, `from`, `to`, `label`, optional `role`, optional `number`.
  - `sync`: the caller waits (solid line, filled head). `return`: the answer, drawn only when the value matters (dashed, open head). `async`: the caller carries on (solid, open head). `self`: the participant calls itself (a loop; `to` is ignored). `lost`: sent but nobody receives it (ends in a dot; give `from`). `found`: comes from outside the diagram (starts from a dot; give `to`). `create`: makes a participant appear lower (dashed, into its box).
  - `role`: `next` (default, ink), `main` (the one path the diagram is about: blue, thick, animated), `fail` (rose, with a rose label), `event` (violet, thin, slowly animated). A return on the main path keeps its own head and takes the main colour.
- **A note**: `{"note": "text", "over": "<participant>", "side": "right"}`. Use it for a reason that no arrow can carry.
- **A destroy**: `{"destroy": "<participant>"}` ends a lifeline with a cross.
- **A fragment**: `{"fragment": "alt", "sections": [{"guard": "password matches", "items": [...]}, {"guard": "else", "items": [...]}]}`. Kinds: `alt` (alternatives, one section per branch), `opt`, `loop`, `par`, `break`, `critical`, `ref`. The guard says under which condition the section happens. Fragments nest at most two levels.

Participants: `id` (used in messages), `label`, optional `icon` (`user phone cart card bell clock pin pot check box bike refund warn star doc store`) and `tone` (`blue violet amber green teal gray`, an owner or domain, never a meaning).

## Writing good content

- A label is one short phrase, about 24 characters at most: a call is code (`POST /orders`) or a verb phrase (*Charge card*); a return is the value (*Token*, *402*).
- Draw a `return` only when the value matters. Activation bars come from a `sync` call and the `return` that answers it, so pair them: a call that is never answered makes no bar.
- Numbers are optional. Use them when other text refers to steps; a branch adds a letter (`6a`, `6b`).
- Put at most one path on `main`. Show failures with `fail`, not with a different kind.
- About six participants and twenty messages fit one diagram; split a larger flow in two.

## Reading the report

`line-through-node`, `nodes-overlap`, `label-covers` and `outside-canvas` are errors; `text-may-not-fit` and `lines-cross` are warnings. A label that covers a lifeline's bar usually means a long label across a short span: shorten it or reorder the participants so that the two that talk most are neighbours. If an error remains, fix it by hand with an overrides file next to the spec (`<name>.overrides.json`, see the flowchart skill) or report it; do not edit the HTML or the `.drawio` file.

## Known limits

A note sits beside its lifeline at the row where it is written and may cover a message that crosses that spot. Bars of overlapping calls on one participant stack side by side. Text width is estimated. In the `.drawio` file, a message label is plain text with a number, not a rounded chip, and the fonts Inter and JetBrains Mono must be installed or draw.io substitutes another font.
