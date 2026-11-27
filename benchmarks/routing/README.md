# Routing: does a request to draw something reach the plugin?

In the held-out evaluation of 0.20.0 the agent wrote its own HTML or SVG in 21 of 28 runs and never loaded Flow (`benchmarks/results/2026-11-27-heldout-0.20.0.md`). This set measures that alone: for each request, the first decisive thing the agent does. It does not judge the picture.

Written on 2026-11-27, before any change to the plugin's routing.

## The set

`requests.json`: 44 requests, written before any run (five hard negatives, n10-n14, were added after an independent review and before the baseline).

- 30 that a diagram plugin should take (`expect: flow`): code, a small repo, a schema, tables, a transcript, documents, a config, a log, a draw.io file, and bare sentences; English and Vietnamese; some ask for a PNG or a phone, most name no format. `asks` says whether the request names a diagram type that a skill's description names (`type`, 11) or only asks to draw, show or visualise something (`generic`, 18): the held-out evaluation failed on the generic kind. One (p25) names the plugin, as a sanity check.
- 14 that it should not (`expect: other`): a bar chart, a line chart and a histogram of data, an explanation in words, an ASCII sketch in the reply, a bug fix, a React page, a Mermaid block in a README, a summary, a slide deck, a format conversion, a painting, a poster, a security review.
- `split`, stratified by `asks`, input kind and language: `dev` (15 + 6) may be looked at while changing the plugin; `held` (15 + 8) is run for the baseline and for the final change, and only its totals are looked at in between.

`input/` holds the files the requests name; the harness adds four standard-library modules (`locks.py`, `handlers.py`, `tarfile.py`, `feedparser.py`) from the Python that runs it (3.13 here).

## The harness

`route.py LABEL PLUGIN_DIR ENV RUNS [ID | SPLIT ...]` runs each request with `claude -p` (model from `ROUTING_MODEL`, default Sonnet; the resolved id is recorded), and stops it at the first decisive event:

- `flow`: a `flow:` skill, or any tool call naming a file of the plugin folder;
- `own:<suffix>`: the agent writes a file with an output suffix (html, svg, png, drawio, pdf, pptx, jpg, webp), or such a file appears in the work folder;
- `text`: a final answer before either (the answer is kept, so a clarifying question, which nobody can answer in `-p` mode, can be told from a reply).

Other skills, reads, scripts and notes are recorded and the run goes on. Each row records whether Flow's skills were listed to the agent at all. Subagents are disallowed, so the decision is the main agent's. Bash is limited to read-only tools plus `python3`, `node` and `mkdir`; a denied command is part of the run. Each worker reuses one work folder path, so the system prompt and its cache stay the same between runs.

Not measured: whether a run that loads Flow stays with it to the end.

Two environments:

- `owner`: this cloud container's settings, with the twelve plugins synced to the owner's account; several compete for pictures (`image-generation`, `superdesign`, `design-skills`, and the built-in `artifact-diagramming`, `dataviz` and `design` skills). This is the owner's cloud setup, not necessarily their own machine.
- `clean`: a fresh config folder, plugin sync off: Flow and the built-in skills only.

## The rule, fixed before the baseline

Every run uses Sonnet: the plugin has to work for a model that is not the strongest, and that is where its gaps show. (The first version of this rule, `c90ee95`, made Opus primary; it was changed before any baseline run finished, on the owner's instruction.)

Primary: the `held` split, Sonnet, `owner` environment, two runs per request.

- **Misses**: runs of `expect: flow` requests whose decision is not `flow`, out of 30.
- **False positives**: runs of `expect: other` requests whose decision is `flow`, out of 16.

A change to routing is kept when all of these hold:

1. Misses fall by at least half and by at least 4 runs.
2. False positives are at most the baseline's plus 2.
3. In `clean` (`held`, one run), hits are not fewer than the baseline's.

Anything less is reported as not shown. Reported beside it and deciding nothing: hits split by `type` and `generic`, a per-request sign test, the `dev` split, and how often Flow was not listed at all.
