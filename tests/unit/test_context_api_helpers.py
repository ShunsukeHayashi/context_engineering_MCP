"""
Unit tests for context_api helper and middleware behavior.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.websockets import WebSocketDisconnect

from context_engineering.context_models import ContextSession


@pytest.fixture
def context_api_module(monkeypatch, tmp_path):
    import os

    os.environ["GEMINI_API_KEY"] = "test-api-key-for-testing"
    os.environ["CONTEXT_TEMPLATE_STORAGE_PATH"] = str(tmp_path / "templates")

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("GEMINI_API_KEY", "test-api-key-for-testing")
        mp.setenv("CONTEXT_TEMPLATE_STORAGE_PATH", str(tmp_path / "templates"))
        with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel") as mock_model:
            mock_response = MagicMock()
            mock_response.text = "{}"
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_instance.generate_content_async = AsyncMock(return_value=mock_response)
            mock_model.return_value = mock_instance
            import context_engineering.context_api as module
            yield module


def _make_request(path: str, headers: list[tuple[bytes, bytes]] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": headers or [],
            "client": ("127.0.0.1", 1234),
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "http_version": "1.1",
        }
    )


@pytest.mark.asyncio
async def test_websocket_manager_connect_broadcast_disconnect(context_api_module):
    manager = context_api_module.WebSocketManager()

    healthy = AsyncMock()
    failing = AsyncMock()
    failing.send_json.side_effect = RuntimeError("socket closed")

    await manager.connect(healthy)
    manager.active_connections.append(failing)
    await manager.broadcast({"type": "ping"})
    manager.disconnect(healthy)

    healthy.accept.assert_awaited_once()
    healthy.send_json.assert_awaited_once()
    assert failing not in manager.active_connections
    assert healthy not in manager.active_connections


@pytest.mark.asyncio
async def test_security_middleware_handler_returns_rate_limit_response(context_api_module, monkeypatch):
    request = _make_request("/api/health")
    monkeypatch.setattr(context_api_module.security_middleware, "get_client_id", lambda _req: "client")
    monkeypatch.setattr(context_api_module.security_middleware, "rate_limit_check", AsyncMock(return_value=False))

    response = await context_api_module.security_middleware_handler(
        request, AsyncMock(return_value=JSONResponse({"ok": True}))
    )

    assert response.status_code == 429
    assert response.body == b'{"detail":"Rate limit exceeded"}'


@pytest.mark.asyncio
async def test_security_middleware_handler_rejects_large_request(context_api_module, monkeypatch):
    request = _make_request("/api/health", headers=[(b"content-length", b"999")])
    monkeypatch.setattr(context_api_module.security_middleware, "get_client_id", lambda _req: "client")
    monkeypatch.setattr(context_api_module.security_middleware, "rate_limit_check", AsyncMock(return_value=True))
    monkeypatch.setattr(context_api_module.security_config, "max_request_size", 10)

    response = await context_api_module.security_middleware_handler(
        request, AsyncMock(return_value=JSONResponse({"ok": True}))
    )

    assert response.status_code == 413
    assert response.body == b'{"detail":"Request too large"}'


@pytest.mark.asyncio
async def test_security_middleware_handler_adds_security_headers(context_api_module, monkeypatch):
    request = _make_request("/api/health")
    monkeypatch.setattr(context_api_module.security_middleware, "get_client_id", lambda _req: "client")
    monkeypatch.setattr(context_api_module.security_middleware, "rate_limit_check", AsyncMock(return_value=True))

    async def call_next(_request):
        return JSONResponse({"ok": True})

    response = await context_api_module.security_middleware_handler(request, call_next)

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.asyncio
async def test_verify_api_key_paths(context_api_module, monkeypatch):
    no_key_request = _make_request("/api/health")
    assert await context_api_module.verify_api_key(no_key_request) is None

    invalid_request = _make_request("/api/health", headers=[(b"x-api-key", b"short")])
    monkeypatch.setattr(context_api_module.security_middleware, "get_client_id", lambda _req: "client")
    with pytest.raises(HTTPException) as exc:
        await context_api_module.verify_api_key(invalid_request)
    assert exc.value.status_code == 401

    valid_request = _make_request("/api/health", headers=[(b"x-api-key", b"valid-key-1234567890")])
    assert await context_api_module.verify_api_key(valid_request) == {"api_key": "valid-key-1234567890"}


@pytest.mark.asyncio
async def test_initialize_components_requires_api_key(context_api_module, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        await context_api_module.initialize_components()


@pytest.mark.asyncio
async def test_health_check_and_find_window(context_api_module):
    context_api_module.sessions_storage.clear()
    session = ContextSession(name="test")
    window = session.create_window(256)
    context_api_module.sessions_storage[session.id] = session
    context_api_module.app_start_time = datetime.now() - timedelta(seconds=5)

    payload = await context_api_module.health_check()
    found = context_api_module.find_window_by_id(window.id)
    missing = context_api_module.find_window_by_id("missing")

    assert payload["status"] == "healthy"
    assert payload["uptime"] >= 4
    assert found is window
    assert missing is None


@pytest.mark.asyncio
async def test_websocket_endpoint_disconnects_cleanly(context_api_module):
    disconnecting_socket = SimpleNamespace(
        accept=AsyncMock(),
        receive_text=AsyncMock(side_effect=WebSocketDisconnect()),
    )

    await context_api_module.websocket_endpoint(disconnecting_socket)

    disconnecting_socket.accept.assert_awaited_once()
    assert disconnecting_socket not in context_api_module.websocket_manager.active_connections


@pytest.mark.asyncio
async def test_lifespan_runs_startup_and_shutdown(context_api_module, monkeypatch):
    initialize = AsyncMock()
    monkeypatch.setattr(context_api_module, "initialize_components", initialize)

    async with context_api_module.lifespan(context_api_module.app):
        assert context_api_module.app_start_time is not None

    initialize.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_context_element_missing_window(context_api_module):
    request = context_api_module.ContextElementRequest(content="hello", type="user")

    with pytest.raises(HTTPException) as exc:
        await context_api_module.add_context_element("missing", request)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_analyze_context_error_paths(context_api_module, monkeypatch):
    with pytest.raises(HTTPException) as exc:
        await context_api_module.analyze_context("missing")
    assert exc.value.status_code == 404

    session = ContextSession(name="analysis")
    window = session.create_window(256)
    context_api_module.sessions_storage[session.id] = session
    monkeypatch.setattr(
        context_api_module,
        "context_analyzer",
        SimpleNamespace(analyze_context_window=AsyncMock(side_effect=RuntimeError("analysis broke"))),
        raising=False,
    )

    with pytest.raises(HTTPException) as exc:
        await context_api_module.analyze_context(window.id)

    assert exc.value.status_code == 500
    assert "analysis broke" in exc.value.detail


@pytest.mark.asyncio
async def test_create_template_and_generate_template_error_paths(context_api_module, monkeypatch):
    monkeypatch.setattr(
        context_api_module,
        "template_manager",
        SimpleNamespace(
            create_template=MagicMock(side_effect=RuntimeError("save broke")),
            generate_template=AsyncMock(side_effect=RuntimeError("generate broke")),
        ),
        raising=False,
    )
    with pytest.raises(HTTPException) as exc:
        await context_api_module.create_template(
            context_api_module.TemplateRequest(
                name="x",
                description="y",
                template="Hello {name}",
                type="completion",
                category="general",
                tags=[],
            )
        )
    assert exc.value.status_code == 500

    with pytest.raises(HTTPException) as exc:
        await context_api_module.generate_template("purpose", [], [])
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_render_template_generic_error(context_api_module, monkeypatch):
    monkeypatch.setattr(
        context_api_module,
        "template_manager",
        SimpleNamespace(render_template=MagicMock(side_effect=RuntimeError("render broke"))),
        raising=False,
    )

    with pytest.raises(HTTPException) as exc:
        await context_api_module.render_template(
            "tmpl",
            context_api_module.TemplateRenderRequest(template_id="tmpl", variables={}),
        )

    assert exc.value.status_code == 500
    assert "render broke" in exc.value.detail


@pytest.mark.asyncio
async def test_optimize_and_auto_optimize_error_paths(context_api_module, monkeypatch):
    missing_request = context_api_module.OptimizationRequest(goals=["reduce_tokens"], constraints={})

    with pytest.raises(HTTPException) as exc:
        await context_api_module.optimize_context("missing", missing_request)
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        await context_api_module.auto_optimize_context("missing")
    assert exc.value.status_code == 404

    session = ContextSession(name="optimization")
    window = session.create_window(256)
    context_api_module.sessions_storage[session.id] = session

    monkeypatch.setattr(
        context_api_module,
        "context_optimizer",
        SimpleNamespace(
            optimize_context_window=AsyncMock(side_effect=RuntimeError("optimize broke")),
            auto_optimize_context=AsyncMock(side_effect=RuntimeError("auto broke")),
            get_optimization_task=MagicMock(return_value=None),
        ),
        raising=False,
    )
    with pytest.raises(HTTPException) as exc:
        await context_api_module.optimize_context(window.id, missing_request)
    assert exc.value.status_code == 500

    with pytest.raises(HTTPException) as exc:
        await context_api_module.auto_optimize_context(window.id)
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_get_optimization_task_missing(context_api_module, monkeypatch):
    monkeypatch.setattr(
        context_api_module,
        "context_optimizer",
        SimpleNamespace(get_optimization_task=MagicMock(return_value=None)),
        raising=False,
    )
    with pytest.raises(HTTPException) as exc:
        await context_api_module.get_optimization_task("missing")

    assert exc.value.status_code == 404
