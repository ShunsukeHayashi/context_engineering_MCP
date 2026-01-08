import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import google.generativeai as genai
from collections import Counter
import asyncio

from .context_models import (
    ContextWindow, ContextElement, ContextType, OptimizationTask,
    OptimizationStatus, ContextAnalysis
)

logger = logging.getLogger(__name__)

class ContextOptimizer:
    """コンテキスト最適化AI機能"""
    
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.optimization_tasks: Dict[str, OptimizationTask] = {}
    
    async def optimize_context_window(self, 
                                    window: ContextWindow, 
                                    optimization_goals: List[str],
                                    constraints: Dict[str, Any] = None) -> OptimizationTask:
        """コンテキストウィンドウの包括的最適化"""
        
        task = OptimizationTask(
            context_id=window.id,
            optimization_type="comprehensive",
            parameters={
                "goals": optimization_goals,
                "constraints": constraints or {}
            }
        )
        
        self.optimization_tasks[task.id] = task
        
        # バックグラウンドで最適化を実行
        asyncio.create_task(self._execute_optimization(task, window))
        
        return task
    
    async def _execute_optimization(self, task: OptimizationTask, window: ContextWindow):
        """最適化タスクを実行"""
        task.status = OptimizationStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        try:
            result = {}
            
            # 目標に応じた最適化を実行
            for goal in task.parameters["goals"]:
                if goal == "reduce_tokens":
                    optimization_result = await self._optimize_for_token_reduction(window, task.parameters["constraints"])
                    result["token_reduction"] = optimization_result
                
                elif goal == "improve_clarity":
                    optimization_result = await self._optimize_for_clarity(window)
                    result["clarity_improvement"] = optimization_result
                
                elif goal == "enhance_relevance":
                    optimization_result = await self._optimize_for_relevance(window)
                    result["relevance_enhancement"] = optimization_result
                
                elif goal == "remove_redundancy":
                    optimization_result = await self._optimize_for_redundancy_removal(window)
                    result["redundancy_removal"] = optimization_result
                
                elif goal == "improve_structure":
                    optimization_result = await self._optimize_for_structure(window)
                    result["structure_improvement"] = optimization_result
                
                task.progress += 1.0 / len(task.parameters["goals"])
            
            task.result = result
            task.status = OptimizationStatus.COMPLETED
            task.completed_at = datetime.now()
            
        except Exception as e:
            task.status = OptimizationStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            logger.error(f"Optimization task {task.id} failed: {str(e)}")
    
    async def _optimize_for_token_reduction(self, 
                                          window: ContextWindow, 
                                          constraints: Dict[str, Any]) -> Dict[str, Any]:
        """トークン削減最適化"""
        
        target_reduction = constraints.get("target_token_reduction", 0.2)  # 20%削減がデフォルト
        min_tokens = constraints.get("min_tokens", 100)
        preserve_elements = constraints.get("preserve_element_types", [])
        
        original_tokens = window.current_tokens
        target_tokens = max(int(original_tokens * (1 - target_reduction)), min_tokens)
        
        optimization_strategies = []
        
        # 戦略1: 低優先度要素の削除
        if window.current_tokens > target_tokens:
            removal_result = await self._remove_low_priority_elements(window, target_tokens, preserve_elements)
            optimization_strategies.append(removal_result)
        
        # 戦略2: 内容の圧縮
        if window.current_tokens > target_tokens:
            compression_result = await self._compress_content(window, target_tokens)
            optimization_strategies.append(compression_result)
        
        # 戦略3: 重複除去
        if window.current_tokens > target_tokens:
            deduplication_result = await self._remove_duplicates(window)
            optimization_strategies.append(deduplication_result)
        
        return {
            "original_tokens": original_tokens,
            "final_tokens": window.current_tokens,
            "reduction_achieved": (original_tokens - window.current_tokens) / original_tokens,
            "target_achieved": window.current_tokens <= target_tokens,
            "strategies_applied": optimization_strategies
        }
    
    async def _remove_low_priority_elements(self, 
                                          window: ContextWindow, 
                                          target_tokens: int,
                                          preserve_types: List[str]) -> Dict[str, Any]:
        """低優先度要素の削除"""
        
        removed_elements = []
        preserved_types = set(preserve_types)
        
        # 優先度順にソート（低優先度から）
        sortable_elements = [
            elem for elem in window.elements 
            if elem.type.value not in preserved_types
        ]
        sortable_elements.sort(key=lambda x: x.priority)
        
        for element in sortable_elements:
            if window.current_tokens <= target_tokens:
                break
            
            if window.remove_element(element.id):
                removed_elements.append({
                    "id": element.id,
                    "type": element.type.value,
                    "priority": element.priority,
                    "tokens": element.token_count,
                    "content_preview": element.content[:100] + "..." if len(element.content) > 100 else element.content
                })
        
        return {
            "strategy": "low_priority_removal",
            "removed_count": len(removed_elements),
            "removed_elements": removed_elements,
            "tokens_saved": sum(elem["tokens"] for elem in removed_elements)
        }
    
    async def _compress_content(self, window: ContextWindow, target_tokens: int) -> Dict[str, Any]:
        """内容の圧縮"""
        
        compressed_elements = []
        
        for element in window.elements[:]:  # コピーを作成して反復
            if window.current_tokens <= target_tokens:
                break
            
            if len(element.content) > 200:  # 長いコンテンツのみ圧縮
                compressed_content = await self._compress_single_content(element.content)
                
                if compressed_content and len(compressed_content) < len(element.content):
                    original_tokens = element.token_count
                    element.content = compressed_content
                    new_tokens = element.token_count
                    
                    compressed_elements.append({
                        "id": element.id,
                        "original_length": len(element.content),
                        "compressed_length": len(compressed_content),
                        "tokens_saved": original_tokens - new_tokens
                    })
        
        return {
            "strategy": "content_compression",
            "compressed_count": len(compressed_elements),
            "compressed_elements": compressed_elements,
            "total_tokens_saved": sum(elem["tokens_saved"] for elem in compressed_elements)
        }
    
    async def _compress_single_content(self, content: str) -> Optional[str]:
        """単一コンテンツの圧縮"""
        try:
            prompt = f"""
            以下のテキストを要点を保持しながら50%程度に圧縮してください。
            重要な情報を失わないよう注意してください。

            元のテキスト:
            {content}

            圧縮されたテキスト:
            """
            
            response = self.model.generate_content(prompt)
            compressed = response.text.strip()
            
            # 圧縮率をチェック
            if len(compressed) < len(content) * 0.9:  # 少なくとも10%削減
                return compressed
            
            return None
            
        except Exception as e:
            logger.error(f"Content compression failed: {str(e)}")
            return None
    
    async def _remove_duplicates(self, window: ContextWindow) -> Dict[str, Any]:
        """重複除去"""
        
        removed_duplicates = []
        seen_content = set()
        
        for element in window.elements[:]:  # コピーを作成
            # 内容の正規化（小文字化、空白除去）
            normalized_content = re.sub(r'\s+', ' ', element.content.lower().strip())
            
            if normalized_content in seen_content:
                if window.remove_element(element.id):
                    removed_duplicates.append({
                        "id": element.id,
                        "type": element.type.value,
                        "tokens": element.token_count,
                        "content_preview": element.content[:100] + "..."
                    })
            else:
                seen_content.add(normalized_content)
        
        return {
            "strategy": "duplicate_removal",
            "removed_count": len(removed_duplicates),
            "removed_duplicates": removed_duplicates,
            "tokens_saved": sum(elem["tokens"] for elem in removed_duplicates)
        }
    
    async def _optimize_for_clarity(self, window: ContextWindow) -> Dict[str, Any]:
        """明確性向上最適化"""
        
        improved_elements = []
        
        for element in window.elements:
            if len(element.content) > 100:  # 長いコンテンツのみ
                improved_content = await self._improve_content_clarity(element.content)
                
                if improved_content and improved_content != element.content:
                    element.content = improved_content
                    improved_elements.append({
                        "id": element.id,
                        "type": element.type.value,
                        "improvement_type": "clarity"
                    })
        
        return {
            "strategy": "clarity_improvement",
            "improved_count": len(improved_elements),
            "improved_elements": improved_elements
        }
    
    async def _improve_content_clarity(self, content: str) -> Optional[str]:
        """コンテンツの明確性向上"""
        try:
            prompt = f"""
            以下のテキストをより明確で理解しやすく書き直してください。
            内容は変えずに、表現を改善してください：

            元のテキスト:
            {content}

            改善されたテキスト:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Clarity improvement failed: {str(e)}")
            return None
    
    async def _optimize_for_relevance(self, window: ContextWindow) -> Dict[str, Any]:
        """関連性向上最適化"""
        
        if not window.elements:
            return {"strategy": "relevance_enhancement", "changes": []}
        
        # 主要トピックを特定
        all_content = " ".join([elem.content for elem in window.elements])
        main_topics = await self._extract_main_topics(all_content)
        
        relevance_scores = []
        reordered_elements = []
        
        # 各要素の関連性をスコア化
        for element in window.elements:
            relevance_score = await self._calculate_relevance_score(element.content, main_topics)
            relevance_scores.append((element, relevance_score))
        
        # 関連性順に並び替え
        relevance_scores.sort(key=lambda x: x[1], reverse=True)
        window.elements = [elem for elem, score in relevance_scores]
        
        return {
            "strategy": "relevance_enhancement",
            "main_topics": main_topics,
            "element_count": len(window.elements),
            "reordered": True
        }
    
    async def _extract_main_topics(self, content: str) -> List[str]:
        """主要トピック抽出"""
        try:
            prompt = f"""
            以下のテキストから主要なトピック3-5個を抽出してください：

            {content}

            トピックのみを改行区切りで回答してください。
            """
            
            response = self.model.generate_content(prompt)
            topics = [topic.strip() for topic in response.text.strip().split('\n') if topic.strip()]
            return topics[:5]  # 最大5個
            
        except Exception as e:
            logger.error(f"Topic extraction failed: {str(e)}")
            return []
    
    async def _calculate_relevance_score(self, content: str, main_topics: List[str]) -> float:
        """関連性スコア計算"""
        if not main_topics:
            return 0.5
        
        try:
            topics_text = ", ".join(main_topics)
            prompt = f"""
            以下のコンテンツが、主要トピック「{topics_text}」にどの程度関連しているか、
            0から1の数値で評価してください（1が最も関連）：

            コンテンツ: {content[:500]}...

            関連性スコア（数値のみ）:
            """
            
            response = self.model.generate_content(prompt)
            score = float(response.text.strip())
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Relevance scoring failed: {str(e)}")
            return 0.5
    
    async def _optimize_for_redundancy_removal(self, window: ContextWindow) -> Dict[str, Any]:
        """冗長性除去最適化"""
        
        # セマンティックな重複を検出
        semantic_duplicates = await self._detect_semantic_duplicates(window.elements)
        
        merged_elements = []
        removed_elements = []
        
        for duplicate_group in semantic_duplicates:
            if len(duplicate_group) > 1:
                # 最も包括的な要素を選択し、他をマージ
                primary_element = max(duplicate_group, key=lambda x: len(x.content))
                other_elements = [elem for elem in duplicate_group if elem != primary_element]
                
                # 他の要素をマージ
                merged_content = await self._merge_similar_contents([elem.content for elem in duplicate_group])
                primary_element.content = merged_content
                
                # 他の要素を削除
                for elem in other_elements:
                    if window.remove_element(elem.id):
                        removed_elements.append(elem.id)
                
                merged_elements.append(primary_element.id)
        
        return {
            "strategy": "redundancy_removal",
            "merged_elements": len(merged_elements),
            "removed_elements": len(removed_elements),
            "duplicate_groups": len(semantic_duplicates)
        }
    
    async def _detect_semantic_duplicates(self, elements: List[ContextElement]) -> List[List[ContextElement]]:
        """セマンティックな重複検出"""
        if len(elements) < 2:
            return []
        
        try:
            # 要素間の類似度を計算
            similarity_matrix = []
            for i, elem1 in enumerate(elements):
                row = []
                for j, elem2 in enumerate(elements):
                    if i == j:
                        row.append(1.0)
                    else:
                        similarity = await self._calculate_semantic_similarity(elem1.content, elem2.content)
                        row.append(similarity)
                similarity_matrix.append(row)
            
            # 類似度が高い要素をグループ化
            duplicate_groups = []
            processed = set()
            
            for i, similarities in enumerate(similarity_matrix):
                if i in processed:
                    continue
                
                group = [elements[i]]
                processed.add(i)
                
                for j, similarity in enumerate(similarities):
                    if j != i and j not in processed and similarity > 0.7:  # 70%以上の類似度
                        group.append(elements[j])
                        processed.add(j)
                
                if len(group) > 1:
                    duplicate_groups.append(group)
            
            return duplicate_groups
            
        except Exception as e:
            logger.error(f"Semantic duplicate detection failed: {str(e)}")
            return []
    
    async def _calculate_semantic_similarity(self, content1: str, content2: str) -> float:
        """セマンティック類似度計算"""
        try:
            prompt = f"""
            以下の2つのテキストの意味的類似度を0から1の数値で評価してください：

            テキスト1: {content1[:300]}...
            テキスト2: {content2[:300]}...

            類似度（数値のみ）:
            """
            
            response = self.model.generate_content(prompt)
            similarity = float(response.text.strip())
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {str(e)}")
            return 0.0
    
    async def _merge_similar_contents(self, contents: List[str]) -> str:
        """類似コンテンツのマージ"""
        try:
            contents_text = "\n\n".join([f"テキスト{i+1}: {content}" for i, content in enumerate(contents)])
            
            prompt = f"""
            以下の類似したテキストを1つに統合してください。
            重複する情報を削除し、すべての重要な情報を保持してください：

            {contents_text}

            統合されたテキスト:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Content merging failed: {str(e)}")
            return contents[0] if contents else ""
    
    async def _optimize_for_structure(self, window: ContextWindow) -> Dict[str, Any]:
        """構造最適化"""
        
        # 要素タイプ別に分類
        type_groups = {}
        for element in window.elements:
            element_type = element.type.value
            if element_type not in type_groups:
                type_groups[element_type] = []
            type_groups[element_type].append(element)
        
        # 最適な順序を決定
        optimal_order = ["system", "user", "assistant", "function", "tool"]
        reordered_elements = []
        
        for element_type in optimal_order:
            if element_type in type_groups:
                # 同タイプ内では優先度順、作成日順でソート
                type_elements = sorted(
                    type_groups[element_type],
                    key=lambda x: (x.priority, x.created_at),
                    reverse=True
                )
                reordered_elements.extend(type_elements)
        
        # 分類されなかった要素を追加
        for element_type, elements in type_groups.items():
            if element_type not in optimal_order:
                reordered_elements.extend(elements)
        
        window.elements = reordered_elements
        
        return {
            "strategy": "structure_optimization",
            "type_groups": {k: len(v) for k, v in type_groups.items()},
            "reordered": True,
            "optimal_order_applied": optimal_order
        }
    
    def get_optimization_task(self, task_id: str) -> Optional[OptimizationTask]:
        """最適化タスクを取得"""
        return self.optimization_tasks.get(task_id)
    
    def list_optimization_tasks(self, context_id: Optional[str] = None) -> List[OptimizationTask]:
        """最適化タスク一覧を取得"""
        tasks = list(self.optimization_tasks.values())
        
        if context_id:
            tasks = [task for task in tasks if task.context_id == context_id]
        
        # 作成日時順でソート
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks
    
    async def auto_optimize_context(self, window: ContextWindow) -> Dict[str, Any]:
        """自動最適化（すべての最適化を適用）"""
        
        analysis_prompt = f"""
        以下のコンテキストを分析し、最適な最適化戦略を提案してください：

        要素数: {len(window.elements)}
        総トークン数: {window.current_tokens}
        トークン使用率: {window.utilization_ratio:.2%}

        要素詳細:
        {self._format_elements_for_analysis(window.elements)}

        以下の最適化目標から最適なものを選択してください：
        - reduce_tokens: トークン数削減
        - improve_clarity: 明確性向上
        - enhance_relevance: 関連性向上
        - remove_redundancy: 冗長性除去
        - improve_structure: 構造改善

        JSON形式で回答:
        {{
            "recommended_goals": ["goal1", "goal2"],
            "priority": "high|medium|low",
            "reasoning": "選択理由",
            "constraints": {{
                "preserve_element_types": ["system"],
                "target_token_reduction": 0.2
            }}
        }}
        """
        
        try:
            response = self.model.generate_content(analysis_prompt)
            recommendations = json.loads(response.text)
            
            # 推奨された最適化を実行
            task = await self.optimize_context_window(
                window,
                recommendations["recommended_goals"],
                recommendations.get("constraints", {})
            )
            
            return {
                "task_id": task.id,
                "recommendations": recommendations,
                "optimization_started": True
            }
            
        except Exception as e:
            logger.error(f"Auto optimization failed: {str(e)}")
            raise
    
    def _format_elements_for_analysis(self, elements: List[ContextElement]) -> str:
        """分析用要素フォーマット"""
        formatted = []
        for i, elem in enumerate(elements[:10]):  # 最初の10要素のみ
            preview = elem.content[:100] + "..." if len(elem.content) > 100 else elem.content
            formatted.append(f"{i+1}. [{elem.type.value}] 優先度:{elem.priority} トークン:{elem.token_count} - {preview}")
        
        if len(elements) > 10:
            formatted.append(f"... 他{len(elements) - 10}要素")
        
        return "\n".join(formatted)