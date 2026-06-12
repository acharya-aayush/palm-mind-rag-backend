import json
from google import genai
from google.genai import types
from fastapi import HTTPException
from pydantic import BaseModel, Field
from app.core.config import settings

# Single modern client using the active 2026 SDK setup
client = genai.Client(api_key=settings.GEMINI_API_KEY)

class BookingExtraction(BaseModel):
    is_booking_intent: bool = Field(
        description="True if user specifically wants to book/schedule an interview."
    )
    name: str | None = Field(
        default=None, 
        description="Full name extracted from text"
    )
    email: str | None = Field(
        default=None, 
        description="Clean validated email address"
    )
    booking_date: str | None = Field(
        default=None, 
        description="Date formatted as YYYY-MM-DD"
    )
    booking_time: str | None = Field(
        default=None, 
        description="Time formatted as HH:MM"
    )

def get_embedding(text: str) -> list[float]:
    """
    Generates text embeddings using gemini-embedding-001, explicitly truncated 
    to 768 dimensions to prevent Pinecone dimension mismatch errors.
    """
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"[Embedding Connection Failure]: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Embedding failed via gemini-embedding-001: {str(e)}"
        )

def extract_booking_intent(message: str) -> BookingExtraction:
    """
    Extracts structured booking metadata using the ultra-cheap, high-volume gemini-3.1-flash-lite.
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=f"Analyze this chat statement for appointment details: {message}",
            config={
                "response_mime_type": "application/json",
                "response_schema": BookingExtraction,
            }
        )
        return BookingExtraction.model_validate_json(response.text)
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Intent extraction failed via gemini-3.1-flash-lite: {str(e)}"
        )

def generate_rag_response(context_chunks: list[str], history: list[dict[str, str]], query: str) -> str:
    """
    Executes context-grounded RAG generation using gemini-3.5-flash.
    Includes an automatic fail-over to gemini-3.1-flash-lite if Google's servers return a 503.
    """
    context_str = "\n\n".join(context_chunks)
    system_instruction = (
        "You are an interview coordination assistant. Answer the user's question accurately using ONLY "
        "the context documents provided below. If you cannot find the answer, politely state that you lack "
        "the information.\n\n"
        f"Context Documents:\n{context_str}"
    )
    
    formatted_contents = []
    for msg in history:
        formatted_contents.append({
            "role": msg["role"], 
            "parts": [{"text": msg["text"]}]
        })
    
    formatted_contents.append({
        "role": "user", 
        "parts": [{"text": query}]
    })
    
    try:
        # Attempt primary execution via frontier model
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=formatted_contents,
            config={"system_instruction": system_instruction}
        )
        return response.text
    except Exception as e:
        # Primary endpoint failed/overloaded -> Trigger immediate high-volume pool fallback
        print(f"[Gemini 3.5 Overload Detected]: {str(e)}. Routing to stable gemini-3.1-flash-lite pipeline...")
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=formatted_contents,
                config={"system_instruction": system_instruction}
            )
            return response.text
        except Exception as fallback_error:
            raise HTTPException(
                status_code=400, 
                detail=f"Generation failed across primary and secondary 2026 pipelines: {str(fallback_error)}"
            )