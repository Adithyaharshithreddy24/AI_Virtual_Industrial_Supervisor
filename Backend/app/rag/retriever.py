from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import get_settings


def get_vector_store() -> Chroma:
    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is not configured")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
    )

    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=embeddings,
        persist_directory=str(settings.resolved_chroma_dir),
    )


def get_retriever(domain_filter: str | None = None, top_k: int = 5):
    vector_store = get_vector_store()
    search_kwargs = {
        "k": top_k,
        "fetch_k": max(top_k * 3, 10),
    }

    if domain_filter:
        search_kwargs["filter"] = {"domain": {"$eq": domain_filter}}

    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs,
    )


def get_collection_health() -> dict:
    vector_store = get_vector_store()
    data = vector_store.get(include=["metadatas"])
    metadatas = data.get("metadatas") or []
    documents = sorted(
        {
            meta.get("source_file")
            for meta in metadatas
            if meta and meta.get("source_file")
        }
    )
    return {
        "total_chunks": len(metadatas),
        "documents": documents,
    }
