"""Score stored runs again with the current rule for tool calls, from their logs.

Usage: python3 benchmarks/routing/rescore.py LABEL ...

A log ends at the decision ``route.py`` made when it ran. A later rule that decides earlier finds
that earlier call; otherwise the recorded decision stands. Files that appeared in the work folder
cannot be seen again, so only tool calls are replayed. Prints each changed run, then rewrites
``results.jsonl`` with the new decisions.
"""

import json
import sys
from pathlib import Path

import route


def first_decision(setup: route.Setup, log: Path) -> str | None:
    """Return the first decision the current rule makes in a run's log.

    Args:
        setup: The result set, for the plugin folder.
        log: The run's stream log.

    Returns:
        The decision, or None when no tool call in the log decides.
    """
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.startswith("{"):
            continue
        message = json.loads(line)
        if message.get("type") != "assistant":
            continue
        for part in message["message"]["content"]:
            if part.get("type") == "tool_use":
                made = route.decide(setup, part["name"], part["input"])
                if made:
                    return made
    return None


def rescore(label: str, plugin: Path) -> None:
    """Rescore one result set in place.

    Args:
        label: The result set's name.
        plugin: The plugin folder its runs used.
    """
    setup = route.Setup(label, plugin.resolve(), "")
    results = route.OUT / label / "results.jsonl"
    rows = [json.loads(line) for line in results.read_text(encoding="utf-8").splitlines()]
    for row in rows:
        made = first_decision(setup, route.OUT / label / f"{row['id']}-{row['run']}" / "log.jsonl")
        if made and made != row["decision"]:
            print(f"{label} {row['id']}-{row['run']}: {row['decision']} -> {made}")
            row["decision"] = made
    results.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


if __name__ == "__main__":
    for name in sys.argv[1:]:
        rescore(name, route.HERE.parent.parent / "plugins" / "flow")
