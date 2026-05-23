"""Build a local embedding index over corpus/ markdown files.

The index is a single JSON file at rag/index/index.json containing:
- meta: model name, dimension, chunk count, built_at
- chunks: list of {id, path, title, tags, summary, text, start_line, end_line,
  vector: [float], char_offset}

By default uses Ollama embeddings (nomic-embed-text). No data leaves the
machine. Run after editing corpus/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "rag" / "config.yaml"


@dataclass
class Chunk:
    id: str
    path: str
    title: str
    tags: list[str]
    summary: str
    text: str
    start_line: int
    end_line: int
    vector: list[float] = field(default_factory=list)


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_front_matter(text: str) -> tuple[dict, str, int]:
    """Return (front_matter_dict, body, body_start_line)."""
    if not text.startswith("---"):
        return {}, text, 1
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text, 1
    fm_raw = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    body_start = text[: end + 4].count("\n") + 2
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError as exc:
        print(f"warning: bad YAML front matter: {exc}", file=sys.stderr)
        fm = {}
    return fm, body, body_start


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_markdown(
    body: str,
    body_start_line: int,
    target_tokens: int,
    overlap_tokens: int,
    min_chunk_tokens: int,
) -> Iterator[tuple[str, int, int]]:
    """Yield (chunk_text, start_line, end_line)."""
    paragraphs = re.split(r"\n\s*\n", body)
    line_cursor = body_start_line
    para_spans: list[tuple[str, int, int]] = []
    for para in paragraphs:
        if not para.strip():
            line_cursor += para.count("\n") + 1
            continue
        para_lines = para.count("\n") + 1
        start = line_cursor
        end = line_cursor + para_lines - 1
        para_spans.append((para, start, end))
        line_cursor = end + 2

    buf: list[tuple[str, int, int]] = []
    buf_tokens = 0
    for para, start, end in para_spans:
        ptokens = approx_tokens(para)
        if buf_tokens + ptokens > target_tokens and buf_tokens >= min_chunk_tokens:
            chunk_text = "\n\n".join(p for p, _, _ in buf)
            yield chunk_text, buf[0][1], buf[-1][2]
            overlap: list[tuple[str, int, int]] = []
            otokens = 0
            for item in reversed(buf):
                t = approx_tokens(item[0])
                if otokens + t > overlap_tokens:
                    break
                overlap.insert(0, item)
                otokens += t
            buf = overlap + [(para, start, end)]
            buf_tokens = sum(approx_tokens(p) for p, _, _ in buf)
        else:
            buf.append((para, start, end))
            buf_tokens += ptokens

    if buf and buf_tokens >= min_chunk_tokens:
        chunk_text = "\n\n".join(p for p, _, _ in buf)
        yield chunk_text, buf[0][1], buf[-1][2]
    elif buf:
        chunk_text = "\n\n".join(p for p, _, _ in buf)
        yield chunk_text, buf[0][1], buf[-1][2]


def iter_corpus_files(corpus_dir: Path) -> Iterator[Path]:
    for p in sorted(corpus_dir.rglob("*.md")):
        yield p


def chunk_id(path: str, start: int, text: str) -> str:
    h = hashlib.sha1(f"{path}:{start}:{text[:64]}".encode("utf-8")).hexdigest()
    return h[:16]


def embed_batch(client, model: str, texts: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for t in texts:
        resp = client.embeddings(model=model, prompt=t)
        out.append(resp["embedding"])
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the RAG index from corpus/")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chunk and report counts without contacting the embedding model.",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    corpus_dir = REPO_ROOT / cfg["paths"]["corpus_dir"]
    index_dir = REPO_ROOT / cfg["paths"]["index_dir"]
    index_dir.mkdir(parents=True, exist_ok=True)

    target = cfg["chunking"]["target_tokens"]
    overlap = cfg["chunking"]["overlap_tokens"]
    min_tokens = cfg["chunking"]["min_chunk_tokens"]

    all_chunks: list[Chunk] = []
    skipped: list[str] = []

    for md_path in iter_corpus_files(corpus_dir):
        raw = md_path.read_text(encoding="utf-8")
        fm, body, body_start = parse_front_matter(raw)
        if not body.strip():
            skipped.append(str(md_path))
            continue
        title = fm.get("title") or md_path.stem
        tags = fm.get("tags") or []
        summary = fm.get("summary") or ""
        rel = md_path.relative_to(REPO_ROOT).as_posix()
        for text, start, end in chunk_markdown(
            body, body_start, target, overlap, min_tokens
        ):
            cid = chunk_id(rel, start, text)
            all_chunks.append(
                Chunk(
                    id=cid,
                    path=rel,
                    title=title,
                    tags=list(tags),
                    summary=summary,
                    text=text,
                    start_line=start,
                    end_line=end,
                )
            )

    print(
        f"corpus files: {sum(1 for _ in iter_corpus_files(corpus_dir))}, "
        f"chunks: {len(all_chunks)}, skipped: {len(skipped)}"
    )

    if args.dry_run:
        out = index_dir / "index.dryrun.json"
        out.write_text(
            json.dumps(
                {
                    "meta": {
                        "dry_run": True,
                        "chunk_count": len(all_chunks),
                        "skipped": skipped,
                    },
                    "chunks": [asdict(c) for c in all_chunks],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"wrote dry-run index to {out}")
        return 0

    try:
        import ollama
    except ImportError:
        print(
            "ollama python client not installed. pip install -r rag/requirements.txt",
            file=sys.stderr,
        )
        return 2

    host = cfg["embedding"]["host"]
    model = cfg["embedding"]["model"]
    client = ollama.Client(host=host)

    print(f"embedding {len(all_chunks)} chunks with {model} on {host}")
    start = time.time()
    prefix = "search_document: " if model.startswith("nomic-embed") else ""
    texts = [
        f"{prefix}{c.title}\nTags: {', '.join(c.tags)}\nSummary: {c.summary}\n\n{c.text}"
        for c in all_chunks
    ]
    vectors = embed_batch(client, model, texts)
    for c, v in zip(all_chunks, vectors):
        c.vector = v
    elapsed = time.time() - start
    dim = len(vectors[0]) if vectors else 0
    print(f"embedded in {elapsed:.1f}s, vector dim {dim}")

    out = index_dir / "index.json"
    out.write_text(
        json.dumps(
            {
                "meta": {
                    "embedding_model": model,
                    "dim": dim,
                    "chunk_count": len(all_chunks),
                    "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                },
                "chunks": [asdict(c) for c in all_chunks],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"wrote index to {out} ({out.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
