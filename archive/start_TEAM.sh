#!/bin/bash

echo "🌉 Starting Bridge Design System - TEAM Launch"
echo "========================================================"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down all services..."
    kill $(jobs -p) 2>/dev/null
    wait
    echo "✅ All services stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start services in background
echo "🚀 Starting Phoenix Server..."
uv run python -m phoenix.server.main serve &
PHOENIX_PID=$!

sleep 3

echo "🚀 Starting LCARS Monitoring..."
uv run python -m bridge_design_system.monitoring.lcars_interface &
LCARS_PID=$!

sleep 2

echo ""
echo "🎯 Background services started successfully!"
echo "========================================"
echo "📊 Phoenix UI:     http://localhost:6006"
echo "🖥️  LCARS Monitor:  http://localhost:5000"
echo "========================================"
echo "🚀 Starting Main System in foreground..."
echo "   (You can interact with it normally)"
echo "   (Press Ctrl+C to stop all services)"
echo "========================================"

# Start main system in foreground (interactive)
# Pass any additional arguments to the main system
if [ $# -gt 0 ]; then
    echo "📝 Additional flags: $@"
    OTEL_BACKEND=phoenix uv run python -m bridge_design_system.main --interactive --disable-gaze "$@"
else
    OTEL_BACKEND=phoenix uv run python -m bridge_design_system.main --interactive --disable-gaze
fi

# When main system exits, cleanup background services
echo ""
echo "🛑 Main system exited, cleaning up background services..."
kill $(jobs -p) 2>/dev/null
wait
echo "✅ All services stopped"