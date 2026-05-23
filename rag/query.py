"""Query the RAG index and print the top-K matching chunks with citations.

Usage:
    python rag/query.py "Is DNR allowed in Islam?"
    python rag/query.py --k 8 --json "How do I book a burial slot?"
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "rag" / "config.yaml"


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_index(index_path: Path) -> dict:
    if not index_path.exists():
        raise SystemExit(
            f"index not found at {index_path}. Run `python rag/build_index.py` first."
        )
    return json.loads(index_path.read_text(encoding="utf-8"))


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def embed_query(cfg: dict, query: str) -> list[float]:
    import ollama

    host = cfg["embedding"]["host"]
    model = cfg["embedding"]["model"]
    client = ollama.Client(host=host)
    prefix = "search_query: " if model.startswith("nomic-embed") else ""
    resp = client.embeddings(model=model, prompt=f"{prefix}{query}")
    return resp["embedding"]


def _keyword_boost(query: str, chunk: dict) -> float:
    """Small lexical boost on top of cosine similarity.

    Rewards matches of query keywords in the chunk title, path slug, and the
    head of the chunk text. Helps exact-keyword queries (DNR, MUIS, iddah,
    faraid) surface the right files when the embedding model treats
    neighbouring concepts as similar.
    """
    import re

    q_terms = {t.lower() for t in re.findall(r"[A-Za-z]{3,}", query)}
    if not q_terms:
        return 0.0
    title = chunk.get("title", "").lower()
    path = chunk.get("path", "").lower()
    text_head = chunk.get("text", "").lower()[:400]
    score = 0.0
    for t in q_terms:
        if t in title:
            score += 0.04
        if t in path:
            score += 0.03
        if t in text_head:
            score += 0.01
    return min(score, 0.15)


def search(
    index: dict,
    query_vec: list[float],
    top_k: int,
    min_score: float,
    query_text: str | None = None,
) -> list[dict]:
    scored: list[tuple[float, dict]] = []
    for c in index["chunks"]:
        v = c.get("vector")
        if not v:
            continue
        s = cosine(query_vec, v)
        if query_text:
            s += _keyword_boost(query_text, c)
        if s >= min_score:
            scored.append((s, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[dict] = []
    for s, c in scored[:top_k]:
        out.append(
            {
                "score": round(s, 4),
                "id": c["id"],
                "path": c["path"],
                "title": c["title"],
                "tags": c.get("tags", []),
                "summary": c.get("summary", ""),
                "start_line": c["start_line"],
                "end_line": c["end_line"],
                "text": c["text"],
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the RAG index.")
    parser.add_argument("query", nargs="?", help="Question. If omitted, reads stdin.")
    parser.add_argument(
        "--k", type=int, default=None, help="Top K, default from config."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json", action="store_true", help="JSON output.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    index_path = REPO_ROOT / cfg["paths"]["index_dir"] / "index.json"
    index = load_index(index_path)

    query = args.query or sys.stdin.read().strip()
    if not query:
        print("no query provided", file=sys.stderr)
        return 2

    top_k = args.k or cfg["retrieval"]["top_k"]
    min_score = cfg["retrieval"]["min_score"]

    qvec = embed_query(cfg, query)
    hits = search(index, qvec, top_k, min_score, query_text=query)

    if args.json:
        print(json.dumps({"query": query, "hits": hits}, ensure_ascii=False, indent=2))
        return 0

    if not hits:
        print("no matches above threshold. Try rephrasing or rebuild the index.")
        return 0

    print(f"Query: {query}\n")
    for i, h in enumerate(hits, 1):
        print(
            f"[{i}] {h['title']}  ({h['path']}:{h['start_line']}-{h['end_line']})  score={h['score']}"
        )
        if h["summary"]:
            print(f"    {h['summary']}")
        snippet = h["text"].strip().splitlines()
        preview = " ".join(snippet)[:280]
        print(f"    > {preview}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
