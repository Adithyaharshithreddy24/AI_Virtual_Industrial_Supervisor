import hashlib
import time
from pathlib import Path

import fitz
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.rag.retriever import get_vector_store


def file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metadata_for_file(filename: str) -> dict:
    name = filename.lower()
    if "yarn mfg prac" in name:
        return {
            "domain": "general_yarn_mfg",
            "doc_type": "textbook_guide",
            "manufacturer": "General",
        }
    if "magnotop" in name:
        return {
            "domain": "trutzschler_magnotop",
            "doc_type": "oem_manual",
            "manufacturer": "Trützschler",
        }
    if "rieter" in name:
        return {
            "domain": "rieter_mmf",
            "doc_type": "oem_manual",
            "manufacturer": "Rieter",
        }
    return {
        "domain": "unknown",
        "doc_type": "unknown",
        "manufacturer": "unknown",
    }


def _splitter_for(doc_type: str) -> RecursiveCharacterTextSplitter:
    settings = get_settings()
    if doc_type == "oem_manual":
        size = settings.chunk_size_oem
        overlap = settings.chunk_overlap_oem
    else:
        size = settings.chunk_size_general
        overlap = settings.chunk_overlap_general
    return RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def _existing_hashes(vector_store: Chroma) -> set[str]:
    data = vector_store.get(include=["metadatas"])
    hashes: set[str] = set()
    for meta in data.get("metadatas") or []:
        if meta and meta.get("file_md5"):
            hashes.add(meta["file_md5"])
    return hashes


def _add_with_retry(vector_store: Chroma, documents: list[Document]) -> None:
    batch_size = 50
    for start in range(0, len(documents), batch_size):
        batch = documents[start : start + batch_size]
        for attempt in range(5):
            try:
                vector_store.add_documents(batch)
                break
            except Exception as exc:
                text = str(exc)
                if "429" not in text and "RESOURCE_EXHAUSTED" not in text:
                    raise
                if attempt == 4:
                    raise
                time.sleep(60)
        time.sleep(1)


def run_ingestion() -> dict:
    settings = get_settings()
    vector_store = get_vector_store()
    existing_hashes = _existing_hashes(vector_store)

    indexed = 0
    total_chunks = 0
    skipped = 0
    failed: list[str] = []

    pdf_files = sorted(settings.resolved_pdf_dir.glob("*.pdf"))
    for pdf_path in pdf_files:
        current_hash = file_md5(pdf_path)
        if current_hash in existing_hashes:
            skipped += 1
            continue

        try:
            info = metadata_for_file(pdf_path.name)
            splitter = _splitter_for(info["doc_type"])
            documents: list[Document] = []
            chunk_index = 0

            with fitz.open(pdf_path) as pdf:
                for page_number, page in enumerate(pdf, start=1):
                    text = page.get_text("text").strip()
                    if not text:
                        continue

                    for chunk in splitter.split_text(text):
                        documents.append(
                            Document(
                                page_content=chunk,
                                metadata={
                                    "source_file": pdf_path.name,
                                    "doc_type": info["doc_type"],
                                    "domain": info["domain"],
                                    "manufacturer": info["manufacturer"],
                                    "page_number": page_number,
                                    "chunk_index": chunk_index,
                                    "file_md5": current_hash,
                                },
                            )
                        )
                        chunk_index += 1

            if documents:
                _add_with_retry(vector_store, documents)
                indexed += 1
                total_chunks += len(documents)
                existing_hashes.add(current_hash)
        except Exception as exc:
            failed.append(f"{pdf_path.name}: {exc}")

    return {
        "status": "success" if not failed else "partial_success",
        "documents_indexed": indexed,
        "total_chunks": total_chunks,
        "skipped_duplicates": skipped,
        "failed_documents": failed,
    }
