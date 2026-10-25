"""Shared checks for reading JSON documents (scenes and specs) while collecting every problem."""

from collections.abc import Collection
from difflib import get_close_matches
from enum import StrEnum
from typing import Any, TypeVar

from .model import Point

Member = TypeVar("Member", bound=StrEnum)

POINT_LENGTH = 2


class SpecError(ValueError):
    """A spec is not valid. The message lists every problem found, one per line."""

    def __init__(self, problems: list[str]) -> None:
        """Keep the problems and join them into the message.

        Args:
            problems: One sentence per problem, each starting with where it was found.
        """
        self.problems = problems
        super().__init__("\n".join(problems))


def suggestion(name: object, candidates: Collection[str]) -> str:
    """Return a hint such as ``; did you mean 'pay'?`` for a mistyped id, or an empty string.

    Args:
        name: The id that was written.
        candidates: The ids that exist.

    Returns:
        The hint to append to a message, or an empty string when nothing is close.
    """
    if not isinstance(name, str):
        return ""
    close = get_close_matches(name, list(candidates), n=1)
    return f"; did you mean '{close[0]}'?" if close else ""


def is_number(value: object) -> bool:
    """Tell whether a JSON value is a number; ``True`` and ``False`` are not."""
    return isinstance(value, int | float) and not isinstance(value, bool)


class Reader:
    """Reads fields of a JSON document and records each problem instead of stopping at one."""

    def __init__(self) -> None:
        """Start with no problems and no ids seen."""
        self.problems: list[str] = []
        self._seen_ids: set[str] = set()

    def report(self, where: str, message: str) -> None:
        """Record one problem.

        Args:
            where: The location, such as ``nodes[2]``.
            message: What is wrong.
        """
        self.problems.append(f"{where}: {message}")

    def check_keys(self, raw: dict[str, Any], allowed: set[str], where: str) -> None:
        """Report every key of ``raw`` that is not in ``allowed``."""
        for key in sorted(set(raw) - allowed):
            self.report(where, f"unknown field '{key}'")

    def identifier(self, raw: dict[str, Any], where: str) -> str:
        """Read an id, which must be a non-empty string used only once.

        Returns:
            The id, or an empty string when it is missing or not a string.
        """
        ident = raw.get("id")
        if not isinstance(ident, str) or not ident:
            self.report(where, "'id' must be a non-empty string")
            return ""
        if ident in self._seen_ids:
            self.report(where, f"id '{ident}' is used twice")
        self._seen_ids.add(ident)
        return ident

    def number(self, raw: dict[str, Any], key: str, where: str) -> float:
        """Read a number field, reporting a problem when it is missing or not a number."""
        value = raw.get(key)
        if is_number(value):
            return value
        self.report(where, f"'{key}' must be a number")
        return 0

    def extent(self, raw: dict[str, Any], key: str, where: str) -> float:
        """Read a width or a height, which must be a positive number."""
        value = self.number(raw, key, where)
        if is_number(raw.get(key)) and value <= 0:
            self.report(where, f"'{key}' must be positive")
        return value

    def text(self, raw: dict[str, Any], key: str, where: str) -> str | None:
        """Read an optional string field.

        Returns:
            The string, or None when the field is absent or not a string (a problem is
            reported for the second case).
        """
        value = raw.get(key)
        if value is not None and not isinstance(value, str):
            self.report(where, f"'{key}' must be a string")
            return None
        return value

    def enum(
        self, enum_type: type[Member], raw: dict[str, Any], key: str, where: str
    ) -> Member | None:
        """Read a field that must be a member of an enum.

        Args:
            enum_type: The enum that lists the allowed values.
            raw: The object that holds the field.
            key: The field name.
            where: Where the object is, for the message.

        Returns:
            The member, or None when the field is absent or not a member (a problem is
            reported for the second case).
        """
        if key not in raw:
            return None
        try:
            return enum_type(raw[key])
        except ValueError:
            allowed = ", ".join(member.value for member in enum_type)
            self.report(where, f"unknown {key} '{raw[key]}'; use one of: {allowed}")
            return None

    def point(self, raw: object, where: str) -> Point | None:
        """Read an ``[x, y]`` pair, or report a problem."""
        if isinstance(raw, list) and len(raw) == POINT_LENGTH and all(map(is_number, raw)):
            return raw[0], raw[1]
        self.report(where, "must be a pair [x, y] of numbers")
        return None
