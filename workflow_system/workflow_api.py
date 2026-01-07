import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio
from contextlib import asynccontextmanager

from workflow_models import Workflow, Task, Agent, WorkflowStatus, TaskStatus
from workflow_generator import WorkflowGenerator, TaskDecomposer
from agent_manager import AgentManager, WorkflowExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# リクエスト・レスポンスモデル
class WorkflowRequest(BaseModel):
    user_input: str
    context: Optional[Dict[str, Any]] = None

class TaskUpdateRequest(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # 切断されたコネクションを削除
        for conn in disconnected:
            self.disconnect(conn)

# グローバル変数
workflows_storage: Dict[str, Workflow] = {}
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリケーション起動時
    logger.info("Workflow API Server starting...")
    
    # バックグラウンドタスクを開始
    asyncio.create_task(background_workflow_processor())
    asyncio.create_task(progress_tracker())
    
    yield
    
    # アプリケーション終了時
    logger.info("Workflow API Server shutting down...")

app = FastAPI(
    title="Workflow Management API",
    description="AI-powered workflow generation, task decomposition, and agent assignment system",
    version="1.0.0",
    lifespan=lifespan
)

# 初期化関数
async def initialize_components():
    global workflow_generator, task_decomposer, agent_manager, workflow_executor
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    workflow_generator = WorkflowGenerator(gemini_api_key)
    task_decomposer = TaskDecomposer(gemini_api_key)
    agent_manager = AgentManager(gemini_api_key)
    workflow_executor = WorkflowExecutor(gemini_api_key)

# API エンドポイント

@app.on_event("startup")
async def startup_event():
    await initialize_components()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """ダッシュボードページを返す"""
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/workflows")
async def create_workflow(request: WorkflowRequest) -> Dict[str, Any]:
    """新しいワークフローを生成"""
    try:
        workflow = await workflow_generator.generate_workflow(
            request.user_input, 
            request.context
        )
        
        workflows_storage[workflow.id] = workflow
        
        # WebSocket経由でクライアントに通知
        await websocket_manager.broadcast({
            "type": "workflow_created",
            "workflow_id": workflow.id,
            "workflow": {
                "id": workflow.id,
                "title": workflow.title,
                "status": workflow.status.value,
                "tasks_count": len(workflow.tasks),
                "agents_count": len(workflow.agents)
            }
        })
        
        return {
            "success": True,
            "workflow_id": workflow.id,
            "title": workflow.title,
            "tasks_count": len(workflow.tasks),
            "agents_count": len(workflow.agents)
        }
        
    except Exception as e:
        logger.error(f"Workflow creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflows")
async def list_workflows() -> Dict[str, Any]:
    """全ワークフローの一覧を取得"""
    workflows_data = []
    
    for workflow in workflows_storage.values():
        workflows_data.append({
            "id": workflow.id,
            "title": workflow.title,
            "status": workflow.status.value,
            "progress": workflow.progress_percentage,
            "tasks_count": len(workflow.tasks),
            "completed_tasks": len([t for t in workflow.tasks if t.status == TaskStatus.COMPLETED]),
            "agents_count": len(workflow.agents),
            "created_at": workflow.created_at.isoformat()
        })
    
    return {"workflows": workflows_data}

@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """特定のワークフローの詳細を取得"""
    if workflow_id not in workflows_storage:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows_storage[workflow_id]
    
    return {
        "id": workflow.id,
        "title": workflow.title,
        "description": workflow.description,
        "status": workflow.status.value,
        "progress": workflow.progress_percentage,
        "created_at": workflow.created_at.isoformat(),
        "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
        "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "assigned_agent_id": task.assigned_agent_id,
                "priority": task.priority,
                "estimated_duration": task.estimated_duration,
                "dependencies": task.dependencies
            }
            for task in workflow.tasks
        ],
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "type": agent.type.value,
                "capabilities": agent.capabilities,
                "current_tasks": len(agent.current_tasks),
                "max_tasks": agent.max_concurrent_tasks,
                "load_percentage": agent.load_percentage
            }
            for agent in workflow.agents
        ]
    }

@app.post("/api/workflows/{workflow_id}/start")
async def start_workflow(workflow_id: str) -> Dict[str, Any]:
    """ワークフローの実行を開始"""
    if workflow_id not in workflows_storage:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows_storage[workflow_id]
    
    if workflow.status == WorkflowStatus.EXECUTING:
        return {"message": "Workflow is already running"}
    
    # バックグラウンドでワークフローを実行
    asyncio.create_task(execute_workflow_background(workflow))
    
    await websocket_manager.broadcast({
        "type": "workflow_started",
        "workflow_id": workflow.id
    })
    
    return {"message": "Workflow execution started"}

@app.post("/api/tasks/{task_id}/update")
async def update_task(task_id: str, request: TaskUpdateRequest) -> Dict[str, Any]:
    """タスクの状態を更新"""
    # タスクを見つける
    task = None
    workflow = None
    
    for wf in workflows_storage.values():
        for t in wf.tasks:
            if t.id == task_id:
                task = t
                workflow = wf
                break
        if task:
            break
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # タスク状態を更新
    try:
        old_status = task.status
        task.status = TaskStatus(request.status)
        
        if request.result:
            task.result = request.result
        
        if request.errors:
            task.errors.extend(request.errors)
        
        if task.status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            
            # エージェントのタスクリストから削除
            if task.assigned_agent_id:
                agent = next((a for a in workflow.agents if a.id == task.assigned_agent_id), None)
                if agent and task.id in agent.current_tasks:
                    agent.current_tasks.remove(task.id)
        
        # 進捗更新を通知
        await websocket_manager.broadcast({
            "type": "task_updated",
            "workflow_id": workflow.id,
            "task_id": task.id,
            "old_status": old_status.value,
            "new_status": task.status.value,
            "progress": workflow.progress_percentage
        })
        
        return {"message": "Task updated successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")

@app.post("/api/tasks/{task_id}/decompose")
async def decompose_task(task_id: str) -> Dict[str, Any]:
    """タスクを小さなサブタスクに分解"""
    # タスクを見つける
    task = None
    workflow = None
    
    for wf in workflows_storage.values():
        for t in wf.tasks:
            if t.id == task_id:
                task = t
                workflow = wf
                break
        if task:
            break
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        subtasks = await task_decomposer.decompose_task(task)
        
        # 元のタスクを置き換え
        task_index = workflow.tasks.index(task)
        workflow.tasks[task_index:task_index+1] = subtasks
        
        await websocket_manager.broadcast({
            "type": "task_decomposed",
            "workflow_id": workflow.id,
            "original_task_id": task.id,
            "subtasks_count": len(subtasks)
        })
        
        return {
            "message": f"Task decomposed into {len(subtasks)} subtasks",
            "subtasks": [{"id": st.id, "title": st.title} for st in subtasks]
        }
        
    except Exception as e:
        logger.error(f"Task decomposition failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats")
async def get_dashboard_stats() -> Dict[str, Any]:
    """ダッシュボード用の統計情報を取得"""
    total_workflows = len(workflows_storage)
    total_tasks = sum(len(wf.tasks) for wf in workflows_storage.values())
    completed_tasks = sum(
        len([t for t in wf.tasks if t.status == TaskStatus.COMPLETED])
        for wf in workflows_storage.values()
    )
    total_agents = sum(len(wf.agents) for wf in workflows_storage.values())
    active_agents = sum(
        len([a for a in wf.agents if len(a.current_tasks) > 0])
        for wf in workflows_storage.values()
    )
    
    # タスク状態分布
    task_distribution = {status.value: 0 for status in TaskStatus}
    for workflow in workflows_storage.values():
        for task in workflow.tasks:
            task_distribution[task.status.value] += 1
    
    # エージェント負荷情報
    agent_loads = []
    for workflow in workflows_storage.values():
        for agent in workflow.agents:
            agent_loads.append({
                "name": agent.name,
                "load_percentage": agent.load_percentage
            })
    
    return {
        "total_workflows": total_workflows,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "total_agents": total_agents,
        "active_agents": active_agents,
        "task_distribution": task_distribution,
        "agent_loads": agent_loads
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket接続エンドポイント"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # クライアントからのメッセージを待つ（キープアライブ）
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

# バックグラウンド処理

async def background_workflow_processor():
    """バックグラウンドでワークフローを処理"""
    while True:
        try:
            for workflow in workflows_storage.values():
                if workflow.status == WorkflowStatus.EXECUTING:
                    # 準備完了のタスクをエージェントにアサイン
                    await agent_manager.assign_tasks(workflow)
            
            await asyncio.sleep(10)  # 10秒ごとに処理
            
        except Exception as e:
            logger.error(f"Background processor error: {str(e)}")
            await asyncio.sleep(10)

async def execute_workflow_background(workflow: Workflow):
    """ワークフローをバックグラウンドで実行"""
    try:
        await workflow_executor.execute_workflow(workflow)
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        workflow.status = WorkflowStatus.FAILED

async def progress_tracker():
    """進捗トラッキング"""
    while True:
        try:
            for workflow in workflows_storage.values():
                if workflow.status == WorkflowStatus.EXECUTING:
                    # 進捗更新を通知
                    await websocket_manager.broadcast({
                        "type": "progress_update",
                        "workflow_id": workflow.id,
                        "progress": workflow.progress_percentage,
                        "task_distribution": {
                            status.value: count 
                            for status, count in workflow.task_distribution.items()
                        }
                    })
            
            await asyncio.sleep(5)  # 5秒ごとに更新
            
        except Exception as e:
            logger.error(f"Progress tracker error: {str(e)}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002)