from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Citation(BaseModel):
    filename: str = Field(description="Name of the source PDF document")
    source_text: str = Field(description="Exact snippet quoted from the PDF context")
    page_number: int = Field(description="Page number where snippet was found")

class DocumentAnswer(BaseModel):
    answer: str = Field(description="Comprehensive answer strictly supported by document context")
    citations: list[Citation] = Field(description="Exact citations supporting the response")

class DocumentOut(BaseModel):
    id: str
    filename: str
    session_id: str
    created_at: Optional[datetime] = None