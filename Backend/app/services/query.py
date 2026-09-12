from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI

from app.core.config import get_settings
from app.rag.service import search_manuals


QUERY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a textile and industrial maintenance documentation assistant.
Answer ONLY from the supplied manual context.
If the answer is not supported by the context, say:
'I don't have enough information in the provided documents.'
Cite the source file and page number in the answer.

Context:
{context}""",
        ),
        ("human", "{question}"),
    ]
)


def run_query(query: str, domain_filter: str | None = None, top_k: int = 5) -> dict:
    settings = get_settings()
    model = ChatMistralAI(
        model=settings.llm_model,
        api_key=settings.mistral_api_key,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )
    retrieved = search_manuals(query, domain_filter=domain_filter, top_k=top_k)
    chain = QUERY_PROMPT | model | StrOutputParser()
    answer = chain.invoke(
        {"context": retrieved["context"], "question": query}
    )
    return {"answer": answer, "sources": retrieved["sources"]}
