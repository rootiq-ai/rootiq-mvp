from typing import List, Dict, Any, Optional
from loguru import logger
import json
from datetime import datetime

from ..utils.vectordb import VectorDBManager

class RAGService:
    def __init__(self):
        self.vector_db = VectorDBManager()
        self.top_k_similar_incidents = 5
        self.confidence_threshold = 0.7
    
    def find_similar_incidents(self, query_text: str, data_type: Optional[str] = None, k: int = None) -> List[Dict[str, Any]]:
        """Find similar incidents from vector database"""
        if k is None:
            k = self.top_k_similar_incidents
            
        try:
            # Search for similar documents
            similar_docs = self.vector_db.search_similar(
                query=query_text,
                n_results=k,
                data_type=data_type
            )
            
            # Filter by confidence threshold
            filtered_docs = [
                doc for doc in similar_docs 
                if doc.get('similarity_score', 0) >= self.confidence_threshold
            ]
            
            # Format for RCA analysis
            incidents = []
            for i, doc in enumerate(filtered_docs):
                incident = {
                    'incident_id': doc.get('id', f'incident_{i+1}'),
                    'description': self._extract_description(doc.get('content', '')),
                    'similarity_score': doc.get('similarity_score', 0.0),
                    'resolution': self._extract_resolution(doc.get('metadata', {})),
                    'timestamp': doc.get('metadata', {}).get('timestamp'),
                    'data_type': doc.get('metadata', {}).get('data_type', 'unknown'),
                    'source': doc.get('metadata', {}).get('source', 'unknown'),
                    'content': doc.get('content', '')
                }
                incidents.append(incident)
            
            logger.info(f"Found {len(incidents)} similar incidents with confidence >= {self.confidence_threshold}")
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to find similar incidents: {str(e)}")
            return []
    
    def add_incident_data(self, observability_data: List[Dict[str, Any]]) -> bool:
        """Add new observability data to the knowledge base"""
        try:
            # Prepare documents for vector storage
            documents = []
            for data in observability_data:
                doc = {
                    'content': data.get('content', ''),
                    'data_type': data.get('data_type', 'unknown'),
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'source': data.get('source', 'unknown'),
                    'metadata': data.get('metadata', {})
                }
                documents.append(doc)
            
            # Add to vector database
            success = self.vector_db.add_documents(documents)
            
            if success:
                logger.info(f"Successfully added {len(documents)} documents to knowledge base")
            else:
                logger.error("Failed to add documents to knowledge base")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add incident data: {str(e)}")
            return False
    
    def get_relevant_context(self, logs: str, metrics: str, traces: str) -> List[Dict[str, Any]]:
        """Get relevant context from all observability data"""
        try:
            all_incidents = []
            
            # Search using logs
            if logs.strip():
                log_incidents = self.find_similar_incidents(logs, data_type="logs")
                all_incidents.extend(log_incidents)
            
            # Search using metrics
            if metrics.strip():
                metric_incidents = self.find_similar_incidents(metrics, data_type="metrics")
                all_incidents.extend(metric_incidents)
            
            # Search using traces
            if traces.strip():
                trace_incidents = self.find_similar_incidents(traces, data_type="traces")
                all_incidents.extend(trace_incidents)
            
            # Remove duplicates and sort by similarity
            unique_incidents = self._deduplicate_incidents(all_incidents)
            sorted_incidents = sorted(unique_incidents, key=lambda x: x['similarity_score'], reverse=True)
            
            # Return top incidents
            return sorted_incidents[:self.top_k_similar_incidents]
            
        except Exception as e:
            logger.error(f"Failed to get relevant context: {str(e)}")
            return []
    
    def _extract_description(self, content: str, max_length: int = 200) -> str:
        """Extract a meaningful description from content"""
        if not content:
            return "No description available"
        
        # Take first line or first sentence, whichever is shorter
        lines = content.split('\n')
        first_line = lines[0].strip()
        
        if len(first_line) <= max_length:
            return first_line
        
        # If first line is too long, truncate at word boundary
        words = first_line.split()
        description = ""
        for word in words:
            if len(description + " " + word) <= max_length:
                description += (" " + word) if description else word
            else:
                break
        
        return description + "..." if len(first_line) > max_length else description
    
    def _extract_resolution(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract resolution information from metadata"""
        try:
            if isinstance(metadata, dict):
                # Look for resolution in metadata
                if 'resolution' in metadata:
                    return metadata['resolution']
                
                # Parse metadata string if it's JSON
                if 'metadata' in metadata:
                    meta_str = metadata['metadata']
                    if isinstance(meta_str, str):
                        try:
                            parsed_meta = json.loads(meta_str)
                            return parsed_meta.get('resolution')
                        except json.JSONDecodeError:
                            pass
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract resolution: {str(e)}")
            return None
    
    def _deduplicate_incidents(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate incidents based on incident_id"""
        seen_ids = set()
        unique_incidents = []
        
        for incident in incidents:
            incident_id = incident.get('incident_id')
            if incident_id not in seen_ids:
                seen_ids.add(incident_id)
                unique_incidents.append(incident)
        
        return unique_incidents
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            stats = self.vector_db.get_collection_stats()
            return {
                "total_incidents": stats.get("total_documents", 0),
                "collection_name": stats.get("collection_name", "unknown"),
                "embedding_model": stats.get("embedding_model", "unknown"),
                "confidence_threshold": self.confidence_threshold,
                "top_k_results": self.top_k_similar_incidents
            }
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {str(e)}")
            return {"error": str(e)}
    
    def clear_knowledge_base(self) -> bool:
        """Clear all data from the knowledge base"""
        try:
            success = self.vector_db.clear_collection()
            if success:
                logger.info("Knowledge base cleared successfully")
            return success
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {str(e)}")
            return False
