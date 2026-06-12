import uvicorn
from fastapi import FastAPI
from app.core.database import engine, Base
from app.api import ingestion, chat

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Palm Mind RAG Platform Backend",
    version="1.0.0",
    description="Production level custom RAG platform featuring dual chunking models and transactional booking orchestration."
)

app.include_router(ingestion.router)
app.include_router(chat.router)

@app.get("/health", tags=["System Diagnostics"])
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)