from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from services.llm_solution import harmful_clause_analysis
from services.upload_doc import extract_text_from_file

router = APIRouter()

class DocumentRequest(BaseModel):
    text: str

@router.post("/get_clauses")
async def get_clauses(request: DocumentRequest):
    return analyze_document(request.text, harmful_clause_analysis)

@router.post("/get_clauses_file")
async def get_clauses_file(file: UploadFile = File(...)):
    text = await extract_text_from_file(file)
    return analyze_document(text, harmful_clause_analysis)


def analyze_document(text: str, chain_function) -> dict:
    chain = chain_function()
    response = chain.invoke({"document": text})
    return response
