from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class ChatSession(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    title: str = Field(default="New Chat")
    messages: List["ChatMessage"] = Relationship(back_populates="session")
    documents: List["Document"] = Relationship(back_populates="session")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Document(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    filename: str
    file_path: str
    session_id: str = Field(foreign_key="chatsession.id")
    session: Optional[ChatSession] = Relationship(back_populates="documents")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="chatsession.id")
    sender: str
    text: str
    citations_json: Optional[str] = Field(default=None)
    session: Optional[ChatSession] = Relationship(back_populates="messages")
    created_at: datetime = Field(default_factory=datetime.utcnow)