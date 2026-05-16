"""Commit message classification helpers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from re import Pattern, compile
from typing import TypedDict

from algorithms.conventional_commits import (
    conventional_commit_match_pattern,
    normalize_intent,
)

SUMMARY_LINE_PRIORITY_PATTERNS: tuple[
    tuple[str, Pattern[str]],
    ...,
] = (
    (
        "revert",
        compile(r"\b(revert|rollback|rolled back|backout|back out)\b"),
    ),
    (
        "merge",
        compile(r"\b(merge|pull request|cherry-pick)\b"),
    ),
    (
        "fix",
        compile(
            r"\b("
            r"fix|fixed|fixes|bug|bugs|hotfix|repair|resolve|resolved|"
            r"escape(?:d|s|ing)?\s+(?:quotes?|regex(?:es)?|regular expressions?)|"
            r"debug|diagnostic|print info|instrument|logging|"
            r"regression|patch"
            r")\b"
        ),
    ),
    (
        "ci",
        compile(r"\b(ci|pipeline|workflow|github actions|buildkite|jenkins)\b"),
    ),
)

FULL_MESSAGE_FEATURE_PATTERN = compile(
    r"\b("
    r"add|adds|added|implement|implements|implemented|"
    r"introduce|introduces|introduced|support|supports|"
    r"supported|enable|enabled"
    r")\b"
)

SUMMARY_LINE_SECONDARY_PATTERNS: tuple[
    tuple[str, Pattern[str]],
    ...,
] = (
    (
        "docs",
        compile(r"\b(doc|docs|documentation|readme|changelog|guide|manual)\b"),
    ),
    (
        "test",
        compile(r"\b(test|tests|testing|spec|specs|assert|coverage)\b"),
    ),
    (
        "perf",
        compile(
            r"\b("
            r"perf|performance|optimi[sz]e|speed|faster|latency|"
            r"throughput|benchmark"
            r")\b"
        ),
    ),
    (
        "refactor",
        compile(
            r"\b("
            r"refactor|cleanup|clean-up|restructure|reorganize|rename|"
            r"extract|simplify|split|dedup|deduplicate|convert|replace|move|"
            r"migrate"
            r")\b"
        ),
    ),
    (
        "chore",
        compile(r"\b(chore|maintenance|housekeeping|license|headers?)\b"),
    ),
    (
        "build",
        compile(
            r"\b("
            r"build|cmake|makefile|compile|compiler|linker|deps?|"
            r"dependency|dependencies|bump|upgrade|downgrade|release"
            r")\b"
        ),
    ),
    (
        "style",
        compile(r"\b(format|formatting|lint|whitespace|typo)\b"),
    ),
)


class IntentCount(TypedDict):
    """Intent aggregate row."""

    intent: str
    count: int


class MessageClassification(TypedDict):
    """Classification for one message."""

    message: str
    intent: str


class CommitMessageClassificationResult(TypedDict):
    """Stable, serialization-friendly classification payload."""

    message_count: int
    intent_counts: list[IntentCount]
    classifications: list[MessageClassification]


def _fallback_non_conventional_intent(
    summary_line: str, message_text: str
) -> str:
    lower_summary_line = summary_line.lower()
    for intent, pattern in SUMMARY_LINE_PRIORITY_PATTERNS:
        if pattern.search(lower_summary_line):
            return intent

    lower_message_text = message_text.lower()
    if FULL_MESSAGE_FEATURE_PATTERN.search(lower_message_text):
        return "feat"

    for intent, pattern in SUMMARY_LINE_SECONDARY_PATTERNS:
        if pattern.search(lower_summary_line):
            return intent
    return "unknown"


def classify_commit_message(message: str) -> str:
    """Classify one commit message into a normalized intent."""
    summary_line = message.splitlines()[0].strip() if message else ""
    if not summary_line:
        return "unknown"

    matched_prefix = conventional_commit_match_pattern.match(summary_line)
    if matched_prefix:
        return normalize_intent(matched_prefix.group(1))

    return _fallback_non_conventional_intent(summary_line, message)


def classify_commit_messages(
    messages: Iterable[str],
) -> CommitMessageClassificationResult:
    """Classify commit messages and produce deterministic aggregate output."""
    classifications: list[MessageClassification] = []

    for message in messages:
        normalized_message = str(message)
        classifications.append(
            {
                "message": normalized_message,
                "intent": classify_commit_message(normalized_message),
            }
        )

    intent_counter = Counter(
        row["intent"] for row in classifications if row["intent"]
    )
    intent_counts: list[IntentCount] = [
        {"intent": intent, "count": count}
        for intent, count in sorted(
            intent_counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]

    return {
        "message_count": len(classifications),
        "intent_counts": intent_counts,
        "classifications": classifications,
    }
