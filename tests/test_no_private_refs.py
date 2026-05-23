"""Scan all tracked files for forbidden private substrings.

This protects the public anonymous nature of the project. Fails fast if any
of the listed substrings appear, except in this test file, the scrub script,
and the rules files that name them as forbidden.

Note: "Friday" was removed from this list in v0.2.0 because the corpus
legitimately discusses Friday prayers (Jumah) throughout. The remaining
identifiers provide adequate protection without false positives.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN = [
    "Farhan",
    "Rasam",
    "frasam",
    "Netflix",
    "netflix",
    "nflx",
    "ndex",
    "TSOS",
    "N-Tech",
    "ASYLLA",
    "JARVIS",
    "Stride",
    "Workbench",
    "Kragle",
    "BDP",
    "Zendesk",
]

ALLOWLIST = {
    "tests/test_no_private_refs.py",
    "scripts/verify-no-private-refs.sh",
    "rules/AGENTS.md",
    "rules/cursor-rule.mdc",
    "CONTRIBUTING.md",
}


def tracked_files() -> list[str]:
    try:
        out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
        return [line for line in out.splitlines() if line]
    except Exception:
        files: list[str] = []
        for p in REPO_ROOT.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(REPO_ROOT).as_posix()
            if any(rel.startswith(skip) for skip in (".git/", ".venv/", "rag/index/")):
                continue
            if "__pycache__" in rel:
                continue
            files.append(rel)
        return files


def test_no_private_refs() -> None:
    pattern = re.compile(r"\b(" + "|".join(re.escape(t) for t in FORBIDDEN) + r")\b")
    hits: list[str] = []
    for rel in tracked_files():
        if rel in ALLOWLIST:
            continue
        p = REPO_ROOT / rel
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        for m in pattern.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            hits.append(f"{rel}:{line_no}: '{m.group(1)}'")
    assert not hits, "Forbidden private references found:\n  " + "\n  ".join(hits)
