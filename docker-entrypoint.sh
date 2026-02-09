#!/bin/bash
set -e

# Cleanup handler for termination signals
cleanup() {
    echo "Termination signal received, stopping processes..."
    kill $BOT_PID $DASHBOARD_PID 2>/dev/null || true
    wait $BOT_PID $DASHBOARD_PID 2>/dev/null || true
    exit 0
}

# Install signal handlers
trap cleanup SIGTERM SIGINT

# Read dashboard port from env (default: 5555)
DASHBOARD_PORT="${DASHBOARD_PORT:-5555}"

# Start the bot in background (runs migrations on startup via bot.py on_startup)
echo "Starting Telegram bot..."
python main.py &
BOT_PID=$!

# Start the dashboard in background
echo "Starting dashboard on port ${DASHBOARD_PORT}..."
python -m uvicorn app.web.dashboard:app --host 0.0.0.0 --port ${DASHBOARD_PORT} &
DASHBOARD_PID=$!

echo "Bot and dashboard started"
echo "Dashboard is available at http://localhost:${DASHBOARD_PORT}"

# Wait for processes to exit
wait $BOT_PID $DASHBOARD_PID
