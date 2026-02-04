#!/usr/bin/env python3
"""
KidBot Data Ingestion Pipeline

Processes text documents into ChromaDB vector store for RAG-based child companion robot.
Supports .txt, .md, and .json files with parallel chunking and batch embedding.

Run from project root: python -m scripts.ingest_data
Or from scripts dir: python ingest_data.py
"""

import json
import os
import sys
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports when run directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import chromadb
import chromadb.errors

# =============================================================================
# Configuration
# =============================================================================

# Paths
RAW_DOCS_DIR = Path("data/raw_docs")
VECTOR_STORE_DIR = Path("data/vector_store")
COLLECTION_NAME = "kidbot_knowledge"

# Embedding model - lightweight for Raspberry Pi deployment
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 64

# Chunking parameters optimized for child Q&A
CHUNK_SIZE = 1200  # ~300 tokens
CHUNK_OVERLAP = 200  # ~50 tokens

# Supported file types
SUPPORTED_EXTENSIONS = {".txt", ".md", ".json"}

# =============================================================================
# File Discovery
# =============================================================================

def discover_files(directory: Path) -> list[Path]:
    """Recursively find all supported text files in directory."""
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(directory.rglob(f"*{ext}"))
    return sorted(files)

# =============================================================================
# Document Loading
# =============================================================================

def load_document(file_path: Path) -> Optional[tuple[str, dict]]:
    """
    Load a document file and return its content with metadata.
    Returns None if file cannot be read.
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            content = file_path.read_text(encoding=encoding)

            # Handle JSON files - extract text content
            if file_path.suffix == ".json":
                try:
                    data = json.loads(content)
                    content = extract_json_text(data)
                except json.JSONDecodeError:
                    pass  # Treat as plain text if not valid JSON

            metadata = {
                "source": str(file_path),
                "filename": file_path.name,
                "extension": file_path.suffix,
            }
            return content, metadata

        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None

    print(f"Failed to decode {file_path} with any encoding")
    return None


def extract_json_text(data, depth: int = 0) -> str:
    """Recursively extract text content from JSON structures."""
    if depth > 10:  # Prevent infinite recursion
        return ""

    if isinstance(data, str):
        return data
    elif isinstance(data, dict):
        parts = []
        for key, value in data.items():
            text = extract_json_text(value, depth + 1)
            if text.strip():
                parts.append(f"{key}: {text}")
        return "\n".join(parts)
    elif isinstance(data, list):
        parts = [extract_json_text(item, depth + 1) for item in data]
        return "\n".join(p for p in parts if p.strip())
    else:
        return str(data) if data is not None else ""

# =============================================================================
# Text Chunking
# =============================================================================

def create_splitter() -> RecursiveCharacterTextSplitter:
    """Create text splitter with configured parameters."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_document(args: tuple[str, dict]) -> list[tuple[str, dict]]:
    """Split document content into chunks with metadata."""
    content, metadata = args
    splitter = create_splitter()

    chunks = splitter.split_text(content)

    result = []
    for i, chunk in enumerate(chunks):
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk_index"] = i
        chunk_metadata["total_chunks"] = len(chunks)
        result.append((chunk, chunk_metadata))

    return result

# =============================================================================
# Main Pipeline
# =============================================================================

def main():
    print("=" * 60)
    print("KidBot Data Ingestion Pipeline")
    print("=" * 60)

    # Validate input directory
    if not RAW_DOCS_DIR.exists():
        print(f"\nError: Input directory not found: {RAW_DOCS_DIR}")
        print("Please create the directory and add your text files.")
        sys.exit(1)

    # Create output directory
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1: File Discovery
    print("\n[Phase 1/4] Discovering files...")
    files = discover_files(RAW_DOCS_DIR)
    print(f"Found {len(files)} files to process")

    if not files:
        print("No files found. Add .txt, .md, or .json files to data/raw_docs/")
        sys.exit(1)

    # Phase 2: Document Loading
    print("\n[Phase 2/4] Loading documents...")
    documents = []
    failed_files = []

    for file_path in tqdm(files, desc="Loading"):
        result = load_document(file_path)
        if result:
            content, metadata = result
            if content.strip():
                documents.append((content, metadata))
        else:
            failed_files.append(file_path)

    print(f"Loaded {len(documents)} documents ({len(failed_files)} failed)")

    if not documents:
        print("No documents loaded successfully.")
        sys.exit(1)

    # Phase 3: Parallel Chunking
    print("\n[Phase 3/4] Chunking documents...")
    num_workers = max(1, cpu_count() - 1)

    all_chunks = []
    with Pool(num_workers) as pool:
        results = list(tqdm(
            pool.imap(chunk_document, documents),
            total=len(documents),
            desc="Chunking"
        ))
        for chunks in results:
            all_chunks.extend(chunks)

    print(f"Created {len(all_chunks)} chunks")

    # Phase 4: Embedding and Storage
    print("\n[Phase 4/4] Generating embeddings and storing...")
    print(f"Loading embedding model: {EMBEDDING_MODEL}")

    model = SentenceTransformer(EMBEDDING_MODEL)

    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))

    # Delete existing collection if present
    try:
        client.delete_collection(COLLECTION_NAME)
    except (ValueError, chromadb.errors.NotFoundError):
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "KidBot knowledge base for child companion robot"}
    )

    # Process in batches
    texts = [chunk[0] for chunk in all_chunks]
    metadatas = [chunk[1] for chunk in all_chunks]

    for i in tqdm(range(0, len(texts), EMBEDDING_BATCH_SIZE), desc="Embedding"):
        batch_texts = texts[i:i + EMBEDDING_BATCH_SIZE]
        batch_metadatas = metadatas[i:i + EMBEDDING_BATCH_SIZE]
        batch_ids = [f"doc_{j}" for j in range(i, i + len(batch_texts))]

        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()

        collection.add(
            ids=batch_ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_metadatas,
        )

    # Final Statistics
    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print("=" * 60)
    print(f"Files processed:    {len(documents)}")
    print(f"Files failed:       {len(failed_files)}")
    print(f"Chunks created:     {len(all_chunks)}")
    print(f"Vector store:       {VECTOR_STORE_DIR}")
    print(f"Collection:         {COLLECTION_NAME}")

    # Verify
    final_count = collection.count()
    print(f"Vectors stored:     {final_count}")

    if failed_files:
        print("\nFailed files:")
        for f in failed_files[:10]:
            print(f"  - {f}")
        if len(failed_files) > 10:
            print(f"  ... and {len(failed_files) - 10} more")


if __name__ == "__main__":
    main()
