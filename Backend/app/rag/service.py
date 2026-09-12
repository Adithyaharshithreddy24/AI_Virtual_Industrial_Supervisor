from app.rag.retriever import get_retriever


def search_manuals(
    query: str,
    domain_filter: str | None = None,
    top_k: int = 5,
) -> dict:
    retriever = get_retriever(domain_filter=domain_filter, top_k=top_k)
    docs = retriever.invoke(query)

    sources = []
    context_parts = []
    for doc in docs:
        meta = doc.metadata
        sources.append(
            {
                "file": meta.get("source_file", "unknown"),
                "page": int(meta.get("page_number", 0)),
                "doc_type": meta.get("doc_type", "unknown"),
                "manufacturer": meta.get("manufacturer", "unknown"),
                "domain": meta.get("domain", "unknown"),
                "chunk_excerpt": doc.page_content[:300],
            }
        )
        context_parts.append(
            f"[Source: {meta.get('source_file', 'unknown')}, "
            f"page {meta.get('page_number', 0)}]\n{doc.page_content}"
        )

    return {
        "context": "\n\n".join(context_parts),
        "sources": sources,
    }
