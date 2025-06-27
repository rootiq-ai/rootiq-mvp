from typing import Dict, Any, List
from loguru import logger
from datetime import datetime
import time

from .llm_service import LLMService
from .rag_service import RAGService

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.models.schemas import RCARequest, RCAResponse, Evidence, RelatedIncident, RemediationSuggestion, ConfidenceLevel

class RCAService:
    def __init__(self):
        self.llm_service = LLMService()
        self.rag_service = RAGService()
    
    def analyze(self, request: RCARequest) -> RCAResponse:
        """Perform comprehensive RCA analysis"""
        start_time = time.time()
        
        try:
            logger.info("Starting RCA analysis")
            
            # Validate input
            if not any([request.logs.strip(), request.metrics.strip(), request.traces.strip()]):
                return self._create_error_response("No observability data provided")
            
            # Get similar incidents from RAG
            similar_incidents = self.rag_service.get_relevant_context(
                request.logs, request.metrics, request.traces
            )
            logger.info(f"Found {len(similar_incidents)} similar incidents")
            
            # Generate analysis using LLM
            analysis = self.llm_service.generate_rca_analysis(
                request.logs, request.metrics, request.traces, similar_incidents
            )
            
            # Convert to response format
            response = self._convert_to_response(analysis, similar_incidents)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            response.processing_time_ms = processing_time
            
            logger.info(f"RCA analysis completed in {processing_time}ms")
            return response
            
        except Exception as e:
            logger.error(f"RCA analysis failed: {str(e)}")
            return self._create_error_response(f"Analysis failed: {str(e)}")
    
    def _convert_to_response(self, analysis: Dict[str, Any], similar_incidents: List[Dict[str, Any]]) -> RCAResponse:
        """Convert LLM analysis to RCAResponse format"""
        try:
            # Parse evidence
            evidence = []
            for ev in analysis.get('evidence', []):
                evidence.append(Evidence(
                    description=ev.get('description', ''),
                    confidence=float(ev.get('confidence', 0.0)),
                    source=ev.get('source', 'unknown'),
                    data_type=ev.get('data_type', 'logs')
                ))
            
            # Parse related incidents (combine from LLM and RAG)
            related_incidents = []
            
            # Add incidents from RAG
            for incident in similar_incidents[:3]:  # Top 3 from RAG
                related_incidents.append(RelatedIncident(
                    incident_id=incident.get('incident_id', ''),
                    description=incident.get('description', ''),
                    similarity_score=incident.get('similarity_score', 0.0),
                    resolution=incident.get('resolution'),
                    timestamp=self._parse_timestamp(incident.get('timestamp'))
                ))
            
            # Add incidents from LLM analysis
            for incident in analysis.get('related_incidents', []):
                related_incidents.append(RelatedIncident(
                    incident_id=incident.get('incident_id', ''),
                    description=incident.get('description', ''),
                    similarity_score=incident.get('similarity_score', 0.0),
                    resolution=incident.get('resolution')
                ))
            
            # Parse remediation suggestions
            remediation_suggestions = []
            for suggestion in analysis.get('remediation_suggestions', []):
                remediation_suggestions.append(RemediationSuggestion(
                    title=suggestion.get('title', ''),
                    description=suggestion.get('description', ''),
                    priority=suggestion.get('priority', 'medium'),
                    estimated_time=suggestion.get('estimated_time'),
                    steps=suggestion.get('steps', [])
                ))
            
            # Determine confidence level
            overall_confidence = float(analysis.get('overall_confidence', 0.0))
            confidence_level = self._determine_confidence_level(overall_confidence)
            
            return RCAResponse(
                root_cause_summary=analysis.get('root_cause_summary', 'Unable to determine root cause'),
                confidence_level=confidence_level,
                overall_confidence=overall_confidence,
                evidence=evidence,
                related_incidents=related_incidents,
                remediation_suggestions=remediation_suggestions,
                processing_time_ms=analysis.get('processing_time_ms', 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to convert analysis to response: {str(e)}")
            return self._create_error_response(f"Response conversion failed: {str(e)}")
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level from numeric score"""
        if confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return None
        
        try:
            # Try different timestamp formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # If no format matches, return None
            return None
            
        except Exception:
            return None
    
    def _create_error_response(self, error_message: str) -> RCAResponse:
        """Create error response"""
        return RCAResponse(
            root_cause_summary=f"Error: {error_message}",
            confidence_level=ConfidenceLevel.LOW,
            overall_confidence=0.0,
            evidence=[Evidence(
                description=f"Analysis failed: {error_message}",
                confidence=0.0,
                source="system",
                data_type="logs"
            )],
            related_incidents=[],
            remediation_suggestions=[RemediationSuggestion(
                title="Check system status",
                description="Verify that all required services are running",
                priority="high",
                estimated_time="5-10 minutes",
                steps=[
                    "Check Ollama service status",
                    "Verify vector database connectivity",
                    "Review input data format",
                    "Check system logs"
                ]
            )]
        )
    
    def ingest_observability_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingest observability data into the knowledge base"""
        try:
            success = self.rag_service.add_incident_data(data)
            
            return {
                "success": success,
                "message": "Data ingested successfully" if success else "Failed to ingest data",
                "ingested_count": len(data) if success else 0,
                "failed_count": 0 if success else len(data)
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest data: {str(e)}")
            return {
                "success": False,
                "message": f"Ingestion failed: {str(e)}",
                "ingested_count": 0,
                "failed_count": len(data)
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services"""
        try:
            llm_available = self.llm_service.is_available()
            rag_stats = self.rag_service.get_knowledge_base_stats()
            
            return {
                "status": "healthy" if llm_available else "degraded",
                "services": {
                    "llm": llm_available,
                    "vector_db": "error" not in rag_stats,
                    "rag": True
                },
                "knowledge_base": rag_stats
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "services": {
                    "llm": False,
                    "vector_db": False,
                    "rag": False
                },
                "error": str(e)
            }
