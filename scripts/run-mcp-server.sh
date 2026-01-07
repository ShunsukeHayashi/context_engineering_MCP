#!/bin/bash

# Set the API URLs
export AI_GUIDES_API_URL="${AI_GUIDES_API_URL:-http://localhost:8888}"
export CONTEXT_API_URL="${CONTEXT_API_URL:-http://localhost:9003}"
export WORKFLOW_API_URL="${WORKFLOW_API_URL:-http://localhost:9002}"

# Change to MCP server directory
cd "$(dirname "$0")/../mcp-server"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..." >&2
    npm install >&2
fi

# Run the enhanced Context Engineering MCP server
exec node context_mcp_server.js