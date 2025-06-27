# 🔍 RootIQ-Generative AI-Driven Observability for Automated Root Cause Analysis in Modern IT Systems

![Screenshot 2025-06-27 at 5 32 19 PM](https://github.com/user-attachments/assets/79693aff-d51c-4e5a-b5e5-bf67bf30afda)

A comprehensive MVP solution that leverages LLaMA3 and RAG (Retrieval-Augmented Generation) to automatically analyze logs, metrics, and traces for intelligent root cause analysis.

## ✅ Python 3.12.3 Compatibility

This platform is **fully compatible with Python 3.12.3** and has been thoroughly tested on Ubuntu systems. All dependencies and import structures have been optimized for this Python version.

## 🚀 Features

- **Multi-Modal Analysis**: Process logs, metrics, and traces simultaneously
- **AI-Powered RCA**: Uses LLaMA3 via Ollama for intelligent analysis
- **RAG Integration**: ChromaDB-powered knowledge base for historical incident correlation
- **Interactive UI**: Clean Streamlit interface for easy interaction
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Real-time Processing**: Fast analysis with confidence scoring
- **Knowledge Base**: Persistent storage of incidents for improved analysis over time
- **Easy Deployment**: One-command setup and startup scripts

## 🏗️ Architecture

```
rca-platform/
├── __init__.py
├── config.py                  # Configuration settings
├── requirements.txt           # Python 3.12.3 compatible dependencies
├── setup.sh                  # Initial setup script
├── start_all.sh              # Start all services (recommended)
├── stop_all.sh               # Stop all services
├── run_backend.sh            # Start backend only
├── run_frontend.sh           # Start frontend only
├── run_ollama.sh             # Start Ollama only
├── README.md
├── frontend/                 # Streamlit UI
│   └── streamlit_app.py
├── backend/                  # FastAPI Backend
│   ├── main.py              # Main application entry
│   ├── models/              # Pydantic schemas
│   ├── services/            # Core business logic
│   │   ├── llm_service.py   # LLaMA3/Ollama integration
│   │   ├── rag_service.py   # RAG and vector search
│   │   └── rca_service.py   # Main RCA orchestration
│   ├── api/                 # API endpoints
│   └── utils/               # Utilities (VectorDB)
├── data/                    # Data storage
│   └── chroma_db/          # ChromaDB vector database
└── logs/                   # Application logs
    ├── ollama.log
    ├── backend.log
    └── frontend.log
```

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **LLM**: LLaMA3 via Ollama
- **Vector Database**: ChromaDB
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Language**: Python 3.12.3

## 📋 Prerequisites

- **Ubuntu** 20.04+ (tested on Ubuntu 22.04)
- **Python 3.12.3** (exactly this version)
- **pip3** (Python package manager)
- **curl** (for Ollama installation)
- **8GB+ RAM** (recommended for LLaMA3)
- **10GB+ free disk space** (for LLaMA3 model)

## 🚀 Quick Start (Recommended)

### 1. Setup
```bash
# Clone or create the project directory
mkdir rca-platform && cd rca-platform

# Copy all the provided files to their respective locations
# (Use the file structure shown above)

# Make scripts executable
chmod +x *.sh

# Run initial setup
./setup.sh
```

### 2. Start Everything (One Command!)
```bash
# Start all services with one command
./start_all.sh
```

This will:
- Start Ollama service
- Download LLaMA3 model (if not present)
- Start the FastAPI backend
- Start the Streamlit frontend
- Show you all the URLs to access

### 3. Access the Application
- **Streamlit UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/v1/health

### 4. Stop Everything
```bash
./stop_all.sh
```

## 🔧 Manual Start (Alternative)

If you prefer to start services individually:

```bash
# Terminal 1 - Start Ollama
./run_ollama.sh

# Terminal 2 - Start Backend (wait for Ollama to be ready)
./run_backend.sh

# Terminal 3 - Start Frontend (wait for backend to be ready)
./run_frontend.sh
```

## 📖 Usage Guide

### Via Streamlit UI

1. **Open the UI** at http://localhost:8501
2. **Check System Status** in the sidebar (should show green checkmarks)
3. **Enter observability data** in the three text boxes:
   - **Logs**: Application logs, error messages, events
   - **Metrics**: Performance metrics, resource usage data
   - **Traces**: Distributed tracing information
4. **Optional**: Save data to knowledge base using "Save to KB" buttons
5. **Click "Run RCA Analysis"** to generate the analysis
6. **Review results** in the organized tabs:
   - Root cause summary with confidence level
   - Evidence supporting the analysis
   - Related historical incidents
   - Remediation suggestions

### Via API

**Perform RCA Analysis:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "logs": "2024-01-01 10:00:00 ERROR Database connection failed",
       "metrics": "cpu_usage: 95%, memory: 8GB/8GB",
       "traces": "span_id: abc123, operation: db_query, duration: 5000ms"
     }'
```

**Upload Data to Knowledge Base:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload/logs" \
     -H "Content-Type: text/plain" \
     -d "Application startup error: Failed to connect to database"
```

**Check System Health:**
```bash
curl http://localhost:8000/api/v1/health
```

## 🧪 Example Data for Testing

### Sample Logs
```
2024-01-01 10:00:00 ERROR [DatabaseService] Connection timeout to primary database
2024-01-01 10:00:05 WARN [DatabaseService] Failover to secondary database initiated
2024-01-01 10:00:10 INFO [HealthCheck] Service marked as degraded
2024-01-01 10:00:15 ERROR [UserService] Unable to authenticate user due to database unavailability
2024-01-01 10:00:20 ERROR [OrderService] Order processing failed - database connection lost
```

### Sample Metrics
```
cpu_usage_percent: 85.2
memory_usage_mb: 7680
memory_total_mb: 8192
disk_io_wait_ms: 45
database_connections_active: 95
database_connections_max: 100
response_time_p50_ms: 1200
response_time_p95_ms: 2500
error_rate_percent: 15.3
```

### Sample Traces
```
span_id: abc123-def456-ghi789
trace_id: xyz789-uvw456-rst123
operation: user_login_flow
duration_ms: 2500
status: error
error_type: database_timeout
parent_span: web_request_handler
child_spans: [auth_validation, database_query, session_creation]
tags: {service: user-service, environment: production, region: us-east-1}
```

## 🔍 Understanding RCA Output

### Root Cause Summary
A concise explanation of the identified root cause with confidence level (High/Medium/Low).

### Evidence
Specific data points that support the root cause analysis, each with:
- Description of the evidence
- Confidence score (0.0-1.0)
- Source (logs/metrics/traces)

### Related Incidents
Historical incidents with similar patterns:
- Similarity score
- Previous resolutions
- Timestamps

### Remediation Suggestions
Actionable steps prioritized by urgency:
- Implementation steps
- Estimated time
- Priority level (Low/Medium/High/Critical)

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analyze` | Perform RCA analysis |
| POST | `/api/v1/ingest` | Ingest observability data |
| POST | `/api/v1/upload/{type}` | Upload logs/metrics/traces |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/stats` | Knowledge base statistics |
| DELETE | `/api/v1/knowledge-base` | Clear knowledge base |

## 🐛 Troubleshooting

### Common Issues

**1. "Import Error" or "Module Not Found"**
```bash
# Ensure you're in the project root directory
cd rca-platform

# Check Python version
python3 --version  # Should be 3.12.3

# Reinstall dependencies
pip3 install -r requirements.txt
```

**2. "Ollama Service Not Starting"**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Manual start
ollama serve

# In another terminal, pull the model
ollama pull llama3
```

**3. "API Connection Errors"**
```bash
# Check if backend is running
curl http://localhost:8000/ping

# Check backend logs
tail -f logs/backend.log

# Restart backend
./stop_all.sh
./start_all.sh
```

**4. "Memory Issues"**
```bash
# Check available memory
free -h

# If low memory, close other applications
# Or use a smaller model (if available)
```

**5. "Port Already in Use"**
```bash
# Check what's using the ports
sudo lsof -i :8000
sudo lsof -i :8501
sudo lsof -i :11434

# Kill processes if needed
sudo kill -9 <PID>

# Or use the stop script
./stop_all.sh
```

### Logs and Debugging

- **All logs**: Check the `logs/` directory
- **Backend logs**: `tail -f logs/backend.log`
- **Frontend logs**: `tail -f logs/frontend.log`
- **Ollama logs**: `tail -f logs/ollama.log`

### Python 3.12.3 Specific Issues

If you encounter import or compatibility issues:

1. **Verify Python version**: `python3 --version`
2. **Update pip**: `pip3 install --upgrade pip`
3. **Reinstall dependencies**: `pip3 install -r requirements.txt --force-reinstall`
4. **Check virtual environment** (if using one): Ensure it's Python 3.12.3

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# API Configuration
API_PORT = 8000
STREAMLIT_PORT = 8501

# LLM Configuration
OLLAMA_MODEL = "llama3"  # Change model if needed

# RAG Configuration
TOP_K_SIMILAR_INCIDENTS = 5
CONFIDENCE_THRESHOLD = 0.7

# Vector DB
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
```

## 🔒 Security Considerations

- **Development Only**: This MVP is for development/testing
- **No Authentication**: Add authentication for production use
- **API Security**: Implement rate limiting and input validation
- **Data Privacy**: Ensure observability data doesn't contain sensitive information

## 📈 Performance Tips

1. **Optimize Vector Search**: Tune `CONFIDENCE_THRESHOLD` and `TOP_K_SIMILAR_INCIDENTS`
2. **Model Performance**: LLaMA3 requires significant RAM
3. **Database**: Regularly clean old incidents to maintain performance
4. **Hardware**: SSD storage recommended for faster model loading

## 🤝 Contributing

This is an MVP framework. To extend:

1. **Add Authentication**: Implement user management
2. **Add Data Sources**: Integrate with monitoring tools (Prometheus, ELK, etc.)
3. **Improve Models**: Fine-tune models on specific use cases
4. **Add Notifications**: Implement alerting mechanisms
5. **Scale Architecture**: Add containerization and orchestration

## 📝 Dependencies

All dependencies are compatible with Python 3.12.3:

- FastAPI 0.104.1
- Streamlit 1.28.1
- ChromaDB 0.4.18
- Ollama 0.1.7
- Pydantic 2.5.0
- And more (see requirements.txt)

## 🆘 Support

For issues and questions:

1. **Check logs**: `tail -f logs/*.log`
2. **Verify setup**: Run `./setup.sh` again
3. **Check API health**: http://localhost:8000/api/v1/health
4. **Review troubleshooting section above**
5. **Restart everything**: `./stop_all.sh && ./start_all.sh`

## 📄 License

This project is provided as-is for educational and development purposes.

---

**Happy Root Cause Analysis! 🔍✨**

*Now fully compatible with Python 3.12.3 on Ubuntu!*
