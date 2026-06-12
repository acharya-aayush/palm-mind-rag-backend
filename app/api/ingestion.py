import io
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from pypdf import PdfReader
from app.core.database import get_db
from app.models.document import DocumentMetadata
from app.services.llm import get_embedding
from app.services.vector_store import upsert_vectors

router = APIRouter(prefix="/api/v1/ingestion", tags=["Ingestion"])

def apply_fixed_chunking(text: str, size: int = 600, overlap: int = 60) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += (size - overlap)
    return chunks

def apply_recursive_chunking(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    strategy: str = Form(...), 
    db: Session = Depends(get_db)):
    contents = await file.read()
    text = ""
    
    if file.filename.endswith(".pdf"):
        pdf = PdfReader(io.BytesIO(contents))
        text = "".join([page.extract_text() for page in pdf.pages])
    elif file.filename.endswith(".txt"):
        text = contents.decode("utf-8")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    if strategy == "fixed":
        chunks = apply_fixed_chunking(text)
    elif strategy == "recursive":
        chunks = apply_recursive_chunking(text)
    else:
        raise HTTPException(status_code=400, detail="Invalid chunking strategy selected.")

    vectors_to_store = []
    for chunk in chunks:
        vector = get_embedding(chunk)
        chunk_id = str(uuid.uuid4())
        vectors_to_store.append((chunk_id, vector, {"text": chunk, "filename": file.filename}))
        
    if vectors_to_store:
        upsert_vectors(vectors_to_store)

    meta = DocumentMetadata(filename=file.filename, strategy=strategy, chunk_count=len(chunks))
    db.add(meta)
    db.commit()

    return {"message": "Ingestion successful", "chunks_processed": len(chunks)}