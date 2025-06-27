# 🔍 RCA Platform

**Generative AI-Driven Observability for Automated Root Cause Analysis in Modern IT Systems**

A comprehensive MVP solution that leverages LLaMA3 and RAG (Retrieval-Augmented Generation) to automatically analyze logs, metrics, and traces for intelligent root cause analysis.

## 🚀 Features

- **Multi-Modal Analysis**: Process logs, metrics, and traces simultaneously
- **AI-Powered RCA**: Uses LLaMA3 via Ollama for intelligent analysis
- **RAG Integration**: ChromaDB-powered knowledge base for historical incident correlation
- **Interactive UI**: Clean Streamlit interface for easy interaction
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Real-time Processing**: Fast analysis with confidence scoring
- **Knowledge Base**: Persistent storage of incidents for improved analysis over time

## 🏗️ Architecture

```
rca-platform/
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
├── requirements.txt         # Python dependencies
├── config.py               # Configuration settings
├── setup.sh               # Setup script
└── README.md              # This file
```

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **LLM**: LLaMA3 via Ollama
- **Vector Database**: ChromaDB
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Language**: Python 3.12.3

## 📋 Prerequisites

- **Ubuntu** (tested on Ubuntu 20.04+)
- **Python 3.12.3**
- **pip** (Python package manager)
- **curl** (for Ollama installation)
- **8GB+ RAM** (recommended for LLaMA3)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository (or create the directory structure)
mkdir rca-platform && cd rca-platform

# Make setup script executable
chmod +x setup.sh

# Run setup (installs dependencies and Ollama)
./setup.sh
```

### 2. Start the Services

**Terminal 1 - Backend API:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend UI:**
```bash
cd frontend
streamlit run streamlit_app.py
```

### 3. Access the Application

- **Streamlit UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/v1/health

## 📖 Usage Guide

### Via Streamlit UI

1. **Open the UI** at http://localhost:8501
2. **Enter observability data** in the three text boxes:
   - **Logs**: Application logs, error messages, events
   - **Metrics**: Performance metrics, resource usage data
   - **Traces**: Distributed tracing information
3. **Click "Run RCA Analysis"** to generate the analysis
4. **Review results** in the organized tabs:
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

## 🔧 Configuration

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

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analyze` | Perform RCA analysis |
| POST | `/api/v1/ingest` | Ingest observability data |
| POST | `/api/v1/upload/{type}` | Upload logs/metrics/traces |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/stats` | Knowledge base statistics |
| DELETE | `/api/v1/knowledge-base` | Clear knowledge base |

## 🧪 Example Data

### Sample Logs
```
2024-01-01 10:00:00 ERROR [DatabaseService] Connection timeout to primary database
2024-01-01 10:00:05 WARN [DatabaseService] Failover to secondary database
2024-01-01 10:00:10 INFO [HealthCheck] Service marked as degraded
```

### Sample Metrics
```
cpu_usage_percent: 85.2
memory_usage_mb: 7680
disk_io_wait: 45ms
database_connections: 95/100
response_time_p95: 2500ms
```

### Sample Traces
```
span_id: abc123-def456
operation: user_login
duration: 2500ms
status: error
error: database_timeout
parent_span: web_request_789
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
- Priority level

## 🐛 Troubleshooting

### Common Issues

**1. Ollama Service Not Starting**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama manually
ollama serve

# In another terminal, pull the model
ollama pull llama3
```

**2. ChromaDB Permission Issues**
```bash
# Fix permissions
chmod -R 755 data/chroma_db/
```

**3. API Connection Errors**
```bash
# Check if backend is running
curl http://localhost:8000/ping

# Check logs
cd backend && python main.py
```

**4. Memory Issues**
- Ensure at least 8GB RAM available
- Close unnecessary applications
- Consider using a smaller model if needed

### Logs and Debugging

**Backend logs**: Check terminal running `python main.py`
**Frontend logs**: Check terminal running `streamlit run streamlit_app.py`
**Ollama logs**: Check `ollama logs` or system logs

## 🔒 Security Considerations

- **Development Only**: This MVP is for development/testing
- **No Authentication**: Add authentication for production use
- **API Security**: Implement rate limiting and input validation
- **Data Privacy**: Ensure observability data doesn't contain sensitive information

## 📈 Performance Tips

1. **Optimize Vector Search**: Tune `CONFIDENCE_THRESHOLD` and `TOP_K_SIMILAR_INCIDENTS`
2. **Model Performance**: Consider using quantized models for faster inference
3. **Database**: Regularly clean old incidents to maintain performance
4. **Caching**: Implement caching for frequently accessed data

## 🤝 Contributing

This is an MVP framework. To extend:

1. **Add Authentication**: Implement user management
2. **Add Data Sources**: Integrate with monitoring tools (Prometheus, ELK, etc.)
3. **Improve Models**: Fine-tune models on specific use cases
4. **Add Notifications**: Implement alerting mechanisms
5. **Scale Architecture**: Add containerization and orchestration

## 📝 License

This project is provided as-is for educational and development purposes.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Verify all services are running
3. Check API documentation at http://localhost:8000/docs
4. Review logs for error messages

---

**Happy Root Cause Analysis! 🔍✨**
