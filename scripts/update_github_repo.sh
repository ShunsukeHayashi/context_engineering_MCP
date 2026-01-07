#!/bin/bash

# Update GitHub repository description and topics

echo "📝 Updating GitHub repository metadata..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "   Install it from: https://cli.github.com/"
    echo ""
    echo "   Or manually update on GitHub:"
    echo "   1. Go to: https://github.com/ShunsukeHayashi/context_-engineering_MCP"
    echo "   2. Click the gear icon next to 'About'"
    echo "   3. Add description and topics"
    exit 1
fi

# Update repository description
gh repo edit ShunsukeHayashi/context_-engineering_MCP \
  --description "🧠 AI-powered Context Engineering platform with 52% token reduction, MCP integration for Claude Desktop, and intelligent prompt optimization" \
  --homepage "https://github.com/ShunsukeHayashi/context_-engineering_MCP#readme"

# Add topics
gh api repos/ShunsukeHayashi/context_-engineering_MCP/topics \
  --method PUT \
  --field names='["context-engineering","mcp","claude-desktop","prompt-engineering","ai-optimization","gemini-ai","llm","prompt-templates","token-optimization","fastapi","context-management","ai-tools","developer-tools","python","nodejs"]'

echo "✅ Repository metadata updated!"
echo ""
echo "📌 Added:"
echo "   - Description: AI-powered Context Engineering platform..."
echo "   - Topics: context-engineering, mcp, claude-desktop, etc."
echo ""
echo "🌟 Your repository is now more discoverable!"