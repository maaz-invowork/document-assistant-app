import uuid
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, PointStruct
from fastembed import TextEmbedding, SparseTextEmbedding
from pypdf import PdfReader
from doc_assistant.config import settings

dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")

def setup_collection(client: QdrantClient):
    if not client.collection_exists(settings.COLLECTION_NAME):
        client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config={"dense": VectorParams(size=384, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams()}
        )

def index_pdf(pdf_path: str, client: QdrantClient, session_id: str = None):
    setup_collection(client)
    reader = PdfReader(pdf_path)
    chunks = []
    
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        page_num = page_idx + 1
        start = 0
        while start < len(text):
            end = start + 500
            chunks.append({"id": str(uuid.uuid4()), "text": text[start:end], "page": page_num})
            start += 450 # 50-char overlap

    texts = [c["text"] for c in chunks]
    dense_embeddings = list(dense_model.embed(texts))
    sparse_embeddings = list(sparse_model.embed(texts))

    points = [
        PointStruct(
            id=chunk["id"],
            vector={"dense": dense_embeddings[i].tolist(), "sparse": sparse_embeddings[i].as_object()},
            payload={"text": chunk["text"], "page": chunk["page"], "session_id": session_id, "filename": os.path.basename(pdf_path).split('_', 1)[-1]}
        )
        for i, chunk in enumerate(chunks)
    ]
    client.upsert(collection_name=settings.COLLECTION_NAME, points=points)