"""Golden retrieval tests.

Checks that a small set of golden questions retrieves the expected corpus
files among the top-K results. Skips gracefully if Ollama is unavailable.

When Ollama is unavailable, still validates that the dry-run index format is
correct so we know corpus chunking works.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rag"))

INDEX = REPO_ROOT / "rag" / "index" / "index.json"
DRY_INDEX = REPO_ROOT / "rag" / "index" / "index.dryrun.json"

GOLDEN = [
    {
        "q": "What do I do in the first hour after death at the hospital?",
        "expected_any": [
            "corpus/20-imminent-death/moment-of-death-checklist.md",
            "corpus/20-imminent-death/at-the-bedside.md",
        ],
    },
    {
        "q": "How do I book a Muslim burial slot in Singapore?",
        "expected_any": [
            "corpus/40-singapore-admin/muis-burial-booking.md",
            "corpus/40-singapore-admin/pusara-aman.md",
        ],
    },
    {
        "q": "Is DNR allowed in Islam?",
        "expected_any": [
            "corpus/10-critical-illness/dnr-and-withdrawal.md",
            "corpus/10-critical-illness/icu-decisions.md",
        ],
    },
    {
        "q": "How does Muslim inheritance work in Singapore?",
        "expected_any": [
            "corpus/60-inheritance/faraid.md",
            "corpus/60-inheritance/syariah-court-inheritance-certificate.md",
        ],
    },
    {
        "q": "What is talqin and how is it done?",
        "expected_any": [
            "corpus/20-imminent-death/talqin.md",
        ],
    },
]


def ollama_available() -> bool:
    import urllib.error
    import urllib.request

    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
        return True
    except (urllib.error.URLError, OSError):
        return False


def ensure_dry_index() -> Path:
    if DRY_INDEX.exists():
        return DRY_INDEX
    subprocess.check_call(
        [sys.executable, str(REPO_ROOT / "rag" / "build_index.py"), "--dry-run"],
        cwd=REPO_ROOT,
    )
    return DRY_INDEX


def test_dry_index_format() -> None:
    p = ensure_dry_index()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "meta" in data and "chunks" in data
    assert data["meta"].get("chunk_count", 0) >= 20, "expected at least 20 chunks"
    for c in data["chunks"][:5]:
        for k in (
            "id",
            "path",
            "title",
            "tags",
            "summary",
            "text",
            "start_line",
            "end_line",
        ):
            assert k in c, f"chunk missing key {k}"


@pytest.mark.skipif(
    not ollama_available(), reason="Ollama not running on localhost:11434"
)
@pytest.mark.skipif(
    not INDEX.exists(), reason="Real index not built. Run python rag/build_index.py"
)
@pytest.mark.parametrize("case", GOLDEN, ids=[g["q"][:40] for g in GOLDEN])
def test_golden_retrieval(case: dict) -> None:
    from query import embed_query, load_config, load_index, search

    cfg = load_config(REPO_ROOT / "rag" / "config.yaml")
    idx = load_index(INDEX)
    qvec = embed_query(cfg, case["q"])
    hits = search(idx, qvec, top_k=8, min_score=0.0, query_text=case["q"])
    paths = {h["path"] for h in hits}
    expected = set(case["expected_any"])
    assert (
        paths & expected
    ), f"None of {expected} found in top-8 hits. Got: {sorted(paths)[:5]}"
