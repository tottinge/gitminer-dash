"""Contract tests for common-pair intent pane rendering behavior."""

from __future__ import annotations

from copy import deepcopy

import pytest

from tests.dash_component_helpers import (
    find_component_by_id,
    walk_components,
)
from visualization.common_pair_intent_pane import (
    DRILLDOWN_HELPER_MESSAGE,
    build_common_pair_intent_pane,
)

BASE_PAYLOAD = {
    "pairing": "pages/strongest_pairings.py ↔ utils/git.py",
    "affinity": "0.58",
    "message_count": 5,
    "intent_counts": [
        {"intent": "fix", "count": 3},
        {"intent": "feat", "count": 2},
    ],
    "evidence_rows": [
        {
            "intent": "fix",
            "hash": "abc1111",
            "date": "2026-05-01",
            "message": "fix(pair): keep selected row sticky",
        },
        {
            "intent": "feat",
            "hash": "def2222",
            "date": "2026-05-02",
            "message": "feat(pair): add compact intent pane",
        },
        {
            "intent": "fix",
            "hash": "ghi3333",
            "date": "2026-05-03",
            "message": "fix(pair): stabilize drilldown evidence mapping",
        },
    ],
}

EXPECTED_FIX_DRILLDOWN_ROWS = [
    {
        "intent": "fix",
        "hash": "abc1111",
        "date": "2026-05-01",
        "message": "fix(pair): keep selected row sticky",
    },
    {
        "intent": "fix",
        "hash": "ghi3333",
        "date": "2026-05-03",
        "message": "fix(pair): stabilize drilldown evidence mapping",
    },
]

EXPECTED_DRILLDOWN_COLUMNS = [
    {"name": "Intent", "id": "intent"},
    {"name": "Hash", "id": "hash"},
    {"name": "Date", "id": "date"},
    {"name": "Message", "id": "message"},
]


def _payload_without(*removed_keys: str):
    payload = deepcopy(BASE_PAYLOAD)
    for key in removed_keys:
        payload.pop(key, None)
    return payload


def _as_list(children):
    if children is None:
        return []
    if isinstance(children, (list, tuple)):
        return list(children)
    return [children]


@pytest.mark.parametrize(
    (
        "payload",
        "focused_intent",
        "component_id_prefix",
        "expected_prefix",
        "expected_pairing",
        "expected_affinity_chip",
        "expected_intent_leader",
        "expected_leader_coverage",
        "expected_evidence_count",
        "expected_intent_chip_texts",
        "expected_preview_count",
        "expect_empty_preview_fallback",
        "expected_drilldown_summary",
        "expected_drilldown_data",
        "expect_non_empty_contract",
    ),
    [
        pytest.param(
            _payload_without(),
            "fix",
            "id-unit-common-pair",
            "id-unit-common-pair",
            "pages/strongest_pairings.py ↔ utils/git.py",
            "Affinity 0.58",
            "Intent leader fix",
            "Leader coverage 60%",
            "Evidence 5",
            ["fix 3 (60%)", "feat 2 (40%)"],
            2,
            False,
            "Drill down into 2 evidence row(s)",
            EXPECTED_FIX_DRILLDOWN_ROWS,
            True,
            id="canonical-values-hit-all-primary-lookups",
        ),
        pytest.param(
            _payload_without("message_count"),
            "fix",
            "id-unit-common-pair",
            "id-unit-common-pair",
            "pages/strongest_pairings.py ↔ utils/git.py",
            "Affinity 0.58",
            "Intent leader fix",
            "Leader coverage 0%",
            "Evidence 0",
            ["fix 3 (0%)", "feat 2 (0%)"],
            2,
            False,
            "Drill down into 2 evidence row(s)",
            EXPECTED_FIX_DRILLDOWN_ROWS,
            True,
            id="missing-message-count-uses-zero-fallback",
        ),
        pytest.param(
            _payload_without("intent_counts"),
            "fix",
            "id-unit-common-pair",
            "id-unit-common-pair",
            "pages/strongest_pairings.py ↔ utils/git.py",
            "Affinity 0.58",
            "Intent leader unknown",
            "Leader coverage 0%",
            "Evidence 5",
            ["No intent data available."],
            2,
            False,
            "Drill down into 2 evidence row(s)",
            EXPECTED_FIX_DRILLDOWN_ROWS,
            True,
            id="missing-intent-counts-uses-empty-list-fallback",
        ),
        pytest.param(
            _payload_without("evidence_rows"),
            "fix",
            "id-unit-common-pair",
            "id-unit-common-pair",
            "pages/strongest_pairings.py ↔ utils/git.py",
            "Affinity 0.58",
            "Intent leader fix",
            "Leader coverage 60%",
            "Evidence 5",
            ["fix 3 (60%)", "feat 2 (40%)"],
            1,
            True,
            "Drill down into 0 evidence row(s)",
            [],
            True,
            id="missing-evidence-rows-uses-empty-list-fallback",
        ),
        pytest.param(
            _payload_without("pairing", "affinity"),
            "fix",
            None,
            "id-common-pair-intent-pane",
            "",
            "Affinity n/a",
            "Intent leader fix",
            "Leader coverage 60%",
            "Evidence 5",
            ["fix 3 (60%)", "feat 2 (40%)"],
            2,
            False,
            "Drill down into 2 evidence row(s)",
            EXPECTED_FIX_DRILLDOWN_ROWS,
            True,
            id="default-prefix-and-pairing-affinity-fallbacks",
        ),
        pytest.param(
            None,
            None,
            None,
            "id-common-pair-intent-pane",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            False,
            id="empty-state-container-contract",
        ),
    ],
)
def test_build_common_pair_intent_pane_parameterized_contract(
    payload,
    focused_intent,
    component_id_prefix,
    expected_prefix,
    expected_pairing,
    expected_affinity_chip,
    expected_intent_leader,
    expected_leader_coverage,
    expected_evidence_count,
    expected_intent_chip_texts,
    expected_preview_count,
    expect_empty_preview_fallback,
    expected_drilldown_summary,
    expected_drilldown_data,
    expect_non_empty_contract,
):
    build_kwargs = {
        "payload": payload,
        "focused_intent": focused_intent,
    }
    if component_id_prefix is not None:
        build_kwargs["component_id_prefix"] = component_id_prefix

    pane = build_common_pair_intent_pane(**build_kwargs)

    container_id = f"{expected_prefix}-container"
    assert pane.id == container_id
    assert pane.style["border"] == "1px solid #d9dee8"

    title_nodes = [
        node
        for node in walk_components(pane)
        if node.__class__.__name__ == "H3"
    ]
    assert len(title_nodes) == 1
    assert title_nodes[0].children == "Pair Intent Snapshot"
    assert title_nodes[0].style == {"margin": "0 0 6px"}

    if not expect_non_empty_contract:
        empty_state_message = find_component_by_id(
            pane,
            f"{expected_prefix}-empty-state-message",
        )
        assert (
            empty_state_message.children
            == "Select a common pair to preview intent and supporting evidence."
        )
        assert empty_state_message.style["margin"] == "0"
        assert empty_state_message.style["color"] == "#64748b"
        return

    pairing_label = find_component_by_id(
        pane,
        f"{expected_prefix}-pairing",
    )
    assert pairing_label.children == expected_pairing
    assert pairing_label.style["fontWeight"] == "600"

    span_texts = [
        node.children
        for node in walk_components(pane)
        if node.__class__.__name__ == "Span" and isinstance(node.children, str)
    ]
    assert expected_affinity_chip in span_texts

    intent_leader_chip = find_component_by_id(
        pane,
        f"{expected_prefix}-summary-intent-leader",
    )
    leader_coverage_chip = find_component_by_id(
        pane,
        f"{expected_prefix}-summary-leader-coverage",
    )
    evidence_count_chip = find_component_by_id(
        pane,
        f"{expected_prefix}-summary-evidence-count",
    )
    assert intent_leader_chip.children == expected_intent_leader
    assert leader_coverage_chip.children == expected_leader_coverage
    assert evidence_count_chip.children == expected_evidence_count

    intent_chip_container = find_component_by_id(
        pane,
        f"{expected_prefix}-intent-chips",
    )
    intent_chip_nodes = _as_list(intent_chip_container.children)
    assert [
        chip.children for chip in intent_chip_nodes
    ] == expected_intent_chip_texts

    helper_copy_nodes = [
        node
        for node in walk_components(pane)
        if node.__class__.__name__ == "P"
        and node.children == DRILLDOWN_HELPER_MESSAGE
    ]
    assert len(helper_copy_nodes) == 1
    assert helper_copy_nodes[0].style["margin"] == "0 0 4px"
    assert helper_copy_nodes[0].style["color"] == "#64748b"

    evidence_preview = find_component_by_id(
        pane,
        f"{expected_prefix}-evidence-preview",
    )
    preview_rows = _as_list(evidence_preview.children)
    assert len(preview_rows) == expected_preview_count
    if expect_empty_preview_fallback:
        assert (
            preview_rows[0].children
            == "No evidence rows available for this focus."
        )

    drilldown_summary = find_component_by_id(
        pane,
        f"{expected_prefix}-drilldown-summary",
    )
    drilldown_table = find_component_by_id(
        pane,
        f"{expected_prefix}-drilldown-table",
    )
    assert drilldown_summary.children == expected_drilldown_summary
    assert drilldown_table.columns == EXPECTED_DRILLDOWN_COLUMNS
    assert drilldown_table.style_cell["textAlign"] == "left"
    assert drilldown_table.data == expected_drilldown_data
