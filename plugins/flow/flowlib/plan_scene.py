"""Write and read what a planning node shows, in the JSON of a scene and in a draw.io style.

The scene format of a planning node is ``"plan": {"status", "progress", "reason", "initials",
"person_tone", "open", "bold", "level", "side", "priority", "hidden"}``; keys that hold their
default are left out.
"""

import base64
import json
from typing import Any

from .model import MindLevel, PlanView, Side, Status, Tone
from .reader import Reader

PLAN_KEYS = {"status", "progress", "reason", "initials", "person_tone", "open", "bold", "level"}
PLAN_KEYS |= {"side", "priority", "hidden"}


def dump_plan(view: PlanView) -> dict[str, Any]:
    """Turn a planning view into JSON, leaving out what holds its default.

    Args:
        view: What a planning node shows.

    Returns:
        A JSON-style dict that ``parse_plan`` accepts.
    """
    optional = {
        "status": view.status.value if view.status else None,
        "progress": view.progress,
        "reason": view.reason,
        "initials": view.initials,
        "person_tone": view.person_tone.value if view.person_tone else None,
        "open": view.is_open,
        "bold": view.is_bold,
        "level": view.level.value if view.level else None,
        "side": view.side.value if view.side else None,
        "priority": view.priority,
        "hidden": view.hidden,
    }
    return {key: value for key, value in optional.items() if value}


def parse_plan(raw: object, where: str, read: Reader) -> PlanView | None:
    """Read a planning view from its JSON, or report why it cannot be read.

    Args:
        raw: The ``plan`` object of a node.
        where: Where the object is, for messages.
        read: The reader that collects problems.

    Returns:
        The view, or None when it is not an object.
    """
    if not isinstance(raw, dict):
        read.report(where, "'plan' must be an object")
        return None
    read.check_keys(raw, PLAN_KEYS, where)
    return PlanView(
        status=read.enum(Status, raw, "status", where),
        progress=read.number(raw, "progress", where) if "progress" in raw else 0.0,
        reason=read.text(raw, "reason", where) or "",
        initials=read.text(raw, "initials", where) or "",
        person_tone=read.enum(Tone, raw, "person_tone", where),
        is_open=raw.get("open") is True,
        is_bold=raw.get("bold") is True,
        level=read.enum(MindLevel, raw, "level", where),
        side=read.enum(Side, raw, "side", where),
        priority=int(read.number(raw, "priority", where)) if "priority" in raw else 0,
        hidden=int(read.number(raw, "hidden", where)) if "hidden" in raw else 0,
    )


def encode_plan(view: PlanView) -> str:
    """Pack a planning view into one word that fits in a draw.io style, which has no semicolons."""
    text = json.dumps(dump_plan(view), separators=(",", ":"))
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def decode_plan(packed: str) -> PlanView | None:
    """Unpack what ``encode_plan`` wrote, or return None when it cannot be read."""
    padded = packed + "=" * (-len(packed) % 4)
    try:
        raw = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
    except ValueError:
        return None
    return parse_plan(raw, "plan", Reader())
