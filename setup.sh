#!/bin/bash

echo "Setting up RCA Platform..."

# Check if Python 3.12.3 is available
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install and setup Ollama
echo "Setting up Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &

# Wait for Ollama to start
sleep 5

# Pull LLaMA3 model
echo "Pulling LLaMA3 model..."
ollama pull llama3

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "1. Start the backend: cd backend && python main.py"
echo "2. Start the frontend: cd frontend && streamlit run streamlit_app.py"
echo ""
echo "API will be available at: http://localhost:8000"
echo "Streamlit UI will be available at: http://localhost:8501"
