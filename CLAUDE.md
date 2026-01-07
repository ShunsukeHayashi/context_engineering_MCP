# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Context Engineering MCP Platform - AI-powered context management for AI applications with:

- **AI Guides API** (port 8888): Curated guides from OpenAI, Google, Anthropic with Gemini-powered search
- **Context Engineering API** (port 9001): Context lifecycle management with analysis, optimization, templates
- **MCP Server**: Native Claude Desktop integration with 15 tools
- **Workflow System** (port 9000): AI-driven workflow generation and task management

## Architecture

```
├── main.py                      # AI Guides FastAPI server (port 8888)
├── gemini_service.py            # Gemini AI integration
├── context_engineering/         # Context Engineering system (port 9001)
│   ├── context_api.py           # FastAPI server with WebSocket
│   ├── context_models.py        # ContextWindow, ContextElement, ContextSession, PromptTemplate
│   ├── context_analyzer.py      # AI-powered analysis (quality scoring, semantic analysis)
│   ├── context_optimizer.py     # Multi-goal optimization (token reduction, clarity, relevance)
│   └── template_manager.py      # Template CRUD, AI generation, rendering
├── mcp-server/
│   ├── index.js                 # Basic AI guides MCP server
│   └── context_mcp_server.js    # Full platform MCP server (15 tools)
├── workflow_system/             # Workflow management (port 9000)
│   ├── workflow_api.py          # API + WebSocket + dashboard
│   ├── workflow_generator.py    # Gemini-powered workflow generation
│   └── agent_manager.py         # Task assignment and load balancing
└── operations/                  # Operational scripts
    └── miyabi-ops.sh            # Miyabi autonomous development wrapper
```

## Commands

### Quick Start
```bash
./quickstart.sh                  # Interactive setup, starts all services
```

### Miyabi (Autonomous Development)
```bash
npm run miyabi:doctor            # Health check (run first)
npm run miyabi:run               # Start autonomous development
npm run miyabi:status            # Check status

# Or via operations script
./operations/miyabi-ops.sh run
./operations/miyabi-ops.sh doctor
```

### AI Guides API (port 8888)
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8888 --reload
```

### Context Engineering API (port 9001)
```bash
cd context_engineering
python -m venv context_env && source context_env/bin/activate
pip install -r requirements.txt
python context_api.py
# Or: ./start_context_engineering.sh
```

### MCP Server
```bash
cd mcp-server
npm install
node context_mcp_server.js       # Runs via stdio for Claude Desktop
```

### Workflow System (port 9000)
```bash
cd workflow_system
pip install -r requirements.txt
./start_workflow_system.sh
```

### Docker
```bash
docker build -t context-engineering-platform .
docker-compose up -d
docker-compose logs -f
```

### Stop Services
```bash
./stop.sh                        # Created by quickstart.sh
```

## Environment Variables

**Required:**
- `GEMINI_API_KEY` - Google Gemini API key
- `GITHUB_TOKEN` - GitHub token for Miyabi (or use `gh auth login`)

**Optional:**
- `CONTEXT_API_URL` - Context API URL for MCP (default: http://localhost:9001)
- `AI_GUIDES_API_URL` - Guides API URL for MCP (default: http://localhost:8888)

## MCP Configuration

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "context-engineering": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-server/context_mcp_server.js"]
    }
  }
}
```

## Key APIs

### AI Guides (8888)
- `GET /health` - Health check
- `GET /guides` - List all guides
- `GET /guides/search?query=` - Keyword search
- `POST /guides/search/gemini` - Semantic search with Gemini
- `GET /guides/{title}/analyze` - AI-powered guide analysis

### Context Engineering (9001)
- `POST /api/sessions` - Create session
- `POST /api/sessions/{id}/windows` - Create context window
- `POST /api/contexts/{window_id}/elements` - Add element
- `POST /api/contexts/{window_id}/analyze` - Analyze context quality
- `POST /api/contexts/{window_id}/optimize` - Optimize with goals
- `POST /api/contexts/{window_id}/auto-optimize` - AI-driven optimization
- `POST /api/templates` - Create template
- `POST /api/templates/generate` - AI-generate template
- `GET /api/stats` - System statistics
- `WS /ws` - WebSocket for real-time updates

### Workflow System (9000)
- `POST /api/workflows` - Create workflow from user input
- `POST /api/workflows/{id}/start` - Execute workflow
- `POST /api/tasks/{id}/decompose` - AI task decomposition
- `GET /api/dashboard/stats` - Dashboard statistics

## MCP Tools (15 total)

**AI Guides (4):** `list_ai_guides`, `search_ai_guides`, `search_guides_with_gemini`, `analyze_guide`

**Context Engineering (7):** `create_context_session`, `create_context_window`, `add_context_element`, `analyze_context`, `optimize_context`, `auto_optimize_context`, `get_context_stats`

**Templates (4):** `create_prompt_template`, `generate_prompt_template`, `list_prompt_templates`, `render_template`

## Key Data Models

**ContextWindow:** Token-limited container with elements, quality metrics
- `max_tokens`: Default 8192
- `reserved_tokens`: Default 512 (for response)
- `utilization_ratio`: Current usage percentage

**ContextElement:** Individual context item
- `type`: system | user | assistant | function | tool | multimodal
- `priority`: 1-10 (higher = more important)
- `tags`: For filtering/organization

**PromptTemplate:** Reusable prompt with variables
- `type`: completion | chat | instruct | fewshot | chain_of_thought | roleplay
- Variables extracted from `{variable_name}` patterns

## Tech Stack

- **Python:** FastAPI, Pydantic, google-generativeai, uvicorn, websockets
- **Node.js:** @modelcontextprotocol/sdk, node-fetch (ESM, Node 18+)
- **AI:** Gemini 2.0 Flash for all AI operations
- **Real-time:** WebSocket for dashboard updates
- **Operations:** Miyabi for autonomous development

## Notes

- Context windows have token limits; elements are rejected if limit exceeded
- Optimization tasks run async; poll `/api/optimization/{task_id}` for status
- MCP server uses stdio transport (no HTTP)
- All Python code uses async/await patterns
- Sessions and templates stored in-memory (no persistence)
