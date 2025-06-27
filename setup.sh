#!/bin/bash

echo "Setting up RCA Platform for Python 3.12.3..."

# Check if Python 3.12.3 is available
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "pip3 not found. Installing pip..."
    sudo apt update
    sudo apt install -y python3-pip
fi

# Upgrade pip
echo "Upgrading pip..."
pip3 install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install and setup Ollama
echo "Setting up Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "Ollama already installed"
fi

# Create data directory
echo "Creating data directories..."
mkdir -p data/chroma_db

# Create run scripts
echo "Creating run scripts..."

# Backend run script
cat > run_backend.sh << 'EOF'
#!/bin/bash
echo "Starting RCA Platform Backend..."
cd backend
export PYTHONPATH="../:$PYTHONPATH"
python3 main.py
EOF

# Frontend run script
cat > run_frontend.sh << 'EOF'
#!/bin/bash
echo "Starting RCA Platform Frontend..."
cd frontend
export PYTHONPATH="../:$PYTHONPATH"
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
EOF

# Ollama setup script
cat > run_ollama.sh << 'EOF'
#!/bin/bash
echo "Starting Ollama and pulling LLaMA3..."

# Start Ollama service in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
echo "Waiting for Ollama to start..."
sleep 10

# Pull LLaMA3 model
echo "Pulling LLaMA3 model (this may take a while)..."
ollama pull llama3

echo "Ollama setup complete!"
echo "Ollama is running with PID: $OLLAMA_PID"
EOF

# Make scripts executable
chmod +x run_backend.sh
chmod +x run_frontend.sh
chmod +x run_ollama.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "1. Terminal 1: ./run_ollama.sh     # Start Ollama and pull model"
echo "2. Terminal 2: ./run_backend.sh    # Start FastAPI backend"
echo "3. Terminal 3: ./run_frontend.sh   # Start Streamlit frontend"
echo ""
echo "📱 Access the application:"
echo "- Streamlit UI: http://localhost:8501"
echo "- API Documentation: http://localhost:8000/docs"
echo "- API Health: http://localhost:8000/api/v1/health"
echo ""
echo "⚠️  Note: Make sure to start Ollama first and wait for LLaMA3 to download!"
