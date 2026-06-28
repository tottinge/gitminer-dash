"""Shared commit presentation model for UI-facing algorithm outputs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CommitPresentation:
    """Normalized commit display payload for algorithm adapters."""

    short_hash: str
    timestamp: str
    actor: str
    message: str


def present_commit(
    commit: Any,
    *,
    timestamp_format: str,
    actor_attribute_name: str,
    message_selector: Callable[[Any], str] | None = None,
    max_message_length: int | None = 100,
) -> CommitPresentation:
    """Normalize commit metadata into a stable display model."""
    raw_hash = getattr(commit, "hexsha", "")
    short_hash = raw_hash[:7] if isinstance(raw_hash, str) else ""

    committed_datetime = getattr(commit, "committed_datetime", None)
    timestamp = (
        committed_datetime.strftime(timestamp_format)
        if committed_datetime is not None
        else ""
    )

    actor_object = getattr(commit, actor_attribute_name, None)
    actor = (
        getattr(actor_object, "name", "") if actor_object is not None else ""
    )

    if message_selector is None:
        raw_message = getattr(commit, "message", "") or ""
        first_line, _separator, _rest = raw_message.partition("\n")
    else:
        first_line = message_selector(commit) or ""

    message = (
        first_line[:max_message_length]
        if max_message_length is not None
        else first_line
    )

    return CommitPresentation(
        short_hash=short_hash,
        timestamp=timestamp,
        actor=actor,
        message=message,
    )
