"""Anchor matches (plan 评判 3rd item: 「对池外固定锚点的成绩」, answers "did it really get stronger"): every
member against a fixed panel of opponents outside the pool, on a fixed panel of seeds (91700000-91799999, the same
every period on purpose: an unchanged member gets the same games, so only new versions are played).

    python -m ladder.anchors table --out ANCHORS.json [--pilots PILOTS.json]
    python -m ladder.anchors run ANCHORS.json --pool POOL --out DIR [--games-per-anchor 10] [--tiers ...]
                                 [--all] [--plan] [--workers 11 --mask 0x3FC3FC]
    python -m ladder.anchors report DIR [--pool POOL]

The panel (ENVIRONMENT 10): the bot's four GENERIC tiers on the bot frozen seven decks (quick greedy+plan, normal
mcts:100+plan = the baseline snapshot, strong mcts:400+plan, strongest mcts:1000+plan), 28 anchors; the trained
pilots join under the default-guess condition once 2.5 is done (`--pilots`: a list of {name, deck, strategy}).
Learned per-deck web levels are never anchors (they pick models by the opponent's identity, L4).

Game i against anchor j: seed 91700000 + 1000 * j + i, the member in seat i % 2. The deal goes through the host's
key (base-2) like every formal game. One ledger line per member version and anchor (DIR/anchors.jsonl, append-only).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for _p in (str(HERE.parent), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

ANCHOR_SEEDS = (91700000, 91800000)
STRIDE = 1000                      # seeds per anchor: game i against anchor j uses ANCHOR_SEEDS[0] + STRIDE * j + i
TIERS = {"快速": "bot:greedy+plan", "普通": "bot:mcts:100+plan", "强": "bot:mcts:400+plan", "最强": "bot:mcts:1000+plan"}
CRAFT_ZH = {1: "精灵", 2: "皇家护卫", 3: "巫师", 4: "龙族", 5: "梦魇", 6: "主教", 7: "超越者"}
FROZEN7 = ROOT / "analysis/pilot/fields/bot-frozen7.txt"


class AnchorError(Exception):
    pass


def table(pilots=None) -> list[dict]:
    from ladder import base
    from ladder.runner import load_deck
    rows = []
    decks = [l.strip().split("|") for l in FROZEN7.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    for tier, spec in TIERS.items():
        for name, code in decks:
            craft = int(base.craft_of(load_deck(code)))
            rows.append({"id": f"A{len(rows):02d}", "name": f"bot {tier}·{CRAFT_ZH[craft]}", "tier": tier,
                         "craft": craft, "deck": code, "strategy": spec, "source": name})
    for p in pilots or []:
        craft = int(base.craft_of(load_deck(p["deck"])))
        rows.append({"id": f"A{len(rows):02d}", "name": p["name"], "tier": "驾驶员", "craft": craft,
                     "deck": p["deck"], "strategy": p["strategy"], "source": p.get("source", "")})
    if len(rows) * STRIDE > ANCHOR_SEEDS[1] - ANCHOR_SEEDS[0]:
        raise AnchorError("too many anchors for the seed panel")
    return rows


def _ledger(out: Path) -> list[dict]:
    f = out / "anchors.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()] if f.exists() else []


def _wilson(w: int, n: int):
    if n == 0:
        return None, None, None
    z, p = 1.96, w / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return round(p, 4), round(c - h, 4), round(c + h, 4)


def plan(anchors: list[dict], pool_dir: Path, out: Path, games: int, tiers=None, every=False):
    """The jobs to play: each active member's current version against each anchor of the chosen tiers, skipping the
    (member, version, anchor, games) already in the ledger unless `every`."""
    from ladder.pool import Pool
    pool = Pool(pool_dir)
    done = {(l["member"], l["version"], l["anchor"], l["games"]) for l in _ledger(out)}
    if games > STRIDE:
        raise AnchorError(f"at most {STRIDE} games per anchor on the panel")
    chosen = [a for a in anchors if tiers is None or a["tier"] in tiers]
    jobs, todo = [], []
    for m in pool.active():
        for j, a in enumerate(anchors):
            if a not in chosen or (not every and (m.mid, m.version, a["id"], games) in done):
                continue
            todo.append((m.mid, m.version, a["id"]))
            for i in range(games):
                seat = i % 2
                sides = [(list(m.deck), m.strategy), (a["deck"], a["strategy"])]
                if seat == 1:
                    sides.reverse()
                jobs.append({"id": f"{m.mid}-v{m.version}-{a['id']}-{i:04d}", "seed": ANCHOR_SEEDS[0] + STRIDE * j + i,
                             "first": None, "decks": [d for d, _ in sides], "strategies": [s for _, s in sides],
                             "labels": {"member": m.mid, "version": m.version, "anchor": a["id"], "seat": seat}})
    return jobs, todo


def run(anchors_path: Path, pool_dir: Path, out: Path, games: int = 10, tiers=None, every=False, workers=4,
        mask=None, step_limit=30.0, key="auto") -> dict:
    from ladder import runner
    anchors = json.loads(Path(anchors_path).read_text(encoding="utf-8"))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    jobs, todo = plan(anchors, pool_dir, out, games, tiers, every)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log = out / f"games-{stamp}.jsonl"
    res = runner.run(jobs, str(log), workers=workers, step_limit=step_limit, mask=mask, quiet=True, key=key) \
        if jobs else {"played": 0}
    per = {}
    if jobs:
        for line in log.read_text(encoding="utf-8").splitlines():
            g = json.loads(line)
            lab = g["labels"]
            k = (lab["member"], lab["version"], lab["anchor"])
            d = per.setdefault(k, {"won": 0, "lost": 0, "draw": 0, "void": 0})
            if g["result"] == "void":
                d["void"] += 1
            elif g.get("winner") is None:
                d["draw"] += 1
            elif g["winner"] == lab["seat"]:
                d["won"] += 1
            else:
                d["lost"] += 1
    with (out / "anchors.jsonl").open("a", encoding="utf-8") as f:
        for (mid, ver, aid), d in sorted(per.items()):
            p, lo, hi = _wilson(d["won"], d["won"] + d["lost"])
            f.write(json.dumps({"member": mid, "version": ver, "anchor": aid, "games": games, **d, "rate": p,
                                "lo": lo, "hi": hi, "log": log.name, "deal": res.get("deal"),
                                "time": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False) + "\n")
    return {"jobs": len(jobs), "pairs": len(todo), "played": res.get("played"), "deal": res.get("deal"),
            "log": str(log) if jobs else None}


def report(out: Path, anchors_path: Path) -> list[dict]:
    """Per member version and tier: won / decided over all anchors of the tier, with a 95% interval."""
    anchors = {a["id"]: a for a in json.loads(Path(anchors_path).read_text(encoding="utf-8"))}
    agg = {}
    for l in _ledger(Path(out)):
        tier = anchors[l["anchor"]]["tier"]
        d = agg.setdefault((l["member"], l["version"], tier), [0, 0])
        d[0] += l["won"]
        d[1] += l["won"] + l["lost"]
    rows = []
    for (mid, ver, tier), (w, n) in sorted(agg.items()):
        p, lo, hi = _wilson(w, n)
        rows.append({"member": mid, "version": ver, "tier": tier, "won": w, "decided": n, "rate": p, "lo": lo,
                     "hi": hi})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ladder.anchors")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("table")
    a.add_argument("--out", required=True)
    a.add_argument("--pilots")
    a = sp.add_parser("run")
    a.add_argument("anchors")
    a.add_argument("--pool", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--games-per-anchor", type=int, default=10)
    a.add_argument("--tiers", nargs="*")
    a.add_argument("--all", action="store_true", help="replay members already anchored")
    a.add_argument("--plan", action="store_true", help="only count the games")
    a.add_argument("--workers", type=int, default=4)
    a.add_argument("--mask", type=lambda x: int(x, 0))
    a = sp.add_parser("report")
    a.add_argument("out")
    a.add_argument("--anchors", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "table":
        pilots = json.loads(Path(args.pilots).read_text(encoding="utf-8")) if args.pilots else None
        rows = table(pilots)
        Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(rows)} anchors -> {args.out}")
    elif args.cmd == "run":
        if args.plan:
            anchors = json.loads(Path(args.anchors).read_text(encoding="utf-8"))
            jobs, todo = plan(anchors, Path(args.pool), Path(args.out), args.games_per_anchor, args.tiers, args.all)
            print(json.dumps({"games": len(jobs), "member_anchor_pairs": len(todo)}, ensure_ascii=False))
        else:
            print(json.dumps(run(Path(args.anchors), Path(args.pool), Path(args.out), args.games_per_anchor,
                                 args.tiers, args.all, args.workers, args.mask), ensure_ascii=False, indent=1))
    elif args.cmd == "report":
        print(json.dumps(report(Path(args.out), Path(args.anchors)), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
