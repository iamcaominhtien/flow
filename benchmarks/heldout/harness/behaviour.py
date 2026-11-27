"""Summarise what each held-out run did, from its stream-json log."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = sys.argv[1:] or ["base", "base2", "new", "new2"]


def summary(log: Path) -> dict[str, object]:
    """Return the skills, input reads, brief, view.js use, turns and cost of one run."""
    skills, reads, brief, view, authored = [], set(), False, False, False
    turns = cost = None
    for line in log.read_text().splitlines():
        if not line.startswith("{"):
            continue
        message = json.loads(line)
        if message.get("type") == "result":
            turns, cost = message.get("num_turns"), message.get("total_cost_usd")
        if message.get("type") != "assistant":
            continue
        for part in message["message"]["content"]:
            if part.get("type") != "tool_use":
                continue
            tool, args = part["name"], part["input"]
            text = json.dumps(args)
            if tool == "Skill":
                skills.append(args.get("skill"))
            if tool in ("Read", "Grep") and "/input/" in text:
                reads.add(args.get("file_path") or args.get("path") or args.get("pattern"))
            if tool == "Bash" and "/input" in args.get("command", "") and any(
                word in args["command"] for word in ("cat ", "sed ", "grep ", "head ")
            ):
                reads.add(args["command"][:60])
            if ".brief.md" in text and tool in ("Write", "Edit", "Bash"):
                brief = True
            if "view.js" in text:
                view = True
            if "Canvas(" in text:
                authored = True
    return {
        "skills": ",".join(s.replace("flow:", "") for s in skills) or "-",
        "input_reads": len(reads),
        "brief": brief,
        "view": view,
        "author_kit": authored,
        "turns": turns,
        "cost": round(cost or 0, 2),
    }


for label in LABELS:
    for run in sorted((HERE / label).iterdir()):
        log = run / "log.jsonl"
        if log.is_file():
            row = summary(log)
            print(f"{label:6} {run.name:14} " + " ".join(f"{k}={v}" for k, v in row.items()))
