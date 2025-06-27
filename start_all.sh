#!/bin/bash

echo "🚀 Starting RCA Platform..."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

# Check if required ports are available
if ! check_port 11434; then
    echo "Ollama might already be running on port 11434"
fi

if ! check_port 8000; then
    echo "❌ Port 8000 is in use. Please stop any service running on this port."
    exit 1
fi

if ! check_port 8501; then
    echo "❌ Port 8501 is in use. Please stop any service running on this port."
    exit 1
fi

# Create log directory
mkdir -p logs

echo "📡 Starting Ollama service..."
# Start Ollama in background
ollama serve > logs/ollama.log 2>&1 &
OLLAMA_PID=$!
echo "Ollama PID: $OLLAMA_PID"

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to initialize..."
sleep 10

# Check if LLaMA3 model exists, if not pull it
echo "🔍 Checking for LLaMA3 model..."
if ! ollama list | grep -q "llama3"; then
    echo "📥 Pulling LLaMA3 model (this may take several minutes)..."
    ollama pull llama3
    if [ $? -eq 0 ]; then
        echo "✅ LLaMA3 model downloaded successfully"
    else
        echo "❌ Failed to download LLaMA3 model"
        kill $OLLAMA_PID
        exit 1
    fi
else
    echo "✅ LLaMA3 model already available"
fi

echo "🔧 Starting Backend API..."
# Start backend in background
cd backend
export PYTHONPATH="../:$PYTHONPATH"
python3 main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 15

# Check if backend is healthy
echo "🔍 Checking backend health..."
for i in {1..10}; do
    if curl -s http://localhost:8000/ping > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Backend failed to start"
        kill $OLLAMA_PID $BACKEND_PID
        exit 1
    fi
    sleep 2
done

echo "🖥️  Starting Frontend UI..."
# Start frontend in background
cd frontend
export PYTHONPATH="../:$PYTHONPATH"
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 10

# Save PIDs for cleanup
echo "$OLLAMA_PID" > logs/ollama.pid
echo "$BACKEND_PID" > logs/backend.pid  
echo "$FRONTEND_PID" > logs/frontend.pid

echo ""
echo "🎉 RCA Platform is now running!"
echo ""
echo "📱 Access the application:"
echo "   🌐 Streamlit UI: http://localhost:8501"
echo "   📖 API Docs: http://localhost:8000/docs"
echo "   ❤️  Health Check: http://localhost:8000/api/v1/health"
echo ""
echo "📊 Service Status:"
echo "   🤖 Ollama (LLaMA3): Running (PID: $OLLAMA_PID)"
echo "   🔧 Backend API: Running (PID: $BACKEND_PID)"
echo "   🖥️  Frontend UI: Running (PID: $FRONTEND_PID)"
echo ""
echo "📄 Logs are available in the logs/ directory"
echo "🛑 To stop all services, run: ./stop_all.sh"
echo ""
echo "⏳ Please wait a moment for all services to fully initialize..."
echo "   Then open http://localhost:8501 in your browser"
