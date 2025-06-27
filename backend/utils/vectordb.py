import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
from typing import List, Dict, Any, Optional
from loguru import logger
import json
from datetime import datetime
import os
from pathlib import Path

# Get the config from the root directory
config_path = Path(__file__).parent.parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

import importlib.util

class VectorDBManager:
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.chroma_db_dir = Path(__file__).parent.parent.parent / "data" / "chroma_db"
        self.chroma_db_dir.mkdir(parents=True, exist_ok=True)
        self.initialize()
    
    def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(self.chroma_db_dir),
                settings=Settings(
                    allow_reset=True,
                    is_persistent=True
                )
            )
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="observability_data",
                metadata={"description": "Observability data for RCA"}
            )
            
            logger.info(f"VectorDB initialized successfully. Collection: observability_data")
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorDB: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector database"""
        try:
            ids = []
            texts = []
            metadatas = []
            
            for doc in documents:
                doc_id = str(uuid.uuid4())
                text = doc.get('content', '')
                metadata = {
                    'data_type': doc.get('data_type', 'unknown'),
                    'timestamp': doc.get('timestamp', datetime.now().isoformat()),
                    'source': doc.get('source', 'unknown'),
                    'metadata': json.dumps(doc.get('metadata', {}))
                }
                
                ids.append(doc_id)
                texts.append(text)
                metadatas.append(metadata)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(documents)} documents to VectorDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to VectorDB: {str(e)}")
            return False
    
    def search_similar(self, query: str, n_results: int = 5, data_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Prepare where clause for filtering
            where_clause = {}
            if data_type:
                where_clause["data_type"] = data_type
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            similar_docs = []
            for i in range(len(results['ids'][0])):
                doc = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': results['metadatas'][0][i]
                }
                similar_docs.append(doc)
            
            logger.info(f"Found {len(similar_docs)} similar documents")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Failed to search similar documents: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": "observability_data",
                "embedding_model": "all-MiniLM-L6-v2"
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"error": str(e)}
    
    def clear_collection(self) -> bool:
        """Clear all documents from collection"""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection("observability_data")
            self.collection = self.client.create_collection(
                name="observability_data",
                metadata={"description": "Observability data for RCA"}
            )
            logger.info("Collection cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {str(e)}")
            return False
