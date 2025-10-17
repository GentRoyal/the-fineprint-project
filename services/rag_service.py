from typing import List, Optional
import asyncio
from fastapi import HTTPException
from services.pinecode_service import initialize_pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from services.notebooklm import generate_analysis_from_chunks

from dotenv import load_dotenv
import os
import logging
logger = logging.getLogger(__name__)

load_dotenv()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")

class RAGService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.pinecone = initialize_pinecone()
        logger.info("RAGService initialized")

    async def get_embeddings(self, text: str) -> List[float]:
        try:
            return await asyncio.to_thread(self.embeddings.embed_query, text)
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def chunk_text(self, text: str) -> List[str]:
        words = text.split()
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + CHUNK_SIZE, len(words))
            chunks.append(" ".join(words[start:end]))
            start += CHUNK_SIZE - CHUNK_OVERLAP
        
        logger.info(f"Chunked into {len(chunks)} segments")
        return chunks

    async def upsert_chunks(self, table: str, doc_id: str, text: str):
        chunks = self.chunk_text(text)
        to_upsert = []

        for idx, chunk in enumerate(chunks):
            try:
                embedding = await self.get_embeddings(chunk)
                to_upsert.append({
                    "id": f"{doc_id}_chunk_{idx}",
                    "values": embedding,
                    "metadata": {
                        "table": table,
                        "id": doc_id,
                        "chunk_index": idx,
                        "chunk": chunk
                    }
                })
            except Exception as e:
                logger.warning(f"Chunk {idx} failed: {e}")
                continue

        if to_upsert:
            try:
                self.pinecone.upsert(vectors=to_upsert)
                logger.info(f"Upserted {len(to_upsert)} chunks")
            except Exception as e:
                logger.error(f"Upsert failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def query_chunks(
        self, 
        query: str, 
        top_k: int = 5, 
        filter_dict: Optional[dict] = None
    ) -> List[dict]:
        try:
            embedding = await self.get_embeddings(query)
            params = {
                "vector": embedding,
                "top_k": top_k,
                "include_metadata": True
            }
            if filter_dict:
                params["filter"] = filter_dict
            
            results = self.pinecone.query(**params)
            return [m['metadata'] for m in results.get('matches', []) 
                   if 'metadata' in m]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def generate_structured_analysis(
        self, 
        doc_id: str, 
        top_k: int = 8
    ) -> dict:
        try:
            metadata = await self.query_chunks(
                "themes issues recommendations",
                top_k=top_k,
                filter_dict={"id": doc_id}
            )

            if not metadata:
                raise HTTPException(status_code=404, detail=f"Doc {doc_id} not found")

            chunks = [m['chunk'] for m in metadata]
            analysis = await generate_analysis_from_chunks(chunks)

            # Map chunk indices
            for theme in analysis.themes:
                for example in theme.examples:
                    for m in metadata:
                        if example.text_snippet in m['chunk']:
                            example.chunk_index = m['chunk_index']
                            break

            logger.info(f"Analysis generated for {doc_id}")
            return analysis.model_dump()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))