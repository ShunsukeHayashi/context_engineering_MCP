#!/usr/bin/env python3
"""
Run a repeatable quality cycle for Context Engineering MCP.

The cycle validates runtime drift, syntax, and tests, then records the result
to Agent Skill Bus inside a hidden workspace so the repository stays clean.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from context_engineering.runtime_health import collect_runtime_health  # noqa: E402

SKILL_BUS_WORKSPACE = PROJECT_ROOT / ".agent-skill-bus-workspace"
REPORTS_DIR = SKILL_BUS_WORKSPACE / "reports"
LATEST_REPORT = REPORTS_DIR / "context-engineering-quality-latest.json"
TASK_DESCRIPTION = "Validate runtime canonical path, MCP syntax, and API test coverage"
PYTHON_EXECUTABLE = (
    PROJECT_ROOT / ".venv" / "bin" / "python"
    if (PROJECT_ROOT / ".venv" / "bin" / "python").exists()
    else Path(sys.executable)
)


def run_command(name: str, command: List[str], cwd: Path) -> Dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "name": name,
        "command": command,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def ensure_skill_bus_workspace() -> None:
    SKILL_BUS_WORKSPACE.mkdir(exist_ok=True)
    marker = SKILL_BUS_WORKSPACE / "skills" / "self-improving-skills" / "skill-runs.jsonl"
    if marker.exists():
        return

    init_result = run_command(
        "agent_skill_bus_init",
        ["npx", "agent-skill-bus", "init"],
        cwd=SKILL_BUS_WORKSPACE,
    )
    if not init_result["passed"]:
        raise RuntimeError(
            f"Agent Skill Bus init failed: {init_result['stderr'] or init_result['stdout']}"
        )


def record_skill_bus_run(result: str, score: float) -> Dict[str, Any]:
    ensure_skill_bus_workspace()
    record_result = run_command(
        "agent_skill_bus_record",
        [
            "npx",
            "agent-skill-bus",
            "record-run",
            "--agent",
            "codex",
            "--skill",
            "context-engineering-quality-cycle",
            "--task",
            TASK_DESCRIPTION,
            "--result",
            result,
            "--score",
            f"{score:.2f}",
        ],
        cwd=SKILL_BUS_WORKSPACE,
    )
    health_result = run_command(
        "agent_skill_bus_health",
        ["npx", "agent-skill-bus", "health"],
        cwd=SKILL_BUS_WORKSPACE,
    )
    return {"record": record_result, "health": health_result}


def calculate_runtime_score(status: str) -> float:
    if status == "ok":
        return 1.0
    if status == "warn":
        return 0.7
    return 0.0


def main() -> int:
    runtime_report = collect_runtime_health(repo_root=PROJECT_ROOT, expected_canonical_root=PROJECT_ROOT)
    command_results = [
        run_command(
            "mcp_server_syntax",
            ["node", "--check", "mcp-server/context_mcp_server.js"],
            cwd=PROJECT_ROOT,
        ),
        run_command(
            "pytest",
            [
                str(PYTHON_EXECUTABLE),
                "-m",
                "pytest",
                "-o",
                "addopts=--strict-markers --strict-config --verbose --tb=short",
                "tests/unit/test_runtime_health.py",
                "tests/unit/test_context_models.py",
                "tests/integration/test_context_api.py",
            ],
            cwd=PROJECT_ROOT,
        ),
    ]

    weighted_score = 0.0
    weighted_score += 0.4 * calculate_runtime_score(runtime_report["status"])
    weighted_score += 0.2 * (1.0 if command_results[0]["passed"] else 0.0)
    weighted_score += 0.4 * (1.0 if command_results[1]["passed"] else 0.0)

    if runtime_report["status"] == "fail" or weighted_score < 0.5:
        result = "fail"
    elif weighted_score < 0.85:
        result = "partial"
    else:
        result = "success"

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    skill_bus_results = record_skill_bus_run(result=result, score=weighted_score)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "result": result,
        "score": round(weighted_score, 2),
        "task": TASK_DESCRIPTION,
        "runtime_health": runtime_report,
        "checks": command_results,
        "agent_skill_bus": skill_bus_results,
    }
    LATEST_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if result != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
