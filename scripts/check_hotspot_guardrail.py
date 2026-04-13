#!/usr/bin/env python3
"""Check hotspot and bridge-metric regression guardrails."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fail when a target file sustains top hotspot rank while "
            "its bridge score rises across rolling windows."
        )
    )
    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Path to git repository (default: current directory).",
    )
    parser.add_argument(
        "--file-path",
        default="visualization/network_graph.py",
        help="Target file path to monitor.",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=90,
        help="Rolling window length in days (default: 90).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=500,
        help="Top-N rows to include in report scans (default: 500).",
    )
    parser.add_argument(
        "--hotspot-rank-threshold",
        type=int,
        default=1,
        help="Maximum hotspot rank considered top-tier (default: 1).",
    )
    parser.add_argument(
        "--min-bridge-score-increase",
        type=float,
        default=0.1,
        help="Minimum bridge score increase to treat as regression.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    from insights.hotspot_guardrail import evaluate_hotspot_guardrail

    parser = _parser()
    args = parser.parse_args(argv)
    result = evaluate_hotspot_guardrail(
        repo_path=args.repo,
        file_path=args.file_path,
        window_days=args.window_days,
        top_n=args.top,
        hotspot_rank_threshold=args.hotspot_rank_threshold,
        min_bridge_score_increase=args.min_bridge_score_increase,
    )
    print(json.dumps(result.to_dict(), indent=2))
    if result.regression_detected:
        print(
            "Guardrail failed: sustained top hotspot rank with rising "
            "bridge score."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
