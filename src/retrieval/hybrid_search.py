"""
Hybrid Search combining Dense (semantic) + Sparse (BM25).
Best approach for Arabic poetry: exact matching + meaning.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .dense_search import DenseRetriever, build_dense_index
from .sparse_search import SparseRetriever, build_sparse_index


@dataclass
class SearchResult:
    """Unified search result."""
    text: str
    verse_text: str
    explanation: str
    score: float
    poet_name: str
    poem_name: str
    source_book: str
    chunk_id: int
    verse_number: int  # رقم البيت في القصيدة
    retrieval_source: str  # 'dense', 'sparse', 'hybrid', 'exact_match'


class HybridRetriever:
    """
    Hybrid retriever combining dense and sparse search.
    
    Strategy:
    1. Try exact match first (fastest, most accurate)
    2. Run both dense and sparse search
    3. Merge and re-rank results
    """
    
    def __init__(
        self,
        dense_retriever: Optional[DenseRetriever] = None,
        sparse_retriever: Optional[SparseRetriever] = None,
        dense_weight: float = 0.3,
        sparse_weight: float = 0.7
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            dense_retriever: Dense (vector) retriever
            sparse_retriever: Sparse (BM25) retriever
            dense_weight: Weight for dense scores (0-1)
            sparse_weight: Weight for sparse scores (0-1)
        """
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        
        # Normalize weights
        total = self.dense_weight + self.sparse_weight
        self.dense_weight /= total
        self.sparse_weight /= total
    
    def build_indices(self, chunks_path: str, vectordb_path: str = "data/vectordb"):
        """
        Build both dense and sparse indices.
        
        Args:
            chunks_path: Path to chunks JSON
            vectordb_path: Path for ChromaDB persistence
        """
        print("Building Dense Index (ChromaDB)...")
        self.dense = DenseRetriever(persist_directory=vectordb_path)
        dense_count = self.dense.build_index(chunks_path)
        print(f"  Indexed {dense_count} documents")
        
        print("Building Sparse Index (BM25)...")
        self.sparse = SparseRetriever()
        sparse_count = self.sparse.build_index(chunks_path)
        print(f"  Indexed {sparse_count} documents")
        
        print("Hybrid index ready!")
    
    def load_indices(self, chunks_path: str, vectordb_path: str = "data/vectordb"):
        """
        Load existing indices.
        """
        # Load dense
        self.dense = DenseRetriever(persist_directory=vectordb_path)
        self.dense.load_index()
        
        # Build sparse (BM25 needs to be rebuilt each time)
        self.sparse = SparseRetriever()
        self.sparse.build_index(chunks_path)
    
    def _normalize_scores(self, results: List[Dict], method: str = "minmax") -> List[Dict]:
        """
        Normalize scores to 0-1 range.
        """
        if not results:
            return results
        
        scores = [r['score'] for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            for r in results:
                r['normalized_score'] = 1.0
        else:
            for r in results:
                r['normalized_score'] = (r['score'] - min_score) / (max_score - min_score)
        
        return results
    
    def _merge_results(
        self,
        dense_results: List[Dict],
        sparse_results: List[Dict],
        k: int
    ) -> List[Dict]:
        """
        Merge and re-rank results from both retrievers.
        
        Uses Reciprocal Rank Fusion (RRF) for combining.
        """
        # Normalize scores
        dense_results = self._normalize_scores(dense_results)
        sparse_results = self._normalize_scores(sparse_results)
        
        # Create merged dict by chunk_id
        merged = {}
        
        # Add dense results
        for i, result in enumerate(dense_results):
            chunk_id = result['metadata'].get('chunk_id')
            if chunk_id not in merged:
                merged[chunk_id] = {
                    'text': result['text'],
                    'metadata': result['metadata'],
                    'dense_score': result.get('normalized_score', 0),
                    'sparse_score': 0,
                    'dense_rank': i + 1,
                    'sparse_rank': len(sparse_results) + 1
                }
            else:
                merged[chunk_id]['dense_score'] = result.get('normalized_score', 0)
                merged[chunk_id]['dense_rank'] = i + 1
        
        # Add sparse results
        for i, result in enumerate(sparse_results):
            chunk_id = result['metadata'].get('chunk_id')
            if chunk_id not in merged:
                merged[chunk_id] = {
                    'text': result['text'],
                    'metadata': result['metadata'],
                    'dense_score': 0,
                    'sparse_score': result.get('normalized_score', 0),
                    'dense_rank': len(dense_results) + 1,
                    'sparse_rank': i + 1
                }
            else:
                merged[chunk_id]['sparse_score'] = result.get('normalized_score', 0)
                merged[chunk_id]['sparse_rank'] = i + 1
        
        # Calculate hybrid score using weighted combination + RRF
        RRF_K = 60  # RRF constant
        for chunk_id, data in merged.items():
            # Weighted score combination
            weighted_score = (
                self.dense_weight * data['dense_score'] +
                self.sparse_weight * data['sparse_score']
            )
            
            # RRF score
            rrf_score = (
                1 / (RRF_K + data['dense_rank']) +
                1 / (RRF_K + data['sparse_rank'])
            )
            
            # Combine both (weighted more towards direct scores)
            data['hybrid_score'] = 0.7 * weighted_score + 0.3 * rrf_score * 10
        
        # Sort by hybrid score
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x['hybrid_score'],
            reverse=True
        )[:k]
        
        # Format final results
        final_results = []
        for result in sorted_results:
            final_results.append({
                'text': result['text'],
                'score': result['hybrid_score'],
                'metadata': result['metadata'],
                'source': 'hybrid',
                'dense_score': result['dense_score'],
                'sparse_score': result['sparse_score']
            })
        
        return final_results
    
    def search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query (verse or part of verse)
            k: Number of results to return
            score_threshold: Minimum score threshold
            
        Returns:
            List of SearchResult objects
        """
        if not self.sparse:
            raise ValueError("Sparse index not initialized. Call build_indices() first.")
        
        # Step 1: Try exact match first
        exact = self.sparse.exact_match(query)
        if exact and exact.get('score', 0) >= 0.9:
            return [self._to_search_result(exact)]
        
        # Step 2: Run searches (with fallback)
        sparse_results = self.sparse.search(query, k=k*2, score_threshold=0.0)
        
        # Try dense search if available
        dense_results = []
        if self.dense:
            try:
                dense_results = self.dense.search(query, k=k*2)
            except Exception:
                # Fallback to sparse only
                pass
        
        # If no dense results, use sparse only
        if not dense_results:
            # Convert sparse results directly
            results = []
            for r in sparse_results[:k]:
                results.append(self._to_search_result(r))
            return results
        
        # Step 3: Merge and re-rank
        merged = self._merge_results(dense_results, sparse_results, k)
        
        # Step 4: Apply threshold and convert to SearchResult
        results = []
        for r in merged:
            if r['score'] >= score_threshold:
                results.append(self._to_search_result(r))
        
        return results
    
    def _to_search_result(self, result: Dict) -> SearchResult:
        """Convert dict to SearchResult."""
        metadata = result.get('metadata', {})
        text = result.get('text', '')
        
        # Extract explanation from text
        explanation = text
        if 'الشرح:' in text:
            explanation = text.split('الشرح:')[1].strip()
        
        return SearchResult(
            text=text,
            verse_text=metadata.get('verse_text', ''),
            explanation=explanation,
            score=result.get('score', 0),
            poet_name=metadata.get('poet_name', ''),
            poem_name=metadata.get('poem_name', ''),
            source_book=metadata.get('source_book', ''),
            chunk_id=metadata.get('chunk_id', 0),
            verse_number=metadata.get('verse_number', 0),
            retrieval_source=result.get('source', 'hybrid')
        )


def create_hybrid_retriever(
    chunks_path: str = "data/processed/all_chunks_final.json",
    vectordb_path: str = "data/vectordb",
    build_new: bool = False
) -> HybridRetriever:
    """
    Factory function to create hybrid retriever.
    
    Args:
        chunks_path: Path to chunks JSON
        vectordb_path: Path for vector DB
        build_new: If True, rebuild indices; else try to load
        
    Returns:
        Configured HybridRetriever
    """
    retriever = HybridRetriever()
    
    if build_new:
        retriever.build_indices(chunks_path, vectordb_path)
    else:
        retriever.load_indices(chunks_path, vectordb_path)
    
    return retriever
