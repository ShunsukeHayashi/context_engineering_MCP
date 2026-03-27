"""
Unit tests for runtime health validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import urllib.error

from context_engineering.runtime_health import (
    collect_runtime_health,
    fetch_api_health,
    format_runtime_health_report,
    load_codex_context_engineering_config,
)


def test_load_codex_context_engineering_config_reads_section(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[mcp_servers.context_engineering]
command = "node"
args = ["/tmp/context_engineering_MCP/mcp-server/context_mcp_server.js"]
working_directory = "/tmp/context_engineering_MCP"
enabled = true
""".strip(),
        encoding="utf-8",
    )

    report = load_codex_context_engineering_config(config_path)

    assert report["status"] == "ok"
    assert report["configured"] is True
    assert report["command"] == "node"
    assert report["working_directory"] == "/tmp/context_engineering_MCP"


def test_load_codex_context_engineering_config_missing_file(tmp_path: Path):
    report = load_codex_context_engineering_config(tmp_path / "missing.toml")

    assert report["status"] == "warn"
    assert report["exists"] is False
    assert report["configured"] is False


def test_load_codex_context_engineering_config_invalid_toml(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    config_path.write_text("[mcp_servers.context_engineering\n", encoding="utf-8")

    report = load_codex_context_engineering_config(config_path)

    assert report["status"] == "fail"
    assert report["exists"] is True
    assert "could not be parsed" in report["message"]


def test_load_codex_context_engineering_config_missing_section(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    config_path.write_text("[mcp_servers.other]\ncommand='node'\n", encoding="utf-8")

    report = load_codex_context_engineering_config(config_path)

    assert report["status"] == "warn"
    assert report["configured"] is False
    assert "not configured" in report["message"]


def test_fetch_api_health_handles_url_errors():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
        report = fetch_api_health("http://127.0.0.1:9999", timeout=0.01)

    assert report["status"] == "fail"
    assert "failed" in report["message"]


def test_fetch_api_health_handles_invalid_json():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"not-json"

    with patch("urllib.request.urlopen", return_value=FakeResponse()):
        report = fetch_api_health("http://127.0.0.1:9003")

    assert report["status"] == "fail"
    assert "not valid JSON" in report["message"]


def test_fetch_api_health_handles_unhealthy_payload():
    payload = json.dumps({"status": "degraded"}).encode("utf-8")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return payload

    with patch("urllib.request.urlopen", return_value=FakeResponse()):
        report = fetch_api_health("http://127.0.0.1:9003")

    assert report["status"] == "fail"
    assert report["payload"]["status"] == "degraded"
    assert "did not report healthy" in report["message"]


def test_collect_runtime_health_detects_config_drift(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "context_engineering_MCP"
    (repo_root / "mcp-server").mkdir(parents=True)
    (repo_root / "mcp-server" / "context_mcp_server.js").write_text("// test", encoding="utf-8")

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[mcp_servers.context_engineering]
command = "node"
args = ["/tmp/elsewhere/context_mcp_server.js"]
working_directory = "/tmp/elsewhere"
enabled = true
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "context_engineering.runtime_health.fetch_api_health",
        lambda api_url: {"status": "ok", "url": api_url, "message": "healthy", "payload": {"status": "healthy"}},
    )

    report = collect_runtime_health(
        repo_root=repo_root,
        config_path=config_path,
        expected_canonical_root=repo_root,
        api_url="http://127.0.0.1:9003",
    )

    assert report["status"] == "fail"
    assert report["checks"]["codex_config"]["status"] == "fail"
    assert "Codex MCP config drift detected." in report["issues"]


def test_collect_runtime_health_returns_ok_when_everything_matches(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "context_engineering_MCP"
    (repo_root / "mcp-server").mkdir(parents=True)
    script_path = repo_root / "mcp-server" / "context_mcp_server.js"
    script_path.write_text("// test", encoding="utf-8")

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f"""
[mcp_servers.context_engineering]
command = "node"
args = ["{script_path}"]
working_directory = "{repo_root}"
enabled = true
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "context_engineering.runtime_health.fetch_api_health",
        lambda api_url: {"status": "ok", "url": api_url, "message": "healthy", "payload": {"status": "healthy"}},
    )

    report = collect_runtime_health(
        repo_root=repo_root,
        config_path=config_path,
        expected_canonical_root=repo_root,
        api_url="http://127.0.0.1:9003",
    )

    assert report["status"] == "ok"
    assert report["checks"]["repo_path"]["status"] == "ok"
    assert report["checks"]["codex_config"]["status"] == "ok"
    assert report["checks"]["api_health"]["status"] == "ok"


def test_collect_runtime_health_warns_when_config_missing(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "context_engineering_MCP"
    (repo_root / "mcp-server").mkdir(parents=True)
    (repo_root / "mcp-server" / "context_mcp_server.js").write_text("// test", encoding="utf-8")

    monkeypatch.setattr(
        "context_engineering.runtime_health.fetch_api_health",
        lambda api_url: {"status": "ok", "url": api_url, "message": "healthy", "payload": {"status": "healthy"}},
    )

    report = collect_runtime_health(
        repo_root=repo_root,
        config_path=tmp_path / "missing.toml",
        expected_canonical_root=repo_root,
        api_url="http://127.0.0.1:9003",
    )

    assert report["status"] == "warn"
    assert report["checks"]["codex_config"]["status"] == "warn"
    assert any("Configure the context_engineering MCP server" in item for item in report["recommendations"])


def test_collect_runtime_health_detects_repo_and_api_failure(tmp_path: Path, monkeypatch):
    repo_root = tmp_path / "repo"
    canonical_root = tmp_path / "canonical"
    (repo_root / "mcp-server").mkdir(parents=True)
    (repo_root / "mcp-server" / "context_mcp_server.js").write_text("// test", encoding="utf-8")
    (canonical_root / "mcp-server").mkdir(parents=True)
    script_path = canonical_root / "mcp-server" / "context_mcp_server.js"
    script_path.write_text("// canonical", encoding="utf-8")

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f"""
[mcp_servers.context_engineering]
command = "node"
args = ["{script_path}"]
working_directory = "{canonical_root}"
enabled = true
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "context_engineering.runtime_health.fetch_api_health",
        lambda api_url: {"status": "fail", "url": api_url, "message": "api down"},
    )

    report = collect_runtime_health(
        repo_root=repo_root,
        config_path=config_path,
        expected_canonical_root=canonical_root,
        api_url="http://127.0.0.1:9003",
    )

    assert report["status"] == "fail"
    assert report["checks"]["repo_path"]["status"] == "fail"
    assert report["checks"]["api_health"]["status"] == "fail"
    assert "Repository path drift detected." in report["issues"]
    assert "Context Engineering API is not healthy." in report["issues"]


def test_format_runtime_health_report_includes_issues_and_recommendations():
    report = {
        "status": "fail",
        "canonical_root": "/canonical",
        "repo_root": "/repo",
        "checks": {
            "repo_path": {"status": "fail", "message": "drift"},
            "codex_config": {"status": "warn", "message": "configure me"},
        },
        "issues": ["Repository path drift detected."],
        "recommendations": ["Use the canonical path."],
    }

    rendered = format_runtime_health_report(report)

    assert "Runtime health: fail" in rendered
    assert "[fail] repo_path: drift" in rendered
    assert "Issues:" in rendered
    assert "Recommendations:" in rendered
