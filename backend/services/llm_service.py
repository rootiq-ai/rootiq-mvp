import ollama
import json
from typing import Dict, Any, Optional
from loguru import logger
import time

class LLMService:
    def __init__(self):
        self.client = ollama.Client(host="http://localhost:11434")
        self.model = "llama3"
        self.max_context_length = 4000
        
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            return self.model in available_models
        except Exception as e:
            logger.error(f"Ollama service not available: {str(e)}")
            return False
    
    def generate_rca_analysis(self, logs: str, metrics: str, traces: str, similar_incidents: list) -> Dict[str, Any]:
        """Generate RCA analysis using LLM"""
        try:
            # Prepare context
            context = self._prepare_context(logs, metrics, traces, similar_incidents)
            
            # Create prompt
            prompt = self._create_rca_prompt(context)
            
            # Generate response
            start_time = time.time()
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 2000
                }
            )
            processing_time = int((time.time() - start_time) * 1000)
            
            # Parse response
            analysis = self._parse_rca_response(response['response'])
            analysis['processing_time_ms'] = processing_time
            
            logger.info(f"Generated RCA analysis in {processing_time}ms")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to generate RCA analysis: {str(e)}")
            return self._get_fallback_response(str(e))
    
    def _prepare_context(self, logs: str, metrics: str, traces: str, similar_incidents: list) -> str:
        """Prepare context for RCA analysis"""
        context_parts = []
        
        if logs.strip():
            context_parts.append(f"=== LOGS ===\n{logs[:1000]}")
        
        if metrics.strip():
            context_parts.append(f"=== METRICS ===\n{metrics[:1000]}")
        
        if traces.strip():
            context_parts.append(f"=== TRACES ===\n{traces[:1000]}")
        
        if similar_incidents:
            incidents_text = "\n".join([
                f"Incident {i+1}: {incident.get('content', '')[:200]}..."
                for i, incident in enumerate(similar_incidents[:3])
            ])
            context_parts.append(f"=== SIMILAR PAST INCIDENTS ===\n{incidents_text}")
        
        context = "\n\n".join(context_parts)
        
        # Truncate if too long
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length] + "... [truncated]"
        
        return context
    
    def _create_rca_prompt(self, context: str) -> str:
        """Create RCA analysis prompt"""
        return f"""You are an expert DevOps engineer performing root cause analysis on IT system issues. 
Analyze the provided observability data and generate a comprehensive RCA report.

OBSERVABILITY DATA:
{context}

Please provide a detailed analysis in the following JSON format:
{{
    "root_cause_summary": "Clear, concise summary of the root cause",
    "confidence_level": "high|medium|low",
    "overall_confidence": 0.0-1.0,
    "evidence": [
        {{
            "description": "Specific evidence supporting the root cause",
            "confidence": 0.0-1.0,
            "source": "logs|metrics|traces",
            "data_type": "logs|metrics|traces"
        }}
    ],
    "related_incidents": [
        {{
            "incident_id": "unique_identifier",
            "description": "Brief description",
            "similarity_score": 0.0-1.0,
            "resolution": "How it was resolved (if known)"
        }}
    ],
    "remediation_suggestions": [
        {{
            "title": "Action title",
            "description": "Detailed description",
            "priority": "low|medium|high|critical",
            "estimated_time": "Estimated time to implement",
            "steps": ["Step 1", "Step 2", "Step 3"]
        }}
    ]
}}

Focus on:
1. Identifying patterns and anomalies
2. Correlating events across logs, metrics, and traces
3. Providing actionable remediation steps
4. Being specific about evidence and confidence levels

Return only valid JSON without any additional text or formatting."""
    
    def _parse_rca_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            analysis = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['root_cause_summary', 'confidence_level', 'overall_confidence']
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = self._get_default_value(field)
            
            # Ensure lists exist
            analysis.setdefault('evidence', [])
            analysis.setdefault('related_incidents', [])
            analysis.setdefault('remediation_suggestions', [])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return self._get_fallback_analysis()
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            'root_cause_summary': 'Unable to determine root cause from provided data',
            'confidence_level': 'low',
            'overall_confidence': 0.1,
            'evidence': [],
            'related_incidents': [],
            'remediation_suggestions': []
        }
        return defaults.get(field, None)
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Get fallback analysis when LLM fails"""
        return {
            "root_cause_summary": "Analysis could not be completed due to processing error",
            "confidence_level": "low",
            "overall_confidence": 0.0,
            "evidence": [{
                "description": "Unable to analyze provided data",
                "confidence": 0.0,
                "source": "system",
                "data_type": "logs"
            }],
            "related_incidents": [],
            "remediation_suggestions": [{
                "title": "Review input data",
                "description": "Ensure logs, metrics, and traces are properly formatted",
                "priority": "medium",
                "estimated_time": "5-10 minutes",
                "steps": ["Check data format", "Verify completeness", "Retry analysis"]
            }]
        }
    
    def _get_fallback_response(self, error_msg: str) -> Dict[str, Any]:
        """Get fallback response with error information"""
        analysis = self._get_fallback_analysis()
        analysis["root_cause_summary"] = f"Analysis failed: {error_msg}"
        return analysis
