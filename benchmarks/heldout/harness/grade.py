"""Grade held-out runs: answers from the picture at the medium's size, against a control.

Usage: python3 grade.py LABEL [ID ...]   (writes LABEL/ID/grade.json)
       python3 grade.py --control ID ... (writes control/ID.json)
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SET = Path("/home/user/flow/benchmarks/heldout")
MEDIUM = {
    "h1-rebase": ("phone", 390, 3),
    "h2-redirect": ("phone", 390, 3),
    "h3-threadpool": ("screen", 1440, 1),
    "h4-meeting": ("slide", 1280, 1),
    "h5-tickets": ("phone", 390, 3),
    "h6-deploy": ("screen", 1440, 1),
    "h7-httpstates": ("phone", 390, 3),
}
TOOLS = ["--allowedTools", "Read", "Glob", "Grep", "--add-dir", str(SET), "--add-dir", str(HERE)]


def section(brief_id: str) -> tuple[list[str], list[str]]:
    """Return the five questions and the five answers of a brief from ANSWERS.md."""
    text = (SET / "ANSWERS.md").read_text()
    part = text.split(f"## {brief_id}", 1)[1].split("\n## ", 1)[0]
    items = re.findall(r"^\d\. (.+)$", part, re.M)
    questions = [item.split("?", 1)[0] + "?" for item in items]
    return questions, items


def ask(prompt: str, cwd: Path) -> str:
    """Run a one-shot Sonnet session and return its final text."""
    run = subprocess.run(
        ["claude", "-p", prompt, "--model", "sonnet", "--max-turns", "30", *TOOLS],
        cwd=cwd, capture_output=True, text=True, check=False,
    )
    return run.stdout.strip()


def last_json(text: str) -> object:
    """Return the last JSON object or list in a reply."""
    for match in reversed(list(re.finditer(r"(\{.*\}|\[.*\])", text, re.S))):
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return None


def pictures(run_dir: Path) -> list[Path]:
    """Return the PNGs a run delivered in its working folder (not its input)."""
    work = run_dir / "work"
    return sorted(p for p in work.rglob("*.png") if "input" not in p.relative_to(work).parts)


def resized(run_dir: Path, brief_id: str) -> list[Path]:
    """Show each PNG at the medium's width and return the new files."""
    _, width, dpr = MEDIUM[brief_id]
    out = run_dir / "graded"
    out.mkdir(exist_ok=True)
    done = []
    for index, png in enumerate(pictures(run_dir)):
        target = out / f"view-{index}.png"
        subprocess.run(["node", str(HERE / "resize.js"), str(png), str(target), str(width), str(dpr)],
                       check=True, env={**os.environ, "NODE_PATH": node_path()})
        done.append(target)
    return done


def node_path() -> str:
    """Return the global node_modules folder, where Playwright is."""
    return subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()


def answer(questions: list[str], views: list[Path], cwd: Path) -> list[str]:
    """Answer the questions from the pictures only."""
    files = "\n".join(str(view) for view in views)
    prompt = (
        "Open these images with the Read tool and look at them; they are a diagram, shown at "
        f"the size a reader sees it:\n{files}\n\nAnswer each question using ONLY what the "
        "images show. If the images do not show it, or the text is too small to read, answer "
        "'not shown'. Do not use outside knowledge. Reply with a JSON list of 5 strings.\n\n"
        + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
    )
    reply = last_json(ask(prompt, cwd))
    return reply if isinstance(reply, list) else ["(no reply)"] * len(questions)


def score(items: list[str], answers: list[str], cwd: Path) -> list[int]:
    """Score each answer 1 when it matches the key in substance, else 0."""
    pairs = "\n".join(
        f"{i + 1}. KEY: {key}\n   ANSWER: {given}" for i, (key, given) in enumerate(zip(items, answers))
    )
    prompt = (
        "Score each answer against its key: 1 if it states the substance of the key (the main "
        "point; wording may differ; a partial answer that gets the main point counts), 0 if it "
        "is wrong, missing or 'not shown'. Reply with a JSON list of 5 integers only.\n\n" + pairs
    )
    reply = last_json(ask(prompt, cwd))
    return reply if isinstance(reply, list) else [0] * len(items)


def fidelity(views: list[Path], brief_id: str, cwd: Path) -> object:
    """Check five drawn claims against the source."""
    source = SET / brief_id / "input"
    where = f"the source files in {source}" if source.is_dir() else "git's documented behaviour"
    files = "\n".join(str(view) for view in views)
    prompt = (
        f"Open these images with the Read tool: a diagram of {where}.\n{files}\n\nPick the five "
        "drawn elements (boxes, decisions, labelled arrows) that make the most specific factual "
        "claims. Check each against the source (read it). Judge each: correct, wrong, or "
        'invented (not in the source). Reply with JSON: {"items": [{"element": str, "verdict": '
        'str, "why": str}], "wrong_or_invented": int}.'
    )
    return last_json(ask(prompt, cwd))


def grade_run(label: str, brief_id: str) -> None:
    """Grade one run and write its grade.json."""
    run_dir = HERE / label / brief_id
    questions, items = section(brief_id)
    views = resized(run_dir, brief_id)
    result: dict[str, object] = {"pictures": [str(p) for p in pictures(run_dir)]}
    if views:
        answers = answer(questions, views, run_dir)
        result.update(answers=answers, scores=score(items, answers, run_dir),
                      fidelity=fidelity(views, brief_id, run_dir))
    else:
        result.update(answers=[], scores=[0] * 5, fidelity=None)
    (run_dir / "grade.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(label, brief_id, result["scores"])


def grade_control(brief_id: str) -> None:
    """Answer the questions with no picture, from what the model already knows."""
    questions, items = section(brief_id)
    out = HERE / "control"
    out.mkdir(exist_ok=True)
    prompt = (
        "Answer each question from what you already know, without any file or tool. If you do "
        "not know, answer 'don't know'. Reply with a JSON list of 5 strings.\n\n"
        + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
    )
    reply = last_json(ask(prompt, out))
    answers = reply if isinstance(reply, list) else ["(no reply)"] * 5
    scores = score(items, answers, out)
    (out / f"{brief_id}.json").write_text(json.dumps({"answers": answers, "scores": scores}, indent=1))
    print("control", brief_id, scores)


if __name__ == "__main__":
    if sys.argv[1] == "--control":
        for each in sys.argv[2:]:
            grade_control(each)
    else:
        for each in sys.argv[2:] or list(MEDIUM):
            grade_run(sys.argv[1], each)
