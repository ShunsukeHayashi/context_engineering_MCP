#!/usr/bin/env python3
"""
CLI entrypoint for Context Engineering runtime health checks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from context_engineering.runtime_health import (  # noqa: E402
    DEFAULT_CODEX_CONFIG_PATH,
    collect_runtime_health,
    format_runtime_health_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Context Engineering runtime health.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Exit non-zero on warnings as well as failures.",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=DEFAULT_CODEX_CONFIG_PATH,
        help="Path to Codex config.toml.",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="Override API base URL (defaults to CONTEXT_API_URL or http://127.0.0.1:9003).",
    )
    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Expected canonical repository root.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = collect_runtime_health(
        repo_root=PROJECT_ROOT,
        config_path=args.config_path,
        api_url=args.api_url,
        expected_canonical_root=args.canonical_root,
    )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print(format_runtime_health_report(report))

    if report["status"] == "fail":
        return 1
    if args.strict_warnings and report["status"] == "warn":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
