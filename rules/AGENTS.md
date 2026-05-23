# AGENTS.md

Tool-agnostic rules for any AI coding agent working on this repo (Cursor, Claude Code, Copilot, Amp, etc.).

## What this repo is

A local-first AI companion for Muslim families in Singapore navigating critical illness, end-of-life, and bereavement. Anonymous, community-benefit. Public on GitHub.

## Identity

- GitHub identity: `ahnrusty`.
- Local git author for commits in this repo: `ahnrusty <ahnrusty@users.noreply.github.com>`. Do not change global git config.

## Hard privacy rules

- No real names of any person.
- No employer names, internal tooling names, internal communication channels, or any corporate context.
- No personal medical details, hospital ward numbers, or real ticket numbers.
- Before pushing, run `scripts/verify-no-private-refs.sh`. Fail the push if it fails.

## Voice rules for any content written into the corpus or docs

- Plain calm English. The reader may be exhausted or grieving.
- No em dashes. Use commas or periods.
- Short paragraphs. Clear next-step bullets when useful.
- Italicise Arabic and Malay terms on first use, and add them to `corpus/90-glossary/`.
- Where qualified scholars disagree (brain death, photographs at janazah, length of tahlil gatherings, women at burial), present the mainstream Singapore-MUIS position first, then briefly note other respected views, then recommend asatizah consultation.
- Never paste large copyrighted material. Summarise in your own words and cite.

## Corpus file format

Every `corpus/**/*.md` file starts with YAML front matter:

```yaml
---
title: short human title
tags: [topic, subtopic]
summary: one or two sentences
sources:
  - name: source name
    url: https://example.gov.sg/...
    accessed: 2026-05-23
    note: one-line credibility statement
---
```

Citations in the body use numbered footnotes that reference the entries in `sources`, like `[^1]`.

## RAG implementation rules

- Default chat backend: Ollama at `localhost:11434`. No external API calls in the default path. No telemetry.
- Default embedding model: `nomic-embed-text`. Default chat model: `gemma3:e4b`.
- Optional OpenAI-compatible mode via `OPENAI_BASE_URL` and `OPENAI_API_KEY`. Only enabled when the user sets these.
- Index files in `rag/index/` are gitignored.
- Retrieval returns top-K chunks with title, path, and line range so the chat layer can cite.

## Testing

- `python -m pytest -q` must pass before committing.
- `tests/test_no_private_refs.py` enforces the hard privacy rules.
- `tests/test_corpus_integrity.py` enforces front matter and tone rules (including no em dashes).
- `tests/test_rag_retrieval.py` validates that golden questions retrieve the expected files. Skips gracefully if Ollama is not available.

## Pull request workflow

1. Edit corpus or code.
2. Run tests locally.
3. Run `scripts/verify-no-private-refs.sh`.
4. Commit with a short conventional message (`docs:`, `feat:`, `fix:`).
5. Push and open a pull request. Request asatizah review for fiqh changes.
