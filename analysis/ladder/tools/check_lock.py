"""Check the files locked at 1.9 (LOCK.md) against the hashes recorded there: their content (line ends made LF)
must not change without Salem's consent. Prints each file that differs; exit 1 if any does.

    python analysis/ladder/tools/check_lock.py
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

LADDER = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\| (ladder/[\w./]+\.py) \| [^|]* \| ([0-9a-f]{64}) \|$")


def recorded() -> dict:
    return {m.group(1): m.group(2) for line in (LADDER / "LOCK.md").read_text(encoding="utf-8").splitlines()
            if (m := ROW.match(line))}


def differs() -> list:
    out = []
    for rel, want in recorded().items():
        p = LADDER / rel
        got = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() if p.exists() else "missing"
        if got != want:
            out.append(f"{rel}: {got[:16]} (locked {want[:16]})")
    return out


if __name__ == "__main__":
    bad = differs()
    print("\n".join(bad) if bad else f"all {len(recorded())} locked files as locked")
    sys.exit(1 if bad else 0)
