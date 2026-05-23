"""Validate the directory subtree: mosques.json, contacts.json, per-mosque markdown."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DIR_ROOT = REPO_ROOT / "corpus" / "80-directory"
MOSQUES_JSON = DIR_ROOT / "mosques.json"
CONTACTS_JSON = DIR_ROOT / "contacts.json"
MOSQUES_DIR = DIR_ROOT / "mosques"


def test_mosques_json_exists_and_schema() -> None:
    assert MOSQUES_JSON.exists(), "mosques.json must exist"
    data = json.loads(MOSQUES_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == 1
    assert data.get("verified_date")
    assert isinstance(data.get("mosques"), list)
    assert data["count"] == len(data["mosques"])
    assert data["count"] >= 65, f"expected at least 65 mosques, got {data['count']}"
    seen_slugs: set[str] = set()
    for m in data["mosques"]:
        for required in ("name", "slug", "region", "muis_url", "verified_date"):
            assert m.get(required), f"mosque {m.get('name')} missing {required}"
        assert m["slug"] not in seen_slugs, f"duplicate slug {m['slug']}"
        seen_slugs.add(m["slug"])
        assert m["muis_url"].startswith(
            "https://www.muis.gov.sg/"
        ), f"non-MUIS source for {m['name']}: {m['muis_url']}"


def test_contacts_json_exists_and_schema() -> None:
    assert CONTACTS_JSON.exists(), "contacts.json must exist"
    data = json.loads(CONTACTS_JSON.read_text(encoding="utf-8"))
    assert data.get("schema_version") == 1
    assert data.get("verified_date")
    cats = data.get("categories")
    assert isinstance(cats, list) and cats
    for cat in cats:
        assert cat.get("name")
        entries = cat.get("entries")
        assert (
            isinstance(entries, list) and entries
        ), f"category {cat['name']} has no entries"
        for e in entries:
            for required in ("service", "source_url", "verified_date"):
                assert e.get(
                    required
                ), f"contact in {cat['name']} missing {required}: {e}"
            assert e["source_url"].startswith(
                "http"
            ), f"contact {e['service']} source_url must start with http"


def test_per_mosque_markdown_has_minimum_fields() -> None:
    files = sorted(MOSQUES_DIR.glob("*.md"))
    assert len(files) >= 65, f"expected 65+ per-mosque markdown files, got {len(files)}"
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{f} missing YAML front matter"
        end = text.find("\n---", 3)
        assert end > 0, f"{f} malformed YAML"
        import yaml

        fm = yaml.safe_load(text[3:end].strip())
        for key in ("title", "name", "address", "sources", "tags"):
            assert key in fm, f"{f} missing front matter key {key}"
        # name is allowed to be just the mosque name
        assert isinstance(fm["sources"], list) and fm["sources"], f"{f} sources empty"


def test_mosques_json_phones_format() -> None:
    """Phones that are present must be all digits or null/unknown."""
    data = json.loads(MOSQUES_JSON.read_text(encoding="utf-8"))
    phone_re = re.compile(r"^[0-9+\-\s]+$")
    for m in data["mosques"]:
        p = m.get("phone")
        if not p:
            continue
        assert phone_re.match(p), f"{m['name']} phone has unexpected chars: {p!r}"
