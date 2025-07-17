#!/usr/bin/env python3
"""
ChromaDB Alert RCA System
Ingests Java alerts/errors, logs, traces, and metrics from CSV
Uses high-quality embeddings to find relevant RCA and fixes
"""

import chromadb
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import logging
from typing import List, Dict, Optional, Union, Tuple
import json
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertRCASystem:
    def __init__(self, csv_file_path: str, collection_name: str = "java_alerts", 
                 max_tokens_per_chunk: int = 512, chunk_overlap: int = 50):
        """
        Initialize the Alert RCA System with ChromaDB and embedding model
        
        Args:
            csv_file_path: Path to the CSV file containing alert data
            collection_name: Name for the ChromaDB collection
            max_tokens_per_chunk: Maximum tokens per chunk for embedding
            chunk_overlap: Number of tokens to overlap between chunks
        """
        self.csv_file_path = csv_file_path
        self.collection_name = collection_name
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.chunk_overlap = chunk_overlap
        
        # Initialize the best embedding model for semantic search
        logger.info("Loading sentence-transformers model: all-mpnet-base-v2")
        self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        
        # Initialize tokenizer for chunking (using the same tokenizer as the embedding model)
        logger.info("Loading tokenizer for chunking")
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-mpnet-base-v2')
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path="./chromadb_data")
        
        # Create or get collection with custom embedding function
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._get_embedding_function(),
            metadata={"description": "Java alerts with RCA and fixes - token-chunked"}
        )
        
        logger.info(f"ChromaDB collection '{self.collection_name}' initialized with {max_tokens_per_chunk} tokens per chunk")
    
    def _get_embedding_function(self):
        """Create custom embedding function for ChromaDB"""
        class SentenceTransformerEmbedding:
            def __init__(self, model):
                self.model = model
            
            def __call__(self, input: List[str]) -> List[List[float]]:
                """Updated interface for ChromaDB 0.4.16+"""
                embeddings = self.model.encode(input, convert_to_tensor=False)
                return embeddings.tolist()
            
            def name(self) -> str:
                """Required method for ChromaDB embedding function"""
                return "sentence-transformers-all-mpnet-base-v2"
        
        return SentenceTransformerEmbedding(self.embedding_model)
    
    def load_and_preprocess_data(self) -> pd.DataFrame:
        """Load and preprocess the CSV data"""
        logger.info(f"Loading data from {self.csv_file_path}")
        
        try:
            df = pd.read_csv(self.csv_file_path)
            logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
            
            # Clean and preprocess data
            df = df.dropna(subset=['log', 'rca', 'fix'])  # Remove rows with missing critical data
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Create searchable content by combining log, trace, and metrics
            df['searchable_content'] = df.apply(self._create_searchable_content, axis=1)
            
            logger.info(f"Preprocessed {len(df)} valid records")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def _create_searchable_content(self, row) -> str:
        """Create comprehensive searchable content from log, trace, and metrics"""
        content_parts = []
        
        # Add log information
        if pd.notna(row['log']):
            content_parts.append(f"Error Log: {row['log']}")
        
        # Add trace information
        if pd.notna(row['trace']):
            content_parts.append(f"Trace: {row['trace']}")
        
        # Add metrics information
        if pd.notna(row['metric']):
            content_parts.append(f"Metrics: {row['metric']}")
        
        return " | ".join(content_parts)
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using the tokenizer"""
        return len(self.tokenizer.encode(text, add_special_tokens=True))
    
    def _chunk_text_by_tokens(self, text: str, alert_id: str) -> List[Dict[str, str]]:
        """
        Split text into chunks based on token count with overlap
        
        Args:
            text: Text to chunk
            alert_id: Alert ID for reference
            
        Returns:
            List of dictionaries containing chunk information
        """
        if not text or not text.strip():
            return []
        
        # If text is short enough, return as single chunk
        token_count = self._count_tokens(text)
        if token_count <= self.max_tokens_per_chunk:
            return [{
                'chunk_id': f"{alert_id}_chunk_0",
                'content': text,
                'chunk_index': 0,
                'total_chunks': 1,
                'token_count': token_count
            }]
        
        # Split text into sentences for better chunking
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            
            # If single sentence exceeds limit, split it further
            if sentence_tokens > self.max_tokens_per_chunk:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append({
                        'chunk_id': f"{alert_id}_chunk_{chunk_index}",
                        'content': ' '.join(current_chunk),
                        'chunk_index': chunk_index,
                        'token_count': current_tokens
                    })
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0
                
                # Split long sentence by words
                word_chunks = self._split_long_sentence(sentence, alert_id, chunk_index)
                chunks.extend(word_chunks)
                chunk_index += len(word_chunks)
                continue
            
            # Check if adding this sentence would exceed limit
            if current_tokens + sentence_tokens > self.max_tokens_per_chunk and current_chunk:
                # Save current chunk
                chunks.append({
                    'chunk_id': f"{alert_id}_chunk_{chunk_index}",
                    'content': ' '.join(current_chunk),
                    'chunk_index': chunk_index,
                    'token_count': current_tokens
                })
                
                # Start new chunk with overlap if configured
                if self.chunk_overlap > 0:
                    overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                    current_chunk = [overlap_text] if overlap_text else []
                    current_tokens = self._count_tokens(' '.join(current_chunk))
                else:
                    current_chunk = []
                    current_tokens = 0
                
                chunk_index += 1
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Add final chunk if exists
        if current_chunk:
            chunks.append({
                'chunk_id': f"{alert_id}_chunk_{chunk_index}",
                'content': ' '.join(current_chunk),
                'chunk_index': chunk_index,
                'token_count': current_tokens
            })
        
        # Update total chunks count
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk['total_chunks'] = total_chunks
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex"""
        # Simple sentence splitting on periods, exclamation marks, question marks
        sentences = re.split(r'[.!?]+', text)
        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _split_long_sentence(self, sentence: str, alert_id: str, start_index: int) -> List[Dict[str, str]]:
        """Split a very long sentence by words when it exceeds token limit"""
        words = sentence.split()
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = start_index
        
        for word in words:
            word_tokens = self._count_tokens(word)
            
            if current_tokens + word_tokens > self.max_tokens_per_chunk and current_chunk:
                chunks.append({
                    'chunk_id': f"{alert_id}_chunk_{chunk_index}",
                    'content': ' '.join(current_chunk),
                    'chunk_index': chunk_index,
                    'token_count': current_tokens
                })
                current_chunk = []
                current_tokens = 0
                chunk_index += 1
            
            current_chunk.append(word)
            current_tokens += word_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'chunk_id': f"{alert_id}_chunk_{chunk_index}",
                'content': ' '.join(current_chunk),
                'chunk_index': chunk_index,
                'token_count': current_tokens
            })
        
        return chunks
    
    def _get_overlap_text(self, chunk_words: List[str], overlap_tokens: int) -> str:
        """Get overlap text from the end of current chunk"""
        if not chunk_words or overlap_tokens <= 0:
            return ""
        
        # Take words from the end until we reach overlap token limit
        overlap_words = []
        current_tokens = 0
        
        for word in reversed(chunk_words):
            word_tokens = self._count_tokens(word)
            if current_tokens + word_tokens > overlap_tokens:
                break
            overlap_words.insert(0, word)
            current_tokens += word_tokens
        
        return ' '.join(overlap_words)
    
    def ingest_data(self, batch_size: int = 100):
        """Ingest data into ChromaDB with token-based chunking"""
        df = self.load_and_preprocess_data()
        
        logger.info("Starting data ingestion with token-based chunking into ChromaDB")
        
        # Clear existing data
        try:
            self.collection.delete()
            logger.info("Cleared existing collection data")
        except:
            pass
        
        # Prepare chunked data for insertion
        all_chunks = []
        total_chunks_created = 0
        
        for idx, row in df.iterrows():
            # Create chunks for the searchable content
            chunks = self._chunk_text_by_tokens(row['searchable_content'], row['alert_id'])
            
            for chunk in chunks:
                chunk_data = {
                    'chunk_id': chunk['chunk_id'],
                    'content': chunk['content'],
                    'metadata': {
                        'alert_id': row['alert_id'],
                        'timestamp': row['timestamp'].isoformat(),
                        'original_log': row['log'],
                        'original_trace': row['trace'] if pd.notna(row['trace']) else "",
                        'original_metric': row['metric'] if pd.notna(row['metric']) else "",
                        'rca': row['rca'],
                        'fix': row['fix'],
                        'chunk_index': chunk['chunk_index'],
                        'total_chunks': chunk['total_chunks'],
                        'token_count': chunk['token_count']
                    }
                }
                all_chunks.append(chunk_data)
            
            total_chunks_created += len(chunks)
            
            if idx % 100 == 0:
                logger.info(f"Processed {idx + 1}/{len(df)} records, created {total_chunks_created} chunks")
        
        logger.info(f"Created {total_chunks_created} chunks from {len(df)} records")
        
        # Batch insert chunks
        total_batches = (len(all_chunks) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(all_chunks))
            batch_chunks = all_chunks[start_idx:end_idx]
            
            # Prepare batch data for ChromaDB
            ids = [chunk['chunk_id'] for chunk in batch_chunks]
            documents = [chunk['content'] for chunk in batch_chunks]
            metadatas = [chunk['metadata'] for chunk in batch_chunks]
            
            try:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                
                logger.info(f"Inserted batch {batch_idx + 1}/{total_batches} "
                           f"({len(batch_chunks)} chunks)")
                
            except Exception as e:
                logger.error(f"Error inserting batch {batch_idx + 1}: {str(e)}")
                raise
        
        logger.info(f"Successfully ingested {total_chunks_created} chunks from {len(df)} alerts")
        return total_chunks_created
    
    def find_rca_and_fix(self, 
                        alert: str = "", 
                        log: str = "", 
                        trace: str = "", 
                        metric: str = "",
                        top_k: int = 5,
                        similarity_threshold: float = 0.7) -> List[Dict]:
        """
        Find RCA and fix recommendations based on input alert data
        
        Args:
            alert: Alert/error description
            log: Log information
            trace: Trace information  
            metric: Metric information
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score to include
            
        Returns:
            List of dictionaries containing RCA and fix recommendations
        """
        # Construct search query from provided inputs
        query_parts = []
        if alert:
            query_parts.append(f"Error Log: {alert}")
        if log:
            query_parts.append(f"Error Log: {log}")
        if trace:
            query_parts.append(f"Trace: {trace}")
        if metric:
            query_parts.append(f"Metrics: {metric}")
        
        if not query_parts:
            logger.warning("No input provided for search")
            return []
        
        query = " | ".join(query_parts)
        logger.info(f"Searching for similar alerts with query length: {len(query)} characters")
        
        try:
            # Search in ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k * 3, 50)  # Get more results to aggregate
            )
            
            if not results['documents'] or not results['documents'][0]:
                logger.info("No similar alerts found")
                return []
            
            # Process and aggregate results
            aggregated_results = self._aggregate_chunk_results(
                results, similarity_threshold, top_k
            )
            
            logger.info(f"Found {len(aggregated_results)} relevant RCA/fix recommendations")
            return aggregated_results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise
    
    def _aggregate_chunk_results(self, 
                                results: Dict, 
                                similarity_threshold: float,
                                top_k: int) -> List[Dict]:
        """
        Aggregate results from multiple chunks belonging to same alerts
        """
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        
        # Group chunks by alert_id
        alert_groups = {}
        
        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
            # Convert distance to similarity score (ChromaDB uses cosine distance)
            similarity = 1 - distance
            
            if similarity < similarity_threshold:
                continue
            
            alert_id = metadata['alert_id']
            
            if alert_id not in alert_groups:
                alert_groups[alert_id] = {
                    'alert_id': alert_id,
                    'chunks': [],
                    'best_similarity': similarity,
                    'rca': metadata['rca'],
                    'fix': metadata['fix'],
                    'timestamp': metadata['timestamp'],
                    'original_log': metadata['original_log'],
                    'original_trace': metadata['original_trace'],
                    'original_metric': metadata['original_metric']
                }
            
            # Update best similarity if this chunk is better
            if similarity > alert_groups[alert_id]['best_similarity']:
                alert_groups[alert_id]['best_similarity'] = similarity
            
            alert_groups[alert_id]['chunks'].append({
                'content': doc,
                'similarity': similarity,
                'chunk_index': metadata['chunk_index'],
                'token_count': metadata['token_count']
            })
        
        # Convert to list and sort by best similarity
        aggregated = list(alert_groups.values())
        aggregated.sort(key=lambda x: x['best_similarity'], reverse=True)
        
        # Format final results
        final_results = []
        for alert_data in aggregated[:top_k]:
            result = {
                'alert_id': alert_data['alert_id'],
                'similarity_score': round(alert_data['best_similarity'], 3),
                'rca': alert_data['rca'],
                'fix': alert_data['fix'],
                'timestamp': alert_data['timestamp'],
                'original_data': {
                    'log': alert_data['original_log'],
                    'trace': alert_data['original_trace'],
                    'metric': alert_data['original_metric']
                },
                'matching_chunks': len(alert_data['chunks']),
                'best_chunk_similarity': round(max(chunk['similarity'] for chunk in alert_data['chunks']), 3)
            }
            final_results.append(result)
        
        return final_results
    
    def search_similar_alerts(self, 
                             query: str, 
                             top_k: int = 5,
                             include_content: bool = False) -> List[Dict]:
        """
        Search for similar alerts using free-form query
        
        Args:
            query: Search query
            top_k: Number of results to return
            include_content: Whether to include chunk content in results
            
        Returns:
            List of similar alerts with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k * 2  # Get extra to deduplicate
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            # Process results
            processed_results = []
            seen_alert_ids = set()
            
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            for doc, metadata, distance in zip(documents, metadatas, distances):
                alert_id = metadata['alert_id']
                
                # Skip if we've already seen this alert (take the best match)
                if alert_id in seen_alert_ids:
                    continue
                
                seen_alert_ids.add(alert_id)
                
                similarity = 1 - distance
                result = {
                    'alert_id': alert_id,
                    'similarity_score': round(similarity, 3),
                    'timestamp': metadata['timestamp'],
                    'rca': metadata['rca'],
                    'fix': metadata['fix'],
                    'chunk_index': metadata['chunk_index'],
                    'total_chunks': metadata['total_chunks']
                }
                
                if include_content:
                    result['content'] = doc
                    result['original_data'] = {
                        'log': metadata['original_log'],
                        'trace': metadata['original_trace'],
                        'metric': metadata['original_metric']
                    }
                
                processed_results.append(result)
                
                if len(processed_results) >= top_k:
                    break
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the ChromaDB collection"""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to analyze
            sample_results = self.collection.get(limit=100)
            
            stats = {
                'total_chunks': count,
                'unique_alerts': len(set(meta['alert_id'] for meta in sample_results['metadatas'])),
                'collection_name': self.collection_name,
                'max_tokens_per_chunk': self.max_tokens_per_chunk,
                'chunk_overlap': self.chunk_overlap
            }
            
            if sample_results['metadatas']:
                token_counts = [meta['token_count'] for meta in sample_results['metadatas']]
                stats['avg_tokens_per_chunk'] = round(np.mean(token_counts), 2)
                stats['max_tokens_in_sample'] = max(token_counts)
                stats['min_tokens_in_sample'] = min(token_counts)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}


def main():
    """Example usage of the Alert RCA System"""
    
    # Initialize the system
    csv_file = "Java_Alerts_RCA_Dataset_10_000_Unique_Entries.csv"
    alert_system = AlertRCASystem(
        csv_file_path=csv_file,
        collection_name="java_alerts_chunked",
        max_tokens_per_chunk=512,
        chunk_overlap=50
    )
    
    print("=== Starting Data Ingestion ===")
    total_chunks = alert_system.ingest_data(batch_size=50)
    print(f"Ingested {total_chunks} chunks")
    
    print("\n=== Collection Statistics ===")
    stats = alert_system.get_collection_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== Example Searches ===")
    
    # Example 1: Search with NullPointerException
    print("\n1. Searching for NullPointerException:")
    results = alert_system.find_rca_and_fix(
        log="java.lang.NullPointerException at com.example.service.method",
        metric="heap_memory_usage: 2048MB, cpu_load: 85%",
        top_k=3
    )
    
    for i, result in enumerate(results, 1):
        print(f"   Result {i} (similarity: {result['similarity_score']}):")
        print(f"   RCA: {result['rca']}")
        print(f"   Fix: {result['fix']}")
        print()
    
    # Example 2: Search with SQL Exception
    print("2. Searching for SQL Connection issues:")
    results = alert_system.find_rca_and_fix(
        alert="Database connection failed",
        trace="operation: fetchData, duration: 5000ms",
        top_k=2
    )
    
    for i, result in enumerate(results, 1):
        print(f"   Result {i} (similarity: {result['similarity_score']}):")
        print(f"   RCA: {result['rca']}")
        print(f"   Fix: {result['fix']}")
        print()
    
    # Example 3: Free-form search
    print("3. Free-form search for memory issues:")
    results = alert_system.search_similar_alerts(
        query="OutOfMemoryError heap space memory",
        top_k=2,
        include_content=True
    )
    
    for i, result in enumerate(results, 1):
        print(f"   Result {i} (similarity: {result['similarity_score']}):")
        print(f"   Alert ID: {result['alert_id']}")
        print(f"   RCA: {result['rca']}")
        print(f"   Fix: {result['fix']}")
        print()


if __name__ == "__main__":
    main()
