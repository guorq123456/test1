"""Anchor matches (plan 评判 3rd item: 「对池外固定锚点的成绩」, answers "did it really get stronger"): once a period,
every member of the pool against every anchor, on fresh seeds (Salem's S11, 11-22: 「每期全员重打，按职业公布」).

    python -m ladder.anchors induct POOL --hof HOF.json [--period N]     # end of a period: the hall of fame
    python -m ladder.anchors table --out ANCHORS.json [--hof HOF.json]
    python -m ladder.anchors run ANCHORS.json --pool POOL --out DIR --code SUBS\\code [--period N]
                                 [--games-per-anchor 10] [--plan] [--workers 23]
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
member plays the same number of games and the counts tell nothing. Seeds: the segment 93510000-94509999 is used up
in order, one seed a game, each period right after the seeds the earlier periods' plans took, in a fixed order
(members by id, anchors by slot, game index); every game is dealt through the host's key (base-2). Before a game is
played every received strategy's module must be found (`--code`, the received submissions; it is looked up, not run),
every host strategy must build and every deck's cards must have scripts.
A period is played once: its plan is written first (DIR/plan-P<P>.json); an interrupted run picks up its own games;
a game voided in a way that may be the setup's or the machine's (a strategy that didn't load, a dead worker, a runner
error) is played once more on its own seed (once per game, however many runs it takes), and if it voids again it is
written down as void and reported, like an engine error; a changed pool or panel is refused. The period's ledger lines (DIR/anchors.jsonl,
append-only, one per member version and anchor) go in one write, on a line of their own, and the period counts once
its plan file names that write and its number of lines ("done", "lines"). The public figures are per class and
tier, rounded, without counts (`classes`); the per-member rows stay with the host. The fixed panel of seeds
91700000-91799999 that played each version once (A40) is no longer used.
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

ANCHOR_SEEDS = (93510000, 94510000)  # S11: fresh seeds every period, used up in order (seed ledger c61debe, SEEDS.md)
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


def _jsonl(f: Path) -> list[dict]:
    """The lines of an append-only JSON-lines file, skipping a line torn by a stop (or NUL padding after a crash)."""
    out = []
    if f.exists():
        for x in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                v = json.loads(x.strip("\x00").strip())
            except ValueError:
                continue
            if isinstance(v, dict):
                out.append(v)
    return out


def _ledger(out: Path) -> list[dict]:
    return _jsonl(Path(out) / "anchors.jsonl")


def _plans(out: Path) -> dict:
    """period -> its plan file (plan-P<P>.json): the seeds it took and, once the ledger lines are written, "done"."""
    plans = {}
    for f in Path(out).glob("plan-P*.json"):
        v = json.loads(f.read_text(encoding="utf-8"))
        plans[v["period"]] = v
    return plans


def _write_json(path: Path, value) -> None:
    import os
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=1))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


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


def _first_seed(out, period: int) -> int:
    """Where period's seeds start: its own plan's if it has one, else right after every seed any plan took
    (the segment is used up in order, period after period, with no gaps and no reuse)."""
    plans = _plans(out) if out is not None else {}
    if period in plans:
        return plans[period]["first_seed"]
    return max((p["first_seed"] + p["jobs"] for p in plans.values()), default=ANCHOR_SEEDS[0])


def plan(anchors: list[dict], pool_dir: Path, games: int, period=None, out=None):
    """This period's games (S11, A48): every active member's current version against every anchor, `games` each,
    seats alternating, one fresh seed a game in a fixed order (members by id, anchors by slot, game index), from
    where the earlier periods' plans in `out` stopped."""
    pool, period = _period_of(pool_dir, period)
    if period < 0:
        raise AnchorError(f"第 {period} 期？")
    base = _first_seed(out, period)
    members = sorted(pool.active(), key=lambda m: m.mid)
    panel = sorted(anchors, key=lambda a: a["slot"])
    n = len(members) * len(panel) * games
    if base + n > ANCHOR_SEEDS[1]:
        raise AnchorError(f"锚点种子段（{ANCHOR_SEEDS[0]}～{ANCHOR_SEEDS[1] - 1}）只剩 {ANCHOR_SEEDS[1] - base} 个，这一期要 {n} 个"
                          f"（{len(members)} 个成员 × {len(panel)} 个锚点 × {games} 局）：先在项目登记表上登记新的一段")
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


SETUP_VOIDS = ("cards with no script", "strategy failed to load", "runner error", "worker died",
               "the strategies took more than", "the check after the game ran past")     # the last two: LD-40
# voids that may come from the host's setup or the machine rather than the game: played once more, on their own seeds
# (a new games-P<P>-redo<k>.jsonl), once per game whatever happens to the runs. One that voids again is deterministic (a factory that fails on
# that seed, a process ended by one of the strategies, a bug in the runner): it is written down as void like
# "engine error ..." and reported (red line: 发现了就记录并报告); the period is never held up by it (11-22 re-review)


def _setup_void(g: dict) -> bool:
    return g.get("result") == "void" and str(g.get("error", "")).startswith(SETUP_VOIDS)


def _use_code(code) -> None:
    """Put the received submissions (subs/code) where the workers import strategies from, as submit gate and puzzles
    run do."""
    import os
    if code is None:
        return
    c = str(Path(code).resolve())
    if not Path(c).is_dir():
        raise AnchorError(f"没有这个目录：{c}（收下的打法在 C:\\claude\\ladder-host\\subs\\code）")
    if c not in sys.path:
        sys.path.insert(0, c)
    os.environ["LADDER_EXTRA_PATH"] = os.pathsep.join(x for x in (c, os.environ.get("LADDER_EXTRA_PATH", "")) if x)


def preflight(jobs: list[dict]) -> list[str]:
    """What can't work at all, before a game is played: a received strategy whose module isn't on the paths (most
    likely a missing --code), a host strategy that doesn't build, a deck with unscripted cards. A received module is
    only looked up, not run: its code runs in the workers, where a failure is that game's void (11-22 third pass)."""
    import importlib.util
    import os
    from ladder.runner import load_deck, make_strategy, unscripted
    for extra in filter(None, os.environ.get("LADDER_EXTRA_PATH", "").split(os.pathsep)):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    bad = []
    for spec in sorted({s for j in jobs for s in j["strategies"]}):
        try:
            if spec.startswith("py:"):
                module = spec.split(":", 2)[1]
                if importlib.util.find_spec(module) is None:
                    bad.append(f"找不到打法 {spec} 的模块 {module}")
            else:
                make_strategy(spec, 1)                # host strategies (bot:, mix:)
        except Exception as e:                        # noqa: BLE001
            bad.append(f"打法 {spec} 载入失败：{type(e).__name__}: {e}")
    for d in sorted({json.dumps(d) for j in jobs for d in j["decks"]}):
        miss = unscripted(load_deck(json.loads(d)))
        if miss:
            bad.append(f"卡组里有没写脚本的卡 {miss}")
    return bad


def run(anchors_path: Path, pool_dir: Path, out: Path, games: int = 10, workers=4, mask=None, step_limit=30.0,
        key="auto", period=None, code=None) -> dict:
    import hashlib
    import os
    from ladder import runner
    anchors = json.loads(Path(anchors_path).read_text(encoding="utf-8"))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _, period = _period_of(pool_dir, period)
    plans = _plans(out)
    if plans.get(period, {}).get("done"):
        raise AnchorError(f"第 {period} 期的锚点已经打过（每期只打一次，A48）")
    _use_code(code)
    jobs, todo = plan(anchors, pool_dir, games, period, out)
    bad = preflight(jobs)
    if bad:
        raise AnchorError("一局没打，先修好再跑：\n" + "\n".join(bad) +
                          "\n（收下的打法要加 --code C:\\claude\\ladder-host\\subs\\code）")
    digest = hashlib.sha256(json.dumps(jobs, sort_keys=True).encode()).hexdigest()
    pf = out / f"plan-P{period}.json"
    if period in plans:
        if plans[period]["sha256"] != digest:
            raise AnchorError(f"第 {period} 期的锚点开打以后，池子或锚点表变了（{pf.name}）：先查清楚，不要换一批局重打")
    else:
        _write_json(pf, {"period": period, "games": games, "jobs": len(jobs), "first_seed": jobs[0]["seed"] if jobs
                         else _first_seed(out, period), "sha256": digest, "anchors": [a["id"] for a in anchors],
                         "time": time.strftime("%Y-%m-%dT%H:%M:%S")})
    main = out / f"games-P{period}.jsonl"
    redo = sorted(out.glob(f"games-P{period}-redo*.jsonl"), key=lambda f: int(f.stem.rsplit("redo", 1)[1]))
    ids = {j["id"] for j in jobs}

    def read():
        got, tries = {}, {}
        for f in [main] + redo:                       # later files replay earlier setup voids: the last line wins
            for g in _jsonl(f):
                if g.get("id") in ids:
                    got[g["id"]] = g
                    if _setup_void(g):
                        tries[g["id"]] = tries.get(g["id"], 0) + 1
        return got, tries

    deal_ids, played = set(), 0
    if jobs:
        res = runner.run(jobs, str(main), workers=workers, step_limit=step_limit, mask=mask, quiet=True, key=key)
        played += res.get("played") or 0
        deal_ids.add(res.get("deal"))
        got, tries = read()
        stale = [j for j in jobs if j["id"] in got and _setup_void(got[j["id"]]) and tries[j["id"]] == 1]
        if stale:                                     # once per game, ever: on its own seed, in a new file
            f = out / f"games-P{period}-redo{len(redo) + 1}.jsonl"
            res = runner.run(stale, str(f), workers=workers, step_limit=step_limit, mask=mask, quiet=True, key=key)
            played += res.get("played") or 0
            deal_ids.add(res.get("deal"))
            redo.append(f)
            got, _ = read()
    else:
        got = {}
    missing = [j["id"] for j in jobs if j["id"] not in got]
    if missing:
        raise AnchorError(f"第 {period} 期的锚点没打完：缺 {len(missing)} 局。台账没写。再跑同一条命令，只补这些局，用它们原来的种子")
    tier = {a["id"]: a["tier"] for a in anchors}
    per, deals, voids = {}, set(), {}
    for g in got.values():
        lab = g["labels"]
        deals.add((g.get("deal") or {}).get("key"))          # the key id the game was dealt with
        k = (lab["member"], lab["version"], lab["craft"], lab["anchor"])
        d = per.setdefault(k, {"won": 0, "lost": 0, "draw": 0, "void": 0})
        if g["result"] == "void":
            d["void"] += 1
            why = str(g.get("error", "")).splitlines()[0] if g.get("error") else "void"
            voids[why] = voids.get(why, 0) + 1
        elif g.get("winner") is None:
            d["draw"] += 1
        elif g["winner"] == lab["seat"]:
            d["won"] += 1
        else:
            d["lost"] += 1
    if len(deals) > 1:
        raise AnchorError(f"第 {period} 期的锚点局用了不止一种发牌（{sorted(map(str, deals))}）：密钥中途换过，先查清楚")
    deal_id = deals.pop() if deals else None
    import secrets
    batch = f"{digest[:12]}-{time.strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}"
    text = "".join(runner.jsonl({"period": period, "member": mid, "version": ver, "craft": craft, "anchor": aid,
                                 "tier": tier[aid], "games": games, **d,
                                 **dict(zip(("rate", "lo", "hi"), _wilson(d["won"], d["won"] + d["lost"]))),
                                 "logs": [f.name for f in [main] + redo], "deal": deal_id, "batch": batch,
                                 "time": time.strftime("%Y-%m-%dT%H:%M:%S")})
                   for (mid, ver, craft, aid), d in sorted(per.items()))
    led = out / "anchors.jsonl"
    if led.exists() and led.stat().st_size:
        with led.open("rb") as f:
            f.seek(-1, 2)
            if f.read(1) != b"\n":
                text = "\n" + text                     # an earlier write was torn: don't glue the first line to it
    with led.open("a", encoding="utf-8") as f:        # one write; the period counts once its plan file names this
        f.write(text)                                 # batch and its number of lines (below)
        f.flush()
        os.fsync(f.fileno())
    if sum(1 for l in _ledger(out) if l.get("batch") == batch) != len(per):
        raise AnchorError(f"第 {period} 期的台账行没写全（{led.name}）：这一期不算打完，再跑同一条命令重写一批")
    _write_json(pf, dict(_plans(out)[period], done=batch, lines=len(per), done_time=time.strftime("%Y-%m-%dT%H:%M:%S")))
    return {"period": period, "jobs": len(jobs), "pairs": len(todo), "played": played, "deal": deal_id,
            "voids": voids, "first_seed": jobs[0]["seed"] if jobs else None,
            "last_seed": jobs[-1]["seed"] if jobs else None, "log": str(main) if jobs else None}


def _lines(out: Path, period=None) -> tuple[int | None, list[dict]]:
    """The ledger lines of one finished period (default: the last finished one). A period counts once its plan file
    names the batch its lines were written in; lines of an interrupted write, or of the old fixed panel (A40, no
    period), are left out."""
    plans = _plans(out)
    done = {p: v["done"] for p, v in plans.items() if v.get("done")}
    lines = [l for l in _ledger(Path(out)) if l.get("period") in done and l.get("batch") == done[l["period"]]]
    whole = {p for p in done if "lines" not in plans[p] or sum(1 for l in lines if l["period"] == p) == plans[p]["lines"]}
    lines = [l for l in lines if l["period"] in whole]          # a batch missing a line doesn't count
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
    for s in (sys.stdout, sys.stderr):           # a redirected or piped console is cp1252 on Windows (ENVIRONMENT
        try:                                      # pitfall 1; 11-23 review: a player's agent pipes the output)
            s.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:                         # noqa: BLE001
            pass
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
    a.add_argument("--code", help="the received submissions (C:\\claude\\ladder-host\\subs\\code)")
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
            jobs, todo = plan(anchors, Path(args.pool), args.games_per_anchor, args.period, Path(args.out))
            print(json.dumps({"games": len(jobs), "member_anchor_pairs": len(todo),
                              "seeds": [jobs[0]["seed"], jobs[-1]["seed"]] if jobs else None}, ensure_ascii=False))
        else:
            print(json.dumps(run(Path(args.anchors), Path(args.pool), Path(args.out), args.games_per_anchor,
                                 args.workers, args.mask, period=args.period, code=args.code), ensure_ascii=False,
                             indent=1))
    elif args.cmd == "report":
        print(json.dumps(report(Path(args.out), Path(args.anchors), args.period), ensure_ascii=False, indent=1))
    elif args.cmd == "classes":
        period, rows = classes(Path(args.out), args.period)
        print(json.dumps({"period": period, "classes": rows}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
