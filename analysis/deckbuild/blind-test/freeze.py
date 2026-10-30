"""Freezing the bot's list, by the rule registered in README.md before any freeze (10-29 21:5xZ).

    PYTHONPATH=. python analysis/deckbuild/blind-test/freeze.py candidates --out runs/freeze/cands.txt
    python -m svsim.tools.deckbuild --league runs/freeze/cands.txt --deals 30 --seed 85940000 --out runs/freeze
    PYTHONPATH=. python analysis/deckbuild/blind-test/freeze.py tiers --league runs/freeze/league.json \
        --cands runs/freeze/cands.txt --out-dir analysis/deckbuild/blind-test

candidates: each search's incumbents (freeze-sources.txt: name|branch|commit|state.json path), made legal by name,
an identical deck kept once (under the first source that has it). tiers: a deck's score is its mean over every other
candidate (league.json); 55% and up is T1, 50% to 55% T2, the rest T3; within one class and tier a deck stays only
if it differs by 8 cards or more, by name, from every higher-scoring deck kept there. Writes frozen.txt
("T1-FOREST-1|deck hash", the class's best first) and frozen.json.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
from collections import Counter
from pathlib import Path

from svsim.cards.pool import POOL
from svsim.tools import deckbuild

HERE = Path(__file__).resolve().parent
CUTS = ((0.55, 1), (0.50, 2))
MIN_APART = 8
CONDITION = "对手卡表已知（牌序、手牌未知）"


def tier_of(mean: float) -> int:
    return next((t for cut, t in CUTS if mean >= cut), 3)


def apart(a: list, b: list) -> int:
    """Cards of `a` not matched in `b`, by name (40 minus the overlap)."""
    na, nb = Counter(POOL[i].name for i in a), Counter(POOL[i].name for i in b)
    return deckbuild.decks.DECK_SIZE - sum((na & nb).values())


def read_state(branch: str, commit: str, path: str) -> dict:
    if subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], capture_output=True).returncode:
        subprocess.run(["git", "fetch", "-q", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}"],
                       check=True)
    text = subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True, text=True, check=True).stdout
    return json.loads(text)


def candidates(sources: str) -> list:
    """(label, ids) of every distinct legal incumbent, labels "source-CLASS"."""
    out, seen = [], set()
    for row in Path(sources).read_text(encoding="utf-8").splitlines():
        row = row.split("#", 1)[0].strip()
        if not row:
            continue
        name, branch, commit, path = (x.strip() for x in row.split("|"))
        field = read_state(branch, commit, path)["field"]
        for cls in sorted(field, key=lambda k: deckbuild.Craft[k]):
            ids = deckbuild.legalize(field[cls], deckbuild.Craft[cls], random.Random(0))
            h = deckbuild.deck_hash(ids)
            if h not in seen:
                seen.add(h)
                out.append((f"{name}-{cls}", ids))
    return out


def tiers(entries: list, means: list) -> list:
    """[{label, tier, class, deck, ids, league_mean, source}], best first within each class and tier."""
    kept: dict = {}
    for (label, ids), m in sorted(zip(entries, means), key=lambda e: -e[1]):
        cls = deckbuild.craft_of_ids(ids).name
        t = tier_of(m)
        group = kept.setdefault((cls, t), [])
        if all(apart(ids, other["ids"]) >= MIN_APART for other in group):
            group.append({"tier": t, "class": cls, "deck": deckbuild.deck_hash(ids), "ids": sorted(ids),
                          "league_mean": m, "source": label})
    out = []
    for (cls, t), group in sorted(kept.items(), key=lambda kv: (kv[0][1], deckbuild.Craft[kv[0][0]])):
        for n, d in enumerate(group, 1):
            out.append({"label": f"T{t}-{cls}-{n}", **d})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("candidates")
    c.add_argument("--sources", default=str(HERE / "freeze-sources.txt"))
    c.add_argument("--out", required=True)
    t = sub.add_parser("tiers")
    t.add_argument("--league", required=True)
    t.add_argument("--cands", required=True)
    t.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    if args.cmd == "candidates":
        cands = candidates(args.sources)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text("".join(f"{lab}|{deckbuild.deck_hash(ids)}\n" for lab, ids in cands), encoding="utf-8")
        print(f"{len(cands)} 副不同的候选卡组（{CONDITION}）")
        return
    league = json.loads(Path(args.league).read_text(encoding="utf-8"))
    entries = deckbuild.read_seeds(args.cands)
    assert [e[0] for e in entries] == league["decks"], "the league was not played on this candidates file"
    frozen = tiers(entries, league["means"])
    out = Path(args.out_dir)
    head = (f"# bot 冻结名单。排名由便宜 bot（{league['agent']}）的循环赛得分决定，每对 {league['deals']} 个发牌，"
            f"种子 {league['seed']} 起；条件：{CONDITION}。\n# T1：55% 以上；T2：50%～55%；T3：其余。\n")
    (out / "frozen.txt").write_text(head + "".join(f"{d['label']}|{d['deck']}\n" for d in frozen), encoding="utf-8")
    (out / "frozen.json").write_text(json.dumps(frozen, ensure_ascii=False, indent=1), encoding="utf-8")
    for d in frozen:
        print(f"{d['label']}: {d['league_mean']:.1%}  （来自 {d['source']}）")


if __name__ == "__main__":
    main()
