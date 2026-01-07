#!/bin/bash

echo "Testing MCP Server..."
echo

# Test initialization
echo "1. Testing initialization..."
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"0.1.0","clientInfo":{"name":"test-client","version":"1.0.0"},"capabilities":{}},"id":1}' | ./run-mcp-server.sh 2>/dev/null | jq .result

echo
echo "2. Testing list tools..."
echo '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}' | ./run-mcp-server.sh 2>/dev/null | jq .result.tools[].name

echo
echo "MCP Server is ready to use in Claude Desktop!"
echo "Restart Claude Desktop to load the 'ai-guides' MCP server."