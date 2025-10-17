import json
import logging
import os
from fastapi import HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional


from langchain_groq import ChatGroq
from langchain.schema import HumanMessage

load_dotenv()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")

logger = logging.getLogger(__name__)

llm_client = ChatGroq(
    model = os.getenv("GROQ_MODEL"),
    api_key = os.getenv("GROQ_API_KEY"),
    temperature = 0.7
)

class Example(BaseModel):
    text_snippet: str = Field(description="Text snippet")
    chunk_index: Optional[int] = None

class Theme(BaseModel):
    name: str
    positives: List[str] = Field()
    negatives: List[str] = Field()
    examples: List[Example] = Field()

class RedFlag(BaseModel):
    clause: str
    reason: str
    severity: str

class UserAction(BaseModel):
    action: str
    where_clause: str
    urgency: str

class AnalysisSchema(BaseModel):
    summary: str
    themes: List[Theme] = Field()
    top_red_flags: List[RedFlag] = Field()
    user_actions: List[UserAction] = Field()

async def call_llm_with_json_output(prompt: str) -> dict:
    try:
        response = await llm_client.ainvoke([HumanMessage(content=prompt)])
        text = response.content.strip()
        
        logger.debug(f"LLM raw response (first 300 chars): {text[:300]}")
        
        # Extract JSON from markdown blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        
        # Remove any leading/trailing whitespace and newlines
        text = text.strip()
        
        if not text:
            raise ValueError("Empty response from LLM")
        
        # Find JSON object boundaries
        json_start = text.find('{')
        json_end = text.rfind('}')
        
        if json_start == -1 or json_end == -1:
            logger.error(f"No JSON object found in response: {text[:200]}")
            raise ValueError("No JSON object boundaries found")
        
        text = text[json_start:json_end + 1]
        logger.debug(f"Extracted JSON: {text[:200]}")
        
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}\nAttempted parse: {text[:200]}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON response: {str(e)}")
    except Exception as e:
        logger.error(f"LLM/JSON processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_analysis_from_chunks(chunks: List[str]) -> AnalysisSchema:
    combined = "\n---\n".join(chunks[:8])  # Limit to 8 chunks
    
    prompt = f"""Analyze these document chunks and return ONLY a valid JSON object (no markdown, no extra text).

                DOCUMENT CHUNKS:
                {combined}

                Return this exact JSON structure:
                {{
                "summary": "brief 2-3 sentence summary of the document",
                "themes": [
                    {{
                    "name": "theme name",
                    "positives": ["positive aspect 1", "positive aspect 2"],
                    "negatives": ["negative aspect 1", "negative aspect 2"],
                    "examples": [{{"text_snippet": "actual quote from document"}}]
                    }},
                    {{
                    "name": "another theme",
                    "positives": ["positive1", "positive2"],
                    "negatives": ["negative1", "negative2"],
                    "examples": [{{"text_snippet": "quote"}}]
                    }},
                    {{
                    "name": "third theme",
                    "positives": ["positive1", "positive2"],
                    "negatives": ["negative1", "negative2"],
                    "examples": [{{"text_snippet": "quote"}}]
                    }}
                ],
                "top_red_flags": [
                    {{"clause": "problematic clause", "reason": "why concerning", "severity": "high"}},
                    {{"clause": "issue 2", "reason": "reason", "severity": "medium"}},
                    {{"clause": "issue 3", "reason": "reason", "severity": "high"}}
                ],
                "user_actions": [
                    {{"action": "what user should do", "where_clause": "document section", "urgency": "high"}},
                    {{"action": "action 2", "where_clause": "section", "urgency": "medium"}},
                    {{"action": "action 3", "where_clause": "section", "urgency": "medium"}}
                ]
                }}

                Start JSON immediately with {{ - no other text."""

    try:
        json_out = await call_llm_with_json_output(prompt)
        return AnalysisSchema(**json_out)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))