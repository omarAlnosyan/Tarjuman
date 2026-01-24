# -*- coding: utf-8 -*-
"""Rebuild search indices from new chunks."""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.retrieval.hybrid_search import create_hybrid_retriever

CHUNKS_PATH = "data/processed/all_chunks_final.json"
VECTORDB_PATH = "data/vectordb"

def main():
    print("=" * 60)
    print("Rebuilding Search Indices")
    print("=" * 60)
    
    print("\nThis will rebuild both BM25 and FAISS indices...")
    print(f"Chunks: {CHUNKS_PATH}")
    print(f"VectorDB: {VECTORDB_PATH}")
    
    # Create/rebuild indices
    print("\nBuilding indices...")
    retriever = create_hybrid_retriever(
        chunks_path=CHUNKS_PATH,
        vectordb_path=VECTORDB_PATH,
        build_new=True  # Force rebuild
    )
    
    print("\nTesting search...")
    
    # Test searches
    test_queries = [
        "قفا نبك من ذكرى حبيب",
        "هل غادر الشعراء",
        "ألا هبي بصحنك",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = retriever.search(query, k=1)
        if results:
            r = results[0]
            print(f"  Found: {r.verse_text[:50]}...")
            print(f"  Poet: {r.poet_name}")
            print(f"  Score: {r.score:.2f}")
        else:
            print("  No results found")
    
    print("\n" + "=" * 60)
    print("Done! Indices rebuilt successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
