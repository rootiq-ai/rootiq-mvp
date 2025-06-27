import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DB_DIR.mkdir(exist_ok=True)

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_BASE_URL = f"http://localhost:{API_PORT}"

# Streamlit Configuration
STREAMLIT_HOST = "0.0.0.0"
STREAMLIT_PORT = 8501

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"

# ChromaDB Configuration
CHROMA_COLLECTION_NAME = "observability_data"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# RCA Configuration
MAX_CONTEXT_LENGTH = 4000
TOP_K_SIMILAR_INCIDENTS = 5
CONFIDENCE_THRESHOLD = 0.7

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
