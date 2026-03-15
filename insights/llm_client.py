"""Provider-agnostic LLM client contract for narrative generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LLMClient(Protocol):
    """Provider-agnostic interface for narrative generation."""

    def generate_narrative(self, prompt_payload: dict[str, object]) -> str:
        """Generate narrative text from prompt payload."""


def _evidence_tokens(hotspot: dict[str, object]) -> list[str]:
    evidence = hotspot.get("evidence", [])
    if not isinstance(evidence, list):
        return []

    tokens: list[str] = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        value = item.get("value")
        if isinstance(kind, str) and isinstance(value, str):
            tokens.append(f"[{kind}:{value}]")
    return tokens


@dataclass(frozen=True)
class TemplateLLMClient:
    """Deterministic local narrative renderer for provider-neutral flows."""

    def generate_narrative(self, prompt_payload: dict[str, object]) -> str:
        hotspots = prompt_payload.get("hotspots", [])
        if not isinstance(hotspots, list):
            return ""

        lines: list[str] = []
        for hotspot in hotspots:
            if not isinstance(hotspot, dict):
                continue

            rank = hotspot.get("rank")
            file_path = hotspot.get("file_path")
            score = hotspot.get("score")
            citations = " ".join(_evidence_tokens(hotspot))
            line = f"Hotspot {rank}: {file_path} (score={score})"
            if citations:
                line = f"{line} {citations}"
            lines.append(line)
        return "\n".join(lines)


def get_llm_client() -> LLMClient:
    """Return default provider-neutral narrative client."""
    return TemplateLLMClient()
