from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from doc_assistant.api.routes import router
from contextlib import asynccontextmanager
from doc_assistant.db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables on startup
    create_db_and_tables()
    yield

app = FastAPI(title="Document Assistant API", lifespan=lifespan)

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "online",
        "message": "Welcome to the Document Assistant API",
        "docs_url": "/docs"
    }

app.include_router(router, prefix="/api/v1")
