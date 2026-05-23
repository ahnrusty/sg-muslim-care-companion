#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> SG Muslim Care Companion setup"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Please install Python 3.10 or newer." >&2
  exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "python: $PY_VERSION"

if [ ! -d ".venv" ]; then
  echo "==> creating .venv"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> installing python deps"
pip install --quiet --upgrade pip
pip install --quiet -r rag/requirements.txt

if command -v ollama >/dev/null 2>&1; then
  echo "==> ollama detected"
  if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "ollama daemon not running. Start it with 'ollama serve' in another terminal." >&2
  else
    for model in nomic-embed-text gemma3:e4b; do
      if ! ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx "$model"; then
        echo "==> pulling $model"
        ollama pull "$model"
      else
        echo "ok: $model already present"
      fi
    done
  fi
else
  echo "ollama not found. Install from https://ollama.com to run locally." >&2
  echo "You can still build the index in dry-run mode, but chat will not work without an LLM." >&2
fi

echo "==> building index"
if command -v ollama >/dev/null 2>&1 && curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
  python rag/build_index.py
else
  python rag/build_index.py --dry-run
fi

echo
echo "setup complete."
echo "  chat:   source .venv/bin/activate && python rag/chat.py"
echo "  query:  source .venv/bin/activate && python rag/query.py 'your question'"
