from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
import httpx
import os
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.instagram.com/v18.0"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

# Import your existing services
from services.llm_solution import harmful_clause_analysis
from services.podcast_text import PodcastGenerator
from services.podcast_sound import generate as generate_audio
from services.upload_doc import extract_text_from_file
import uuid

class WhatsAppMessage(BaseModel):
    object: str
    entry: list

class WhatsAppStatus:
    RECEIVED = "received"
    SENT = "sent"
    FAILED = "failed"

@router.get("/webhook")
async def verify_webhook(token: str = None, challenge: str = None):
    """
    Webhook verification endpoint for WhatsApp
    """
    if token != VERIFY_TOKEN:
        return {"status": "unauthorized"}, 403
    
    return {"challenge": challenge}

@router.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming WhatsApp messages
    """
    try:
        data = await request.json()
        
        # Process in background to respond quickly
        background_tasks.add_task(process_message, data)
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}, 400

async def process_message(data: dict):
    """
    Process incoming WhatsApp messages
    """
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                
                # Check for messages
                messages = value.get("messages", [])
                for message in messages:
                    await handle_message(message, value)
                
                # Handle status updates
                statuses = value.get("statuses", [])
                for status in statuses:
                    logger.info(f"Message status: {status}")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")

async def handle_message(message: dict, metadata: dict):
    """
    Route message to appropriate handler
    """
    sender = message.get("from")
    message_type = message.get("type")
    timestamp = message.get("timestamp")
    message_id = message.get("id")
    
    try:
        if message_type == "text":
            text_content = message.get("text", {}).get("body", "")
            await process_text_message(sender, text_content, message_id)
        
        # elif message_type == "document":
        #     await process_document_message(sender, message.get("document", {}), message_id)
        
        else:
            await send_message(sender, f"Unsupported message type: {message_type}")
    
    except Exception as e:
        logger.error(f"Error handling message from {sender}: {str(e)}")
        await send_message(sender, "An error occurred processing your message.")

async def process_text_message(phone_number: str, text: str, message_id: str):
    """
    Process text messages - route to clause analyzer or podcast generator
    """
    text_lower = text.lower().strip()
    
    try:
        # Command routing
        if text_lower.startswith("/analyze"):
            # Extract document text after command
            doc_text = text[len("/analyze"):].strip()
            if not doc_text:
                await send_message(phone_number, "Please provide text to analyze. Usage: /analyze [document text]")
                return
            
            await send_message(phone_number, "🔍 Analyzing document for harmful clauses...")
            response = await analyze_clauses(doc_text)
            await send_message(phone_number, format_clause_response(response))
        
        elif text_lower.startswith("/podcast"):
            doc_text = text[len("/podcast"):].strip()
            if not doc_text:
                await send_message(phone_number, "Please provide text for podcast. Usage: /podcast [document text]")
                return
            
            await send_message(phone_number, "🎙️ Generating podcast from your document...")
            await generate_podcast_from_text(phone_number, doc_text, message_id)
        
        else:
            # Default: show help
            help_text = """👋 Welcome! Here are available commands:

/analyze [text] - Analyze document for harmful clauses
/podcast [text] - Generate a podcast from your document

Send a document or image for direct analysis."""
            await send_message(phone_number, help_text)
    
    except Exception as e:
        logger.error(f"Error processing text message: {str(e)}")
        await send_message(phone_number, "Error processing your request. Please try again.")

async def process_document_message(phone_number: str, document: dict, message_id: str):
    """
    Process document uploads - extract text and analyze
    """
    try:
        media_id = document.get("id")
        
        await send_message(phone_number, "📄 Processing document...")
        
        # Download document from WhatsApp servers
        file_data = await download_media(media_id)
        
        # Extract text from document
        text = await extract_text_from_file(file_data)
        
        # Analyze clauses
        response = await analyze_clauses(text)
        await send_message(phone_number, format_clause_response(response))
    
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        await send_message(phone_number, "Error processing document. Please try again.")

async def process_image_message(phone_number: str, image: dict, message_id: str):
    """
    Process image messages - could use OCR if needed
    """
    await send_message(phone_number, "📸 Image received. Currently text-based analysis only.")

async def analyze_clauses(text: str) -> dict:
    """
    Call your existing clause analyzer
    """
    from clause_analyzer import analyze_document
    return await analyze_document(text, harmful_clause_analysis)

async def generate_podcast_from_text(phone_number: str, text: str, message_id: str):
    """
    Generate podcast and send to WhatsApp
    """
    try:
        from conversation import analyze_document as analyze_for_podcast
        
        doc_id = await analyze_for_podcast(text)
        
        generator = PodcastGenerator()
        podcast = await generator.generate_podcast(doc_id=doc_id, top_k=8)
        conversation = generator.format_for_display(podcast)
        
        audio_file = generate_audio(conversation)
        
        # Send audio file to WhatsApp
        await send_audio(phone_number, audio_file)
    
    except Exception as e:
        logger.error(f"Error generating podcast: {str(e)}")
        await send_message(phone_number, "Error generating podcast. Please try again.")

async def download_media(media_id: str) -> bytes:
    """
    Download media from WhatsApp servers
    """
    async with httpx.AsyncClient() as client:
        # Get media URL
        url_response = await client.get(
            f"{WHATSAPP_API_URL}/{media_id}",
            params={"access_token": WHATSAPP_TOKEN}
        )
        media_url = url_response.json().get("url")
        
        # Download media
        media_response = await client.get(
            media_url,
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        )
        return media_response.content

async def send_message(phone_number: str, text: str):
    """
    Send text message via WhatsApp
    """
    async with httpx.AsyncClient() as client:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {"body": text}
        }
        
        response = await client.post(
            f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages",
            json=payload,
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send message: {response.text}")
        
        return response.json()

async def send_audio(phone_number: str, file_path: str):
    """
    Send audio file via WhatsApp
    """
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as audio_file:
            files = {
                "file": (file_path, audio_file, "audio/wav")
            }
            
            # Upload media first
            upload_response = await client.post(
                f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/media",
                files=files,
                data={
                    "messaging_product": "whatsapp",
                    "access_token": WHATSAPP_TOKEN
                }
            )
            
            media_id = upload_response.json().get("id")
            
            # Send audio message
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone_number,
                "type": "audio",
                "audio": {"id": media_id}
            }
            
            response = await client.post(
                f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages",
                json=payload,
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            )
            
            return response.json()

def format_clause_response(response: dict) -> str:
    """
    Format clause analysis response for WhatsApp
    """
    if isinstance(response, dict):
        formatted = "📋 **Clause Analysis Results:**\n\n"
        for key, value in response.items():
            formatted += f"**{key}:** {value}\n"
        return formatted
    return str(response)