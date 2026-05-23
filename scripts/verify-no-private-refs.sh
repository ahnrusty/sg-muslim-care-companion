#!/usr/bin/env bash
# Scan tracked files for forbidden private substrings.
# Exit 1 if any are found.

set -euo pipefail

cd "$(dirname "$0")/.."

FORBIDDEN=(
  "Farhan"
  "Rasam"
  "frasam"
  "Netflix"
  "netflix"
  "nflx"
  "ndex"
  "TSOS"
  "N-Tech"
  "ASYLLA"
  "JARVIS"
  "Stride"
  "Workbench"
  "Kragle"
  "BDP"
  "Zendesk"
)

if [ -d .git ]; then
  FILES=$(git ls-files)
else
  FILES=$(find . -type f -not -path './.git/*' -not -path './.venv/*' -not -path './rag/index/*' -not -path './**/__pycache__/*')
fi

FAIL=0
for term in "${FORBIDDEN[@]}"; do
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if [ "$f" = "scripts/verify-no-private-refs.sh" ] || \
       [ "$f" = "rules/AGENTS.md" ] || \
       [ "$f" = "rules/cursor-rule.mdc" ] || \
       [ "$f" = "CONTRIBUTING.md" ] || \
       [ "$f" = "tests/test_no_private_refs.py" ]; then
      continue
    fi
    if grep -nI --binary-files=without-match -w "$term" "$f" >/dev/null 2>&1; then
      echo "FORBIDDEN: $f matches '$term'"
      grep -nI --binary-files=without-match -w "$term" "$f" | head -5
      FAIL=1
    fi
  done <<< "$FILES"
done

if [ "$FAIL" -ne 0 ]; then
  echo
  echo "Pre-push scrub failed. Remove the forbidden substrings before pushing." >&2
  exit 1
fi
echo "ok: no forbidden private references found in tracked files."
