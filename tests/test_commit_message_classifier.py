"""Tests for algorithms.commit_message_classifier."""

from algorithms.commit_message_classifier import (
    classify_commit_message,
    classify_commit_messages,
)


def test_classify_commit_message_returns_unknown_without_fallback_signal():
    assert classify_commit_message("this is not conventional") == "unknown"


def test_classify_commit_message_fallback_detects_docs_intent():
    message = "New docs using hugo and hextra (#6474)"
    assert classify_commit_message(message) == "docs"


def test_classify_commit_message_fallback_detects_refactor_intent():
    message = "[NSim] move top level inputs to the correct position (#15469)"
    assert classify_commit_message(message) == "refactor"


def test_classify_commit_message_fallback_detects_debug_as_fix():
    message = "[OB] Print info about symbolic Jacobian (#15068)"
    assert classify_commit_message(message) == "fix"


def test_classify_commit_message_uses_first_line_for_multiline_messages():
    message = "refactor(parser)!: replace parser API\n\nBody details"
    assert classify_commit_message(message) == "refactor"


def test_classify_commit_messages_returns_empty_contract_for_empty_input():
    result = classify_commit_messages([])

    assert result == {
        "message_count": 0,
        "intent_counts": [],
        "classifications": [],
    }


def test_classify_commit_messages_aggregates_counts_and_preserves_order():
    messages = [
        "feat(ui): add card",
        "FIX: patch crash",
        "Update OSMC-PL 1.8 License headers for OMCompiler/Compiler",
    ]

    result = classify_commit_messages(messages)

    assert result["message_count"] == 3
    assert result["intent_counts"] == [
        {"intent": "chore", "count": 1},
        {"intent": "feat", "count": 1},
        {"intent": "fix", "count": 1},
    ]
    assert result["classifications"] == [
        {"message": "feat(ui): add card", "intent": "feat"},
        {"message": "FIX: patch crash", "intent": "fix"},
        {
            "message": "Update OSMC-PL 1.8 License headers for OMCompiler/Compiler",
            "intent": "chore",
        },
    ]


def test_classify_commit_messages_sorts_tied_intent_counts_by_intent_name():
    messages = [
        "feat(api): add endpoint",
        "chore: update lockfile",
        "feat(ui): add button",
        "docs: update guide",
    ]

    result = classify_commit_messages(messages)

    assert result["intent_counts"] == [
        {"intent": "feat", "count": 2},
        {"intent": "chore", "count": 1},
        {"intent": "docs", "count": 1},
    ]


def test_classify_commit_messages_openmodelica_mock_payload_refines_intents():
    messages = [
        "Util.isSome/isNone do not exist (#15567)\n\nThey were removed for the builtin some time ago.",
        "Replace equations with algorithms in MetaModelica (#15502)",
        "Replace equations with algorithms in MetaModelica (#15468)",
        (
            "Update OSMC-PL 1.8 License headers for OMCompiler/Compiler (#15398)\n\n"
            "* CI: Add Python and .tpl file support to license checker\n"
            "- Add OSMC-PL 1.8 header templates for Python files\n"
            "- Fix all --fix-license branches to handle Python files\n"
            "- Add _replace_license_header() dispatcher to route by file type\n"
        ),
        "[OB] Print info about symbolic Jacobian (#15068)\n\n",
    ]

    result = classify_commit_messages(messages)

    assert result["message_count"] == 5
    assert result["intent_counts"] == [
        {"intent": "refactor", "count": 2},
        {"intent": "feat", "count": 1},
        {"intent": "fix", "count": 1},
        {"intent": "unknown", "count": 1},
    ]
    assert result["classifications"] == [
        {
            "message": "Util.isSome/isNone do not exist (#15567)\n\nThey were removed for the builtin some time ago.",
            "intent": "unknown",
        },
        {
            "message": "Replace equations with algorithms in MetaModelica (#15502)",
            "intent": "refactor",
        },
        {
            "message": "Replace equations with algorithms in MetaModelica (#15468)",
            "intent": "refactor",
        },
        {
            "message": (
                "Update OSMC-PL 1.8 License headers for OMCompiler/Compiler (#15398)\n\n"
                "* CI: Add Python and .tpl file support to license checker\n"
                "- Add OSMC-PL 1.8 header templates for Python files\n"
                "- Fix all --fix-license branches to handle Python files\n"
                "- Add _replace_license_header() dispatcher to route by file type\n"
            ),
            "intent": "feat",
        },
        {
            "message": "[OB] Print info about symbolic Jacobian (#15068)\n\n",
            "intent": "fix",
        },
    ]
