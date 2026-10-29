"""The P3 pool (the architecture thread 2026-10-29 19:45Z; Salem 19:44Z approved ten times the shared net's self-play):
P2's 432 decks and the distinct decks of deck search F's round 0 (claude/deck-runs-F, deals.jsonl "deck", tags "r0:"),
B-r1's 7 decks and S1's 7 held-out decks left out (the gate's field, and the validation decks).

    python analysis/sharednet/p3pool.py --p2 analysis/sharednet/fields/P2-pool.txt --deals DEALS [DEALS ...] \
        --source "claude/deck-runs-F <commit>" --out analysis/sharednet/fields/P3-pool.txt

A deck is its sorted card ids (a deck already in P2 or met again is skipped). The new decks are labelled
P-F0-<class>-<n>, n counting within the class in the order of the smallest sha256 of the deck code first, so the
file does not depend on the order of the deals. Lines "label|deck code", LF endings; the first line a comment saying
where the decks came from. Prints the counts and the file's sha256 (learn.scaledata play --pool records it).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

CLASSES = {1: "forest", 2: "sword", 3: "rune", 4: "dragon", 5: "abyss", 6: "haven", 7: "portal"}


def main() -> None:
    from svsim.cards import deckcode
    from svsim.learn.scaledata import pool_of
    from svsim.tools.deckgate import read_field
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--p2", required=True)
    ap.add_argument("--deals", nargs="+", required=True, help="deck search F's deals.jsonl files")
    ap.add_argument("--round", default="r0", help="the tag prefix of the deals to take")
    ap.add_argument("--source", required=True, help="where the deals came from (branch and commit), for the comment")
    ap.add_argument("--exclude", nargs="+", default=["analysis/sharednet/fields/B-r1.txt"])
    ap.add_argument("--holdout", default="analysis/sharednet/s1/holdout-decks.json")
    ap.add_argument("--c-pool", default="analysis/sharednet/fields/C-r0-pool.txt", help="where the held-out labels are")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    p2_text = Path(args.p2).read_text(encoding="utf-8")
    p2 = pool_of(args.p2)
    seen = {tuple(sorted(ids)) for _, ids in p2}
    left_out = set()
    for f in args.exclude:
        left_out |= {tuple(sorted(ids)) for _, ids in read_field(f)}
    held = set(json.loads(Path(args.holdout).read_text(encoding="utf-8")))
    left_out |= {tuple(sorted(ids)) for label, ids in pool_of(args.c_pool) if label in held}
    if seen & left_out:
        raise SystemExit("P2 holds a deck that has to be left out")
    new: dict = {}
    deals = skipped_out = 0
    for path in args.deals:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            if not str(d.get("tag", "")).startswith(args.round + ":"):
                continue
            deals += 1
            fmt, craft, ids = deckcode.decode_deck(d["deck"])
            key = tuple(sorted(ids))
            if key in left_out:
                skipped_out += 1
                continue
            if key in seen or key in new:
                continue
            new[key] = (int(craft), deckcode.encode_deck(fmt, craft, sorted(ids)))
    by_class: dict = {}
    for key, (craft, code) in new.items():
        by_class.setdefault(craft, []).append(code)
    lines = []
    for craft in sorted(by_class):
        for n, code in enumerate(sorted(by_class[craft], key=lambda c: hashlib.sha256(c.encode()).hexdigest()), 1):
            lines.append(f"P-F0-{CLASSES.get(craft, craft)}-{n}|{code}")
    body = [l for l in p2_text.splitlines() if l.strip() and not l.startswith("#")]
    head = (f"# P3 (the architecture thread 2026-10-29 19:45Z): P2's {len(body)} decks, then the {len(lines)} distinct "
            f"decks of deck search F {args.round} ({args.source}, deals.jsonl deck) not in P2; B-r1's 7 and S1's 7 "
            f"held-out decks left out")
    text = "\n".join([head] + body + lines) + "\n"
    Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    pool = pool_of(args.out)
    print(json.dumps({"deals": deals, "p2": len(body), "new": len(lines), "left_out_deals": skipped_out,
                      "pool": len(pool), "by_class": {CLASSES.get(c, c): len(v) for c, v in sorted(by_class.items())},
                      "sha256": hashlib.sha256(Path(args.out).read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
