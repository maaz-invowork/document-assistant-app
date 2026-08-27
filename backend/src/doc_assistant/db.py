from sqlmodel import SQLModel, create_engine, Session
from doc_assistant.config import settings

# SQLite database file path
sqlite_url = f"sqlite:///{settings.UPLOAD_DIR}/chat_history.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session