#!/bin/bash

# Context Engineering Platform - Quick Start Script
# This script gets you up and running in 2 minutes!

echo "🧠 Context Engineering Platform - Quick Start"
echo "==========================================="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Please install Python 3.10+ from https://python.org"
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "   Please install Node.js 16+ from https://nodejs.org"
    exit 1
fi

echo "✅ Prerequisites checked"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📋 Created .env file from .env.example"
    else
        echo "⚠️  No .env file found. Creating one..."
        echo "GEMINI_API_KEY=" > .env
    fi
fi

# Check for API key
if ! grep -q "GEMINI_API_KEY=.+" .env; then
    echo ""
    echo "🔑 Gemini API Key Required"
    echo "   Get your free API key at: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "   Enter your Gemini API key: " api_key
    sed -i.bak "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$api_key/" .env
    rm .env.bak 2>/dev/null
    echo "   ✅ API key saved"
fi

echo ""
echo "🚀 Starting Context Engineering Platform..."
echo ""

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Kill existing processes on our ports
if check_port 9001; then
    echo "⚠️  Port 9001 is in use. Stopping existing process..."
    lsof -ti:9001 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Start Context Engineering API
echo "1️⃣  Starting Context Engineering API..."
cd context_engineering

# Create virtual environment if it doesn't exist
if [ ! -d "context_env" ]; then
    python3 -m venv context_env
    echo "   Created virtual environment"
fi

# Activate and install dependencies
source context_env/bin/activate
pip install -r ../requirements.txt -q

# Start the API server in background
nohup python context_api.py > ../logs/context_api.log 2>&1 &
API_PID=$!
echo "   ✅ Context Engineering API started (PID: $API_PID)"

cd ..

# Wait for API to be ready
echo "   Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:9001/api/stats >/dev/null 2>&1; then
        echo "   ✅ API is ready!"
        break
    fi
    sleep 1
done

# Start MCP Server
echo ""
echo "2️⃣  Starting MCP Server..."
cd mcp-server

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install -q
fi

# Start MCP server in background
nohup node context_mcp_server.js > ../logs/mcp_server.log 2>&1 &
MCP_PID=$!
echo "   ✅ MCP Server started (PID: $MCP_PID)"

cd ..

# Create logs directory if it doesn't exist
mkdir -p logs

# Display success message
echo ""
echo "🎉 Success! Context Engineering Platform is running!"
echo ""
echo "📍 Access Points:"
echo "   • Dashboard: http://localhost:9001"
echo "   • API Docs:  http://localhost:9001/docs"
echo "   • Logs:      ./logs/"
echo ""
echo "🚀 Next Steps:"
echo "   1. Run the example: python examples/quick_start.py"
echo "   2. Configure Claude Desktop (see README)"
echo "   3. Start optimizing your AI contexts!"
echo ""
echo "📖 Documentation: https://github.com/ShunsukeHayashi/context_-engineering_MCP"
echo ""
echo "To stop the servers:"
echo "   kill $API_PID $MCP_PID"
echo ""

# Save PIDs for easy shutdown
echo "$API_PID" > logs/api.pid
echo "$MCP_PID" > logs/mcp.pid

# Create stop script
cat > stop.sh << 'EOF'
#!/bin/bash
echo "Stopping Context Engineering Platform..."
if [ -f logs/api.pid ]; then
    kill $(cat logs/api.pid) 2>/dev/null
    rm logs/api.pid
fi
if [ -f logs/mcp.pid ]; then
    kill $(cat logs/mcp.pid) 2>/dev/null
    rm logs/mcp.pid
fi
echo "✅ All services stopped"
EOF
chmod +x stop.sh

echo "💡 Tip: Use ./stop.sh to stop all services"
echo ""