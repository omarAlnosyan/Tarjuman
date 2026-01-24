# -*- coding: utf-8 -*-
"""
Tarjuman API Runner
"""
import sys
import uvicorn

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    print("=" * 60)
    print("Tarjuman API Starting...")
    print("=" * 60)
    print()
    print("API Docs:  http://localhost:8000/docs")
    print("ReDoc:     http://localhost:8000/redoc")
    print("Health:    http://localhost:8000/health")
    print()
    print("-" * 60)
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False  # Disabled to avoid crashes during file changes
    )
