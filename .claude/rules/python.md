---
paths:
  - "**/*.py"
---

# Python code rules

These apply to every Python file in this repo except `docs/`, which holds a frozen snapshot. Code is read far more often than written, so write it for the next reader.

## Names

- A name says what the thing is or does. No single letters (`w`, `h`, `t`, `s`, `r`, `d`, `n`) and no cryptic abbreviations, except `i`/`j` for a plain index and `x`/`y` for coordinates.
- Functions are verbs (`validate_scene`, `shorten_last_segment`). Variables and attributes are nouns (`node_ids`, `label_chip`). Booleans read as a question (`has_arrow`, `is_animated`).
- Do not reuse one name for two things in a function, and do not name something after its type (`data`, `obj`, `lst`, `tmp`, `res`).
- Private helpers start with `_`. Modules are short nouns (`scene`, `theme`), never `utils`/`helpers`/`common`.
- When a name needs a comment to explain it, rename it instead.

## Documentation

- Every module, class and function has a docstring, public or private. No exceptions for "obvious" helpers.
- Use Google style. A function that takes arguments documents **every** argument under `Args:`; one that returns something documents it under `Returns:`; one that raises on purpose documents it under `Raises:`.
- The first line is a one-line summary in the imperative ("Return the HTML for a scene."), ending with a full stop.
- Say what and why, not how. Do not repeat the code in words.
- A comment explains a decision or a non-obvious constraint, never what the next line does. Delete commented-out code.

```python
def shorten_last_segment(points: list[Point], gap: float) -> list[Point]:
    """Pull the last point back so an arrowhead tip touches the box.

    Args:
        points: The edge route, at least two points.
        gap: Distance to remove from the end of the last segment, in pixels.

    Returns:
        A new list; the input is not changed. The input itself is returned
        when the last segment is not longer than ``gap``.
    """
```

## Structure

- One function does one thing and fits on a screen (about 30 lines). When a function needs a comment to mark its "parts", split it at the parts.
- No more than 3 levels of nesting. Use early returns and guard clauses instead of `else` ladders.
- At most 4 parameters. Past that, pass a small dataclass, not a longer list. No boolean flag parameters that switch behaviour; write two functions.
- Build structured text (HTML, SVG, XML) from small named pieces, not one long f-string with logic inside. Put each repeated fragment in its own function.
- Order a file top to bottom: module docstring, imports, constants and enums, classes, public functions, then private helpers.
- Do not write dead code, unused parameters, or a helper used once that only renames something.
- Prefer a plain function over a class unless there is state to keep. Prefer a dataclass over a dict with fixed keys.

## Constants and enums

- No magic numbers or strings. A number with a meaning (a size, a gap, a font size, a timeout) or a string used in more than one place is a named module-level constant in `UPPER_CASE`, with a comment on the unit when it is not obvious (`ARROW_GAP_PX`).
- A closed set of values is an `enum.Enum` (or `enum.StrEnum` when the value is written to JSON or HTML): shapes, line roles, label kinds, node tones. Compare with the member, never with a bare string.
- Values that belong to the design (colours, sizes, spacing, animation speeds) live in `theme.json` and are read through `theme.py`. They are never repeated in code.
- A literal is fine when its meaning is obvious from the line (`0`, `1`, `2` for halving, an index, an empty string).

## Types

- Annotate every function signature and every module-level constant. Use built-in generics (`list[str]`, `dict[str, int]`, `X | None`).

## Before you finish

Run `ruff format .`, `ruff check .` and `python3 -m pytest`. The Claude Code hook already formats and lints each file you edit; it does not check these rules, so re-read your own diff against this page.
