from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.booking import InterviewBooking
from app.services.redis_mem import get_chat_history, save_chat_history
#  Fixed imports
from app.services.llm import get_embedding, extract_booking_intent, generate_rag_response
from app.services.vector_store import query_vectors  # Added this line

router = APIRouter(prefix="/api/v1/chat", tags=["Conversational RAG"])

@router.post("", response_model=ChatResponse)
def handle_conversation(payload: ChatRequest, db: Session = Depends(get_db)):
    history = get_chat_history(payload.session_id)
    
    booking_data = extract_booking_intent(payload.message)
    booking_saved = False
    
    if booking_data.is_booking_intent:
        if all([booking_data.name, booking_data.email, booking_data.booking_date, booking_data.booking_time]):
            try:
                parsed_date = datetime.strptime(booking_data.booking_date, "%Y-%m-%d").date()
                parsed_time = datetime.strptime(booking_data.booking_time, "%H:%M").time()
                
                booking = InterviewBooking(
                    name=booking_data.name,
                    email=booking_data.email,
                    booking_date=parsed_date,
                    booking_time=parsed_time
                )
                db.add(booking)
                db.commit()
                booking_saved = True
                reply = f"Thank you {booking_data.name}. Your interview has been successfully booked for {booking_data.booking_date} at {booking_data.booking_time}."
            except Exception:
                reply = "I encountered an issue verifying the date or time formatting. Could you please state it clearly?"
        else:
            reply = "I see you want to schedule an interview. Please provide your full name, email, date, and preferred time."
            
        history.append({"role": "user", "text": payload.message})
        history.append({"role": "model", "text": reply})
        save_chat_history(payload.session_id, history)
        return ChatResponse(reply=reply, booking_saved=booking_saved)

    query_vector = get_embedding(payload.message)
    context_chunks = query_vectors(query_vector, top_k=3)
    
    reply = generate_rag_response(context_chunks, history, payload.message)
    
    history.append({"role": "user", "text": payload.message})
    history.append({"role": "model", "text": reply})
    save_chat_history(payload.session_id, history)
    
    return ChatResponse(reply=reply, booking_saved=False)