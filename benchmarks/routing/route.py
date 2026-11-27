"""Measure whether an agent picks the Flow plugin for a request, up to the point it makes a picture.

Usage: python3 benchmarks/routing/route.py LABEL PLUGIN_DIR ENV RUNS [ID | SPLIT ...]

ENV is ``owner`` (the container's own settings and synced plugins) or ``clean`` (a fresh config
folder, sync off: Flow and the built-in skills only). Each run gets a fresh copy of ``input/`` plus
four standard-library modules, and is stopped at its first decisive event:

- a ``flow:`` skill other than the entry skill ``flow:draw`` (which only routes), or a tool call
  that names a file of the plugin folder other than that skill's and ``WORKING.md``: ``flow``;
- a file with an output suffix written, or newly present in the work folder: ``own:<suffix>``;
- a final answer before either: ``text`` (with the answer kept, to tell a question from a reply).

Other skills, reads, searches, scripts and notes are recorded and the run goes on. One JSON line
per run goes to ``OUT/LABEL/results.jsonl``, including whether Flow's skills were listed to the
agent and which model served it.
"""

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import sysconfig
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

HERE: Path = Path(__file__).resolve().parent
OUT: Path = Path(os.environ.get("ROUTING_OUT", "/tmp/routing"))
MODEL: str = os.environ.get("ROUTING_MODEL", "sonnet")
WORKERS: int = 6
TIMEOUT_S: int = 300
MAX_TURNS: int = 20
ANSWER_CHARS: int = 400  # how much of a final answer is kept
STDLIB_FILES: tuple[str, ...] = (
    "asyncio/locks.py",
    "logging/handlers.py",
    "tarfile.py",
    "email/feedparser.py",
)
OUTPUT_SUFFIXES: frozenset[str] = frozenset(
    {".png", ".svg", ".html", ".htm", ".drawio", ".pdf", ".pptx", ".jpg", ".jpeg", ".webp"}
)
READ_ONLY: tuple[str, ...] = ("ls", "find", "grep", "wc", "head", "tail", "cat", "sed", "sort")
ALLOWED: list[str] = [
    "Read", "Write", "Edit", "Glob", "Grep", "Skill", "Bash(python3:*)", "Bash(node:*)",
    "Bash(mkdir:*)", "Bash(uniq:*)", "Bash(cut:*)", "Bash(awk:*)", "Bash(file:*)",
    *(f"Bash({name}:*)" for name in READ_ONLY),
]  # fmt: skip
NO_SYNC: dict[str, str] = {"CLAUDE_CODE_SYNC_PLUGINS": "0", "CLAUDE_CODE_SYNC_SKILLS": "0"}
FLOW_SKILL: str = "flow:"
ENTRY_SKILL: str = "flow:draw"  # routes on to a type skill; loading it alone decides nothing
ROUTING_FILES: tuple[str, ...] = ("skills/draw/", "skills/WORKING.md")  # read before routing
WRITES_OUTPUT: re.Pattern[str] = re.compile(
    r"(>|\btee\s+)\s*['\"]?[\w./-]+\.(png|svg|html?|drawio|pdf|pptx|jpe?g|webp)\b"
)  # a shell redirect or tee into an output file
LOCK: threading.Lock = threading.Lock()
# Each worker reuses one work folder path, so the agent's system prompt (which names its folder)
# is the same from run to run and its prompt cache is read instead of written again.
SLOTS: queue.Queue[int] = queue.Queue()


@dataclass(frozen=True)
class Setup:
    """What every run of a result set shares."""

    label: str
    plugin: Path
    env_kind: str


@dataclass
class Run:
    """What one run has shown so far."""

    work: Path
    before: frozenset[Path]
    decision: str = "none"
    calls: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    answer: str = ""
    end: str = ""
    listed: bool = False
    model: str = ""


def decide(setup: Setup, tool: str, args: dict[str, object]) -> str | None:
    """Return the decision a tool call makes, or None when it is not decisive.

    Args:
        setup: The result set; its plugin folder marks a use of Flow.
        tool: The tool's name.
        args: Its input.

    Returns:
        ``flow``, ``own:<suffix>`` or None.
    """
    if tool == "Skill":
        name = str(args.get("skill", ""))
        return "flow" if name.startswith(FLOW_SKILL) and name != ENTRY_SKILL else None
    text = json.dumps(args)
    if str(setup.plugin) in text and not any(name in text for name in ROUTING_FILES):
        return "flow"
    suffix = Path(str(args.get("file_path", ""))).suffix.lower()
    if tool in ("Write", "Edit") and suffix in OUTPUT_SUFFIXES:
        return "own:" + suffix.lstrip(".")
    if tool == "Bash" and WRITES_OUTPUT.search(str(args.get("command", ""))):
        return "own:bash"
    return None


def new_output(run: Run) -> str | None:
    """Return ``own:<suffix>`` when an output file has appeared in the work folder.

    Args:
        run: The run, with the files present before it started.

    Returns:
        The decision, or None when no new output file is there.
    """
    for path in run.work.rglob("*"):
        if path.suffix.lower() in OUTPUT_SUFFIXES and path not in run.before:
            return "own:" + path.suffix.lstrip(".").lower()
    return None


def read_event(setup: Setup, run: Run, message: dict[str, object]) -> str | None:
    """Update a run from one stream event and return its decision, if this event makes one.

    Args:
        setup: The result set.
        run: The run so far.
        message: One event of the stream.

    Returns:
        The decision, or None.
    """
    kind = message.get("type")
    if kind == "system" and message.get("subtype") == "init":
        run.listed = any(str(name).startswith(FLOW_SKILL) for name in message.get("skills", []))
        run.model = str(message.get("model", ""))
    if kind == "result":
        run.end = str(message.get("subtype", ""))
        run.answer = str(message.get("result", ""))[:ANSWER_CHARS]
        return new_output(run) or "text"
    if kind != "assistant":
        return None
    for part in message["message"]["content"]:
        made = _read_tool_call(setup, run, part) if part.get("type") == "tool_use" else None
        if made:
            return made
    return new_output(run)


def _read_tool_call(setup: Setup, run: Run, part: dict[str, object]) -> str | None:
    """Record one tool call and return its decision, naming the Flow skill when one decides.

    Args:
        setup: The result set.
        run: The run so far.
        part: A ``tool_use`` part of an assistant message.

    Returns:
        ``flow:<skill>``, ``flow``, ``own:<suffix>`` or None.
    """
    name, args = str(part["name"]), part["input"]
    run.calls.append(name)
    if name == "Skill":
        run.skills.append(str(args.get("skill", "")))
    made = decide(setup, name, args)
    if made == "flow" and name == "Skill":
        return "flow:" + str(args.get("skill", "")).removeprefix(FLOW_SKILL)
    return made


def watch(setup: Setup, run: Run, process: subprocess.Popen[str], log: Path) -> None:
    """Read the agent's stream until a decision, copying it to a log.

    Args:
        setup: The result set.
        run: The run; its decision is set here.
        process: The running agent.
        log: Where the stream is copied.
    """
    assert process.stdout is not None
    with log.open("w", encoding="utf-8") as copy:
        for line in process.stdout:
            copy.write(line)
            if not line.startswith("{"):
                continue
            made = read_event(setup, run, json.loads(line))
            if made:
                run.decision = made
                return
    run.decision = new_output(run) or "none"


def prepare(work: Path) -> frozenset[Path]:
    """Fill a fresh work folder with the inputs.

    Args:
        work: The folder; it must not exist yet.

    Returns:
        The files present before the agent starts.
    """
    shutil.copytree(HERE / "input", work)
    lib = Path(sysconfig.get_paths()["stdlib"])
    for name in STDLIB_FILES:
        shutil.copy(lib / name, work / Path(name).name)
    return frozenset(work.rglob("*"))


def command(plugin: Path, request: str) -> list[str]:
    """Return the agent's command line.

    Args:
        plugin: The plugin folder.
        request: The request text.

    Returns:
        The argument list.
    """
    return [
        "claude", "-p", request, "--model", MODEL, "--plugin-dir", str(plugin),
        "--permission-mode", "acceptEdits", "--allowedTools", *ALLOWED,
        "--disallowedTools", "Agent", "Task", "--max-turns", str(MAX_TURNS),
        "--output-format", "stream-json", "--verbose",
    ]  # fmt: skip


def run_one(setup: Setup, entry: dict[str, str], index: int) -> dict[str, object]:
    """Run one request once.

    Args:
        setup: The result set's name, plugin folder and environment kind.
        entry: The request.
        index: The run's number for this request.

    Returns:
        The result row.
    """
    base = OUT / setup.label / f"{entry['id']}-{index}"
    base.mkdir(parents=True, exist_ok=True)
    slot = SLOTS.get()
    try:
        return _run_in(setup, entry, index, OUT / "slots" / f"w{slot}")
    finally:
        SLOTS.put(slot)


def _run_in(setup: Setup, entry: dict[str, str], index: int, work: Path) -> dict[str, object]:
    """Run one request once in a given work folder.

    Args:
        setup: The result set's name, plugin folder and environment kind.
        entry: The request.
        index: The run's number for this request.
        work: The worker's folder, emptied and filled here.

    Returns:
        The result row.
    """
    base = OUT / setup.label / f"{entry['id']}-{index}"
    shutil.rmtree(work, ignore_errors=True)
    run = Run(work=work, before=prepare(work))
    env = dict(os.environ)
    if setup.env_kind == "clean":
        env |= {"CLAUDE_CONFIG_DIR": str(OUT / "clean-config"), **NO_SYNC}
    process = subprocess.Popen(
        command(setup.plugin, entry["text"]), cwd=run.work, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )  # fmt: skip
    timer = threading.Timer(TIMEOUT_S, process.kill)
    timer.start()
    try:
        watch(setup, run, process, base / "log.jsonl")
    finally:
        timer.cancel()
        process.kill()
        process.wait()
    row = {key: entry[key] for key in ("id", "expect", "split", "asks")} | {"run": index}
    row |= {"decision": run.decision, "listed": run.listed, "model": run.model}
    return row | {"skills": run.skills, "calls": run.calls, "end": run.end, "answer": run.answer}


def run_and_record(setup: Setup, entry: dict[str, str], index: int) -> None:
    """Run one request once and append its row, or an error row when the run fails.

    Args:
        setup: The result set.
        entry: The request.
        index: The run's number for this request.
    """
    try:
        row = run_one(setup, entry, index)
    except Exception as error:
        row = {"id": entry["id"], "run": index, "decision": "error", "error": repr(error)}
    with LOCK, (OUT / setup.label / "results.jsonl").open("a", encoding="utf-8") as results:
        results.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{setup.label} {entry['id']}-{index} {row['decision']}", flush=True)


def main(argv: list[str]) -> None:
    """Run every chosen request RUNS times, several at once, and check that each left a row.

    Args:
        argv: LABEL PLUGIN_DIR ENV RUNS, then request ids or split names (all when none).
    """
    label, plugin, env_kind, runs, *ids = argv
    entries = json.loads((HERE / "requests.json").read_text(encoding="utf-8"))
    chosen = [entry for entry in entries if not ids or entry["id"] in ids or entry["split"] in ids]
    (OUT / label).mkdir(parents=True, exist_ok=True)
    (OUT / "clean-config").mkdir(parents=True, exist_ok=True)
    setup = Setup(label, Path(plugin).resolve(), env_kind)
    for slot in range(WORKERS):
        SLOTS.put(slot)
    with ThreadPoolExecutor(WORKERS) as pool:
        for entry in chosen:
            for index in range(int(runs)):
                pool.submit(run_and_record, setup, entry, index)
    rows = (OUT / label / "results.jsonl").read_text(encoding="utf-8").splitlines()
    print(f"{len(rows)} rows in {label}; this call ran {len(chosen) * int(runs)}")


if __name__ == "__main__":
    main(sys.argv[1:])
