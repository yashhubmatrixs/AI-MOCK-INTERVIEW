"""
Persistent vector storage for the knowledge-base embeddings, using ChromaDB.

Where things live
-----------------
  backend/data/knowledge/   your notes (.md / .txt / .pdf)  <- the source of truth
  backend/data/chroma/      ChromaDB's own folder (created automatically)
                              chroma.sqlite3   passages, ids and metadata
                              <uuid>/          the vector index files
                            Don't edit it by hand. It can always be deleted: it is
                            rebuilt from the notes the next time embeddings are used.

How it is used
--------------
rag_service hands over one Entry per knowledge passage. `sync` makes the Chroma
collection hold exactly those passages: passages already stored are NOT embedded
again, new or edited ones are embedded and added, removed ones are deleted. So
editing one note re-embeds only that note, and restarting the server costs nothing.

The collection name includes the embedding model (e.g. knowledge-nomic-embed-text), so
switching models never mixes vectors of different sizes. Chroma compares vectors by
cosine distance; similarity here is 1 - distance.

Chroma is only used when embeddings are enabled. If it isn't installed or its folder
can't be opened, VectorStoreError is raised and rag_service falls back to keyword search.
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env")

DEFAULT_PATH = _BACKEND_DIR / "data" / "chroma"
_PAGE = 1000


class VectorStoreError(Exception):
    """ChromaDB isn't installed or couldn't be used. The message is safe to show."""


@dataclass(frozen=True)
class Entry:
    key: str        # content hash: same text + same model = same key
    text: str       # what gets embedded
    document: str   # what Chroma stores next to the vector
    metadata: dict  # str / int / float / bool values only


def store_path() -> Path:
    """Folder ChromaDB keeps its files in (RAG_CHROMA_PATH in .env; relative paths are
    relative to the backend folder)."""
    raw = os.getenv("RAG_CHROMA_PATH", "").strip()
    if not raw:
        return DEFAULT_PATH
    path = Path(raw)
    return path if path.is_absolute() else _BACKEND_DIR / path


def entry_key(model: str, text: str) -> str:
    return hashlib.sha1(f"{model}|{text}".encode("utf-8")).hexdigest()


def collection_name(model: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", model).strip("-")[:40] or "model"
    return f"knowledge-{slug}"


# ---------------------------------------------------------------------------
# Handles
# ---------------------------------------------------------------------------

_lock = threading.RLock()
_client = None
_client_path: Path | None = None
_collections: dict = {}


def _reset_handles() -> None:
    global _client, _client_path
    _client = None
    _client_path = None
    _collections.clear()
    # ChromaDB also keeps its own per-folder connection cache. Without clearing it, a
    # folder that was deleted or moved while the server ran would stay "read-only".
    try:
        from chromadb.api.shared_system_client import SharedSystemClient

        SharedSystemClient.clear_system_cache()
    except Exception:
        pass  # chromadb not installed, or a version without this helper


def reset() -> None:
    """Forget the open connection (used by tests and when the folder is changed)."""
    with _lock:
        _reset_handles()


def _chroma(what: str, fn: Callable, *args, **kwargs):
    """Run one ChromaDB call; any failure becomes a VectorStoreError and the cached
    handles are dropped so the next attempt reconnects from scratch."""
    try:
        return fn(*args, **kwargs)
    except VectorStoreError:
        raise
    except Exception as exc:
        with _lock:
            _reset_handles()
        raise VectorStoreError(f"ChromaDB problem while {what}: {exc}")


def _get_client():
    global _client, _client_path
    path = store_path()
    with _lock:
        if _client is not None and _client_path == path:
            return _client
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise VectorStoreError("ChromaDB isn't installed. Run: pip install -r requirements.txt")

        def open_store():
            path.mkdir(parents=True, exist_ok=True)
            # Telemetry off: nothing about your notes or questions leaves the machine.
            return chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))

        _reset_handles()
        _client = _chroma(f"opening the folder {path}", open_store)
        _client_path = path
        return _client


def _collection(model: str):
    name = collection_name(model)
    with _lock:
        col = _collections.get(name)
        if col is None:
            client = _get_client()
            col = _chroma(
                "opening the collection",
                client.get_or_create_collection,
                name=name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=None,  # we always pass our own vectors
            )
            _collections[name] = col
        return col


def _stored_ids(col) -> set[str]:
    ids: list[str] = []
    offset = 0
    while True:
        page = _chroma("listing stored passages", col.get, include=[], limit=_PAGE, offset=offset)["ids"]
        ids.extend(page)
        if len(page) < _PAGE:
            return set(ids)
        offset += _PAGE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sync(
    model: str,
    entries: Sequence[Entry],
    embed: Callable[[list[str]], list[list[float]]],
    batch_size: int = 16,
) -> int:
    """Make the collection hold exactly `entries`. Only entries not already stored are
    passed to `embed` (texts in, vectors out; any error it raises propagates unchanged).
    Returns how many were embedded."""
    wanted = {e.key: e for e in entries}
    with _lock:
        col = _collection(model)
        stored = _stored_ids(col)

        stale = [key for key in stored if key not in wanted]
        for start in range(0, len(stale), 500):
            _chroma("removing outdated passages", col.delete, ids=stale[start:start + 500])

        missing = [e for key, e in wanted.items() if key not in stored]
        for start in range(0, len(missing), batch_size):
            part = missing[start:start + batch_size]
            vectors = embed([e.text for e in part])
            if len(vectors) != len(part):
                raise VectorStoreError("The embedding model returned the wrong number of vectors.")
            _chroma(
                "saving embeddings",
                col.upsert,
                ids=[e.key for e in part],
                documents=[e.document for e in part],
                embeddings=[[float(x) for x in v] for v in vectors],
                metadatas=[e.metadata for e in part],
            )
        return len(missing)


def query(model: str, vector: Sequence[float], n: int) -> list[tuple[str, float]]:
    """The n closest stored passages as (key, cosine similarity), best first."""
    col = _collection(model)
    total = _chroma("counting stored passages", col.count)
    if not total:
        return []
    res = _chroma(
        "searching",
        col.query,
        query_embeddings=[[float(x) for x in vector]],
        n_results=min(n, total),
        include=["distances"],
    )
    return [(key, 1.0 - float(dist)) for key, dist in zip(res["ids"][0], res["distances"][0])]


def count(model: str) -> int:
    return _chroma("counting stored passages", _collection(model).count)
