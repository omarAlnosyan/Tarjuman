"""
Retrieval module for Al-Fasih Arabic Poetry RAG.
Provides hybrid search (dense + sparse) for verse matching.
"""

from .embeddings import ArabicEmbeddings, get_embeddings
from .dense_search import DenseRetriever, build_dense_index
from .sparse_search import SparseRetriever, build_sparse_index
from .hybrid_search import HybridRetriever, SearchResult, create_hybrid_retriever

__all__ = [
    'ArabicEmbeddings',
    'get_embeddings',
    'DenseRetriever',
    'build_dense_index',
    'SparseRetriever',
    'build_sparse_index',
    'HybridRetriever',
    'SearchResult',
    'create_hybrid_retriever',
]
