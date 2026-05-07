import os
import json
import hashlib
from datetime import datetime

import chromadb
from google import genai

_client = None
_collection = None
_genai_client = None

MEMORY_DIR = os.path.join(os.path.dirname(__file__), ".memory")


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    os.makedirs(MEMORY_DIR, exist_ok=True)
    _client = chromadb.PersistentClient(path=MEMORY_DIR)
    workspace = os.getenv("MMM_WORKSPACE", "default")
    safe_name = "analyses_" + hashlib.md5(workspace.encode()).hexdigest()[:8]
    _collection = _client.get_or_create_collection(
        name=safe_name,
        metadata={"hnsw:space": "cosine"}
    )
    return _collection


def _embed(text: str) -> list[float]:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client()
    result = _genai_client.models.embed_content(
        model="text-embedding-004",
        contents=text
    )
    return result.embeddings[0].values


def store_analysis(query: str, synthesis_text: str, date: str = None, channel: str = None, mmm_snapshot: str = None):
    try:
        col = _get_collection()
        doc_id = hashlib.md5(f"{query}{datetime.utcnow().isoformat()}".encode()).hexdigest()
        combined = f"Query: {query}\n\nFindings:\n{synthesis_text}"
        embedding = _embed(combined)
        metadata = {
            "query": query[:500],
            "date": date or "",
            "channel": channel or "",
            "stored_at": datetime.utcnow().isoformat(),
            "mmm_snapshot": (mmm_snapshot or "")[:1000],
        }
        col.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[combined],
            metadatas=[metadata]
        )
        print(f"[memory] stored analysis id={doc_id}")
    except Exception as e:
        print(f"[memory] store failed: {e}")


def retrieve_similar(query: str, top_k: int = 3) -> list[dict]:
    try:
        col = _get_collection()
        if col.count() == 0:
            return []
        embedding = _embed(query)
        results = col.query(
            query_embeddings=[embedding],
            n_results=min(top_k, col.count()),
            include=["documents", "metadatas", "distances"]
        )
        out = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            similarity = 1 - dist
            if similarity < 0.55:
                continue
            out.append({
                "document": doc,
                "date": meta.get("date", ""),
                "channel": meta.get("channel", ""),
                "stored_at": meta.get("stored_at", ""),
                "similarity": round(similarity, 3)
            })
        return out
    except Exception as e:
        print(f"[memory] retrieve failed: {e}")
        return []


def format_memory_for_agent(memories: list[dict]) -> str:
    if not memories:
        return ""
    lines = ["--- HISTORICAL ANALYSIS CONTEXT (similar past investigations) ---"]
    for i, m in enumerate(memories, 1):
        lines.append(f"\n[Past Investigation {i}] similarity={m['similarity']} date={m['date']} channel={m['channel']}")
        lines.append(m["document"])
    lines.append("--- END HISTORICAL CONTEXT ---")
    return "\n".join(lines)
