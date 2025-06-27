#!/bin/bash

echo "🛑 Stopping RCA Platform..."

# Function to kill process and its children
kill_process() {
    if [ -f "$1" ]; then
        PID=$(cat "$1")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping process $PID..."
            pkill -P $PID  # Kill children first
            kill $PID
            sleep 2
            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
            fi
        fi
        rm -f "$1"
    fi
}

# Stop services in reverse order
echo "🖥️  Stopping Frontend..."
kill_process "logs/frontend.pid"

echo "🔧 Stopping Backend..."
kill_process "logs/backend.pid"

echo "🤖 Stopping Ollama..."
kill_process "logs/ollama.pid"

# Additional cleanup - kill any remaining processes
echo "🧹 Cleaning up remaining processes..."

# Kill any remaining Streamlit processes
pkill -f "streamlit run"

# Kill any remaining FastAPI processes
pkill -f "main.py"

# Kill any remaining Ollama processes
pkill -f "ollama serve"

# Clean up port usage
echo "🔌 Cleaning up ports..."
fuser -k 8501/tcp 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 11434/tcp 2>/dev/null || true

echo ""
echo "✅ RCA Platform stopped successfully!"
echo "📄 Logs are preserved in the logs/ directory"
echo ""
echo "🚀 To start again, run: ./start_all.sh"
