"""Read and check the spec of a Gantt chart.

The JSON format::

    {"type": "gantt", "title": "...", "desc": "...", "today": "2026-04-20",
     "tasks": [{"id", "label", "owner", "start", "end", "group", "status", "progress", "reason",
                "after", "critical"}],
     "milestones": [{"id", "label", "date" | "at" | "after", "group"}],
     "people": {"Ava Lopez": {"initials": "AL", "tone": "blue"}}}

Time is read in one of three ways, never mixed:

* **Dates**: ``start`` and ``end`` are ISO dates and ``end`` is the last day of the task. The
  first column is the Monday on or before the earliest date (or ``axis_start``).
* **Weeks**: ``start`` and ``end`` are week numbers from 1, ``end`` included (``start`` 3,
  ``end`` 5 is W3 to W5). ``length`` in weeks can replace ``end``.
* **Periods** (the older form): ``periods`` names the columns, ``start`` counts from 0 and
  ``length`` is a number of periods; ``end`` is the last period, counted from 0.

``after`` is the id, or a list of ids, of what must finish first. ``status`` is ``done``,
``in_progress``, ``planned`` or ``blocked``; it is worked out from ``progress`` when absent.
"""

import math
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from typing import Any

from ..model import Status
from ..reader import Reader, SpecError, is_number, suggestion
from .people import Person, person_of, read_people

SPEC_KEYS = {
    "type", "title", "desc", "theme", "periods", "weeks", "axis_start", "today", "tasks",
    "milestones", "people",
}  # fmt: skip
TASK_KEYS = {
    "id", "label", "owner", "start", "end", "length", "group", "status", "progress", "reason",
    "after", "critical", "tone",
}  # fmt: skip
MILESTONE_KEYS = {"id", "label", "date", "at", "after", "group"}
DAYS_PER_WEEK = 7
MONDAY = 0
TOLERANCE = 1e-9  # positions are fractions of a week; closer than this counts as equal


class TimeMode(StrEnum):
    """How the start and the end of a task are written."""

    DATES = "dates"
    WEEKS = "weeks"
    PERIODS = "periods"


@dataclass(frozen=True)
class Axis:
    """The columns of the chart."""

    mode: TimeMode
    count: int  # the number of columns
    start: date | None  # the date of the left edge, when the chart is read in dates
    labels: tuple[str, ...]  # the names of the columns, when the spec names them


@dataclass(frozen=True)
class Task:
    """One bar. Positions are counted in columns from the left edge of the chart."""

    id: str
    label: str
    start: float
    end: float
    owner: Person | None
    group: str | None
    status: Status
    progress: float
    reason: str
    after: tuple[str, ...]
    is_critical: bool


@dataclass(frozen=True)
class Milestone:
    """A date on its own row, drawn as a diamond."""

    id: str
    label: str
    at: float
    group: str | None
    after: tuple[str, ...]


@dataclass(frozen=True)
class GanttSpec:
    """A checked Gantt chart."""

    title: str | None
    description: str | None
    axis: Axis
    today: float | None
    tasks: tuple[Task, ...]
    milestones: tuple[Milestone, ...]


@dataclass(frozen=True)
class _Scale:
    """Turns what a spec says about time into positions, in columns from the left edge."""

    mode: TimeMode
    axis_start: date | None
    periods: tuple[str, ...]


def read_spec(raw: object) -> GanttSpec:
    """Check a Gantt spec and turn it into the description the layout works on.

    Args:
        raw: The result of ``json.loads`` on the spec.

    Returns:
        The checked spec.

    Raises:
        SpecError: With every problem found.
    """
    if not isinstance(raw, dict):
        raise SpecError(["the spec must be a JSON object"])
    read = Reader()
    read.check_keys(raw, SPEC_KEYS, "spec")
    scale = _scale(raw, read)
    pinned = read_people(raw, read)
    tasks = _tasks(raw, (scale, pinned), read)
    milestones = _milestones(raw, tasks, scale, read)
    axis = _axis(raw, scale, (tasks, milestones), read)
    today = _today(raw, scale, axis, read)
    _check_links(tasks, milestones, read)
    if not tasks:
        read.report("spec", "'tasks' must list at least one task")
    if read.problems:
        raise SpecError(read.problems)
    title, description = read.text(raw, "title", "spec"), read.text(raw, "desc", "spec")
    return GanttSpec(title, description, axis, today, tuple(tasks), tuple(milestones))


def _scale(raw: dict[str, Any], read: Reader) -> _Scale:
    """Choose how time is read: from ``periods`` if there are any, else from the first start."""
    periods = raw.get("periods")
    if periods is not None:
        names_ok = (
            isinstance(periods, list) and periods and all(isinstance(p, str) for p in periods)
        )
        if not names_ok:
            read.report("spec", "'periods' must be a non-empty list of names such as W1, W2")
            return _Scale(TimeMode.PERIODS, None, ())
        return _Scale(TimeMode.PERIODS, None, tuple(periods))
    dates = _written_dates(raw, read)
    if not dates:
        return _Scale(TimeMode.WEEKS, None, ())
    first = min(dates)
    axis_start = _read_date(raw.get("axis_start"), "axis_start", read) or first
    return _Scale(TimeMode.DATES, axis_start - timedelta(days=axis_start.weekday()), ())


def _written_dates(raw: dict[str, Any], read: Reader) -> list[date]:
    """Return every date written in the tasks and the milestones, to find the first one."""
    found = []
    items = [(item, key) for item in _objects(raw, "tasks") for key in ("start", "end")]
    items += [(item, "date") for item in _objects(raw, "milestones")]
    for item, key in items:
        if isinstance(item.get(key), str):
            parsed = _read_date(item[key], key, read)
            found += [parsed] if parsed else []
    return found


def _objects(raw: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Return the objects of a list field, leaving out what is not an object."""
    items = raw.get(key, [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _read_date(value: object, where: str, read: Reader) -> date | None:
    """Read an ISO date such as ``2026-03-02``, or report why it cannot be read."""
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        read.report(where, f"'{value}' is not a date; write it as 2026-03-02")
        return None


def _to_position(value: object, scale: _Scale, is_end: bool) -> float | None:
    """Turn a date or a number from a spec into a position in columns, or None if it is neither.

    Args:
        value: A date string, or a number.
        scale: How the spec reads time.
        is_end: Whether the value is the last day (or week) of a task, which is included.

    Returns:
        The position of the left edge of that day or week, or of its right edge for an end.
    """
    extra = 1 if is_end else 0
    if scale.mode is TimeMode.DATES and isinstance(value, str) and scale.axis_start:
        try:
            days = (date.fromisoformat(value) - scale.axis_start).days
        except ValueError:
            return None
        return (days + extra) / DAYS_PER_WEEK
    if not is_number(value) or scale.mode is TimeMode.DATES:
        return None
    if scale.mode is TimeMode.WEEKS:
        return float(value) - 1 + extra
    return float(value) + extra


def _span(item: dict[str, Any], scale: _Scale, place: tuple[str, Reader]) -> tuple[float, float]:
    """Read where a task starts and ends, from ``start`` and ``end`` or ``start`` and ``length``."""
    where, read = place
    start = _to_position(item.get("start"), scale, is_end=False)
    if start is None:
        read.report(where, f"'start' must be {_how_to_write(scale)}")
        return 0.0, 1.0
    if "end" in item:
        end = _to_position(item["end"], scale, is_end=True)
        if end is None:
            read.report(where, f"'end' must be {_how_to_write(scale)}")
            return start, start + 1
    else:
        length = item.get("length")
        if not is_number(length) or length <= 0:
            read.report(where, "needs an 'end' or a positive 'length'")
            return start, start + 1
        end = start + float(length)
    if end - start < TOLERANCE:
        read.report(where, "ends before it starts")
    return start, end


def _how_to_write(scale: _Scale) -> str:
    """Say how a start or an end is written in the way the spec reads time."""
    if scale.mode is TimeMode.DATES:
        return "a date such as 2026-03-02"
    if scale.mode is TimeMode.WEEKS:
        return "a week number from 1"
    return "a period number from 0"


def _tasks(
    raw: dict[str, Any], context: tuple[_Scale, dict[str, dict[str, object]]], read: Reader
) -> list[Task]:
    """Read the tasks, in the order written."""
    scale, pinned = context
    items = raw.get("tasks", [])
    if not isinstance(items, list):
        read.report("spec", "'tasks' must be a list")
        return []
    tasks = []
    for index, item in enumerate(items):
        where = f"tasks[{index}]"
        if not isinstance(item, dict):
            read.report(where, "must be an object")
            continue
        read.check_keys(item, TASK_KEYS, where)
        tasks.append(_task(item, index, (scale, pinned), (where, read)))
    return tasks


def _task(
    item: dict[str, Any],
    index: int,
    context: tuple[_Scale, dict[str, dict[str, object]]],
    place: tuple[str, Reader],
) -> Task:
    """Read one task."""
    scale, pinned = context
    where, read = place
    start, end = _span(item, scale, place)
    label = read.text(item, "label", where) or f"Task {index + 1}"
    owner = read.text(item, "owner", where)
    status, progress = _status(item, place)
    return Task(
        id=read.identifier(item, where) if "id" in item else f"task{index + 1}",
        label=label,
        start=start,
        end=end,
        owner=person_of(owner, pinned) if owner else None,
        group=read.text(item, "group", where),
        status=status,
        progress=progress,
        reason=read.text(item, "reason", where) or "",
        after=_after(item, place),
        is_critical=item.get("critical") is True,
    )


def _status(item: dict[str, Any], place: tuple[str, Reader]) -> tuple[Status, float]:
    """Read the status and the progress of a task; work out the status from the progress."""
    where, read = place
    progress = item.get("progress")
    if progress is not None and not (is_number(progress) and 0 <= progress <= 1):
        read.report(where, "'progress' must be a number from 0 to 1")
        progress = None
    declared = read.enum(Status, item, "status", where)
    status = declared or _status_from(progress)
    if status is Status.DONE:
        progress = 1.0
    if status is Status.BLOCKED and not item.get("reason"):
        read.report(where, "a blocked task needs a short 'reason'")
    return status, float(progress or 0.0)


def _status_from(progress: object) -> Status:
    """Work out a status from the progress alone: none is planned, all is done."""
    if not is_number(progress) or progress <= 0:
        return Status.PLANNED
    return Status.DONE if progress >= 1 else Status.IN_PROGRESS


def _after(item: dict[str, Any], place: tuple[str, Reader]) -> tuple[str, ...]:
    """Read ``after``: one id or a list of ids."""
    where, read = place
    value = item.get("after", [])
    ids = [value] if isinstance(value, str) else value
    if not (isinstance(ids, list) and all(isinstance(each, str) for each in ids)):
        read.report(where, "'after' must be an id or a list of ids")
        return ()
    return tuple(ids)


def _milestones(
    raw: dict[str, Any], tasks: list[Task], scale: _Scale, read: Reader
) -> list[Milestone]:
    """Read the milestones, each on the date it is written with, or at the end of its task."""
    items = raw.get("milestones", [])
    if not isinstance(items, list):
        read.report("spec", "'milestones' must be a list")
        return []
    ends = {task.id: task.end for task in tasks}
    found = []
    for index, item in enumerate(items):
        where = f"milestones[{index}]"
        if not isinstance(item, dict):
            read.report(where, "must be an object")
            continue
        read.check_keys(item, MILESTONE_KEYS, where)
        found.append(_milestone(item, index, (scale, ends), (where, read)))
    return found


def _milestone(
    item: dict[str, Any],
    index: int,
    context: tuple[_Scale, dict[str, float]],
    place: tuple[str, Reader],
) -> Milestone:
    """Read one milestone."""
    scale, ends = context
    where, read = place
    after = _after(item, place)
    return Milestone(
        id=read.identifier(item, where) if "id" in item else f"milestone{index + 1}",
        label=read.text(item, "label", where) or f"Milestone {index + 1}",
        at=_milestone_position(item, after, (scale, ends), place),
        group=read.text(item, "group", where),
        after=after,
    )


def _milestone_position(
    item: dict[str, Any],
    after: tuple[str, ...],
    context: tuple[_Scale, dict[str, float]],
    place: tuple[str, Reader],
) -> float:
    """Place a milestone: on its ``date``, at its ``at``, or at the end of what it follows."""
    scale, ends = context
    where, read = place
    if "date" in item:
        position = _to_position(item["date"], scale, is_end=False)
    elif "at" in item:
        position = float(item["at"]) if is_number(item["at"]) else None
    else:
        known = [ends[each] for each in after if each in ends]
        position = max(known) if known else None
    if position is None:
        read.report(where, "needs a 'date', an 'at' or an 'after' that names a task")
        return 0.0
    return position


def _axis(
    raw: dict[str, Any],
    scale: _Scale,
    items: tuple[list[Task], list[Milestone]],
    read: Reader,
) -> Axis:
    """Count the columns: the named periods, or as many weeks as the last item needs."""
    tasks, milestones = items
    last = max([task.end for task in tasks] + [each.at for each in milestones], default=1.0)
    if scale.mode is TimeMode.PERIODS:
        count = len(scale.periods)
        if last > count + TOLERANCE:
            read.report(
                "spec", f"something ends in period {math.ceil(last)}, but there are only {count}"
            )
        return Axis(scale.mode, count, None, scale.periods)
    wanted = raw.get("weeks", 0)
    if not is_number(wanted) or wanted < 0:
        read.report("spec", "'weeks' must be a number of weeks")
        wanted = 0
    count = max(math.ceil(last - TOLERANCE), int(wanted), 1)
    return Axis(scale.mode, count, scale.axis_start, ())


def _today(raw: dict[str, Any], scale: _Scale, axis: Axis, read: Reader) -> float | None:
    """Read ``today``: a date, or a position counted in columns from the left edge."""
    if "today" not in raw:
        return None
    value = raw["today"]
    if isinstance(value, str):
        position = _to_position(value, scale, is_end=False)
    else:
        position = float(value) if is_number(value) else None
    if position is None:
        read.report("today", f"must be {_how_to_write(scale)}")
        return None
    if not 0 <= position <= axis.count:
        read.report("today", "is outside the chart; leave it out or move it")
        return None
    return position


def _check_links(tasks: list[Task], milestones: list[Milestone], read: Reader) -> None:
    """Report an ``after`` that names nothing, or that points at something that ends later."""
    ends = {task.id: task.end for task in tasks}
    ends.update({each.id: each.at for each in milestones})
    starts = {task.id: task.start for task in tasks}
    starts.update({each.id: each.at for each in milestones})
    for item in (*tasks, *milestones):
        for name in item.after:
            if name not in ends:
                read.report(
                    f"'{item.id}'", f"'after' names '{name}', not a task{suggestion(name, ends)}"
                )
            elif starts[item.id] < ends[name] - TOLERANCE:
                read.report(f"'{item.id}'", f"starts before '{name}' ends")
