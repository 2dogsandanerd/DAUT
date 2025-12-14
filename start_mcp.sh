#!/bin/bash
# start_mcp.sh
# Starts the MCP Server with configured environment variables

# Default Key if not set (Change this in production!)
export MCP_API_KEY=${MCP_API_KEY:-"secret-token-123"}
export MCP_PORT=${MCP_PORT:-8001} # Use 8001 to avoid conflict with UI maybe? Or user said 8000. Let's stick to 8000 if UI is on 8501.
export MCP_HOST=${MCP_HOST:-"0.0.0.0"}

# Check if venv exists
if [ -d "venv" ]; then
    PYTHON="./venv/bin/python"
else
    PYTHON="python"
fi

echo "🚀 Starting DAUT MCP Server..."
echo "🔑 API Key: ${MCP_API_KEY}"
echo "📡 Port: ${MCP_PORT}"

$PYTHON mcp_entry.py
