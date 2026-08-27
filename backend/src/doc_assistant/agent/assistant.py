import os
from dotenv import load_dotenv
load_dotenv()
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import Prefetch, FusionQuery, Fusion
from qdrant_client import models
from fastembed import TextEmbedding, SparseTextEmbedding
from pydantic_ai import Agent, RunContext
from doc_assistant.schemas import DocumentAnswer
from doc_assistant.config import settings

print("[DEBUG] Initializing Qdrant Client & Embedding Models...")
qdrant_client = QdrantClient(path=settings.QDRANT_DB_PATH)
dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")
print("[DEBUG] Models initialized successfully.")

@dataclass
class QdrantDeps:
    client: QdrantClient
    collection: str
    session_id: str | None = None

doc_agent = Agent[QdrantDeps, DocumentAnswer](
    'openrouter:deepseek/deepseek-chat',
    output_type=DocumentAnswer,
    deps_type=QdrantDeps,
    system_prompt=(
        "You are an expert Document Assistant. "
        "For general greetings, simple pleasantries, or meta-questions (e.g., 'hello', 'who are you?'), "
        "respond politely without forcing document search. Leave the citations array empty. "
        "For any specific question about the document content, ALWAYS query using `qdrant_hybrid_search` "
        "and provide accurate ground-truth citations, including the exact filename, source_text, and page_number."
    )
)

@doc_agent.tool
async def qdrant_hybrid_search(ctx: RunContext[QdrantDeps], query: str, limit: int = 4) -> list[dict]:
    print(f"\n[TOOL CALLED] qdrant_hybrid_search called with query: '{query}'")
    
    print("[TOOL] Computing dense & sparse embeddings for query...")
    query_dense = list(dense_model.embed([query]))[0].tolist()
    query_sparse = list(sparse_model.embed([query]))[0].as_object()

    query_filter = None
    if ctx.deps.session_id:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="session_id",
                    match=models.MatchValue(value=ctx.deps.session_id)
                )
            ]
        )

    results = ctx.deps.client.query_points(
        collection_name=ctx.deps.collection,
        prefetch=[
            Prefetch(query=query_dense, using="dense", limit=limit * 2, filter=query_filter),
            Prefetch(query=query_sparse, using="sparse", limit=limit * 2, filter=query_filter)
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        query_filter=query_filter,
        limit=limit
    )
    retrieved_chunks = [{"filename": p.payload.get("filename", "Unknown Document"), "snippet": p.payload["text"], "page": p.payload["page"]} for p in results.points]
    print(f"[TOOL] Found {len(retrieved_chunks)} matching context chunks from Qdrant for session '{ctx.deps.session_id}`.")
    return retrieved_chunks

async def ask_assistant(question: str, session_id: str = None) -> DocumentAnswer:
    print(f"\n[AGENT START] Received question: '{question}' - for session: '{session_id}'")
    deps = QdrantDeps(client=qdrant_client, collection=settings.COLLECTION_NAME, session_id=session_id)
    try:
        print("[AGENT] Sending request to OpenRouter LLM...")
        # Limiting model retry loops to prevent hanging indefinitely
        result = await doc_agent.run(question, deps=deps, usage_limits=None)
        print("[AGENT SUCCESS] Agent finished and structured output validated.")
        return result.output
    except Exception as e:
        print(f"[AGENT ERROR] Execution failed: {e}")
        raise e