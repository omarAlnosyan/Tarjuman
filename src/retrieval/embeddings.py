"""
Embeddings module for Al-Fasih Arabic Poetry RAG.
Uses multilingual-e5-base for Arabic semantic search.
"""

from typing import List
from langchain_huggingface import HuggingFaceEmbeddings


class ArabicEmbeddings:
    """
    Arabic-optimized embeddings using multilingual-e5-base.
    Best performance for Arabic semantic search.
    """
    
    DEFAULT_MODEL = "intfloat/multilingual-e5-base"
    
    def __init__(self, model_name: str = None, device: str = "cpu"):
        """
        Initialize embeddings model.
        
        Args:
            model_name: HuggingFace model name
            device: 'cpu' or 'cuda'
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={"device": self.device},
            encode_kwargs={"normalize_embeddings": True}
        )
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        # E5 models require 'query: ' prefix for queries
        return self.embeddings.embed_query(f"query: {text}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        # E5 models require 'passage: ' prefix for documents
        prefixed = [f"passage: {t}" for t in texts]
        return self.embeddings.embed_documents(prefixed)
    
    def get_langchain_embeddings(self) -> HuggingFaceEmbeddings:
        """Return LangChain-compatible embeddings object."""
        return self.embeddings


def get_embeddings(device: str = "cpu") -> ArabicEmbeddings:
    """Factory function to create embeddings."""
    return ArabicEmbeddings(device=device)
