"""
Dense (Vector) Search using ChromaDB.
Semantic search for Arabic poetry verses.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from .embeddings import ArabicEmbeddings, get_embeddings


class DenseRetriever:
    """
    Dense retriever using ChromaDB for semantic search.
    """
    
    def __init__(
        self,
        persist_directory: str = "data/vectordb",
        collection_name: str = "poetry_verses",
        embeddings: Optional[ArabicEmbeddings] = None
    ):
        """
        Initialize dense retriever.
        
        Args:
            persist_directory: Directory to persist ChromaDB
            collection_name: Name of the collection
            embeddings: Embeddings model (creates default if None)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embeddings = embeddings or get_embeddings()
        self.vectorstore = None
    
    def build_index(self, chunks_path: str) -> int:
        """
        Build vector index from chunks JSON file.
        
        Args:
            chunks_path: Path to all_chunks_final.json
            
        Returns:
            Number of documents indexed
        """
        # Load chunks
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        # Convert to LangChain Documents
        documents = []
        for chunk in chunks:
            doc = Document(
                page_content=chunk.get('text', ''),
                metadata={
                    'chunk_id': chunk.get('chunk_id'),
                    'verse_text': chunk.get('verse_text', ''),
                    'verse_number': chunk.get('verse_number'),
                    'poet_name': chunk.get('poet_name', ''),
                    'poem_name': chunk.get('poem_name', ''),
                    'source_book': chunk.get('source', {}).get('book', ''),
                    'has_explanation': chunk.get('metadata', {}).get('has_explanation', False)
                }
            )
            documents.append(doc)
        
        # Create ChromaDB vectorstore
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings.get_langchain_embeddings(),
            persist_directory=self.persist_directory,
            collection_name=self.collection_name
        )
        
        return len(documents)
    
    def load_index(self) -> bool:
        """
        Load existing vector index.
        
        Returns:
            True if loaded successfully
        """
        try:
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings.get_langchain_embeddings(),
                collection_name=self.collection_name
            )
            return True
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar verses.
        
        Args:
            query: Search query (verse or part of verse)
            k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of results with scores
        """
        if not self.vectorstore:
            raise ValueError("Index not loaded. Call build_index() or load_index() first.")
        
        # Search with scores
        results = self.vectorstore.similarity_search_with_relevance_scores(
            query,
            k=k
        )
        
        # Format results
        formatted = []
        for doc, score in results:
            if score >= score_threshold:
                formatted.append({
                    'text': doc.page_content,
                    'score': score,
                    'metadata': doc.metadata,
                    'source': 'dense'
                })
        
        return formatted
    
    def get_retriever(self, k: int = 5):
        """Get LangChain retriever object."""
        if not self.vectorstore:
            raise ValueError("Index not loaded.")
        return self.vectorstore.as_retriever(search_kwargs={"k": k})


def build_dense_index(
    chunks_path: str = "data/processed/all_chunks_final.json",
    persist_dir: str = "data/vectordb"
) -> DenseRetriever:
    """
    Convenience function to build dense index.
    """
    retriever = DenseRetriever(persist_directory=persist_dir)
    count = retriever.build_index(chunks_path)
    print(f"Indexed {count} documents in ChromaDB")
    return retriever
