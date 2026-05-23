# Design rationale

## Why local-first

The questions this companion answers are deeply private. They concern a family member's illness, death, and inheritance. The conversations may happen at a bedside, in a mosque office, or at home at 3am. They should not require an internet connection. They should not be logged anywhere outside the user's machine.

Running on a local Ollama model keeps everything on the device. No telemetry. No external calls in the default path.

## Why small models

`gemma3:e4b` is around 5 GB and runs at conversational speed on a recent Mac. It is good enough for a tight RAG loop where the answer is anchored to retrieved corpus chunks. The retrieved context does most of the work. The model's job is to summarise faithfully and decline gracefully.

For users on older machines, `qwen3:8b` or smaller works. For users with more compute, `gemma3:27b` improves clarity on edge cases.

## Why a small markdown corpus instead of a vector database

For a few hundred chunks the simplest thing that works is a flat JSON index with cosine similarity in Python. No service to run. No migration to manage. The corpus is version controlled, reviewable in a pull request, and human readable when grepped at a bedside.

If the corpus grows past a few thousand chunks, swap in sqlite-vec or chromadb behind the same `rag/query.py` surface.

## Why a strict citation discipline

The reader may act on what they read. Acting on fiqh without a real scholar, on medicine without a doctor, or on inheritance law without a lawyer can cause real harm. Every corpus file lists its sources in front matter. Every chat answer lists the file and line range it drew from. The chat is told to answer only from the provided context and to refuse plainly when the context does not cover the question.

## Why plain English

The reader may be exhausted, grieving, or trying to read this on a small phone in poor light. Long sentences, technical jargon, em dashes, and gratuitous formality all add friction. The voice rules in `rules/system-prompt.md` and `CONTRIBUTING.md` are the result.

## Why anonymous

The project is community-benefit. It does not promote any individual, company, or organisation. It defers to Singapore Muslim community institutions where relevant (MUIS, Syariah Court, AMP, PERGAS, MENDAKI, AIC, mosques). Keeping it anonymous keeps the attention on the content and the institutions, not the author.

## Why the disagreement convention

For topics where qualified scholars hold different positions (brain death, photographs at janazah, the religious status of 40-day commemorations, women attending burial), the companion presents the mainstream Singapore-MUIS position first, then briefly notes other respected views, then recommends asatizah consultation. This mirrors what a careful imam would say to a family in a mosque office.

## Why not a web UI yet

A web UI adds privacy, hosting, and accessibility complexity that is not needed to deliver value today. A future contributor may add a local PWA or a Telegram bot wrapper. The retrieval and chat scripts already expose clean Python entry points to support that.
