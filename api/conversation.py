from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services.upload_doc import extract_text_from_file
from services.rag_service import RAGService
from services.podcast_text import PodcastGenerator
from services.podcast_sound import generate as generate_audio
import uuid

router = APIRouter()

class DocumentRequest(BaseModel):
    text: str

@router.post("/conversation_clauses")
async def get_clauses(request: DocumentRequest):
    file_path = await generate_podcast_script(request.text)
    return FileResponse(file_path, media_type="audio/wav", filename="podcast.wav")

@router.post("/conversation_clauses_file")
async def get_clauses_file(file: UploadFile = File(...)):
    text = await extract_text_from_file(file)
    file_path = await generate_podcast_script(text)
    return FileResponse(file_path, media_type="audio/wav", filename="podcast.wav")

async def analyze_document(text: str):
    rag_service = RAGService()
    doc_id = str(uuid.uuid4())
    table = "documents"
    
    await rag_service.upsert_chunks(table, doc_id, text)
    return doc_id

async def generate_podcast_script(text: str):
    doc_id = await analyze_document(text)
    
    generator = PodcastGenerator()
    podcast = await generator.generate_podcast(doc_id=doc_id, top_k=8)
    conversation = generator.format_for_display(podcast)
    
    file_path = generate_audio(conversation)
    return file_path