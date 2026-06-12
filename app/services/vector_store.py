from pinecone import Pinecone
from app.core.config import settings

pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(settings.PINECONE_INDEX_NAME)

def upsert_vectors(vectors: list[tuple[str, list[float], dict]]) -> None:
    formatted = [{"id": v[0], "values": v[1], "metadata": v[2]} for v in vectors]
    index.upsert(vectors=formatted)

def query_vectors(query_vector: list[float], top_k: int = 3) -> list[str]:
    results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    return [match["metadata"]["text"] for match in results["matches"] if "metadata" in match]