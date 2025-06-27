from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DataType(str, Enum):
    LOGS = "logs"
    METRICS = "metrics"
    TRACES = "traces"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ObservabilityData(BaseModel):
    data_type: DataType
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RCARequest(BaseModel):
    logs: str = ""
    metrics: str = ""
    traces: str = ""
    context: Optional[str] = None

class Evidence(BaseModel):
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    data_type: DataType

class RelatedIncident(BaseModel):
    incident_id: str
    description: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    resolution: Optional[str] = None
    timestamp: Optional[datetime] = None

class RemediationSuggestion(BaseModel):
    title: str
    description: str
    priority: str = Field(pattern="^(low|medium|high|critical)$")
    estimated_time: Optional[str] = None
    steps: List[str] = []

class RCAResponse(BaseModel):
    root_cause_summary: str
    confidence_level: ConfidenceLevel
    overall_confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[Evidence]
    related_incidents: List[RelatedIncident]
    remediation_suggestions: List[RemediationSuggestion]
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[int] = None

class IngestDataRequest(BaseModel):
    data: List[ObservabilityData]

class IngestDataResponse(BaseModel):
    success: bool
    message: str
    ingested_count: int
    failed_count: int = 0

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, bool]
