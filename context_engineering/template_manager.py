import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import google.generativeai as genai
from pathlib import Path

from .context_models import PromptTemplate, PromptTemplateType, ContextElement, ContextWindow

logger = logging.getLogger(__name__)

class TemplateManager:
    """プロンプトテンプレート管理システム"""
    
    def __init__(self, gemini_api_key: str, storage_path: str = "templates"):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_templates()
        self._initialize_default_templates()
    
    def _load_templates(self):
        """保存されたテンプレートを読み込み"""
        template_files = self.storage_path.glob("*.json")
        for file_path in template_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    template = self._dict_to_template(data)
                    self.templates[template.id] = template
            except Exception as e:
                logger.error(f"Failed to load template from {file_path}: {str(e)}")
    
    def _save_template(self, template: PromptTemplate):
        """テンプレートを保存"""
        file_path = self.storage_path / f"{template.id}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._template_to_dict(template), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save template {template.id}: {str(e)}")
    
    def _template_to_dict(self, template: PromptTemplate) -> Dict[str, Any]:
        """テンプレートを辞書に変換"""
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "template": template.template,
            "variables": template.variables,
            "type": template.type.value,
            "category": template.category,
            "tags": template.tags,
            "usage_count": template.usage_count,
            "quality_score": template.quality_score,
            "created_by": template.created_by,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }
    
    def _dict_to_template(self, data: Dict[str, Any]) -> PromptTemplate:
        """辞書からテンプレートを作成"""
        return PromptTemplate(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            template=data["template"],
            variables=data["variables"],
            type=PromptTemplateType(data["type"]),
            category=data["category"],
            tags=data["tags"],
            usage_count=data["usage_count"],
            quality_score=data["quality_score"],
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
    
    def _initialize_default_templates(self):
        """デフォルトテンプレートの初期化"""
        if not self.templates:
            default_templates = [
                {
                    "name": "基本的な質問応答",
                    "description": "シンプルな質問応答用テンプレート",
                    "template": "質問: {question}\n\n以下の情報を参考に回答してください:\n{context}\n\n回答:",
                    "type": PromptTemplateType.COMPLETION,
                    "category": "qa",
                    "tags": ["basic", "qa"]
                },
                {
                    "name": "専門家ロールプレイ",
                    "description": "特定の専門分野の専門家として回答",
                    "template": "あなたは{expertise}の専門家です。{years}年の経験があります。\n\n質問: {question}\n\n専門知識を活かして詳細に回答してください:",
                    "type": PromptTemplateType.ROLEPLAY,
                    "category": "expert",
                    "tags": ["roleplay", "expert"]
                },
                {
                    "name": "段階的思考プロセス",
                    "description": "ステップバイステップで問題を解決",
                    "template": "問題: {problem}\n\n以下の手順で段階的に解決してください:\n1. 問題の理解\n2. 必要な情報の整理\n3. 解決方法の検討\n4. 最適解の選択\n5. 結論\n\n解答:",
                    "type": PromptTemplateType.CHAIN_OF_THOUGHT,
                    "category": "problem_solving",
                    "tags": ["step_by_step", "analysis"]
                },
                {
                    "name": "Few-Shot学習",
                    "description": "例を示して同様のタスクを実行",
                    "template": "以下の例を参考に、同様のタスクを実行してください:\n\n{examples}\n\n新しいタスク: {task}\n回答:",
                    "type": PromptTemplateType.FEWSHOT,
                    "category": "learning",
                    "tags": ["few_shot", "examples"]
                },
                {
                    "name": "コード生成",
                    "description": "プログラミングコード生成用",
                    "template": "言語: {language}\n要件: {requirements}\n\n以下の仕様でコードを生成してください:\n- {specifications}\n\nコード:\n```{language}\n{code}\n```\n\n説明:",
                    "type": PromptTemplateType.COMPLETION,
                    "category": "coding",
                    "tags": ["code", "programming"]
                }
            ]
            
            for template_data in default_templates:
                template = PromptTemplate(
                    name=template_data["name"],
                    description=template_data["description"],
                    template=template_data["template"],
                    type=template_data["type"],
                    category=template_data["category"],
                    tags=template_data["tags"],
                    created_by="system"
                )
                template.variables = template.extract_variables()
                self.create_template(template)
    
    def create_template(self, template: PromptTemplate) -> str:
        """新しいテンプレートを作成"""
        template.variables = template.extract_variables()
        template.updated_at = datetime.now()
        
        self.templates[template.id] = template
        self._save_template(template)
        
        logger.info(f"Created template: {template.name} ({template.id})")
        return template.id
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """テンプレートを取得"""
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[PromptTemplate]:
        """テンプレート一覧を取得"""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        # 使用回数と品質スコアでソート
        templates.sort(key=lambda t: (t.usage_count, t.quality_score), reverse=True)
        return templates
    
    def search_templates(self, query: str) -> List[PromptTemplate]:
        """テンプレートを検索"""
        query_lower = query.lower()
        matching_templates = []
        
        for template in self.templates.values():
            score = 0
            
            # 名前での一致
            if query_lower in template.name.lower():
                score += 3
            
            # 説明での一致
            if query_lower in template.description.lower():
                score += 2
            
            # タグでの一致
            if any(query_lower in tag.lower() for tag in template.tags):
                score += 2
            
            # カテゴリでの一致
            if query_lower in template.category.lower():
                score += 1
            
            if score > 0:
                matching_templates.append((template, score))
        
        # スコア順にソート
        matching_templates.sort(key=lambda x: x[1], reverse=True)
        return [template for template, score in matching_templates]
    
    def update_template(self, template_id: str, **updates) -> bool:
        """テンプレートを更新"""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.now()
        if 'template' in updates:
            template.variables = template.extract_variables()
        
        self._save_template(template)
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """テンプレートを削除"""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        if template.created_by == "system":
            logger.warning(f"Cannot delete system template: {template_id}")
            return False
        
        del self.templates[template_id]
        
        # ファイルも削除
        file_path = self.storage_path / f"{template_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        return True
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> Optional[str]:
        """テンプレートをレンダリング"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        # 使用回数を増加
        template.usage_count += 1
        template.updated_at = datetime.now()
        self._save_template(template)
        
        return template.render(variables)
    
    async def generate_template(self, 
                              purpose: str, 
                              examples: List[str] = None,
                              constraints: List[str] = None) -> PromptTemplate:
        """AIでテンプレートを自動生成"""
        
        examples_text = ""
        if examples:
            examples_text = f"\n\n期待する出力例:\n" + "\n".join([f"- {ex}" for ex in examples])
        
        constraints_text = ""
        if constraints:
            constraints_text = f"\n\n制約条件:\n" + "\n".join([f"- {c}" for c in constraints])
        
        prompt = f"""
        以下の目的のためのプロンプトテンプレートを作成してください:

        目的: {purpose}{examples_text}{constraints_text}

        以下の形式でJSON回答してください:
        {{
            "name": "テンプレート名",
            "description": "テンプレートの説明",
            "template": "実際のテンプレート（変数は{{variable_name}}の形式）",
            "type": "completion|chat|instruct|fewshot|chain_of_thought|roleplay",
            "category": "カテゴリ名",
            "tags": ["タグ1", "タグ2"]
        }}
        
        テンプレートには適切な変数を含めてください。
        """
        
        try:
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            
            template = PromptTemplate(
                name=data["name"],
                description=data["description"],
                template=data["template"],
                type=PromptTemplateType(data["type"]),
                category=data["category"],
                tags=data["tags"],
                created_by="ai_generated"
            )
            
            template_id = self.create_template(template)
            logger.info(f"AI generated template: {template.name}")
            return template
            
        except Exception as e:
            logger.error(f"Template generation failed: {str(e)}")
            raise
    
    async def optimize_template(self, template_id: str) -> Dict[str, Any]:
        """テンプレートを最適化"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        prompt = f"""
        以下のプロンプトテンプレートを分析し、改善提案を行ってください:

        名前: {template.name}
        説明: {template.description}
        テンプレート:
        {template.template}

        以下の観点で分析してください:
        1. 明確性 - 指示が明確で理解しやすいか
        2. 完全性 - 必要な情報がすべて含まれているか
        3. 効率性 - 無駄な記述がないか
        4. 一貫性 - 用語や形式が一貫しているか
        5. 柔軟性 - 様々な場面で使える汎用性があるか

        JSON形式で回答:
        {{
            "current_score": {{
                "clarity": 0.8,
                "completeness": 0.7,
                "efficiency": 0.9,
                "consistency": 0.8,
                "flexibility": 0.6
            }},
            "issues": ["問題点1", "問題点2"],
            "improvements": ["改善案1", "改善案2"],
            "optimized_template": "最適化されたテンプレート",
            "explanation": "最適化の説明"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            # 品質スコアを更新
            scores = result["current_score"]
            overall_score = sum(scores.values()) / len(scores)
            template.quality_score = overall_score
            self._save_template(template)
            
            return result
            
        except Exception as e:
            logger.error(f"Template optimization failed: {str(e)}")
            raise
    
    def get_template_stats(self) -> Dict[str, Any]:
        """テンプレート統計情報を取得"""
        if not self.templates:
            return {}
        
        templates = list(self.templates.values())
        
        # カテゴリ別集計
        categories = {}
        for template in templates:
            if template.category not in categories:
                categories[template.category] = 0
            categories[template.category] += 1
        
        # タイプ別集計
        types = {}
        for template in templates:
            type_name = template.type.value
            if type_name not in types:
                types[type_name] = 0
            types[type_name] += 1
        
        # 使用統計
        usage_counts = [t.usage_count for t in templates]
        quality_scores = [t.quality_score for t in templates if t.quality_score > 0]
        
        return {
            "total_templates": len(templates),
            "categories": categories,
            "types": types,
            "total_usage": sum(usage_counts),
            "avg_usage_per_template": sum(usage_counts) / len(templates) if templates else 0,
            "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "most_used_template": max(templates, key=lambda t: t.usage_count).name if templates else None,
            "highest_quality_template": max(templates, key=lambda t: t.quality_score).name if quality_scores else None
        }

class ContextTemplateIntegrator:
    """コンテキストとテンプレートの統合"""
    
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
    
    def apply_template_to_context(self, 
                                context_window: ContextWindow, 
                                template_id: str, 
                                variables: Dict[str, Any]) -> ContextWindow:
        """テンプレートをコンテキストウィンドウに適用"""
        
        rendered = self.template_manager.render_template(template_id, variables)
        if not rendered:
            raise ValueError(f"Failed to render template {template_id}")
        
        # 新しいコンテキスト要素を作成
        template_element = ContextElement(
            content=rendered,
            type=ContextType.SYSTEM,
            role="template",
            metadata={
                "template_id": template_id,
                "variables": variables,
                "applied_at": datetime.now().isoformat()
            },
            tags=["template", "generated"],
            priority=8  # テンプレートは高優先度
        )
        
        # コンテキストウィンドウに追加
        success = context_window.add_element(template_element)
        if not success:
            raise ValueError("Failed to add template to context window (token limit exceeded)")
        
        context_window.template_id = template_id
        return context_window
    
    def extract_template_from_context(self, context_window: ContextWindow) -> Optional[PromptTemplate]:
        """コンテキストウィンドウからテンプレートを抽出"""
        if len(context_window.elements) < 2:
            return None
        
        # 要素の内容を分析してパターンを抽出
        contents = [elem.content for elem in context_window.elements]
        
        # 共通パターンを見つけて変数化
        # 実装は簡略化
        template_content = "\n\n".join(contents)
        
        # 自動的に変数を検出（数値、固有名詞等を変数化）
        variables_detected = self._detect_variables(template_content)
        
        for var_name, var_values in variables_detected.items():
            # 最初の値を変数プレースホルダーに置換
            if var_values:
                template_content = template_content.replace(var_values[0], f"{{{var_name}}}")
        
        template = PromptTemplate(
            name="Extracted Template",
            description="コンテキストから抽出されたテンプレート",
            template=template_content,
            type=PromptTemplateType.COMPLETION,
            category="extracted",
            tags=["extracted", "auto_generated"],
            created_by="auto_extract"
        )
        
        return template
    
    def _detect_variables(self, content: str) -> Dict[str, List[str]]:
        """コンテンツから変数候補を検出"""
        variables = {}
        
        # 数値パターン
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', content)
        if numbers:
            variables["number"] = numbers
        
        # 日付パターン
        dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b', content)
        if dates:
            variables["date"] = dates
        
        # メールアドレス
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        if emails:
            variables["email"] = emails
        
        # URL
        urls = re.findall(r'https?://[^\s]+', content)
        if urls:
            variables["url"] = urls
        
        return variables