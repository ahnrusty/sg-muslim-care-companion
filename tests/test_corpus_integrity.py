"""Corpus integrity tests.

Every markdown file in corpus/ must:
- start with valid YAML front matter
- have title, tags, summary, sources
- have at least one source with name and url
- contain no em dashes
- contain no forbidden private substrings (handled by test_no_private_refs.py)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS = REPO_ROOT / "corpus"


def corpus_files() -> list[Path]:
    return sorted(p for p in CORPUS.rglob("*.md"))


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    return yaml.safe_load(text[3:end].strip()) or {}, text[end + 4 :]


@pytest.mark.parametrize(
    "md", corpus_files(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_front_matter(md: Path) -> None:
    raw = md.read_text(encoding="utf-8")
    fm, body = parse_front_matter(raw)
    assert fm, f"{md} has no YAML front matter"
    for required in ("title", "tags", "summary", "sources"):
        assert required in fm, f"{md} missing front matter key '{required}'"
    assert (
        isinstance(fm["tags"], list) and fm["tags"]
    ), f"{md} tags must be a non-empty list"
    assert (
        isinstance(fm["sources"], list) and fm["sources"]
    ), f"{md} sources must be a non-empty list"
    for i, s in enumerate(fm["sources"]):
        assert isinstance(s, dict), f"{md} source[{i}] must be a mapping"
        assert s.get("name"), f"{md} source[{i}] missing name"
        url = s.get("url", "")
        assert url.startswith("http"), f"{md} source[{i}] url must start with http"
    assert body.strip(), f"{md} has empty body"


@pytest.mark.parametrize(
    "md", corpus_files(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_no_em_dashes(md: Path) -> None:
    raw = md.read_text(encoding="utf-8")
    assert "—" not in raw, f"{md} contains em dash (—). Use commas or periods instead."


def test_minimum_corpus_size() -> None:
    files = corpus_files()
    assert len(files) >= 20, f"corpus has {len(files)} files, expected at least 20"


def test_minimum_citations() -> None:
    total = 0
    for md in corpus_files():
        raw = md.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(raw)
        total += len(fm.get("sources") or [])
    assert total >= 40, f"corpus has {total} citations, expected at least 40"
