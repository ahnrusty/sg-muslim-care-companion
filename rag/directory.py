"""Directory CLI for the SG Muslim Care Companion.

Two modes:

  python rag/directory.py --mosque "Sultan"
  python rag/directory.py --postal 198833

Postal-code lookup is best-effort, by postal-code prefix. No external geocoding.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MOSQUES = REPO_ROOT / "corpus" / "80-directory" / "mosques.json"
CONTACTS = REPO_ROOT / "corpus" / "80-directory" / "contacts.json"


def load_mosques() -> list[dict]:
    data = json.loads(MOSQUES.read_text(encoding="utf-8"))
    return data.get("mosques", [])


def load_contacts() -> dict:
    return json.loads(CONTACTS.read_text(encoding="utf-8"))


def normalise(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def find_by_name(query: str, mosques: list[dict]) -> list[dict]:
    q = normalise(query)
    exact: list[dict] = []
    partial: list[dict] = []
    for m in mosques:
        n = normalise(m["name"])
        s = normalise(m["slug"])
        if q == n or q == s:
            exact.append(m)
        elif q in n or q in s:
            partial.append(m)
    return exact or partial


def find_by_postal(postal: str, mosques: list[dict]) -> list[tuple[int, dict]]:
    """Return mosques ranked by postal-code prefix overlap."""
    postal = postal.strip()
    if not postal.isdigit() or len(postal) < 2:
        return []
    ranked: list[tuple[int, dict]] = []
    for m in mosques:
        mp = (m.get("postal") or "").strip()
        if not mp or not mp.isdigit():
            continue
        common = 0
        for a, b in zip(postal, mp):
            if a == b:
                common += 1
            else:
                break
        if common >= 1:
            ranked.append((common, m))
    ranked.sort(key=lambda x: (-x[0], x[1]["name"]))
    return ranked[:10]


def print_mosque(m: dict) -> None:
    print(f"\nMasjid {m['name']}  ({m['region']} district)")
    if m.get("address"):
        postal = f", Singapore {m['postal']}" if m.get("postal") else ""
        print(f"  Address: {m['address']}{postal}")
    else:
        print("  Address: unknown -- verify with mosque directly")
    if m.get("phone"):
        print(f"  Phone:   {m['phone']}")
    else:
        print("  Phone:   unknown -- verify with mosque directly")
    if m.get("email"):
        print(f"  Email:   {m['email']}")
    if m.get("website"):
        print(f"  Web:     {m['website']}")
    if m.get("muis_url"):
        print(f"  MUIS:    {m['muis_url']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MUIS mosque and contact directory lookup."
    )
    parser.add_argument("--mosque", help="Mosque name or slug.")
    parser.add_argument("--postal", help="6-digit Singapore postal code.")
    parser.add_argument("--list", action="store_true", help="List all mosques.")
    parser.add_argument(
        "--contacts", action="store_true", help="Print categorised contact list."
    )
    parser.add_argument("--json", action="store_true", help="JSON output.")
    args = parser.parse_args()

    mosques = load_mosques()

    if args.list:
        if args.json:
            print(json.dumps(mosques, ensure_ascii=False, indent=2))
            return 0
        for m in mosques:
            print(
                f"{m['name']:40s}  {m['region']:6s}  {m.get('phone') or '(verify)':12s}"
            )
        return 0

    if args.contacts:
        contacts = load_contacts()
        if args.json:
            print(json.dumps(contacts, ensure_ascii=False, indent=2))
            return 0
        print(f"Verified: {contacts.get('verified_date')}")
        print(contacts.get("disclaimer", ""))
        for cat in contacts.get("categories", []):
            print(f"\n== {cat['name']} ==")
            for e in cat.get("entries", []):
                phone = e.get("phone") or "-"
                print(f"  {e['service']:50s}  {phone}")
        return 0

    if args.mosque:
        hits = find_by_name(args.mosque, mosques)
        if not hits:
            print(f"No mosque matched {args.mosque!r}.")
            return 1
        if args.json:
            print(json.dumps(hits, ensure_ascii=False, indent=2))
            return 0
        for m in hits:
            print_mosque(m)
        return 0

    if args.postal:
        ranked = find_by_postal(args.postal, mosques)
        if not ranked:
            print("No mosques found by postal-code prefix. Try --list.")
            return 1
        if args.json:
            print(json.dumps([m for _, m in ranked], ensure_ascii=False, indent=2))
            return 0
        print(f"Best-effort matches near postal {args.postal} (by postal-code prefix):")
        for score, m in ranked:
            print(
                f"  prefix={score}  postal={m.get('postal') or '?'}  {m['name']} ({m['region']})"
            )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
