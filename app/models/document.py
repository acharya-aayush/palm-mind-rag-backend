from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from app.core.database import Base

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    strategy = Column(String, nullable=False)
    chunk_count = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)