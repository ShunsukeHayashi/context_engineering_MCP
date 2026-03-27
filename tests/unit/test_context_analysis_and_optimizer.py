"""
Unit tests for context analysis and optimization logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from context_engineering.context_analyzer import ContextAnalyzer, MultimodalAnalyzer, RAGAnalyzer
from context_engineering.context_models import ContextElement, ContextType, ContextWindow, MultimodalContext, OptimizationStatus, RAGContext
from context_engineering.context_optimizer import ContextOptimizer


def make_analyzer():
    with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel") as mock_model:
        model_instance = MagicMock()
        mock_model.return_value = model_instance
        analyzer = ContextAnalyzer("test-key")
    return analyzer, model_instance


def make_optimizer():
    with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel") as mock_model:
        model_instance = MagicMock()
        mock_model.return_value = model_instance
        optimizer = ContextOptimizer("test-key")
    return optimizer, model_instance


def test_context_analyzer_basic_metrics_and_efficiency():
    analyzer, _ = make_analyzer()
    window = ContextWindow(
        max_tokens=1000,
        elements=[
            ContextElement(content="System guidance here", type=ContextType.SYSTEM, priority=9),
            ContextElement(content="User asks for a detailed answer", type=ContextType.USER, priority=5),
            ContextElement(content="User asks for a detailed answer", type=ContextType.ASSISTANT, priority=4),
        ],
    )

    basic = analyzer._calculate_basic_metrics(window)
    structure = analyzer._analyze_structure(window)
    efficiency = analyzer._analyze_token_efficiency(window)

    assert basic["total_elements"] == 3
    assert structure["system_ratio"] == pytest.approx(1 / 3)
    assert efficiency["redundancy_score"] > 0
    assert efficiency["efficiency_score"] < 1


def test_context_analyzer_empty_and_redundancy_branches():
    analyzer, _ = make_analyzer()
    empty_window = ContextWindow(max_tokens=100)

    basic = analyzer._calculate_basic_metrics(empty_window)
    structure = analyzer._analyze_structure(empty_window)
    efficiency = analyzer._analyze_token_efficiency(empty_window)
    redundancy = analyzer._calculate_redundancy(
        ContextWindow(
            max_tokens=100,
            elements=[ContextElement(content="", type=ContextType.USER)],
        )
    )

    assert basic["total_elements"] == 0
    assert structure == {}
    assert efficiency == {}
    assert redundancy == 0.0


@pytest.mark.asyncio
async def test_context_analyzer_assess_and_comprehensive_analysis():
    analyzer, _ = make_analyzer()
    window = ContextWindow(
        max_tokens=800,
        elements=[
            ContextElement(content="System instruction", type=ContextType.SYSTEM, priority=10),
            ContextElement(content="User instruction repeated", type=ContextType.USER, priority=4),
        ],
    )

    async def fake_semantic(_window):
        return {
            "metrics": {
                "topic_consistency": 0.9,
                "logical_flow": 0.8,
                "information_redundancy": 0.2,
                "context_clarity": 0.85,
                "goal_alignment": 0.9,
            },
            "insights": ["consistent"],
        }

    async def fake_quality(_window, metrics):
        assert metrics["topic_consistency"] == 0.9
        return {
            "score": 0.88,
            "issues": ["minor issue"],
            "strengths": ["good clarity"],
            "recommendations": ["keep structure"],
        }

    analyzer._analyze_semantic_consistency = fake_semantic
    analyzer._assess_quality = fake_quality

    result = await analyzer.analyze_context_window(window)

    assert result.quality_score == 0.88
    assert "consistent" in result.insights
    assert "good clarity" in result.strengths


@pytest.mark.asyncio
async def test_context_analyzer_semantic_and_quality_fallbacks():
    analyzer, model = make_analyzer()
    window = ContextWindow(
        max_tokens=100,
        elements=[ContextElement(content="Only one topic", type=ContextType.USER, priority=3)],
    )

    model.generate_content.side_effect = RuntimeError("semantic failure")
    semantic = await analyzer._analyze_semantic_consistency(window)

    quality_low = await analyzer._assess_quality(
        window,
        {
            "token_utilization": 0.95,
            "topic_consistency": 0.4,
            "logical_flow": 0.5,
            "context_clarity": 0.5,
            "efficiency_score": 0.4,
            "redundancy_score": 0.7,
        },
    )
    quality_default = await analyzer._assess_quality(window, {})

    assert semantic["metrics"]["topic_consistency"] == 0.5
    assert "分析エラー" in semantic["insights"][0]
    assert "トークン使用率が高すぎます（90%超）" in quality_low["issues"]
    assert "話題の一貫性が低いです" in quality_low["issues"]
    assert "情報の重複が多いです" in quality_low["issues"]
    assert quality_default["score"] == 0.5


@pytest.mark.asyncio
async def test_multimodal_and_rag_analyzers():
    with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel") as mock_model:
        mock_model.return_value = MagicMock()
        multimodal = MultimodalAnalyzer("test-key")
        rag = RAGAnalyzer("test-key")

    context = MultimodalContext(
        text_content="Describe the uploaded diagram",
        image_urls=["a.png", "b.png"],
        document_urls=["spec.pdf"],
        extracted_content={"ocr": "diagram details"},
    )
    async def fake_cross_modal(_context):
        return 0.91

    multimodal._analyze_cross_modal_consistency = fake_cross_modal
    multimodal_result = await multimodal.analyze_multimodal_context(context)

    rag_context = RAGContext(
        query="pricing policy",
        retrieved_documents=[
            {"content": "pricing policy for enterprise accounts"},
            {"content": "enterprise pricing and billing policy"},
            {"content": "support escalation workflow"},
        ],
        similarity_scores=[0.9, 0.82, 0.4],
    )

    async def fake_relevance(_rag):
        return {
            "metrics": {
                "query_relevance": 0.9,
                "result_redundancy": 0.2,
                "coverage_completeness": 0.8,
            },
            "insights": ["strong retrieval"],
        }

    rag._analyze_retrieval_relevance = fake_relevance
    rag_result = await rag.analyze_rag_context(rag_context)

    assert multimodal_result.metrics["modality_diversity"] == pytest.approx(3 / 5)
    assert rag_result.metrics["avg_similarity_score"] == pytest.approx((0.9 + 0.82 + 0.4) / 3)
    assert "strong retrieval" in rag_result.insights
    assert rag_result.metrics["retrieval_diversity"] >= 0


@pytest.mark.asyncio
async def test_multimodal_and_rag_fallback_paths():
    with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel") as mock_model:
        model = MagicMock()
        mock_model.return_value = model
        multimodal = MultimodalAnalyzer("test-key")
        rag = RAGAnalyzer("test-key")

    rich_context = MultimodalContext(
        text_content="long text",
        image_urls=["1.png", "2.png", "3.png", "4.png", "5.png", "6.png", "7.png", "8.png", "9.png"],
        audio_urls=["1.mp3"],
        video_urls=["1.mp4"],
        document_urls=["1.pdf"],
        extracted_content={"ocr": "text"},
    )
    model.generate_content.side_effect = RuntimeError("cross modal failure")
    multimodal_result = await multimodal.analyze_multimodal_context(rich_context)

    rag_context = RAGContext(
        query="query",
        retrieved_documents=[{"content": ""}, {"content": ""}],
        similarity_scores=[],
    )
    rag.model.generate_content.side_effect = RuntimeError("rag failure")
    relevance = await rag._analyze_retrieval_relevance(rag_context)
    diversity_single = rag._calculate_retrieval_diversity(RAGContext(query="q", retrieved_documents=[{"content": "one"}]))
    diversity_empty = rag._calculate_retrieval_diversity(rag_context)

    assert multimodal_result.metrics["cross_modal_consistency"] == 0.5
    assert any("画像の数が多すぎます" in item for item in multimodal_result.recommendations)
    assert any("総トークン数が多すぎます" in item for item in multimodal_result.recommendations)
    assert relevance["metrics"]["query_relevance"] == 0.5
    assert "分析エラー" in relevance["insights"][0]
    assert diversity_single == 0.0
    assert diversity_empty == 0.0


@pytest.mark.asyncio
async def test_context_optimizer_low_priority_and_duplicates():
    optimizer, _ = make_optimizer()
    window = ContextWindow(
        max_tokens=40,
        reserved_tokens=5,
        elements=[
            ContextElement(content="Low priority duplicate", priority=1, type=ContextType.USER),
            ContextElement(content="Low priority duplicate", priority=2, type=ContextType.USER),
            ContextElement(content="Keep this system rule", priority=10, type=ContextType.SYSTEM),
        ],
    )

    removed = await optimizer._remove_low_priority_elements(window, target_tokens=10, preserve_types=["system"])
    deduped = await optimizer._remove_duplicates(window)

    assert removed["removed_count"] >= 1
    assert any(element.type == ContextType.SYSTEM for element in window.elements)
    assert deduped["tokens_saved"] >= 0


@pytest.mark.asyncio
async def test_context_optimizer_helper_early_breaks_and_success_paths():
    optimizer, model = make_optimizer()

    no_op_window = ContextWindow(
        max_tokens=200,
        elements=[ContextElement(content="short text", type=ContextType.USER, priority=1)],
    )
    removed = await optimizer._remove_low_priority_elements(
        no_op_window,
        target_tokens=no_op_window.current_tokens,
        preserve_types=[],
    )
    compressed = await optimizer._compress_content(
        no_op_window,
        target_tokens=no_op_window.current_tokens,
    )

    duplicate_window = ContextWindow(
        max_tokens=500,
        elements=[
            ContextElement(content="same content", type=ContextType.USER, priority=1),
            ContextElement(content="same content", type=ContextType.USER, priority=2),
        ],
    )
    deduped = await optimizer._remove_duplicates(duplicate_window)

    model.generate_content.return_value = MagicMock(text="alpha\nbeta\ngamma\ndelta\nepsilon\nzeta")
    topics = await optimizer._extract_main_topics("some text")
    no_topic_score = await optimizer._calculate_relevance_score("content", [])

    assert removed["removed_count"] == 0
    assert compressed["compressed_count"] == 0
    assert deduped["removed_count"] == 1
    assert topics == ["alpha", "beta", "gamma", "delta", "epsilon"]
    assert no_topic_score == 0.5


@pytest.mark.asyncio
async def test_context_optimizer_relevance_structure_and_auto_optimize():
    optimizer, model = make_optimizer()
    window = ContextWindow(
        max_tokens=500,
        elements=[
            ContextElement(content="gamma topic", type=ContextType.USER, priority=2),
            ContextElement(content="alpha topic", type=ContextType.SYSTEM, priority=10),
            ContextElement(content="beta topic", type=ContextType.ASSISTANT, priority=5),
        ],
    )

    async def fake_topics(_content):
        return ["alpha", "beta"]

    optimizer._extract_main_topics = fake_topics

    async def fake_relevance(content, _topics):
        if "alpha" in content:
            return 0.9
        if "beta" in content:
            return 0.7
        return 0.2

    optimizer._calculate_relevance_score = fake_relevance
    relevance = await optimizer._optimize_for_relevance(window)
    structure = await optimizer._optimize_for_structure(window)

    assert relevance["reordered"] is True
    assert window.elements[0].content == "alpha topic"
    assert structure["optimal_order_applied"][0] == "system"

    recommendation_response = """```json
{"recommended_goals":["reduce_tokens","improve_structure"],"priority":"high","reasoning":"cleanup","constraints":{"target_token_reduction":0.2}}
```"""
    model.generate_content.return_value = MagicMock(text=recommendation_response)

    async def fake_optimize_context_window(_window, goals, constraints):
        task = optimizer.optimization_tasks.setdefault(
            "auto-task",
            type("Task", (), {"id": "auto-task"})()
        )
        assert goals == ["reduce_tokens", "improve_structure"]
        assert constraints["target_token_reduction"] == 0.2
        return task

    optimizer.optimize_context_window = fake_optimize_context_window
    auto = await optimizer.auto_optimize_context(window)

    assert auto["optimization_started"] is True
    assert auto["task_id"] == "auto-task"

    model.generate_content.side_effect = RuntimeError("auto failed")
    with pytest.raises(RuntimeError):
        await optimizer.auto_optimize_context(window)
    model.generate_content.side_effect = None


@pytest.mark.asyncio
async def test_context_optimizer_execute_tasks_and_duplicate_detection():
    optimizer, _ = make_optimizer()
    window = ContextWindow(
        max_tokens=500,
        elements=[
            ContextElement(content="alpha detail", type=ContextType.USER, priority=5),
            ContextElement(content="alpha detail expanded", type=ContextType.USER, priority=6),
            ContextElement(content="different topic", type=ContextType.ASSISTANT, priority=4),
        ],
    )

    async def fake_similarity(left, right):
        if "alpha" in left and "alpha" in right:
            return 0.9
        return 0.1

    optimizer._calculate_semantic_similarity = fake_similarity
    groups = await optimizer._detect_semantic_duplicates(window.elements)
    assert len(groups) == 1
    assert len(groups[0]) == 2

    async def fake_reduce(_window, _constraints):
        return {"strategy": "reduce"}

    async def fake_clarity(_window):
        return {"strategy": "clarity"}

    optimizer._optimize_for_token_reduction = fake_reduce
    optimizer._optimize_for_clarity = fake_clarity

    task = await optimizer.optimize_context_window(window, ["reduce_tokens", "improve_clarity"], {})
    await optimizer._execute_optimization(task, window)

    assert task.status == OptimizationStatus.COMPLETED
    assert "token_reduction" in task.result
    assert "clarity_improvement" in task.result


@pytest.mark.asyncio
async def test_context_optimizer_executes_remaining_goals_and_ignores_unknown():
    optimizer, _ = make_optimizer()
    window = ContextWindow(
        max_tokens=500,
        elements=[ContextElement(content="alpha", type=ContextType.USER, priority=5)],
    )

    async def fake_relevance(_window):
        return {"strategy": "relevance"}

    async def fake_redundancy(_window):
        return {"strategy": "redundancy"}

    async def fake_structure(_window):
        return {"strategy": "structure"}

    optimizer._optimize_for_relevance = fake_relevance
    optimizer._optimize_for_redundancy_removal = fake_redundancy
    optimizer._optimize_for_structure = fake_structure

    task = await optimizer.optimize_context_window(
        window,
        ["enhance_relevance", "remove_redundancy", "improve_structure", "unknown_goal"],
        {},
    )
    await optimizer._execute_optimization(task, window)

    assert task.status == OptimizationStatus.COMPLETED
    assert task.progress == 1.0
    assert task.result["relevance_enhancement"]["strategy"] == "relevance"
    assert task.result["redundancy_removal"]["strategy"] == "redundancy"
    assert task.result["structure_improvement"]["strategy"] == "structure"


@pytest.mark.asyncio
async def test_context_optimizer_marks_failed_tasks():
    optimizer, _ = make_optimizer()
    window = ContextWindow(
        max_tokens=500,
        elements=[ContextElement(content="alpha", type=ContextType.USER, priority=5)],
    )

    async def failing_relevance(_window):
        raise RuntimeError("relevance exploded")

    optimizer._optimize_for_relevance = failing_relevance

    task = await optimizer.optimize_context_window(window, ["enhance_relevance"], {})
    await optimizer._execute_optimization(task, window)

    assert task.status == OptimizationStatus.FAILED
    assert task.error_message == "relevance exploded"
    assert task.completed_at is not None


@pytest.mark.asyncio
async def test_context_optimizer_token_reduction_strategies_and_noop():
    optimizer, _ = make_optimizer()
    window = ContextWindow(
        max_tokens=1000,
        elements=[
            ContextElement(content="low " * 80, type=ContextType.USER, priority=1),
            ContextElement(content="high " * 80, type=ContextType.SYSTEM, priority=9),
            ContextElement(content="low " * 80, type=ContextType.USER, priority=2),
        ],
    )

    async def fake_remove_low_priority(_window, target_tokens, preserve_types):
        assert target_tokens > 0
        assert preserve_types == ["system"]
        _window.elements = _window.elements[1:]
        return {"strategy": "low_priority_removal"}

    async def fake_compress(_window, target_tokens):
        assert target_tokens > 0
        _window.elements[0].content = "compressed"
        return {"strategy": "content_compression"}

    async def fake_remove_duplicates(_window):
        return {"strategy": "duplicate_removal"}

    optimizer._remove_low_priority_elements = fake_remove_low_priority
    optimizer._compress_content = fake_compress
    optimizer._remove_duplicates = fake_remove_duplicates

    reduced = await optimizer._optimize_for_token_reduction(
        window,
        {
            "target_token_reduction": 0.9,
            "min_tokens": 1,
            "preserve_element_types": ["system"],
        },
    )

    noop_window = ContextWindow(
        max_tokens=1000,
        elements=[ContextElement(content="tiny", type=ContextType.USER, priority=5)],
    )
    noop = await optimizer._optimize_for_token_reduction(
        noop_window,
        {"target_token_reduction": 0.0, "min_tokens": 1000},
    )

    assert len(reduced["strategies_applied"]) == 3
    assert reduced["original_tokens"] >= reduced["final_tokens"]
    assert noop["strategies_applied"] == []


@pytest.mark.asyncio
async def test_context_optimizer_compression_and_fallback_paths():
    optimizer, model = make_optimizer()
    long_content = "A" * 260
    window = ContextWindow(
        max_tokens=200,
        elements=[
            ContextElement(content=long_content, type=ContextType.USER, priority=5),
            ContextElement(content="B" * 240, type=ContextType.ASSISTANT, priority=4),
        ],
    )

    model.generate_content.return_value = MagicMock(text="short summary")
    compression = await optimizer._compress_content(window, target_tokens=0)
    direct = await optimizer._compress_single_content(long_content)

    assert compression["compressed_count"] >= 1
    assert compression["total_tokens_saved"] >= 0
    assert direct == "short summary"

    model.generate_content.return_value = MagicMock(text="X" * len(long_content))
    assert await optimizer._compress_single_content(long_content) is None

    model.generate_content.side_effect = RuntimeError("model error")
    assert await optimizer._compress_single_content(long_content) is None
    model.generate_content.side_effect = None


@pytest.mark.asyncio
async def test_context_optimizer_clarity_and_merge_fallbacks():
    optimizer, model = make_optimizer()
    element = ContextElement(content="This sentence needs to be clearer." * 6, type=ContextType.USER, priority=5)
    window = ContextWindow(max_tokens=400, elements=[element])

    model.generate_content.return_value = MagicMock(text="Clearer sentence.")
    improved = await optimizer._optimize_for_clarity(window)
    merged = await optimizer._merge_similar_contents(["alpha", "beta"])

    assert improved["improved_count"] == 1
    assert window.elements[0].content == "Clearer sentence."
    assert merged == "Clearer sentence."

    model.generate_content.side_effect = RuntimeError("boom")
    assert await optimizer._improve_content_clarity("text") is None
    assert await optimizer._extract_main_topics("text") == []
    assert await optimizer._calculate_relevance_score("text", ["topic"]) == 0.5
    assert await optimizer._calculate_semantic_similarity("left", "right") == 0.0
    assert await optimizer._merge_similar_contents(["alpha", "beta"]) == "alpha"
    model.generate_content.side_effect = None


@pytest.mark.asyncio
async def test_context_optimizer_score_clamping_and_empty_relevance():
    optimizer, model = make_optimizer()
    model.generate_content.return_value = MagicMock(text="1.7")
    assert await optimizer._calculate_relevance_score("text", ["topic"]) == 1.0

    model.generate_content.return_value = MagicMock(text="-1")
    assert await optimizer._calculate_semantic_similarity("left", "right") == 0.0

    empty_window = ContextWindow(max_tokens=100)
    relevance = await optimizer._optimize_for_relevance(empty_window)
    duplicates = await optimizer._detect_semantic_duplicates([ContextElement(content="solo", type=ContextType.USER)])

    assert relevance == {"strategy": "relevance_enhancement", "changes": []}
    assert duplicates == []


@pytest.mark.asyncio
async def test_context_optimizer_duplicate_detection_failure_and_structure_tail():
    optimizer, _ = make_optimizer()

    async def broken_similarity(_left, _right):
        raise RuntimeError("similarity failed")

    optimizer._calculate_semantic_similarity = broken_similarity
    failed = await optimizer._detect_semantic_duplicates(
        [
            ContextElement(content="one", type=ContextType.USER),
            ContextElement(content="two", type=ContextType.USER),
        ]
    )

    window = ContextWindow(
        max_tokens=500,
        elements=[
            ContextElement(content="custom", type=ContextType.MULTIMODAL, priority=1),
            ContextElement(content="system", type=ContextType.SYSTEM, priority=5),
        ],
    )
    structured = await optimizer._optimize_for_structure(window)

    assert failed == []
    assert structured["reordered"] is True
    assert window.elements[-1].type == ContextType.MULTIMODAL


@pytest.mark.asyncio
async def test_context_optimizer_redundancy_removal_success_path():
    optimizer, _ = make_optimizer()
    first = ContextElement(content="short", type=ContextType.USER, priority=3)
    second = ContextElement(content="much longer duplicate text", type=ContextType.USER, priority=4)
    third = ContextElement(content="other", type=ContextType.ASSISTANT, priority=2)
    window = ContextWindow(max_tokens=500, elements=[first, second, third])

    async def fake_duplicates(_elements):
        return [[first, second]]

    async def fake_merge(contents):
        assert "short" in contents[0] or "short" in contents[1]
        return "merged duplicate text"

    optimizer._detect_semantic_duplicates = fake_duplicates
    optimizer._merge_similar_contents = fake_merge

    result = await optimizer._optimize_for_redundancy_removal(window)

    assert result["merged_elements"] == 1
    assert result["removed_elements"] == 1
    assert result["duplicate_groups"] == 1
    assert len(window.elements) == 2


def test_context_optimizer_format_elements_and_task_listing():
    optimizer, _ = make_optimizer()
    first = optimizer.optimization_tasks.setdefault("1", type("Task", (), {"id": "1", "context_id": "ctx", "created_at": 1})())
    second = optimizer.optimization_tasks.setdefault("2", type("Task", (), {"id": "2", "context_id": "ctx", "created_at": 2})())
    third = optimizer.optimization_tasks.setdefault("3", type("Task", (), {"id": "3", "context_id": "other", "created_at": 3})())

    formatted = optimizer._format_elements_for_analysis(
        [ContextElement(content=f"element {i}", type=ContextType.USER, priority=i % 10 + 1) for i in range(12)]
    )
    listed = optimizer.list_optimization_tasks("ctx")

    assert "... 他2要素" in formatted
    assert [task.id for task in listed] == ["2", "1"]
    assert optimizer.get_optimization_task("3") is third
