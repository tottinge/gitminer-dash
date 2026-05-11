#!/usr/bin/env python3
"""Run mutmut while disabling setproctitle in forked workers.

On some macOS setups, calling setproctitle in mutmut child processes can
produce intermittent worker crashes (exit code -11). This wrapper keeps mutmut's
normal behavior but replaces setproctitle with a no-op to stabilize signals.
"""

from __future__ import annotations

import argparse

import mutmut.__main__ as mutmut_main


def _noop_setproctitle(*_args, **_kwargs) -> None:
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run mutmut with setproctitle disabled in workers."
    )
    parser.add_argument(
        "--max-children",
        type=int,
        default=None,
        help="Maximum number of child workers (defaults to mutmut default).",
    )
    parser.add_argument(
        "mutant_names",
        nargs="*",
        help="Optional specific mutant names to run.",
    )
    args = parser.parse_args()

    mutmut_main.setproctitle = _noop_setproctitle
    mutmut_main._run(args.mutant_names, args.max_children)


if __name__ == "__main__":
    main()
