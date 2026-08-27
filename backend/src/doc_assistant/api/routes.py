import os
import uuid
import json
from typing import List
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from doc_assistant.schemas import DocumentAnswer, DocumentOut
from doc_assistant.services.pdf_parser import index_pdf
from doc_assistant.agent.assistant import ask_assistant, qdrant_client
from doc_assistant.config import settings
from sqlmodel import Session, select
from doc_assistant.db import get_session
from doc_assistant.models import ChatSession, ChatMessage, Document
from qdrant_client.http import models as qmodels

router = APIRouter()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

@router.post("/sessions", response_model=ChatSession)
def create_session(title: str = "New Chat", db: Session = Depends(get_session)):
    count = db.exec(select(ChatSession)).all()
    next_number = len(count) + 1
    session = ChatSession(id=str(uuid.uuid4()), title=f"Conversation {next_number}")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSession])
def get_sessions(db: Session = Depends(get_session)):
    return db.exec(select(ChatSession).order_by(ChatSession.created_at.asc())).all()

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
def get_session_messages(session_id: str, db: Session = Depends(get_session)):
    return db.exec(select(ChatMessage).where(ChatMessage.session_id == session_id)).all()

@router.get("/sessions/{session_id}/documents", response_model=List[DocumentOut])
def get_session_documents(
    session_id: str, 
    db: Session = Depends(get_session)
):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    documents = db.exec(
        select(Document).where(Document.session_id == session_id)
    ).all()
    
    return documents

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_session)):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    documents = db.exec(
        select(Document).where(Document.session_id == session_id)
    ).all()

    for doc in documents:
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError as e:
                print(f"Error deleting file {doc.file_path}: {e}")
        db.delete(doc)
    
    try:
        qdrant_client.delete(
            collection_name=settings.COLLECTION_NAME,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="session_id",
                            match=qmodels.MatchValue(value=session_id)
                        )
                    ]
                )
            )
        )
    except Exception as e:
        print(f"Error deleting vectors from Qdrant for session {session_id}: {e}")

    messages = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    ).all()
    for message in messages:
        db.delete(message)

    db.delete(session)
    db.commit()

    return {"status": "deleted", "session_id": session_id}

@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_session)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError as e:
            print(f"Error deleting file {doc.file_path}: {e}")

    try:
        qdrant_client.delete(
            collection_name=settings.COLLECTION_NAME,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="session_id",
                            match=qmodels.MatchValue(value=doc.session_id)
                        ),
                        qmodels.FieldCondition(
                            key="filename",
                            match=qmodels.MatchValue(value=doc.filename)
                        )
                    ]
                )
            )
        )
    except Exception as e:
        print(f"Error deleting vectors for document {doc.filename}: {e}")

    db.delete(doc)
    db.commit()

    return {"status": "deleted", "document_id": document_id}

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...), 
    session_id: str = Form(None),
    db: Session = Depends(get_session)
    ):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs are accepted.")

    chat_session = db.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    file_filename = f"{session_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, file_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    index_pdf(file_path, client=qdrant_client, session_id=session_id)

    doc_record = Document(
        id=str(uuid.uuid4()),
        filename=file.filename,
        file_path=file_path,
        session_id=session_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(doc_record)
        
    db.commit()

    return {"status": "success", "filename": file.filename, "document_id": doc_record.id}

@router.post("/query", response_model=DocumentAnswer)
async def query_document(
    question: str, 
    session_id: str, 
    db: Session = Depends(get_session)
):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = ChatMessage(session_id=session_id, sender="user", text=question)
    db.add(user_msg)
    db.commit()

    answer_data = await ask_assistant(question, session_id)

    assistant_msg = ChatMessage(
        session_id=session_id,
        sender="assistant",
        text=answer_data.answer,
        citations_json=json.dumps([c.model_dump() for c in answer_data.citations])
    )
    db.add(assistant_msg)
    db.commit()

    return answer_data
