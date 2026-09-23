#!/bin/bash
# ==============================================================================
# GreenClaim AI — Local Full-Stack Development Runner
# ==============================================================================

set -e

# Detect script directory (workspace root)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "================================================================="
echo "🌱 Starting GreenClaim AI Full-Stack Workspace"
echo "================================================================="

# Trap to kill both processes on Ctrl+C or exit
cleanup() {
  echo ""
  echo "🛑 Shutting down backend and frontend processes..."
  kill $(jobs -p) 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 1. Start FastAPI Backend
echo "🚀 [1/2] Starting FastAPI Backend on http://localhost:8000..."
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 2

# Check if backend is alive
curl -s http://localhost:8000/api/v1/health > /dev/null && echo "✅ Backend online & SQLite seeded!" || echo "⏳ Waiting for backend to finish startup..."

# 2. Start Vite Frontend
echo "💻 [2/2] Starting Vite React Frontend on http://localhost:5173..."
cd "$ROOT_DIR/frontend"
npm run dev -- --host &
FRONTEND_PID=$!

echo ""
echo "================================================================="
echo "✨ GreenClaim AI is running!"
echo "   - Web Dashboard: http://localhost:5173"
echo "   - FastAPI Swagger Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/api/v1/health"
echo "================================================================="
echo "Press [Ctrl+C] to stop all servers."

# Wait for background processes
wait
