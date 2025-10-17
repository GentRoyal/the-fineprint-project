from services.notebooklm import RAGService
import asyncio
import json
from typing import List

async def analyze_document(doc_id: str, top_k: int = 10) -> dict:
    """
    Convenience function to analyze a document by ID.
    
    Usage:
        result = await analyze_document("doc123")
    """
    service = RAGService()
    return await service.generate_structured_analysis(doc_id, top_k)


async def store_document(doc_id: str, text: str, table: str = "documents"):
    """
    Convenience function to store a document.
    
    Usage:
        await store_document("doc123", "Document text here...")
    """
    service = RAGService()
    await service.upsert_chunks(table, doc_id, text)


async def search_documents(query: str, top_k: int = 5) -> List[dict]:
    """
    Convenience function to search across all documents.
    
    Usage:
        results = await search_documents("contract terms", top_k=10)
    """
    service = RAGService()
    return await service.query_chunks(query, top_k)

async def main():
    rag = RAGService()
    
    # Generate analysis
    result = await rag.generate_structured_analysis(
        doc_id="ec3df64b",
        top_k=5
    )
    
    print(json.dumps(result, indent=2))

asyncio.run(main())