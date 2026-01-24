"""
Sparse (BM25) Search for exact verse matching.
Critical for Arabic poetry where exact words matter.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from rank_bm25 import BM25Okapi

# Arabic normalization
try:
    from pyarabic import araby
    HAS_PYARABIC = True
except ImportError:
    HAS_PYARABIC = False


class SparseRetriever:
    """
    BM25-based sparse retriever for exact matching.
    Essential for Arabic poetry where exact wording matters.
    """
    
    def __init__(self):
        """Initialize sparse retriever."""
        self.bm25 = None
        self.documents = []
        self.tokenized_corpus = []
    
    def normalize_arabic(self, text: str) -> str:
        """
        Normalize Arabic text for better matching.
        """
        if not text:
            return ""
        
        # إزالة التشكيل يدوياً (أهم شيء)
        tashkeel = '\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670'
        for char in tashkeel:
            text = text.replace(char, '')
        
        if HAS_PYARABIC:
            try:
                # Remove tashkeel (diacritics)
                text = araby.strip_tashkeel(text)
                # Normalize hamza
                text = araby.normalize_hamza(text)
                # Normalize alef
                text = araby.normalize_ligature(text)
            except:
                pass
        
        # إزالة "..." والنقاط
        text = text.replace('...', ' ').replace('…', ' ')
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Arabic text.
        """
        normalized = self.normalize_arabic(text)
        # Simple whitespace tokenization for Arabic
        tokens = normalized.split()
        return tokens
    
    def build_index(self, chunks_path: str) -> int:
        """
        Build BM25 index from chunks.
        
        Args:
            chunks_path: Path to all_chunks_final.json
            
        Returns:
            Number of documents indexed
        """
        # Load chunks
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        self.documents = chunks
        
        # Create tokenized corpus from verse_text (for exact matching)
        self.tokenized_corpus = []
        for chunk in chunks:
            verse_text = chunk.get('verse_text', '')
            full_text = chunk.get('text', '')
            # Combine verse and explanation for matching
            combined = f"{verse_text} {full_text}"
            tokens = self.tokenize(combined)
            self.tokenized_corpus.append(tokens)
        
        # Build BM25 index
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        return len(self.documents)
    
    def search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for matching verses using BM25.
        
        Args:
            query: Search query
            k: Number of results
            score_threshold: Minimum BM25 score
            
        Returns:
            List of results with scores
        """
        if not self.bm25:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Tokenize query
        query_tokens = self.tokenize(query)
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:k]
        
        # Format results
        results = []
        for idx in top_indices:
            score = scores[idx]
            if score >= score_threshold:
                chunk = self.documents[idx]
                results.append({
                    'text': chunk.get('text', ''),
                    'score': float(score),
                    'metadata': {
                        'chunk_id': chunk.get('chunk_id'),
                        'verse_text': chunk.get('verse_text', ''),
                        'verse_number': chunk.get('verse_number'),
                        'poet_name': chunk.get('poet_name', ''),
                        'poem_name': chunk.get('poem_name', ''),
                        'source_book': chunk.get('source', {}).get('book', ''),
                    },
                    'source': 'sparse'
                })
        
        return results
    
    def exact_match(self, verse: str) -> Optional[Dict[str, Any]]:
        """
        Try to find exact match for a verse.
        
        Args:
            verse: The verse text to match
            
        Returns:
            Matching document or None
        """
        if not self.documents:
            return None
        
        normalized_query = self.normalize_arabic(verse)
        # إزالة "..." من النص المبحث عنه
        normalized_query = normalized_query.replace('...', '').replace('…', '').strip()
        
        # البحث في جميع الأبيات
        for chunk in self.documents:
            verse_text = chunk.get('verse_text', '')
            if not verse_text:
                continue
                
            normalized_verse = self.normalize_arabic(verse_text)
            # إزالة "..." من البيت في قاعدة البيانات
            normalized_verse = normalized_verse.replace('...', '').replace('…', '').strip()
            
            # Check if query is contained in verse (السماح بالبحث الجزئي)
            if normalized_query in normalized_verse:
                return {
                    'text': chunk.get('text', ''),
                    'score': 1.0,  # Perfect match
                    'metadata': {
                        'chunk_id': chunk.get('chunk_id'),
                        'verse_text': verse_text,
                        'verse_number': chunk.get('verse_number'),
                        'poet_name': chunk.get('poet_name', ''),
                        'poem_name': chunk.get('poem_name', ''),
                        'source_book': chunk.get('source', {}).get('book', '') if isinstance(chunk.get('source'), dict) else '',
                    },
                    'source': 'exact_match'
                }
        
        return None


def build_sparse_index(
    chunks_path: str = "data/processed/all_chunks_final.json"
) -> SparseRetriever:
    """
    Convenience function to build sparse index.
    """
    retriever = SparseRetriever()
    count = retriever.build_index(chunks_path)
    print(f"Indexed {count} documents in BM25")
    return retriever
