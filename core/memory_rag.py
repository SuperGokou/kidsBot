"""
Memory Manager for KidBot RAG System

Handles document ingestion and semantic search using ChromaDB.
Optimized for large datasets (500MB+) with memory-efficient processing.
Uses Streamlit caching for performance optimization.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator, Optional

import chromadb
import chromadb.errors
import streamlit as st
from sentence_transformers import SentenceTransformer


# =============================================================================
# Cached Resource Loaders
# =============================================================================

@st.cache_resource
def load_embedding_model(model_name: str) -> SentenceTransformer:
    """
    Load and cache the sentence transformer embedding model.

    This is decorated with @st.cache_resource to ensure the model
    is only loaded once, even across Streamlit reruns.

    Args:
        model_name: Name of the sentence-transformers model

    Returns:
        Loaded SentenceTransformer model
    """
    print(f"[Cache] Loading embedding model: {model_name}...")
    return SentenceTransformer(model_name)


@st.cache_resource
def get_chroma_client(vector_store_path: str) -> chromadb.PersistentClient:
    """
    Get and cache the ChromaDB persistent client.

    This ensures only one database connection is created.

    Args:
        vector_store_path: Path to the vector store directory

    Returns:
        ChromaDB PersistentClient
    """
    print(f"[Cache] Connecting to ChromaDB at: {vector_store_path}...")
    return chromadb.PersistentClient(path=vector_store_path)


@st.cache_resource
def get_memory_manager(_config: dict) -> "MemoryManager":
    """
    Get a cached MemoryManager instance.

    The underscore prefix on _config tells Streamlit not to hash it
    (since dicts can be complex to hash).

    Args:
        _config: Configuration dictionary from config.yaml

    Returns:
        Cached MemoryManager instance
    """
    print("[Cache] Creating MemoryManager instance...")
    return MemoryManager(_config)


class MemoryManager:
    """Manages the knowledge base for the Child Companion Robot."""

    def __init__(self, config: dict):
        """
        Initialize the Memory Manager.

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.paths = config["paths"]
        self.rag_config = config["rag"]

        # Paths
        self.raw_docs_path = Path(self.paths["raw_docs"])
        self.vector_store_path = Path(self.paths["vector_store"])
        self.processed_files_path = self.vector_store_path / "processed_files.json"

        # Ensure directories exist
        self.raw_docs_path.mkdir(parents=True, exist_ok=True)
        self.vector_store_path.mkdir(parents=True, exist_ok=True)

        # Use cached ChromaDB client
        self.client = get_chroma_client(str(self.vector_store_path))
        self.collection = self._get_or_create_collection()

        # Use cached embedding model
        self.embedding_model = load_embedding_model(self.rag_config["embedding_model"])

        # Load processed files registry
        self.processed_files = self._load_processed_files()

    def _get_or_create_collection(self) -> chromadb.Collection:
        """Get existing collection or create a new one."""
        collection_name = self.rag_config["collection_name"]
        try:
            return self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "KidBot knowledge base"}
            )
        except Exception as e:
            print(f"Error accessing collection: {e}")
            raise

    def _load_processed_files(self) -> dict:
        """Load the registry of processed files."""
        if self.processed_files_path.exists():
            try:
                with open(self.processed_files_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_processed_files(self):
        """Save the registry of processed files."""
        with open(self.processed_files_path, "w") as f:
            json.dump(self.processed_files, f, indent=2)

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of a file for change detection."""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _read_file_generator(self, file_path: Path) -> Generator[str, None, None]:
        """
        Read file content with encoding fallback.
        Uses generator pattern to be memory efficient.
        """
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                    yield content
                    return
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"  Error reading file: {e}")
                return

        print(f"  Failed to decode file with any encoding")

    def _split_text(self, text: str) -> list[str]:
        """
        Split text into chunks using recursive character splitting.

        Args:
            text: The text to split

        Returns:
            List of text chunks
        """
        chunk_size = self.rag_config["chunk_size"]
        chunk_overlap = self.rag_config["chunk_overlap"]

        # Separators in order of preference
        separators = ["\n\n", "\n", ". ", " ", ""]

        chunks = []
        self._recursive_split(text, separators, chunk_size, chunk_overlap, chunks)
        return chunks

    def _recursive_split(
        self,
        text: str,
        separators: list[str],
        chunk_size: int,
        chunk_overlap: int,
        chunks: list[str]
    ):
        """Recursively split text using the best available separator."""
        if len(text) <= chunk_size:
            if text.strip():
                chunks.append(text.strip())
            return

        # Find the best separator that exists in the text
        separator = ""
        for sep in separators:
            if sep in text:
                separator = sep
                break

        if not separator:
            # No separator found, split by chunk_size
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk = text[i:i + chunk_size].strip()
                if chunk:
                    chunks.append(chunk)
            return

        # Split by the separator
        parts = text.split(separator)

        current_chunk = ""
        for part in parts:
            test_chunk = current_chunk + separator + part if current_chunk else part

            if len(test_chunk) <= chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                # Handle overlap
                if chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_text + separator + part
                else:
                    current_chunk = part

                # If single part is too large, recursively split
                if len(current_chunk) > chunk_size:
                    self._recursive_split(
                        current_chunk,
                        separators[1:] if len(separators) > 1 else [""],
                        chunk_size,
                        chunk_overlap,
                        chunks
                    )
                    current_chunk = ""

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

    def _process_file_generator(self, file_path: Path) -> Generator[tuple[str, dict], None, None]:
        """
        Process a single file and yield chunks with metadata.
        Memory efficient - processes one file at a time.
        """
        for content in self._read_file_generator(file_path):
            if not content.strip():
                return

            chunks = self._split_text(content)

            for i, chunk in enumerate(chunks):
                metadata = {
                    "source": str(file_path),
                    "filename": file_path.name,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                yield chunk, metadata

    def ingest_data(self):
        """
        Ingest all documents from raw_docs directory into ChromaDB.

        Uses generator pattern to process files one by one,
        avoiding memory overflow with large datasets.
        """
        print("\n" + "=" * 50)
        print("Starting Data Ingestion")
        print("=" * 50)

        # Find all .txt files
        txt_files = list(self.raw_docs_path.rglob("*.txt"))
        md_files = list(self.raw_docs_path.rglob("*.md"))
        all_files = txt_files + md_files

        if not all_files:
            print(f"No .txt or .md files found in {self.raw_docs_path}")
            print("Ingestion complete (no new files).")
            return

        print(f"Found {len(all_files)} files to check")

        # Track statistics
        files_processed = 0
        files_skipped = 0
        total_chunks = 0
        batch_size = self.rag_config["batch_size"]

        # Batch buffers
        batch_ids = []
        batch_texts = []
        batch_metadatas = []

        # Get current max ID
        try:
            existing_count = self.collection.count()
            current_id = existing_count
        except Exception:
            current_id = 0

        for file_path in all_files:
            # Check if file was already processed
            file_hash = self._compute_file_hash(file_path)
            file_key = str(file_path)

            if file_key in self.processed_files:
                if self.processed_files[file_key] == file_hash:
                    files_skipped += 1
                    continue
                else:
                    print(f"File changed, re-processing: {file_path.name}")

            print(f"Processing file: {file_path.name}...")

            # Process file using generator
            file_chunks = 0
            for chunk_text, metadata in self._process_file_generator(file_path):
                batch_ids.append(f"doc_{current_id}")
                batch_texts.append(chunk_text)
                batch_metadatas.append(metadata)
                current_id += 1
                file_chunks += 1

                # Insert batch when full
                if len(batch_texts) >= batch_size:
                    self._insert_batch(batch_ids, batch_texts, batch_metadatas)
                    total_chunks += len(batch_texts)
                    batch_ids = []
                    batch_texts = []
                    batch_metadatas = []

            # Mark file as processed
            self.processed_files[file_key] = file_hash
            files_processed += 1
            print(f"  -> {file_chunks} chunks created")

        # Insert remaining batch
        if batch_texts:
            self._insert_batch(batch_ids, batch_texts, batch_metadatas)
            total_chunks += len(batch_texts)

        # Save processed files registry
        self._save_processed_files()

        # Print summary
        print("\n" + "-" * 50)
        print("Ingestion Complete!")
        print(f"  Files processed: {files_processed}")
        print(f"  Files skipped (unchanged): {files_skipped}")
        print(f"  New chunks added: {total_chunks}")
        print(f"  Total vectors in DB: {self.collection.count()}")
        print("-" * 50 + "\n")

    def _insert_batch(self, ids: list[str], texts: list[str], metadatas: list[dict]):
        """Insert a batch of documents into ChromaDB."""
        if not texts:
            return

        # Generate embeddings
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False).tolist()

        # Insert into ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def query_memory(self, query_text: str, n_results: int = 3) -> list[str]:
        """
        Search the knowledge base for relevant context.

        Args:
            query_text: The user's question/input
            n_results: Number of results to return

        Returns:
            List of relevant text chunks
        """
        if self.collection.count() == 0:
            return []

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results, self.collection.count())
            )

            if results and results["documents"]:
                return results["documents"][0]

        except Exception as e:
            print(f"Error querying memory: {e}")

        return []

    def add_memory(self, text: str, metadata: Optional[dict] = None) -> bool:
        """
        Add a new memory to the knowledge base.

        This is used for the Auto-Learning feature where the robot
        extracts and saves useful information from conversations.

        Args:
            text: The memory text to save
            metadata: Optional metadata (source, timestamp, etc.)

        Returns:
            True if saved successfully, False otherwise
        """
        if not text or not text.strip():
            return False

        try:
            # Generate unique ID
            current_count = self.collection.count()
            doc_id = f"memory_{current_count}"

            # Default metadata
            if metadata is None:
                metadata = {}

            metadata.update({
                "source": "conversation",
                "type": "learned_fact",
                "timestamp": datetime.now().isoformat()
            })

            # Generate embedding and add to collection
            embedding = self.embedding_model.encode([text], show_progress_bar=False).tolist()

            self.collection.add(
                ids=[doc_id],
                embeddings=embedding,
                documents=[text],
                metadatas=[metadata]
            )

            print(f"[Memory] Saved new memory: {text[:50]}...")
            return True

        except Exception as e:
            print(f"[Memory] Error saving memory: {e}")
            return False

    def clear_all_memories(self) -> bool:
        """
        Clear all memories from the database.

        Used for factory reset.

        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.rag_config["collection_name"])
            self.collection = self._get_or_create_collection()

            # Clear processed files registry
            self.processed_files = {}
            self._save_processed_files()

            print("[Memory] All memories cleared.")
            return True

        except Exception as e:
            print(f"[Memory] Error clearing memories: {e}")
            return False

    def get_recent_memories(self, hours: int = 24) -> list[str]:
        """
        Retrieve learned memories from the last N hours.

        Args:
            hours: Number of hours to look back (default 24)

        Returns:
            List of memory texts from the specified time period
        """
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        try:
            # Get all learned facts
            results = self.collection.get(
                where={"type": "learned_fact"},
                include=["documents", "metadatas"]
            )

            if not results or not results["documents"]:
                return []

            # Filter by timestamp
            recent = []
            for doc, meta in zip(results["documents"], results["metadatas"]):
                ts = meta.get("timestamp", "")
                if ts >= cutoff_time:
                    recent.append(doc)

            return recent

        except Exception as e:
            print(f"[Memory] Error getting recent memories: {e}")
            return []

    def get_stats(self) -> dict:
        """Get statistics about the knowledge base."""
        return {
            "total_documents": self.collection.count(),
            "processed_files": len(self.processed_files),
            "collection_name": self.rag_config["collection_name"]
        }
