# Large diagrams: layout on frozen content

Two briefs of about 160 nodes each, written by an agent that had not seen the arrangement kit, with the content frozen (nodes, kinds, sets, connections) so a run tests layout, not reading:

- `l1-claims/brief.md`: an insurance claim process, 169 nodes, 5 actors, 28 decisions, 2 loops, 3 failure ends, 2 parallel blocks, 3 sets, one 15-step sequence with no branch.
- `l2-import/brief.md`: how Python's `import` finds and loads a module, 157 nodes from the CPython 3.13 source, 11 failure nodes, 6 sets.

`run.sh LABEL PLUGIN_DIR BRIEF_ID` runs Sonnet once with the author skill named, for a screen. `measure.py MEDIUM SCENE...` prints page size, screens filled, smallest text at the medium, empty share of zones, longest line, backward lines and ink.

## Rule, fixed before the first run (2026-11-27)

Compared: the plugin before the arrangement kit (`c86dcdc`, new colours, no kit) and after (`fde0a45` and later, same colours, with `flowlib.arrange` and the skill section). One Sonnet run per brief and version.

The kit is kept when, on both briefs:

1. the empty share of zones is lower after than before, and
2. backward lines are no more after than before, and
3. the page fills no more than 1.2 times the screens it filled before,

and a side-by-side look at the two pictures of each brief (by the main agent, then shown to the owner) does not prefer before. With one run per version this is a smoke test, not a measurement: a pass says the kit is used and does not make things worse; it does not say by how much it helps.
