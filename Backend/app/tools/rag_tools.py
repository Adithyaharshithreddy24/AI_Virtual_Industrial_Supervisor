import json
from langchain.tools import tool

from app.rag.service import search_manuals


@tool
def search_manual(
    query: str,
    domain_filter: str | None = None,
    top_k: int = 5,
) -> str:
    """Search approved industrial user manuals for machine troubleshooting information.

    Use this tool when the operator's problem needs machine-specific instructions,
    alarm meanings, troubleshooting procedures, or manual-backed safety guidance.
    """
    result = search_manuals(query, domain_filter=domain_filter, top_k=top_k)
    return json.dumps(result, ensure_ascii=False)
