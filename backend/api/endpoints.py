from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
from loguru import logger

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.models.schemas import (
    RCARequest, RCAResponse, ObservabilityData, 
    IngestDataRequest, IngestDataResponse, HealthCheck
)
from backend.services.rca_service import RCAService

# Initialize router
router = APIRouter()

# Global RCA service instance
rca_service = RCAService()

@router.post("/analyze", response_model=RCAResponse)
async def perform_rca_analysis(request: RCARequest):
    """
    Perform Root Cause Analysis on provided observability data
    """
    try:
        logger.info("Received RCA analysis request")
        response = rca_service.analyze(request)
        return response
    except Exception as e:
        logger.error(f"RCA analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/ingest", response_model=IngestDataResponse)
async def ingest_observability_data(request: IngestDataRequest):
    """
    Ingest observability data into the knowledge base for future RCA
    """
    try:
        logger.info(f"Ingesting {len(request.data)} observability records")
        
        # Convert Pydantic models to dictionaries
        data_dicts = []
        for item in request.data:
            data_dict = {
                "content": item.content,
                "data_type": item.data_type.value,
                "timestamp": item.timestamp.isoformat() if item.timestamp else None,
                "source": item.source,
                "metadata": item.metadata or {}
            }
            data_dicts.append(data_dict)
        
        result = rca_service.ingest_observability_data(data_dicts)
        
        return IngestDataResponse(
            success=result["success"],
            message=result["message"],
            ingested_count=result["ingested_count"],
            failed_count=result.get("failed_count", 0)
        )
        
    except Exception as e:
        logger.error(f"Data ingestion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )

@router.post("/upload/{data_type}")
async def upload_data(data_type: str, content: str):
    """
    Simple endpoint to upload logs, metrics, or traces
    """
    try:
        if data_type not in ["logs", "metrics", "traces"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="data_type must be one of: logs, metrics, traces"
            )
        
        # Create observability data
        observability_data = [{
            "content": content,
            "data_type": data_type,
            "timestamp": None,
            "source": "api_upload",
            "metadata": {"upload_type": "direct"}
        }]
        
        result = rca_service.ingest_observability_data(observability_data)
        
        return {
            "success": result["success"],
            "message": f"Successfully uploaded {data_type} data",
            "data_type": data_type,
            "content_length": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Check the health status of all services
    """
    try:
        health_data = rca_service.get_health_status()
        
        return HealthCheck(
            status=health_data["status"],
            services=health_data["services"]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/stats")
async def get_knowledge_base_stats():
    """
    Get statistics about the knowledge base
    """
    try:
        stats = rca_service.rag_service.get_knowledge_base_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )

@router.delete("/knowledge-base")
async def clear_knowledge_base():
    """
    Clear all data from the knowledge base
    """
    try:
        success = rca_service.rag_service.clear_knowledge_base()
        
        if success:
            return {"message": "Knowledge base cleared successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear knowledge base"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear knowledge base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear knowledge base: {str(e)}"
        )

@router.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "RCA Platform API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze - Perform RCA analysis",
            "ingest": "POST /ingest - Ingest observability data",
            "upload": "POST /upload/{data_type} - Upload specific data type",
            "health": "GET /health - Health check",
            "stats": "GET /stats - Knowledge base statistics",
            "clear": "DELETE /knowledge-base - Clear knowledge base"
        }
    }
