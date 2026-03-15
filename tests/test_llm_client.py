"""Tests for `insights/llm_client.py`."""

from insights.llm_client import get_llm_client


def test_default_llm_client_renders_narrative_with_evidence_citations():
    prompt_payload = {
        "hotspots": [
            {
                "rank": 1,
                "file_path": "src/a.py",
                "score": 3.0,
                "evidence": [
                    {"kind": "file", "value": "src/a.py"},
                    {"kind": "metric", "value": "commit_count=3"},
                ],
            }
        ]
    }

    narrative = get_llm_client().generate_narrative(
        prompt_payload=prompt_payload
    )

    assert "Hotspot 1: src/a.py (score=3.0)" in narrative
    assert "[file:src/a.py]" in narrative
    assert "[metric:commit_count=3]" in narrative


def test_default_llm_client_output_is_deterministic_for_same_payload():
    prompt_payload = {
        "hotspots": [
            {
                "rank": 1,
                "file_path": "src/a.py",
                "score": 3.0,
                "evidence": [
                    {"kind": "file", "value": "src/a.py"},
                    {"kind": "metric", "value": "commit_count=3"},
                ],
            }
        ]
    }
    client = get_llm_client()

    first = client.generate_narrative(prompt_payload=prompt_payload)
    second = client.generate_narrative(prompt_payload=prompt_payload)

    assert first == second
