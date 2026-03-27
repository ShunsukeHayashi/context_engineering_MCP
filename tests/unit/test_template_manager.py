"""
Unit tests for template management.
"""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest

from context_engineering.context_models import ContextElement, ContextType, ContextWindow, PromptTemplate, PromptTemplateType
from context_engineering.template_manager import ContextTemplateIntegrator, TemplateManager


def make_manager(tmp_path, response_text='{"name":"AI Template","description":"Generated","template":"Hello {name}","type":"completion","category":"general","tags":["ai"]}'):
    with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel") as mock_model:
        response = MagicMock()
        response.text = response_text
        model_instance = MagicMock()
        model_instance.generate_content.return_value = response
        mock_model.return_value = model_instance
        manager = TemplateManager("test-key", storage_path=str(tmp_path / "templates"))
    return manager, model_instance


def test_template_manager_initializes_defaults_and_stats(tmp_path):
    manager, _ = make_manager(tmp_path)

    templates = manager.list_templates()
    stats = manager.get_template_stats()

    assert len(templates) >= 5
    assert stats["total_templates"] >= 5
    assert "qa" in stats["categories"]


def test_template_manager_empty_stats_and_serialization_helpers(tmp_path):
    manager, _ = make_manager(tmp_path)
    manager.templates.clear()

    assert manager.get_template_stats() == {}

    raw = {
        "id": "tmpl-1",
        "name": "Name",
        "description": "Desc",
        "template": "Hello {name}",
        "variables": ["name"],
        "type": "completion",
        "category": "general",
        "tags": ["x"],
        "usage_count": 2,
        "quality_score": 0.5,
        "created_by": "tester",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    template = manager._dict_to_template(raw)
    encoded = manager._template_to_dict(template)

    assert encoded["id"] == "tmpl-1"
    assert manager.get_template("missing") is None


def test_template_manager_crud_and_search(tmp_path):
    manager, _ = make_manager(tmp_path)
    template = PromptTemplate(
        name="Support Escalation",
        description="Escalation template",
        template="Customer {customer_name} needs {issue_type}",
        type=PromptTemplateType.COMPLETION,
        category="support",
        tags=["support", "priority"],
        created_by="tester",
    )

    template_id = manager.create_template(template)
    rendered = manager.render_template(template_id, {"customer_name": "Alice", "issue_type": "help"})
    search_results = manager.search_templates("support")

    assert rendered == "Customer Alice needs help"
    assert manager.get_template(template_id).usage_count == 1
    assert any(item.id == template_id for item in search_results)

    updated = manager.update_template(template_id, description="Updated", template="Case {case_id}")
    assert updated is True
    assert manager.get_template(template_id).variables == ["case_id"]

    deleted = manager.delete_template(template_id)
    assert deleted is True
    assert manager.get_template(template_id) is None

    assert manager.update_template("missing", description="nope") is False
    assert manager.delete_template("missing") is False
    assert manager.render_template("missing", {}) is None


def test_template_manager_protects_system_templates(tmp_path):
    manager, _ = make_manager(tmp_path)
    system_template = next(iter(manager.templates.values()))

    assert manager.delete_template(system_template.id) is False


@pytest.mark.asyncio
async def test_template_manager_generate_and_optimize_template(tmp_path):
    generate_response = """```json
{"name":"Generated Support","description":"AI generated","template":"Assist {user}","type":"completion","category":"support","tags":["ai","support"]}
```"""
    optimize_response = """```json
{"current_score":{"clarity":0.8,"completeness":0.9,"efficiency":0.7,"consistency":0.8,"flexibility":0.6},"issues":["too generic"],"improvements":["add constraints"],"optimized_template":"Assist {user} quickly","explanation":"more direct"}
```"""
    manager, model = make_manager(tmp_path, response_text=generate_response)
    model.generate_content.side_effect = [
        MagicMock(text=generate_response),
        MagicMock(text=optimize_response),
    ]

    template = await manager.generate_template("Customer support")
    result = await manager.optimize_template(template.id)

    assert template.created_by == "ai_generated"
    assert result["optimized_template"] == "Assist {user} quickly"
    assert manager.get_template(template.id).quality_score == 0.76


@pytest.mark.asyncio
async def test_template_manager_generate_and_optimize_error_paths(tmp_path):
    manager, model = make_manager(tmp_path)
    model.generate_content.side_effect = RuntimeError("generation failed")

    with pytest.raises(RuntimeError):
        await manager.generate_template("Customer support")

    with pytest.raises(ValueError):
        await manager.optimize_template("missing")

    custom_template = PromptTemplate(
        name="Optimizable",
        description="desc",
        template="Hi {name}",
        type=PromptTemplateType.COMPLETION,
        category="general",
        tags=["x"],
        created_by="tester",
    )
    template_id = manager.create_template(custom_template)
    model.generate_content.side_effect = RuntimeError("optimize failed")

    with pytest.raises(RuntimeError):
        await manager.optimize_template(template_id)


def test_template_manager_load_and_save_error_paths(tmp_path):
    storage_path = tmp_path / "templates"
    storage_path.mkdir()
    (storage_path / "broken.json").write_text("{not-json", encoding="utf-8")

    with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel") as mock_model:
        mock_model.return_value = MagicMock()
        manager = TemplateManager("test-key", storage_path=str(storage_path))

    assert manager.templates

    with patch("builtins.open", mock_open()) as mocked_open:
        mocked_open.side_effect = OSError("save failed")
        manager._save_template(next(iter(manager.templates.values())))


def test_template_manager_filters_and_integrator_error_paths(tmp_path):
    manager, _ = make_manager(tmp_path)
    integrator = ContextTemplateIntegrator(manager)
    listed = manager.list_templates(category="does-not-exist", tags=["missing"])

    assert listed == []

    with pytest.raises(ValueError):
        integrator.apply_template_to_context(ContextWindow(max_tokens=100), "missing", {})

    custom_template = PromptTemplate(
        name="Huge",
        description="desc",
        template="A" * 5000,
        type=PromptTemplateType.COMPLETION,
        category="ops",
        tags=["notify"],
        created_by="tester",
    )
    template_id = manager.create_template(custom_template)
    with pytest.raises(ValueError):
        integrator.apply_template_to_context(ContextWindow(max_tokens=1), template_id, {})

    assert integrator.extract_template_from_context(ContextWindow(max_tokens=100)) is None


def test_context_template_integrator_detect_variables(tmp_path):
    manager, _ = make_manager(tmp_path)
    integrator = ContextTemplateIntegrator(manager)
    detected = integrator._detect_variables(
        "Contact alice@example.com on 2026-03-27 via https://example.com and budget 42."
    )

    assert detected["email"] == ["alice@example.com"]
    assert detected["date"] == ["2026-03-27"]
    assert detected["url"] == ["https://example.com"]
    assert detected["number"] == ["2026", "03", "27", "42"] or "42" in detected["number"]


def test_context_template_integrator_apply_and_extract(tmp_path):
    manager, _ = make_manager(tmp_path)
    integrator = ContextTemplateIntegrator(manager)

    custom_template = PromptTemplate(
        name="Notifier",
        description="Notification template",
        template="Notify {email} before {date}",
        type=PromptTemplateType.COMPLETION,
        category="ops",
        tags=["notify"],
        created_by="tester",
    )
    template_id = manager.create_template(custom_template)

    window = ContextWindow(max_tokens=2000)
    updated_window = integrator.apply_template_to_context(
        window,
        template_id,
        {"email": "alice@example.com", "date": "2026-03-27"},
    )

    assert updated_window.template_id == template_id
    assert updated_window.elements[0].type == ContextType.SYSTEM
    assert "alice@example.com" in updated_window.elements[0].content

    extracted = integrator.extract_template_from_context(
        ContextWindow(
            max_tokens=1000,
            elements=[
                ContextElement(content="Contact alice@example.com on 2026-03-27"),
                ContextElement(content="See https://example.com/case/123 and amount 42"),
            ],
        )
    )

    assert extracted is not None
    assert "{email}" in extracted.template or "{date}" in extracted.template or "{url}" in extracted.template
