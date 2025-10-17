from fastapi import UploadFile
import pdfplumber

async def extract_text_from_file(file: UploadFile) -> str:
    content = await file.read()
    
    if file.filename.endswith('.txt'):
        return content.decode('utf-8')
    
    elif file.filename.endswith('.pdf'):
        with pdfplumber.open(file.file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text
    
    # Add more formats if needed
    else:
        return content.decode('utf-8')