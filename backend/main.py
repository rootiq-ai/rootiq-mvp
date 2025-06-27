from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import API_HOST, API_PORT, LOG_LEVEL, LOG_FORMAT
from backend.api.endpoints import router

# Configure logging
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL, format=LOG_FORMAT)

# Create FastAPI app
app = FastAPI(
    title="RCA Platform API",
    description="Generative AI-Driven Observability for Automated Root Cause Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting RCA Platform API...")
    logger.info(f"API will be available at http://{API_HOST}:{API_PORT}")
    logger.info(f"Documentation at http://{API_HOST}:{API_PORT}/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RCA Platform API...")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RCA Platform API is running",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
        "api": "/api/v1"
    }

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}

if __name__ == "__main__":
    logger.info(f"Starting server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
