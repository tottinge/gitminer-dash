"""Focused helper-level tests for ai_insights mutation coverage."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tests import setup_path

setup_path()


class _Remote:
    def __init__(
        self,
        name: str,
        *,
        urls: list[object] | None = None,
        url: object = "",
    ) -> None:
        self.name = name
        self.urls = [] if urls is None else urls
        self.url = url


class _Repo:
    def __init__(self, remotes) -> None:
        self.remotes = remotes


class _RemoteWithoutName:
    def __init__(
        self, *, urls: list[object] | None = None, url: object = ""
    ) -> None:
        self.urls = [] if urls is None else urls
        self.url = url


class _RemoteWithoutUrls:
    def __init__(self, name: str, *, url: object = "") -> None:
        self.name = name
        self.url = url


class _RemoteWithoutUrl:
    def __init__(self, name: str, *, urls: list[object] | None = None) -> None:
        self.name = name
        self.urls = [] if urls is None else urls


def _hotspot(file_path: str, score: float, evidence) -> SimpleNamespace:
    return SimpleNamespace(file_path=file_path, score=score, evidence=evidence)


@patch("dash.register_page")
def test_extract_remote_url_variants(_):
    import pages.ai_insights as module

    assert module._extract_remote_url(SimpleNamespace(remotes=None)) == ""
    assert module._extract_remote_url(SimpleNamespace()) == ""
    assert (
        module._extract_remote_url(
            _Repo(
                remotes=[
                    _Remote("upstream", urls=["https://example.com/other.git"]),
                    _Remote(
                        "origin", urls=[123, "https://example.com/repo.git"]
                    ),
                ]
            )
        )
        == "https://example.com/repo.git"
    )
    assert (
        module._extract_remote_url(
            _Repo(remotes=[_Remote("origin", urls=[123], url="git@x:y/z.git")])
        )
        == "git@x:y/z.git"
    )
    assert (
        module._extract_remote_url(_Repo(remotes=[_Remote("upstream")])) == ""
    )
    assert (
        module._extract_remote_url(
            _Repo(
                remotes=[
                    _RemoteWithoutName(urls=[1, 2], url=""),
                    _Remote("origin", urls=["https://example.com/final.git"]),
                ]
            )
        )
        == "https://example.com/final.git"
    )
    assert (
        module._extract_remote_url(
            _Repo(
                remotes=[
                    _RemoteWithoutUrls("origin", url=""),
                ]
            )
        )
        == ""
    )
    assert (
        module._extract_remote_url(
            _Repo(
                remotes=[
                    _RemoteWithoutUrl("origin", urls=[1, 2]),
                ]
            )
        )
        == ""
    )
    assert (
        module._extract_remote_url(
            _Repo(
                remotes=[
                    _RemoteWithoutUrl("origin", urls=[1, 2]),
                    _Remote(
                        "origin", urls=["https://example.com/later-origin.git"]
                    ),
                ]
            )
        )
        == ""
    )


@patch("dash.register_page")
def test_repo_and_markdown_link_helpers(_):
    import pages.ai_insights as module

    https_repo = _Repo(
        remotes=[_Remote("origin", urls=["https://github.com/acme/repo.git"])]
    )
    ssh_repo = _Repo(
        remotes=[_Remote("origin", urls=["git@github.com:acme/repo.git"])]
    )
    no_origin_repo = _Repo(
        remotes=[_Remote("upstream", urls=["https://github.com/acme/repo.git"])]
    )

    assert (
        module._repo_web_base_url(https_repo) == "https://github.com/acme/repo"
    )
    assert module._repo_web_base_url(ssh_repo) == "https://github.com/acme/repo"
    assert module._repo_web_base_url(no_origin_repo) == ""
    assert (
        module._repo_web_base_url(
            _Repo(remotes=[_Remote("origin", urls=["invalid"])])
        )
        == ""
    )

    assert module._file_markdown_link("src/a.py", "") == "src/a.py"
    assert (
        module._file_markdown_link("src/a.py", "/repo")
        == "[`src/a.py`](file:///repo/src/a.py)"
    )
    assert (
        module._file_display_markdown_link("src/a.py", no_origin_repo)
        == "src/a.py"
    )
    assert (
        module._file_display_markdown_link("src/with space.py", https_repo)
        == "[src/with space.py](https://github.com/acme/repo/blob/HEAD/src/with%20space.py)"
    )
    assert (
        module._file_display_markdown_link("src/a/b.py", https_repo)
        == "[src/a/b.py](https://github.com/acme/repo/blob/HEAD/src/a/b.py)"
    )

    assert module._commit_markdown_link("", https_repo) == ""
    assert module._commit_markdown_link("abc1234", no_origin_repo) == "abc1234"
    assert (
        module._commit_markdown_link("abc1234", https_repo)
        == "[abc1234](https://github.com/acme/repo/commit/abc1234)"
    )


@patch("dash.register_page")
def test_parsers_and_normalizers(_):
    import pages.ai_insights as module

    evidence = [
        SimpleNamespace(kind="file", value="src/a.py"),
        SimpleNamespace(kind="metric", value="commit_count=12"),
    ]
    assert (
        module._evidence_value(_hotspot("src/a.py", 1.0, evidence), "metric")
        == "commit_count=12"
    )
    assert (
        module._evidence_value(_hotspot("src/a.py", 1.0, evidence), "missing")
        == ""
    )

    assert module._parse_commit_count("commit_count=12") == 12
    assert module._parse_commit_count("commit_count=0") == 0
    assert module._parse_commit_count("count=12") == 0
    assert module._parse_commit_count("commit_count=-1") == 0

    assert module._normalize_top_n(None) == 10
    assert module._normalize_top_n(0) == 10
    assert module._normalize_top_n(-5) == 10
    assert module._normalize_top_n(1) == 1
    assert module._normalize_top_n(7) == 7

    assert module._normalize_min_score(None) == 0.0
    assert module._normalize_min_score(-1) == 0.0
    assert module._normalize_min_score(2) == 2.0
    assert module._normalize_min_score(2.5) == 2.5


@patch("dash.register_page")
def test_filter_reason_and_action_helpers(_):
    import pages.ai_insights as module

    assert module._is_config_or_lock_path("a.toml")
    assert module._is_config_or_lock_path("a.lock")
    assert module._is_config_or_lock_path("a.yaml")
    assert module._is_config_or_lock_path("a.yml")
    assert module._is_config_or_lock_path("a.ini")
    assert module._is_config_or_lock_path("a.cfg")
    assert not module._is_config_or_lock_path("src/a.py")

    assert not module._passes_filters("src/a.py", 4.0, 5.0, [])
    assert module._passes_filters("src/a.py", 5.0, 5.0, [])
    assert not module._passes_filters(
        "a.toml", 10.0, 0.0, [module.FILTER_EXCLUDE_CONFIG]
    )
    assert not module._passes_filters(
        "tests/test_a.py", 10.0, 0.0, [module.FILTER_EXCLUDE_TESTS]
    )
    assert module._passes_filters(
        "src/a.py", 10.0, 0.0, [module.FILTER_EXCLUDE_TESTS]
    )

    assert module._risk_reason("src/a.py", 10.0, 0) == "elevated_score"
    assert module._risk_reason("src/a.py", 1.0, 0) == ""
    assert "high_churn" in module._risk_reason("src/a.py", 5.0, 20)
    assert "ui_orchestration_surface" in module._risk_reason(
        "pages/a.py", 5.0, 1
    )
    assert (
        module._risk_reason("visualization/a.py", 5.0, 1)
        == "visualization_logic_surface"
    )
    assert (
        module._risk_reason("a.toml", 5.0, 1)
        == "dependency_or_config_touchpoint"
    )
    assert (
        module._risk_reason("a.lock", 5.0, 1)
        == "dependency_or_config_touchpoint"
    )

    assert (
        module._suggested_action("a.toml", 25.0, 25)
        == "tighten_dependency_workflow"
    )
    assert (
        module._suggested_action("pages/a.py", 25.0, 25)
        == "extract_service_boundary"
    )
    assert (
        module._suggested_action("pages/a.py", 10.0, 20)
        == "extract_service_boundary"
    )
    assert (
        module._suggested_action("visualization/a.py", 10.0, 5)
        == "split_layout_and_rendering"
    )
    assert (
        module._suggested_action("src/a.py", 10.0, 25)
        == "reduce_change_surface_with_helpers"
    )
    assert module._suggested_action("src/a.py", 1.0, 1) == "monitor_next_period"


@patch("dash.register_page")
def test_period_trend_and_row_helpers(_):
    import pages.ai_insights as module

    begin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = begin + timedelta(days=30)
    previous_begin, previous_end = module._previous_period_bounds(begin, end)
    assert previous_end == begin
    assert previous_end - previous_begin == end - begin

    assert module._trend_bucket(2.0, 0.0) == "new"
    assert module._trend_bucket(0.0, 0.0) == "stable"
    assert module._trend_bucket(1.0, 0.0) == "new"
    assert module._trend_bucket(2.6, 2.0) == "rising"
    assert module._trend_bucket(2.5, 2.0) == "stable"
    assert module._trend_bucket(1.4, 2.0) == "falling"
    assert module._trend_bucket(1.5, 2.0) == "stable"
    assert module._trend_bucket(2.4, 2.0) == "stable"

    repo = _Repo(
        remotes=[_Remote("origin", urls=["https://github.com/acme/repo.git"])]
    )
    evidence = [
        SimpleNamespace(kind="file", value="pages/a.py"),
        SimpleNamespace(kind="metric", value="commit_count=21"),
        SimpleNamespace(kind="commit", value="abc1234"),
    ]
    row = module._row(
        rank=2,
        hotspot=_hotspot("pages/a.py", 9.9, evidence),
        repo=repo,
        repo_path="/repo",
        previous_scores={"pages/a.py": 7.0},
    )
    assert row["rank"] == 2
    assert row["file_path"] == "pages/a.py"
    assert row["score"] == 9.9
    assert row["score_delta"] == 2.9
    assert row["trend"] == "rising"
    assert row["commit_count"] == 21
    assert row["risk_reason"] == "high_churn, ui_orchestration_surface"
    assert row["suggested_action"] == "extract_service_boundary"
    assert (
        row["evidence_refs"]
        == "file:pages/a.py | metric:commit_count=21 | commit:abc1234"
    )
    assert (
        "github.com/acme/repo/blob/HEAD/pages/a.py" in row["file_display_link"]
    )
    assert "github.com/acme/repo/commit/abc1234" in row["latest_commit_link"]

    precision_row = module._row(
        rank=1,
        hotspot=_hotspot(
            "src/precision.py",
            1.2344,
            [
                SimpleNamespace(kind="metric", value="commit_count=1"),
                SimpleNamespace(kind="commit", value="p123"),
            ],
        ),
        repo=repo,
        repo_path="/repo",
        previous_scores={"src/precision.py": 1.115},
    )
    assert precision_row["score"] == 1.23
    assert precision_row["score_delta"] == 0.12


@patch("dash.register_page")
def test_claim_and_evidence_row_helpers(_):
    import pages.ai_insights as module

    assert module._invalid_claim_row(
        {
            "line": 7,
            "reason": "unknown_citation",
            "claim": "something",
            "unknown_citations": ["a", "b"],
        }
    ) == {
        "line": 7,
        "reason": "unknown_citation",
        "claim": "something",
        "unknown_citations": "a | b",
    }
    assert (
        module._invalid_claim_row(
            {
                "line": 8,
                "reason": "missing_citation",
                "claim": "other",
                "unknown_citations": "n/a",
            }
        )["unknown_citations"]
        == ""
    )
    assert (
        module._invalid_claim_row(
            {
                "line": 9,
                "reason": "missing_citation",
                "claim": "no-citations-key",
            }
        )["unknown_citations"]
        == ""
    )

    assert module._evidence_rows_from_refs("") == []
    assert module._evidence_rows_from_refs(
        "file:src/a.py | metric:commit_count=2 | malformed"
    ) == [
        {"kind": "file", "value": "src/a.py"},
        {"kind": "metric", "value": "commit_count=2"},
        {"kind": "malformed", "value": ""},
    ]
    assert module._evidence_rows_from_refs("metric:key:subvalue") == [
        {"kind": "metric", "value": "key:subvalue"}
    ]


@patch("dash.register_page")
def test_strict_narrative_result_invokes_dependencies(_):
    import pages.ai_insights as module

    report = MagicMock()
    prompt_payload = {"prompt": "payload"}
    narrative_text = "narrative [file:src/a.py]"
    llm_client = MagicMock()
    llm_client.generate_narrative.return_value = narrative_text
    with (
        patch.object(
            module, "build_prompt_payload", return_value=prompt_payload
        ) as mock_prompt,
        patch.object(module, "get_llm_client", return_value=llm_client),
        patch.object(
            module,
            "validate_narrative_citations",
            return_value={
                "passed": False,
                "invalid_claims": [
                    {
                        "line": 1,
                        "reason": "missing_citation",
                        "claim": "x",
                        "unknown_citations": [],
                    }
                ],
            },
        ) as mock_validate,
    ):
        result = module._strict_narrative_result(report)

    mock_prompt.assert_called_once_with(report=report)
    llm_client.generate_narrative.assert_called_once_with(
        prompt_payload=prompt_payload
    )
    mock_validate.assert_called_once_with(
        report=report, narrative_text=narrative_text
    )
    assert result["passed"] is False
    assert result["narrative_text"] == ""
    assert result["invalid_claims"] == [
        {
            "line": 1,
            "reason": "missing_citation",
            "claim": "x",
            "unknown_citations": "",
        }
    ]
