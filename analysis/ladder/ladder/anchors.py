"""Anchor matches (plan 评判 3rd item: 「对池外固定锚点的成绩」, answers "did it really get stronger"): once a period,
every member of the pool against every anchor, on fresh seeds (Salem's S11, 11-22: 「每期全员重打，按职业公布」).

    python -m ladder.anchors induct POOL --hof HOF.json [--period N]     # end of a period: the hall of fame
    python -m ladder.anchors table --out ANCHORS.json [--hof HOF.json]
    python -m ladder.anchors run ANCHORS.json --pool POOL --out DIR [--period N] [--games-per-anchor 10] [--plan]
                                 [--workers 23]
    python -m ladder.anchors report DIR --anchors ANCHORS.json [--period N]          # host only: per member
    python -m ladder.anchors classes DIR [--period N]                                 # the public figures

The panel (Salem's S9, 11-22: 「基线快照 + 名人堂」; the bot's other tiers are not anchors, the trained pilots only a
reference in the starting measurement 2.6):
- 基线快照: the seven baseline lists (bot frozen seven) with the default strategy mcts:100+plan: everyone's start.
- 名人堂: at the end of every period, each class's first member (A41: the highest mean relative CR since its last
  change, among the members with at least 300 games since it) frozen with its list and that version's strategy, if
  it isn't a baseline member or a version already in. Salem 11-22: after a few periods the panel becomes each class's
  top three of the hall of fame (how to rank them and from which period: to be agreed with Salem first).
Every anchor keeps its slot for good (baseline 0-6, hall of fame 7, 8, ... in the order they came in).

The run (S11, A48): at the end of period P (ladder done, hall of fame inducted, before `pool advance`) every active
member's current version plays every anchor `games` times, seats alternating, its own frozen copy included (a
baseline member is its class's 基线快照 anchor; a hall-of-fame member may still be on the frozen version), so every
member plays the same number of games and the counts tell nothing. Seeds: period P takes 93510000 + 50000 * P
onwards, one per game in a fixed order (members by id, anchors by slot, game index), all through the host's key
(base-2). A period is played once: its plan is written first (DIR/plan-P<P>.json) and an interrupted run picks up
its own games; a second run of a period that has ledger lines is refused. One ledger line per (period, member,
version, anchor) in DIR/anchors.jsonl, append-only. The public figures are per class and tier, rounded, without
counts (`classes`); the per-member rows stay with the host. The fixed panel of seeds 91700000-91799999 that played
each version once (A40) is no longer used.
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

ANCHOR_SEEDS = (93510000, 94510000)  # S11: every period on fresh seeds (seed ledger c61debe, SEEDS.md)
PERIOD_BLOCK = 50000               # period P plays seeds ANCHOR_SEEDS[0] + PERIOD_BLOCK * P onwards, at most this many
HOF_MIN_GAMES = 300                # A41: a class's first is picked among members with >= 300 games since their change
BASELINE_SPEC = "bot:mcts:100+plan"
TIERS = ("基线快照", "名人堂")
CRAFT_ZH = {1: "精灵", 2: "皇家护卫", 3: "巫师", 4: "龙族", 5: "梦魇", 6: "主教", 7: "超越者"}
FROZEN7 = ROOT / "analysis/pilot/fields/bot-frozen7.txt"


class AnchorError(Exception):
    pass


def _read_hof(path) -> list[dict]:
    p = Path(path) if path else None
    return json.loads(p.read_text(encoding="utf-8")) if p and p.exists() else []


def table(hof=None) -> list[dict]:
    """The anchor panel: the baseline snapshot (slots 0-6), then the hall of fame in the order it came in."""
    from ladder import base
    from ladder.runner import load_deck
    rows = []
    decks = [l.strip().split("|") for l in FROZEN7.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    for name, code in decks:
        craft = int(base.craft_of(load_deck(code)))
        rows.append({"id": f"A{len(rows):02d}", "slot": len(rows), "name": f"基线快照·{CRAFT_ZH[craft]}",
                     "tier": "基线快照", "craft": craft, "deck": code, "strategy": BASELINE_SPEC, "source": name})
    for h in _read_hof(hof):
        rows.append({"id": f"A{h['slot']:02d}", "slot": h["slot"], "name": f"名人堂 第{h['period']}期·{CRAFT_ZH[h['craft']]}",
                     "tier": "名人堂", "craft": h["craft"], "deck": h["deck"], "strategy": h["strategy"],
                     "source": f"{h['mid']} v{h['version']}", "mid": h["mid"], "version": h["version"]})
    return rows


def induct(pool_dir, hof_path, period=None) -> list[dict]:
    """End of a period (S9): each class's first member joins the hall of fame (A41). Returns the new entries."""
    from ladder import leaderboard as L
    pool, series = L.load(pool_dir)
    hof = _read_hof(hof_path)
    have = {(h["mid"], h["version"]) for h in hof}
    period = pool.period if period is None else period
    if any(h["period"] == period for h in hof):
        raise AnchorError(f"period {period} already inducted")
    new = []
    for craft in sorted(CRAFT_ZH):
        best = None
        for m in pool.active(craft):
            pts = series.points[m.mid][series.change_at[m.mid]:]
            if len(pts) < HOF_MIN_GAMES:
                continue
            rel = sum(c - mu for c, mu in pts[-L.WINDOW_GAMES:]) / len(pts[-L.WINDOW_GAMES:])
            if best is None or rel > best[0]:
                best = (rel, m, len(pts))
        if best is None:
            continue
        rel, m, n = best
        if m.owner == "baseline" or (m.mid, m.version) in have:
            continue                                  # the baseline is in the panel already; a version only once
        slot = 7 + len(hof) + len(new)
        new.append({"slot": slot, "period": period, "craft": craft, "mid": m.mid, "version": m.version,
                    "deck": list(m.deck), "strategy": m.strategy, "rel_cr": round(rel, 1), "games": n,
                    "time": time.strftime("%Y-%m-%dT%H:%M:%S")})
    if new or not Path(hof_path).exists():
        Path(hof_path).write_text(json.dumps(hof + new, ensure_ascii=False, indent=1), encoding="utf-8")
    return new


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


def _period_of(pool_dir, period):
    from ladder.pool import Pool
    pool = Pool(pool_dir)
    return pool, (pool.period if period is None else int(period))


def plan(anchors: list[dict], pool_dir: Path, games: int, period=None):
    """This period's games (S11, A48): every active member's current version against every anchor, `games` each,
    seats alternating, on the period's own block of seeds in a fixed order."""
    pool, period = _period_of(pool_dir, period)
    base = ANCHOR_SEEDS[0] + PERIOD_BLOCK * period
    if period < 0 or base + PERIOD_BLOCK > ANCHOR_SEEDS[1]:
        raise AnchorError(f"第 {period} 期不在锚点种子段里（{ANCHOR_SEEDS[0]}～{ANCHOR_SEEDS[1] - 1}，每期 {PERIOD_BLOCK}）："
                          "先在登记表上登记新的一段")
    members = sorted(pool.active(), key=lambda m: m.mid)
    panel = sorted(anchors, key=lambda a: a["slot"])
    if len(members) * len(panel) * games > PERIOD_BLOCK:
        raise AnchorError(f"{len(members)} 个成员 × {len(panel)} 个锚点 × {games} 局超过每期 {PERIOD_BLOCK} 个种子")
    jobs, todo = [], []
    for m in members:
        for a in panel:
            todo.append((m.mid, m.version, a["id"]))
            for i in range(games):
                seat = i % 2
                sides = [(list(m.deck), m.strategy), (a["deck"], a["strategy"])]
                if seat == 1:
                    sides.reverse()
                jobs.append({"id": f"P{period}-{m.mid}-v{m.version}-{a['id']}-{i:04d}", "seed": base + len(jobs),
                             "first": None, "decks": [d for d, _ in sides], "strategies": [s for _, s in sides],
                             "labels": {"period": period, "member": m.mid, "version": m.version, "craft": m.craft,
                                        "anchor": a["id"], "seat": seat}})
    return jobs, todo


def run(anchors_path: Path, pool_dir: Path, out: Path, games: int = 10, workers=4, mask=None, step_limit=30.0,
        key="auto", period=None) -> dict:
    import hashlib
    from ladder import runner
    anchors = json.loads(Path(anchors_path).read_text(encoding="utf-8"))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _, period = _period_of(pool_dir, period)
    if any(l.get("period") == period for l in _ledger(out)):
        raise AnchorError(f"第 {period} 期的锚点已经打过（每期只打一次，A48）")
    jobs, todo = plan(anchors, pool_dir, games, period)
    digest = hashlib.sha256(json.dumps(jobs, sort_keys=True).encode()).hexdigest()
    pf = out / f"plan-P{period}.json"
    if pf.exists():
        if json.loads(pf.read_text(encoding="utf-8"))["sha256"] != digest:
            raise AnchorError(f"第 {period} 期的锚点开打以后，池子或锚点表变了（{pf.name}）：先查清楚，不要换一批局重打")
    else:
        pf.write_text(json.dumps({"period": period, "games": games, "jobs": len(jobs), "sha256": digest,
                                  "anchors": [a["id"] for a in anchors], "time": time.strftime("%Y-%m-%dT%H:%M:%S")},
                                 ensure_ascii=False, indent=1), encoding="utf-8")
    log = out / f"games-P{period}.jsonl"
    res = runner.run(jobs, str(log), workers=workers, step_limit=step_limit, mask=mask, quiet=True, key=key) \
        if jobs else {"played": 0}
    ids = {j["id"] for j in jobs}
    tier = {a["id"]: a["tier"] for a in anchors}
    got = {}
    if jobs:
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                g = json.loads(line.strip("\x00").strip())
            except ValueError:
                continue                              # a line torn by a stop: its game was played again
            if isinstance(g, dict) and g.get("id") in ids:
                got[g["id"]] = g
    if len(got) != len(jobs):
        raise AnchorError(f"第 {period} 期的锚点没打完（{log.name} 里 {len(got)}/{len(jobs)} 局）：再跑一次同一条命令接着打")
    per, deals = {}, set()
    for g in got.values():
        lab = g["labels"]
        deals.add((g.get("deal") or {}).get("key"))          # the key id the game was dealt with
        k = (lab["member"], lab["version"], lab["craft"], lab["anchor"])
        d = per.setdefault(k, {"won": 0, "lost": 0, "draw": 0, "void": 0})
        if g["result"] == "void":
            d["void"] += 1
        elif g.get("winner") is None:
            d["draw"] += 1
        elif g["winner"] == lab["seat"]:
            d["won"] += 1
        else:
            d["lost"] += 1
    if len(deals) > 1:
        raise AnchorError(f"第 {period} 期的锚点局用了不止一种发牌（{sorted(map(str, deals))}）：密钥中途换过，先查清楚")
    deal_id = deals.pop() if deals else None
    with (out / "anchors.jsonl").open("a", encoding="utf-8") as f:
        for (mid, ver, craft, aid), d in sorted(per.items()):
            p, lo, hi = _wilson(d["won"], d["won"] + d["lost"])
            f.write(json.dumps({"period": period, "member": mid, "version": ver, "craft": craft, "anchor": aid,
                                "tier": tier[aid], "games": games, **d, "rate": p, "lo": lo, "hi": hi,
                                "log": log.name, "deal": deal_id, "time": time.strftime("%Y-%m-%dT%H:%M:%S")},
                               ensure_ascii=False) + "\n")
    return {"period": period, "jobs": len(jobs), "pairs": len(todo), "played": res.get("played"), "deal": deal_id,
            "log": str(log) if jobs else None}


def _lines(out: Path, period=None) -> tuple[int | None, list[dict]]:
    """The ledger lines of one period (default: the last period that has lines)."""
    lines = [l for l in _ledger(Path(out)) if "period" in l]       # lines without a period: the old fixed panel (A40)
    if period is None:
        period = max((l["period"] for l in lines), default=None)
    return period, [l for l in lines if l["period"] == period]


def report(out: Path, anchors_path: Path, period=None) -> list[dict]:
    """Host only. Per member version and tier, one period: won / decided over all anchors of the tier, 95% interval."""
    anchors = {a["id"]: a for a in json.loads(Path(anchors_path).read_text(encoding="utf-8"))}
    period, lines = _lines(out, period)
    agg = {}
    for l in lines:
        d = agg.setdefault((l["member"], l["version"], anchors[l["anchor"]]["tier"]), [0, 0])
        d[0] += l["won"]
        d[1] += l["won"] + l["lost"]
    rows = []
    for (mid, ver, tier), (w, n) in sorted(agg.items()):
        p, lo, hi = _wilson(w, n)
        rows.append({"period": period, "member": mid, "version": ver, "tier": tier, "won": w, "decided": n, "rate": p,
                     "lo": lo, "hi": hi})
    return rows


def classes(out: Path, period=None) -> tuple[int | None, list[dict]]:
    """The public figures (S11): one period, per member class and tier (and the whole pool), whole percent with a 95%
    interval, no counts, no ids."""
    period, lines = _lines(out, period)
    agg = {}
    for l in lines:
        for c in (CRAFT_ZH[l["craft"]], "全池"):
            d = agg.setdefault((c, l["tier"]), [0, 0])
            d[0] += l["won"]
            d[1] += l["won"] + l["lost"]
    order = list(CRAFT_ZH.values()) + ["全池"]
    rows = []
    for (c, tier), (w, n) in sorted(agg.items(), key=lambda x: (order.index(x[0][0]), TIERS.index(x[0][1]))):
        if n:
            p, lo, hi = _wilson(w, n)
            rows.append({"craft": c, "tier": tier, "rate": round(100 * p), "lo": round(100 * lo), "hi": round(100 * hi)})
    return period, rows


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ladder.anchors")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("induct")
    a.add_argument("pool")
    a.add_argument("--hof", required=True)
    a.add_argument("--period", type=int)
    a = sp.add_parser("table")
    a.add_argument("--out", required=True)
    a.add_argument("--hof")
    a = sp.add_parser("run")
    a.add_argument("anchors")
    a.add_argument("--pool", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--games-per-anchor", type=int, default=10)
    a.add_argument("--period", type=int, help="default: the pool's current period")
    a.add_argument("--plan", action="store_true", help="only count the games")
    a.add_argument("--workers", type=int, default=4)
    a.add_argument("--mask", type=lambda x: int(x, 0))
    a = sp.add_parser("report")
    a.add_argument("out")
    a.add_argument("--anchors", required=True)
    a.add_argument("--period", type=int)
    a = sp.add_parser("classes")
    a.add_argument("out")
    a.add_argument("--period", type=int)
    args = ap.parse_args(argv)
    if args.cmd == "induct":
        print(json.dumps(induct(Path(args.pool), Path(args.hof), args.period), ensure_ascii=False, indent=1))
    elif args.cmd == "table":
        rows = table(args.hof)
        Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(rows)} anchors -> {args.out}")
    elif args.cmd == "run":
        if args.plan:
            anchors = json.loads(Path(args.anchors).read_text(encoding="utf-8"))
            jobs, todo = plan(anchors, Path(args.pool), args.games_per_anchor, args.period)
            print(json.dumps({"games": len(jobs), "member_anchor_pairs": len(todo)}, ensure_ascii=False))
        else:
            print(json.dumps(run(Path(args.anchors), Path(args.pool), Path(args.out), args.games_per_anchor,
                                 args.workers, args.mask, period=args.period), ensure_ascii=False, indent=1))
    elif args.cmd == "report":
        print(json.dumps(report(Path(args.out), Path(args.anchors), args.period), ensure_ascii=False, indent=1))
    elif args.cmd == "classes":
        period, rows = classes(Path(args.out), args.period)
        print(json.dumps({"period": period, "classes": rows}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
