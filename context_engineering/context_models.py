from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from enum import Enum
from datetime import datetime
import uuid
import json

class ContextType(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"
    MULTIMODAL = "multimodal"

class ContextQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    NEEDS_IMPROVEMENT = "needs_improvement"

class PromptTemplateType(Enum):
    COMPLETION = "completion"
    CHAT = "chat"
    INSTRUCT = "instruct"
    FEWSHOT = "fewshot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    ROLEPLAY = "roleplay"

class OptimizationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ContextElement:
    """Context Engineering の基本要素"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    type: ContextType = ContextType.USER
    role: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def token_count(self) -> int:
        """簡易トークン数推定（日本語・英語混合対応）"""
        # 日本語は文字ベースで推定（1文字≈0.5トークン）、英語は単語ベース
        # 混合テキストは文字数÷3で近似
        if not self.content:
            return 0
        return max(1, len(self.content) // 3)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "type": self.type.value,
            "role": self.role,
            "metadata": self.metadata,
            "tags": self.tags,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

@dataclass
class PromptTemplate:
    """プロンプトテンプレート管理"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    template: str = ""
    variables: List[str] = field(default_factory=list)
    type: PromptTemplateType = PromptTemplateType.COMPLETION
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    quality_score: float = 0.0
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def render(self, variables: Dict[str, Any]) -> str:
        """テンプレートに変数を適用してレンダリング"""
        rendered = self.template
        for var, value in variables.items():
            placeholder = f"{{{var}}}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered
    
    def extract_variables(self) -> List[str]:
        """テンプレートから変数を抽出"""
        import re
        variables = re.findall(r'\{(\w+)\}', self.template)
        return list(set(variables))

@dataclass
class ContextWindow:
    """コンテキストウィンドウ管理"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    elements: List[ContextElement] = field(default_factory=list)
    max_tokens: int = 8192
    reserved_tokens: int = 512  # レスポンス用予約
    template_id: Optional[str] = None
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def current_tokens(self) -> int:
        """現在のトークン数"""
        return sum(element.token_count for element in self.elements)
    
    @property
    def available_tokens(self) -> int:
        """利用可能トークン数"""
        return self.max_tokens - self.current_tokens - self.reserved_tokens
    
    @property
    def utilization_ratio(self) -> float:
        """トークン使用率"""
        return self.current_tokens / self.max_tokens
    
    def add_element(self, element: ContextElement) -> bool:
        """要素追加（トークン制限チェック付き）"""
        if self.current_tokens + element.token_count <= self.max_tokens - self.reserved_tokens:
            self.elements.append(element)
            return True
        return False
    
    def remove_element(self, element_id: str) -> bool:
        """要素削除"""
        for i, element in enumerate(self.elements):
            if element.id == element_id:
                del self.elements[i]
                return True
        return False
    
    def optimize_for_tokens(self) -> Dict[str, Any]:
        """トークン制限に合わせた最適化"""
        optimization_result = {
            "removed_elements": [],
            "compressed_elements": [],
            "tokens_saved": 0
        }
        
        if self.current_tokens <= self.max_tokens - self.reserved_tokens:
            return optimization_result
        
        # 優先度の低い要素から削除
        sorted_elements = sorted(self.elements, key=lambda x: x.priority)
        original_tokens = self.current_tokens
        
        while self.current_tokens > self.max_tokens - self.reserved_tokens and self.elements:
            removed = sorted_elements.pop(0)
            self.elements.remove(removed)
            optimization_result["removed_elements"].append(removed.id)
        
        optimization_result["tokens_saved"] = original_tokens - self.current_tokens
        return optimization_result

@dataclass
class ContextAnalysis:
    """コンテキスト分析結果"""
    context_id: str
    analysis_type: str
    metrics: Dict[str, float] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    issues: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "analysis_type": self.analysis_type,
            "metrics": self.metrics,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "quality_score": self.quality_score,
            "issues": self.issues,
            "strengths": self.strengths,
            "analyzed_at": self.analyzed_at.isoformat()
        }

@dataclass
class OptimizationTask:
    """コンテキスト最適化タスク"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context_id: str = ""
    optimization_type: str = ""  # token_reduction, clarity_improvement, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: OptimizationStatus = OptimizationStatus.PENDING
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class ContextSession:
    """コンテキストセッション管理"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    windows: List[ContextWindow] = field(default_factory=list)
    active_window_id: Optional[str] = None
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def get_active_window(self) -> Optional[ContextWindow]:
        """アクティブなコンテキストウィンドウを取得"""
        if not self.active_window_id:
            return None
        
        for window in self.windows:
            if window.id == self.active_window_id:
                return window
        return None
    
    def create_window(self, max_tokens: int = 8192) -> ContextWindow:
        """新しいコンテキストウィンドウを作成"""
        window = ContextWindow(max_tokens=max_tokens)
        self.windows.append(window)
        self.active_window_id = window.id
        return window

@dataclass
class MultimodalContext:
    """マルチモーダルコンテキスト"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text_content: str = ""
    image_urls: List[str] = field(default_factory=list)
    audio_urls: List[str] = field(default_factory=list)
    video_urls: List[str] = field(default_factory=list)
    document_urls: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_status: str = "pending"  # pending, processing, completed, failed
    extracted_content: Dict[str, str] = field(default_factory=dict)  # modality -> content
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_token_estimate(self) -> int:
        """全モダリティのトークン数推定"""
        text_tokens = len(self.text_content.split()) * 1.3
        
        # 画像: 約1000トークン/画像として推定
        image_tokens = len(self.image_urls) * 1000
        
        # 抽出されたコンテンツ
        extracted_tokens = sum(
            len(content.split()) * 1.3 
            for content in self.extracted_content.values()
        )
        
        return int(text_tokens + image_tokens + extracted_tokens)

@dataclass 
class RAGContext:
    """RAG (Retrieval-Augmented Generation) コンテキスト"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    retrieved_documents: List[Dict[str, Any]] = field(default_factory=list)
    similarity_scores: List[float] = field(default_factory=list)
    retrieval_metadata: Dict[str, Any] = field(default_factory=dict)
    context_synthesis: str = ""  # 検索結果を統合したコンテキスト
    relevance_scores: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_retrieved_document(self, document: Dict[str, Any], score: float):
        """検索結果ドキュメントを追加"""
        self.retrieved_documents.append(document)
        self.similarity_scores.append(score)
    
    def synthesize_context(self, max_tokens: int = 2000) -> str:
        """検索結果を統合してコンテキストを生成"""
        if not self.retrieved_documents:
            return ""
        
        # スコア順にソート
        sorted_docs = sorted(
            zip(self.retrieved_documents, self.similarity_scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        synthesized = []
        current_tokens = 0
        
        for doc, score in sorted_docs:
            doc_content = doc.get('content', str(doc))
            doc_tokens = len(doc_content.split()) * 1.3
            
            if current_tokens + doc_tokens > max_tokens:
                break
            
            synthesized.append(f"[関連度: {score:.2f}] {doc_content}")
            current_tokens += doc_tokens
        
        self.context_synthesis = "\n\n".join(synthesized)
        return self.context_synthesis
