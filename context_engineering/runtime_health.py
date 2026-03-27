"""
Runtime health checks for Context Engineering MCP.

This module validates the active repository path, Codex MCP configuration,
and API health so runtime drift is detected before it affects planning quality.
"""

from __future__ import annotations

import json
import os
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CODEX_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
DEFAULT_API_URL = "http://127.0.0.1:9003"


def resolve_repo_root(repo_root: Optional[Path] = None) -> Path:
    """Resolve the canonical repository root for this package."""
    if repo_root is not None:
        return repo_root.expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def load_codex_context_engineering_config(
    config_path: Path = DEFAULT_CODEX_CONFIG_PATH,
) -> Dict[str, Any]:
    """Read the context_engineering MCP section from Codex config."""
    expanded_path = config_path.expanduser()
    if not expanded_path.exists():
        return {
            "status": "warn",
            "exists": False,
            "configured": False,
            "path": str(expanded_path),
            "message": "Codex config file was not found.",
        }

    try:
        data = tomllib.loads(expanded_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        return {
            "status": "fail",
            "exists": True,
            "configured": False,
            "path": str(expanded_path),
            "message": f"Codex config could not be parsed: {exc}",
        }

    section = (data.get("mcp_servers") or {}).get("context_engineering")
    if not section:
        return {
            "status": "warn",
            "exists": True,
            "configured": False,
            "path": str(expanded_path),
            "message": "context_engineering MCP server is not configured in Codex config.",
        }

    return {
        "status": "ok",
        "exists": True,
        "configured": True,
        "path": str(expanded_path),
        "command": section.get("command"),
        "args": section.get("args") or [],
        "working_directory": section.get("working_directory"),
    }


def fetch_api_health(api_url: str = DEFAULT_API_URL, timeout: float = 5.0) -> Dict[str, Any]:
    """Fetch the Context Engineering API health endpoint."""
    health_url = f"{api_url.rstrip('/')}/api/health"
    try:
        with urllib.request.urlopen(health_url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return {
            "status": "fail",
            "url": health_url,
            "message": f"API health request failed: {exc}",
        }
    except json.JSONDecodeError as exc:
        return {
            "status": "fail",
            "url": health_url,
            "message": f"API health response was not valid JSON: {exc}",
        }

    api_status = payload.get("status")
    return {
        "status": "ok" if api_status == "healthy" else "fail",
        "url": health_url,
        "payload": payload,
        "message": "API is healthy." if api_status == "healthy" else "API did not report healthy status.",
    }


def collect_runtime_health(
    repo_root: Optional[Path] = None,
    config_path: Path = DEFAULT_CODEX_CONFIG_PATH,
    api_url: Optional[str] = None,
    expected_canonical_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Collect runtime health across repository path, Codex config, and API."""
    resolved_repo_root = resolve_repo_root(repo_root)
    configured_api_url = api_url or os.getenv("CONTEXT_API_URL") or DEFAULT_API_URL
    canonical_root = resolve_repo_root(
        expected_canonical_root
        or Path(os.getenv("CONTEXT_ENGINEERING_CANONICAL_PATH", str(resolved_repo_root)))
    )

    checks: Dict[str, Dict[str, Any]] = {}
    issues = []
    recommendations = []

    repo_ok = resolved_repo_root == canonical_root
    checks["repo_path"] = {
        "status": "ok" if repo_ok else "fail",
        "expected": str(canonical_root),
        "actual": str(resolved_repo_root),
        "message": "Repository path matches canonical runtime path."
        if repo_ok
        else "Repository path does not match canonical runtime path.",
    }
    if not repo_ok:
        issues.append("Repository path drift detected.")
        recommendations.append("Use the canonical platform/_mcp/context_engineering_MCP path.")

    config_report = load_codex_context_engineering_config(config_path)
    expected_script_path = canonical_root / "mcp-server" / "context_mcp_server.js"
    config_status = config_report["status"]

    if config_report.get("configured"):
        working_directory = config_report.get("working_directory")
        args = config_report.get("args") or []
        script_path = args[0] if args else None

        resolved_workdir = (
            Path(working_directory).expanduser().resolve()
            if working_directory
            else None
        )
        resolved_script = (
            Path(script_path).expanduser().resolve()
            if script_path
            else None
        )

        if resolved_workdir != canonical_root or resolved_script != expected_script_path:
            config_status = "fail"
            config_report["message"] = "Codex config points to a non-canonical runtime path."
            issues.append("Codex MCP config drift detected.")
            recommendations.append("Update ~/.codex/config.toml to use the canonical platform path.")
        else:
            config_report["message"] = "Codex config matches canonical runtime path."

        config_report["expected_working_directory"] = str(canonical_root)
        config_report["actual_working_directory"] = str(resolved_workdir) if resolved_workdir else None
        config_report["expected_script_path"] = str(expected_script_path)
        config_report["actual_script_path"] = str(resolved_script) if resolved_script else None

    if config_status == "warn":
        recommendations.append("Configure the context_engineering MCP server in ~/.codex/config.toml.")
    elif config_status == "fail" and not config_report.get("message"):
        config_report["message"] = "Codex config validation failed."

    checks["codex_config"] = {
        **config_report,
        "status": config_status,
    }

    api_report = fetch_api_health(configured_api_url)
    checks["api_health"] = api_report
    if api_report["status"] != "ok":
        issues.append("Context Engineering API is not healthy.")
        recommendations.append("Restart the API server and confirm /api/health returns status=healthy.")

    overall_status = "ok"
    if any(check["status"] == "fail" for check in checks.values()):
        overall_status = "fail"
    elif any(check["status"] == "warn" for check in checks.values()):
        overall_status = "warn"

    return {
        "status": overall_status,
        "canonical_root": str(canonical_root),
        "repo_root": str(resolved_repo_root),
        "checks": checks,
        "issues": issues,
        "recommendations": recommendations,
    }


def format_runtime_health_report(report: Dict[str, Any]) -> str:
    """Render a readable runtime health summary."""
    lines = [
        f"Runtime health: {report['status']}",
        f"Canonical root: {report['canonical_root']}",
        f"Repo root: {report['repo_root']}",
        "",
    ]

    for name, check in report["checks"].items():
        lines.append(f"[{check['status']}] {name}: {check.get('message', '')}".strip())

    if report["issues"]:
        lines.extend(["", "Issues:"])
        lines.extend(f"- {issue}" for issue in report["issues"])

    if report["recommendations"]:
        lines.extend(["", "Recommendations:"])
        lines.extend(f"- {recommendation}" for recommendation in report["recommendations"])

    return "\n".join(lines)
