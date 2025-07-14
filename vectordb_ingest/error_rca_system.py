#!/usr/bin/env python3
"""
Error RCA and Fix Storage System using ChromaDB and Ollama
Stores Java production errors with RCA analysis and fixes for intelligent retrieval
"""

import pandas as pd
import chromadb
from chromadb.config import Settings
import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorRCASystem:
    def __init__(self, 
                 chroma_persist_directory: str = "./chroma_db",
                 ollama_base_url: str = "http://localhost:11434",
                 model_name: str = "llama3"):
        """
        Initialize the Error RCA system with ChromaDB and Ollama
        
        Args:
            chroma_persist_directory: Directory to persist ChromaDB data
            ollama_base_url: Base URL for Ollama API
            model_name: Name of the Ollama model to use
        """
        self.ollama_base_url = ollama_base_url
        self.model_name = model_name
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection
        self.collection_name = "java_production_errors"
        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Java production errors with RCA and fixes"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def get_embedding_from_ollama(self, text: str) -> List[float]:
        """
        Get embeddings from Ollama using the specified model
        
        Args:
            text: Text to embed
            
        Returns:
            List of float values representing the embedding
        """
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise Exception(f"Failed to get embedding: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error to Ollama: {e}")
            raise Exception(f"Failed to connect to Ollama: {e}")
    
    def create_document_text(self, row: Dict) -> str:
        """
        Create a comprehensive text document from error data for embedding
        
        Args:
            row: Dictionary containing error data
            
        Returns:
            Formatted text combining all relevant error information
        """
        doc_parts = []
        
        # Add error title and description
        if row.get('error_title'):
            doc_parts.append(f"Error: {row['error_title']}")
        
        if row.get('error_description'):
            doc_parts.append(f"Description: {row['error_description']}")
        
        # Add error type and severity
        if row.get('error_type'):
            doc_parts.append(f"Type: {row['error_type']}")
        
        if row.get('severity'):
            doc_parts.append(f"Severity: {row['severity']}")
        
        # Add RCA analysis
        if row.get('rca_analysis'):
            doc_parts.append(f"Root Cause Analysis: {row['rca_analysis']}")
        
        # Add fix solution
        if row.get('fix_solution'):
            doc_parts.append(f"Solution: {row['fix_solution']}")
        
        # Add tags
        if row.get('tags'):
            doc_parts.append(f"Tags: {row['tags']}")
        
        # Add source
        if row.get('source'):
            doc_parts.append(f"Source: {row['source']}")
        
        return " | ".join(doc_parts)
    
    def generate_document_id(self, row: Dict) -> str:
        """
        Generate a unique document ID based on error content
        
        Args:
            row: Dictionary containing error data
            
        Returns:
            Unique document ID
        """
        # Create hash from key fields to ensure uniqueness
        key_content = f"{row.get('error_title', '')}-{row.get('error_description', '')}-{row.get('timestamp', '')}"
        return hashlib.md5(key_content.encode()).hexdigest()
    
    def load_csv_data(self, csv_file_path: str) -> pd.DataFrame:
        """
        Load and prepare CSV data
        
        Args:
            csv_file_path: Path to the CSV file
            
        Returns:
            DataFrame with loaded data
        """
        try:
            df = pd.read_csv(csv_file_path)
            logger.info(f"Loaded {len(df)} records from {csv_file_path}")
            
            # Handle missing values
            df = df.fillna('')
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
    
    def store_errors_in_chromadb(self, csv_file_path: str, batch_size: int = 100):
        """
        Process CSV data and store in ChromaDB with embeddings
        
        Args:
            csv_file_path: Path to the CSV file containing error data
            batch_size: Number of documents to process in each batch
        """
        df = self.load_csv_data(csv_file_path)
        
        total_records = len(df)
        logger.info(f"Processing {total_records} error records...")
        
        # Process in batches
        for i in range(0, total_records, batch_size):
            batch_df = df.iloc[i:i+batch_size]
            
            documents = []
            embeddings = []
            ids = []
            metadatas = []
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(total_records + batch_size - 1)//batch_size}")
            
            for _, row in batch_df.iterrows():
                try:
                    # Create document text for embedding
                    doc_text = self.create_document_text(row.to_dict())
                    
                    # Get embedding from Ollama
                    embedding = self.get_embedding_from_ollama(doc_text)
                    
                    # Create document ID
                    doc_id = self.generate_document_id(row.to_dict())
                    
                    # Prepare metadata
                    metadata = {
                        "error_title": str(row.get('error_title', '')),
                        "error_type": str(row.get('error_type', '')),
                        "severity": str(row.get('severity', '')),
                        "source": str(row.get('source', '')),
                        "timestamp": str(row.get('timestamp', '')),
                        "tags": str(row.get('tags', '')),
                        "url": str(row.get('url', '')),
                        "rca_analysis": str(row.get('rca_analysis', ''))[:1000],  # Limit length
                        "fix_solution": str(row.get('fix_solution', ''))[:1000],  # Limit length
                        "error_description": str(row.get('error_description', ''))[:500]  # Limit length
                    }
                    
                    documents.append(doc_text)
                    embeddings.append(embedding)
                    ids.append(doc_id)
                    metadatas.append(metadata)
                    
                except Exception as e:
                    logger.error(f"Error processing record {row.get('id', 'unknown')}: {e}")
                    continue
            
            # Add batch to ChromaDB
            if documents:
                try:
                    self.collection.add(
                        documents=documents,
                        embeddings=embeddings,
                        ids=ids,
                        metadatas=metadatas
                    )
                    logger.info(f"Successfully added {len(documents)} documents to ChromaDB")
                except Exception as e:
                    logger.error(f"Error adding batch to ChromaDB: {e}")
        
        logger.info("Finished processing all error records")
    
    def search_similar_errors(self, 
                            query_text: str, 
                            n_results: int = 5,
                            include_rca: bool = True,
                            include_fix: bool = True) -> List[Dict]:
        """
        Search for similar errors based on query text
        
        Args:
            query_text: Text description of the error to search for
            n_results: Number of similar errors to return
            include_rca: Whether to include RCA analysis in results
            include_fix: Whether to include fix solutions in results
            
        Returns:
            List of similar errors with metadata
        """
        try:
            # Get embedding for query
            query_embedding = self.get_embedding_from_ollama(query_text)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                result = {
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'error_title': results['metadatas'][0][i].get('error_title', ''),
                    'error_description': results['metadatas'][0][i].get('error_description', ''),
                    'error_type': results['metadatas'][0][i].get('error_type', ''),
                    'severity': results['metadatas'][0][i].get('severity', ''),
                    'source': results['metadatas'][0][i].get('source', ''),
                    'timestamp': results['metadatas'][0][i].get('timestamp', ''),
                    'tags': results['metadatas'][0][i].get('tags', ''),
                    'url': results['metadatas'][0][i].get('url', '')
                }
                
                if include_rca:
                    result['rca_analysis'] = results['metadatas'][0][i].get('rca_analysis', '')
                
                if include_fix:
                    result['fix_solution'] = results['metadatas'][0][i].get('fix_solution', '')
                
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching for similar errors: {e}")
            return []
    
    def search_by_filters(self, 
                         error_type: Optional[str] = None,
                         severity: Optional[str] = None,
                         source: Optional[str] = None,
                         n_results: int = 10) -> List[Dict]:
        """
        Search errors by metadata filters
        
        Args:
            error_type: Filter by error type
            severity: Filter by severity level
            source: Filter by source system
            n_results: Maximum number of results to return
            
        Returns:
            List of matching errors
        """
        try:
            where_filter = {}
            
            if error_type:
                where_filter["error_type"] = error_type
            if severity:
                where_filter["severity"] = severity
            if source:
                where_filter["source"] = source
            
            if where_filter:
                results = self.collection.get(
                    where=where_filter,
                    limit=n_results,
                    include=['documents', 'metadatas']
                )
            else:
                results = self.collection.get(
                    limit=n_results,
                    include=['documents', 'metadatas']
                )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'])):
                result = {
                    'error_title': results['metadatas'][i].get('error_title', ''),
                    'error_description': results['metadatas'][i].get('error_description', ''),
                    'error_type': results['metadatas'][i].get('error_type', ''),
                    'severity': results['metadatas'][i].get('severity', ''),
                    'source': results['metadatas'][i].get('source', ''),
                    'timestamp': results['metadatas'][i].get('timestamp', ''),
                    'rca_analysis': results['metadatas'][i].get('rca_analysis', ''),
                    'fix_solution': results['metadatas'][i].get('fix_solution', ''),
                    'tags': results['metadatas'][i].get('tags', ''),
                    'url': results['metadatas'][i].get('url', '')
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching by filters: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the stored error collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample of records to analyze metadata
            sample = self.collection.get(limit=100, include=['metadatas'])
            
            if sample['metadatas']:
                error_types = set()
                severities = set()
                sources = set()
                
                for metadata in sample['metadatas']:
                    if metadata.get('error_type'):
                        error_types.add(metadata['error_type'])
                    if metadata.get('severity'):
                        severities.add(metadata['severity'])
                    if metadata.get('source'):
                        sources.add(metadata['source'])
                
                return {
                    'total_errors': count,
                    'unique_error_types': list(error_types),
                    'unique_severities': list(severities),
                    'unique_sources': list(sources),
                    'sample_size': len(sample['metadatas'])
                }
            else:
                return {'total_errors': count}
                
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {'error': str(e)}

def main():
    """
    Example usage of the Error RCA System
    """
    # Initialize the system
    system = ErrorRCASystem()
    
    # Load and store error data from CSV
    csv_file = "java_production_errors_10k.csv"
    
    print("Loading error data into ChromaDB...")
    system.store_errors_in_chromadb(csv_file, batch_size=50)
    
    # Get collection statistics
    print("\nCollection Statistics:")
    stats = system.get_collection_stats()
    print(json.dumps(stats, indent=2))
    
    # Example: Search for similar errors
    print("\nSearching for similar errors...")
    query = "NullPointerException in user authentication service"
    similar_errors = system.search_similar_errors(query, n_results=3)
    
    print(f"\nTop 3 similar errors for query: '{query}'")
    for i, error in enumerate(similar_errors, 1):
        print(f"\n{i}. Similarity: {error['similarity_score']:.3f}")
        print(f"   Title: {error['error_title']}")
        print(f"   Type: {error['error_type']}")
        print(f"   Severity: {error['severity']}")
        print(f"   RCA: {error['rca_analysis'][:100]}...")
        print(f"   Fix: {error['fix_solution'][:100]}...")
    
    # Example: Filter by error type
    print("\nFiltering by error type...")
    filtered_errors = system.search_by_filters(error_type="RuntimeException", n_results=3)
    
    print(f"\nTop 3 RuntimeException errors:")
    for i, error in enumerate(filtered_errors, 1):
        print(f"\n{i}. Title: {error['error_title']}")
        print(f"   Severity: {error['severity']}")
        print(f"   Source: {error['source']}")

if __name__ == "__main__":
    main()
