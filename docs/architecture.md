# Architecture

## Goals

1. Run well on a laptop, fully offline, no telemetry.
2. Give accurate, calm, simple answers grounded in authoritative Singapore sources.
3. Always cite. Always defer to qualified humans for fiqh, medicine, and law.

## Components

```
+----------------+        +-------------------+       +------------------+
| corpus/*.md    | -----> | rag/build_index.py | ---> | rag/index/*.json |
| (versioned)    |        | chunk + embed     |       | (gitignored)     |
+----------------+        +-------------------+       +------------------+
                                                              |
                                                              v
+----------------+        +-------------------+       +------------------+
| user question  | -----> | rag/query.py      | ---> | top-K chunks     |
|                |        | (cosine search)   |       |                  |
+----------------+        +-------------------+       +------------------+
                                                              |
                                                              v
+--------------------------------------------------+    +------------------+
| rag/chat.py                                      |--> | Ollama chat     |
|  - system prompt (rules/system-prompt.md)        |    |  (or OPENAI_*)  |
|  - top-K context, trimmed to token budget        |<---|                 |
|  - last N turns of history                       |    +------------------+
+--------------------------------------------------+
```

## Corpus design

The corpus is a tree of small markdown files, one focused subject per file. Each file declares its sources in YAML front matter so they travel with the content into the index and into citations.

## Embeddings

Default model is `nomic-embed-text` via Ollama. Cosine similarity over a flat in-memory list. The index is a single JSON file, regenerable in seconds for a corpus of this size. No external vector database, no SQLite migration headaches.

If you grow the corpus past a few thousand chunks, consider swapping in [sqlite-vec](https://github.com/asg017/sqlite-vec) or [chromadb](https://www.trychroma.com) without changing the public surface of `rag/query.py`.

## Chat

Default model is `gemma3:e4b`. The system prompt is in `rules/system-prompt.md`. Each turn:

1. Embed the user question.
2. Retrieve top-K with a minimum cosine threshold.
3. Trim to a token budget. Dedupe.
4. Build a single system message that contains the system prompt plus the numbered context.
5. Send the last few turns of history plus the new user message.
6. Print the answer, then list the sources by `[n] path:line-range title`.

## Privacy

- No telemetry.
- No external API calls in the default path.
- The chat history lives in memory only. Hitting `:reset` clears it. Exiting clears it.
- The user can opt in to an OpenAI-compatible endpoint by setting `OPENAI_BASE_URL`. That is the only way data leaves the machine.

## Failure modes

- If retrieval returns nothing above the threshold, the chat replies with a plain refusal and recommends consulting the right human (asatizah, doctor, Syariah Court).
- If Ollama is not running, the chat exits with a clear error. `rag/build_index.py --dry-run` still works so the corpus structure can be validated in CI.
- If `OPENAI_BASE_URL` is set but the endpoint is unreachable, the chat surfaces the HTTP error and exits the turn.
