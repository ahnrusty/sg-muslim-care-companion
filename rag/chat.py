"""Local-first chat loop using Ollama plus the corpus RAG index.

Default backend: Ollama at localhost:11434, gemma3:e4b.
Optional backend: any OpenAI-compatible endpoint via OPENAI_BASE_URL.

Privacy: no telemetry. No data leaves the machine on the default path.

Usage:
    python rag/chat.py
    python rag/chat.py --model qwen3:8b
    OPENAI_BASE_URL=https://api.example.com/v1 OPENAI_API_KEY=sk-... python rag/chat.py
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "rag"))
from query import embed_query, load_config, load_index, search  # noqa: E402

DEFAULT_CONFIG = REPO_ROOT / "rag" / "config.yaml"

BANNER = """\
SG Muslim Care Companion
A local-first navigator for Muslim families in Singapore.

This is not a substitute for a qualified asatizah, a licensed doctor, or a
Syariah lawyer. It is a navigator. For religious rulings, consult the Office
of the Mufti or your local mosque imam. For medical decisions, talk to the
treating doctor. For inheritance and legal matters, contact the Syariah Court
of Singapore.

Type your question and press Enter. Type :q to quit, :reset to clear history.
"""


def read_system_prompt(cfg: dict) -> str:
    path = REPO_ROOT / cfg["paths"]["system_prompt"]
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "You are a calm, careful assistant. Answer only from the provided context."


def trim_context(hits: list[dict], max_tokens: int) -> list[dict]:
    used = 0
    kept: list[dict] = []
    for h in hits:
        t = max(1, len(h["text"]) // 4)
        if used + t > max_tokens and kept:
            break
        kept.append(h)
        used += t
    return kept


def format_context(hits: list[dict]) -> tuple[str, list[dict]]:
    lines: list[str] = []
    for i, h in enumerate(hits, 1):
        lines.append(
            f"[{i}] {h['title']} ({h['path']}:{h['start_line']}-{h['end_line']})"
        )
        lines.append(h["text"].strip())
        lines.append("")
    return "\n".join(lines), hits


def build_messages(
    system_prompt: str, history: list[dict], user: str, context: str
) -> list[dict]:
    sys_msg = {
        "role": "system",
        "content": (
            f"{system_prompt}\n\n"
            "Answer ONLY using the context below. If the context does not contain "
            "the answer, say so plainly and recommend consulting an asatizah, the "
            "treating doctor, or the Syariah Court as appropriate. Cite sources "
            "using the bracketed numbers like [1], [2].\n\n"
            f"Context:\n{context}"
        ),
    }
    msgs = [sys_msg] + history + [{"role": "user", "content": user}]
    return msgs


def chat_ollama(
    model: str, host: str, messages: list[dict], temperature: float, num_ctx: int
) -> str:
    import ollama

    client = ollama.Client(host=host)
    resp = client.chat(
        model=model,
        messages=messages,
        options={"temperature": temperature, "num_ctx": num_ctx},
    )
    return resp["message"]["content"]


def chat_openai(model: str, messages: list[dict], temperature: float) -> str:
    import httpx

    base = os.environ["OPENAI_BASE_URL"].rstrip("/")
    key = os.environ.get("OPENAI_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    payload = {"model": model, "messages": messages, "temperature": temperature}
    r = httpx.post(
        f"{base}/chat/completions", json=payload, headers=headers, timeout=120
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def wrap_print(text: str, width: int = 88) -> None:
    for para in text.split("\n"):
        if not para.strip():
            print()
            continue
        for line in textwrap.wrap(para, width=width) or [""]:
            print(line)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chat with the local SG Muslim care companion."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--model", default=None, help="Override chat model.")
    parser.add_argument("--k", type=int, default=None, help="Override top-K retrieval.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    index_path = REPO_ROOT / cfg["paths"]["index_dir"] / "index.json"
    index = load_index(index_path)
    system_prompt = read_system_prompt(cfg)

    chat_model = args.model or cfg["chat"]["model"]
    chat_host = cfg["chat"]["host"]
    temperature = cfg["chat"]["temperature"]
    num_ctx = cfg["chat"]["num_ctx"]
    top_k = args.k or cfg["retrieval"]["top_k"]
    min_score = cfg["retrieval"]["min_score"]
    max_ctx_tokens = cfg["retrieval"]["max_context_tokens"]

    use_openai = bool(os.environ.get("OPENAI_BASE_URL"))

    print(BANNER)
    backend = (
        "openai-compatible: " + os.environ["OPENAI_BASE_URL"]
        if use_openai
        else f"ollama: {chat_host} / {chat_model}"
    )
    print(f"Backend: {backend}")
    print(
        f"Index: {index['meta'].get('chunk_count', '?')} chunks, embedding {index['meta'].get('embedding_model', '?')}"
    )
    print()

    history: list[dict] = []
    while True:
        try:
            user = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not user:
            continue
        if user in (":q", ":quit", ":exit"):
            return 0
        if user == ":reset":
            history = []
            print("(history cleared)")
            continue

        try:
            qvec = embed_query(cfg, user)
        except Exception as exc:
            print(f"embedding error: {exc}", file=sys.stderr)
            continue

        hits = search(index, qvec, top_k, min_score, query_text=user)
        hits = trim_context(hits, max_ctx_tokens)
        if not hits:
            print(
                "\nI do not have this in my sources. Please consult your local "
                "mosque imam, an asatizah recognised under ARS, the treating "
                "doctor, or the Syariah Court of Singapore depending on the "
                "question.\n"
            )
            continue

        context, used = format_context(hits)
        messages = build_messages(system_prompt, history, user, context)

        try:
            if use_openai:
                answer = chat_openai(chat_model, messages, temperature)
            else:
                answer = chat_ollama(
                    chat_model, chat_host, messages, temperature, num_ctx
                )
        except Exception as exc:
            print(f"chat error: {exc}", file=sys.stderr)
            continue

        print()
        wrap_print(answer)
        print("\nSources:")
        for i, h in enumerate(used, 1):
            print(
                f"  [{i}] {h['path']}:{h['start_line']}-{h['end_line']}  {h['title']}"
            )
        print()

        history.append({"role": "user", "content": user})
        history.append({"role": "assistant", "content": answer})
        if len(history) > 8:
            history = history[-8:]

    return 0


if __name__ == "__main__":
    sys.exit(main())
