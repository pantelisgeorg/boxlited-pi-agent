#!/usr/bin/env bash
# Start the pdf-tools MCP server as a Streamable-HTTP endpoint for the
# llama.cpp web UI (and any browser-based MCP client).
#
# Usage:  ./start-pdf-mcp.sh
# Then in the llama UI (http://localhost:8080) -> Settings -> MCP Servers:
#   URL:       http://localhost:8765/mcp
#   Transport: Streamable HTTP
#
# Ctrl+C to stop. Leave this terminal open while you use the tools.
set -euo pipefail

PORT="${PORT:-8765}"
SERVER="$(dirname "$0")/pdf_server.py"
UV="/home/george/.local/bin/uv"

echo "Starting pdf-tools MCP bridge on http://localhost:${PORT}/mcp"
echo "  server script: $SERVER"
echo "  (add this URL in the llama UI with transport 'Streamable HTTP')"
echo

exec npx -y supergateway \
  --stdio "$UV run --script \"$SERVER\"" \
  --outputTransport streamableHttp --streamableHttpPath /mcp --stateful \
  --port "$PORT" --cors
