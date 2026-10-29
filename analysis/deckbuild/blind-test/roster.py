"""The roster of the blind test's cross-play league (metric 5): one deck per class from each group of sources.txt.

Each group's deck for a class is the one the group itself ranks highest: the best tier its label names (T1 < T2 < ...,
S < P < W, STRONG < PLAYABLE < WEAK, 强 < 可玩 < 弱), then file order. Groups name tiers their own way, so a label with no tier we know counts as
after every named tier. Every deck is made legal by name first (deckbuild.legalize; changes are counted, not shown: a 4th copy replaced,
or only a reprint's id swapped for the id the pool keeps).

    PYTHONPATH=. python analysis/deckbuild/blind-test/roster.py --out runs/blind-league/roster.txt

prints only counts per group, so whoever builds the roster before the bot's list is frozen sees no deck of a Claude
group; writes "group/label|deck hash" lines for deckbuild --league --cross-groups.
"""
from __future__ import annotations

import argparse
import random
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from svsim.cards.pool import POOL
from svsim.tools import deckbuild

HERE = Path(__file__).resolve().parent
TIERS = [(re.compile(r"(?:^|[-_/ ])T([1-9])(?=$|[-_/ ])", re.I), lambda m: int(m.group(1))),
         (re.compile(r"(?:^|[-_/ ])([SPW])[0-9]*(?=$|[-_/ ])"), lambda m: "SPW".index(m.group(1)) + 1),
         (re.compile(r"^(STRONG|PLAYABLE|WEAK|强|可玩|弱)(?=$|[-_/ ])", re.I),
          lambda m: ["STRONG", "PLAYABLE", "WEAK", "强", "可玩", "弱"].index(m.group(1).upper()) % 3 + 1)]


def tier(label: str) -> int:
    for rx, f in TIERS:
        m = rx.search(label)
        if m:
            return f(m)
    return 99


def pick(entries: list) -> dict:
    """{class name: (label, ids)}: per class, the lowest tier, then the first line."""
    best: dict = {}
    for n, (label, ids) in enumerate(entries):
        cls = deckbuild.craft_of_ids(ids).name
        key = (tier(label), n)
        if cls not in best or key < best[cls][0]:
            best[cls] = (key, label, ids)
    return {c: (v[1], v[2]) for c, v in best.items()}


def read_source(branch: str, sha: str, path: str) -> list:
    if subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True).returncode:
        subprocess.run(["git", "fetch", "-q", "origin", branch], check=True)
    text = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True, text=True, check=True).stdout
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "decks.txt").write_text(text, encoding="utf-8")
        return deckbuild.read_seeds(str(Path(d) / "decks.txt"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sources", default=str(HERE / "sources.txt"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lines = []
    for row in Path(args.sources).read_text(encoding="utf-8").splitlines():
        row = row.split("#", 1)[0].strip()
        if not row:
            continue
        group, branch, sha, path = (x.strip() for x in row.split("|"))
        entries = read_source(branch, sha, path)
        chosen = pick(entries)
        fixed = renamed = 0
        for cls, (label, ids) in sorted(chosen.items(), key=lambda kv: deckbuild.Craft[kv[0]]):
            legal = deckbuild.legalize(ids, deckbuild.Craft[cls], random.Random(0))
            names = (Counter(POOL[i].name for i in ids), Counter(POOL[i].name for i in legal))
            fixed += names[0] != names[1]
            renamed += names[0] == names[1] and sorted(legal) != sorted(ids)    # a reprint's id, same card
            lines.append(f"{group}/{label}|{deckbuild.deck_hash(legal)}")
        tiers = sorted(tier(chosen[c][0]) for c in chosen)
        print(f"{group}: {len(entries)} 副，取 {len(chosen)} 副（职业 {', '.join(sorted(chosen))}；档位 {tiers}；"
              f"改合法 {fixed} 副，只换卡号 {renamed} 副）")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
