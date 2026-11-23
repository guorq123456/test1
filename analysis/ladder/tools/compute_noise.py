"""How noisy is the receipt's compute ratio (A52: the cap 1.08x the default's per-step CPU; S15: refused above 1.15x)?

    python analysis/ladder/tools/compute_noise.py --sets 40 --seeds 92796000 92800000 --workers 3 --out noise.json

The receipt's smoke games are pairs on the same deals, seats and strategy seeds: once with the submission, once
with the default strategy (its "twin"). Two ways to compare their per-step CPU, both measured here:
- twins (LD-55, the old way): the submission's games over the twins'. The two go their own ways once the
  decisions differ, so they are compared on different positions.
- shadow (LD-56, what receive does now): the submission's games over the default strategy replayed move for move
  on the submission's own games (submit._shadow): the same positions. Its twin game is replayed too, in the same
  batch: twin game and twin shadow are the same computation, so their ratio is what a step costs in a game against
  in a shadow just then, and the submission's ratio is divided by it ("shadow"; "shadow_raw" is without that).
Here the "submission" is the default strategy itself with another strategy seed for its own seat: the same cost per
step, other random choices; about 60% of its games still repeat the twin's moves, so the twins' figures are also
given on the games that went their own way ("diverged"), as a real submission's do. The shadow uses the twin's
seeds (other random choices than the stand-in's, as a real submission's code would be). Every set of 10 pairs is
laid out like submit.smoke_jobs. Whole pairs are resampled to see the spread for n pairs and how often a
submission that truly costs k x the default would be refused. --standin adaptive / overhead (tools/standins.py)
put a strategy whose cost against the default's changes with the position in the submission's seat instead (on the
twin's seeds, as receive): the spread is then the measurement's for such a strategy (LD-57; centred on its own
sample ratio, its true one being unknown).

A measurement of the tool only: these games say nothing about strength.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as S
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))                                   # tools/standins.py (spawned workers get sys.path)

from ladder import base  # noqa: E402
from ladder.runner import run  # noqa: E402
from ladder.runner import guarded_map  # noqa: E402
from ladder.submit import DEFAULT, COMPUTE_CAP, COMPUTE_REFUSE, pooled_ratio, shadow_rows, shadow_task  # noqa: E402


STANDINS = {"seed": None, "adaptive": "py:standins:Adaptive", "overhead": "py:standins:Overhead"}


def jobs_for(sets: int, seeds: tuple[int, int], rng: random.Random, games: int = 10, exclude=frozenset(),
             standin: str = "seed"):
    lists = base.baseline_lists()
    crafts = sorted(lists)
    free = [s for s in range(*seeds) if s not in exclude]
    if len(free) < sets * games:
        raise SystemExit(f"{sets} sets need {sets * games} seeds; {seeds[0]}-{seeds[1] - 1} has {len(free)} unused")
    pool = rng.sample(free, sets * games)
    jobs = []
    for s in range(sets):
        mine = list(lists[crafts[s % len(crafts)]])
        for i in range(games):
            seed = pool[s * games + i]
            seat = i % 2
            opp = list(lists[crafts[i % len(crafts)]])
            sseeds = [rng.randrange(1, 2 ** 31), rng.randrange(1, 2 ** 31)]
            other = list(sseeds)
            other[seat] = rng.randrange(1, 2 ** 31)                 # same strategy, other seed for its own seat
            spec = STANDINS[standin]
            for side, ss in (("sub", other if spec is None else sseeds), ("default", sseeds)):
                sides = [mine, opp] if seat == 0 else [opp, mine]
                strategies = [DEFAULT, DEFAULT]
                if side == "sub" and spec is not None:
                    strategies[seat] = spec                          # a stand-in of another cost, receive's seeds
                jobs.append({"id": f"set{s:03d}-g{i:02d}-{side}", "seed": seed, "first": None, "decks": sides,
                             "strategies": strategies, "strategy_seeds": ss,
                             "labels": {"set": s, "game": i, "side": side, "seat": seat}})
    return jobs


def summary(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return {"n": 0}
    q = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
    return {"n": len(xs), "mean": round(S.fmean(xs), 4), "sd": round(S.stdev(xs), 4) if len(xs) > 1 else None,
            "min": round(xs[0], 4), "p05": round(q(0.05), 4), "median": round(q(0.5), 4), "p95": round(q(0.95), 4),
            "max": round(xs[-1], 4), "over": {str(t): sum(1 for x in xs if x > t) for t in (COMPUTE_CAP, COMPUTE_REFUSE)}}


def bootstrap(rows, sizes=(10, 20, 30, 50, 100, 200), scales=(1.0, 1.03, 1.05, 1.08, 1.1), draws=20000, seed=5):
    """Resample whole pairs (rows: submission CPU, its steps, default CPU, its steps): the pooled ratio's spread
    for a measurement of n pairs, and how often it lands over the cap when the submission really costs `scale`
    times the default. The stand-in costs the same as the default by construction, so the whole sample is centred
    on 1.0 first (its own small offset is noise too)."""
    if len(rows) < 2:
        return {"pairs": len(rows)}
    rng = random.Random(seed)
    r0 = pooled_ratio(rows)
    out = {"pairs": len(rows), "sample_ratio": round(r0, 4)}
    for n in sizes:
        rs = []
        for _ in range(draws):
            t = [0, 0, 0, 0]
            for _ in range(n):
                r = rows[rng.randrange(len(rows))]
                for i in range(4):
                    t[i] += r[i]
            rs.append((t[0] / t[1]) / (t[2] / t[3]) / r0)
        rs.sort()
        out[n] = {"sd": round(S.stdev(rs), 4), "p95": round(rs[int(0.95 * draws)], 4),
                  "over": {str(t): {str(k): round(sum(1 for x in rs if x * k > t) / draws, 4) for k in scales}
                           for t in (COMPUTE_CAP, COMPUTE_REFUSE)}}
    return out


def method(rows_by_set: dict) -> dict:
    rows = [r for v in rows_by_set.values() for r in v]
    return {"per_10": summary([pooled_ratio(v) for v in rows_by_set.values()]), "bootstrap": bootstrap(rows)}


def _jsonl(p: Path) -> list:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--sets", type=int, default=40)
    a.add_argument("--seeds", type=int, nargs=2, required=True)
    a.add_argument("--workers", type=int, default=3)
    a.add_argument("--mask", type=lambda x: int(x, 0), default=None)
    a.add_argument("--rng-seed", type=int, default=1)
    a.add_argument("--standin", choices=sorted(STANDINS), default="seed",
                   help="seed: the default with another seed (the same cost everywhere); adaptive / overhead: "
                        "tools/standins.py, a cost that changes with the position (LD-57)")
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--analyze-only", action="store_true",
                   help="play nothing: read the games (and the shadows, if there) already there")
    a.add_argument("--shadow-only", action="store_true", help="the games are there already: only replay the shadows")
    a.add_argument("--exclude", type=Path, action="append", default=[],
                   help="a games file of an earlier run, or a .txt of seeds: those are never drawn again")
    args = a.parse_args()
    rng = random.Random(args.rng_seed)
    used = set()
    for p in args.exclude:                         # a games file of an earlier run, or a list of seeds (one a line)
        if p.suffix == ".txt":
            used |= {int(x) for x in p.read_text(encoding="utf-8").split() if x.isdigit()}
        else:
            used |= {g["seed"] for g in _jsonl(p)}
    jobs = jobs_for(args.sets, tuple(args.seeds), rng, exclude=used, standin=args.standin)
    games, shadows = args.out.with_suffix(".games.jsonl"), args.out.with_suffix(".shadows.jsonl")
    t0 = time.time()
    if not (args.analyze_only or args.shadow_only):
        if games.exists():
            raise SystemExit(f"{games} is there already: --analyze-only / --shadow-only, or another --out")
        run(jobs, str(games), workers=args.workers, mask=args.mask, quiet=True)
    logs = {g["id"]: g for g in _jsonl(games)}
    pairs = []
    for j in jobs:
        if j["labels"]["side"] != "sub":
            continue
        sub, ref = logs.get(j["id"]), logs.get(j["id"].replace("-sub", "-default"))
        if sub and ref and sub.get("result") in ("normal", "draw") and ref.get("result") in ("normal", "draw"):
            pairs.append((j["labels"]["set"], j["labels"]["seat"], sub, ref))
    if not args.analyze_only and (args.shadow_only or not shadows.exists()):
        # as receive: the submission's game and its twin one after the other, both on the pair's seeds (the stand-in
        # played its own seat on another seed, so its shadow makes other random choices, as a real submission's)
        tasks = [t for _, seat, sub, ref in pairs
                 for t in (shadow_task(sub, seat, seeds=ref["strategy_seeds"]), shadow_task(ref, seat))]
        got = guarded_map("ladder.submit:_shadow", tasks, workers=args.workers, mask=args.mask)
        shadows.write_text("".join(json.dumps(g) + "\n" for g in got), encoding="utf-8")
    got = _jsonl(shadows) if shadows.exists() else []
    if got and len(got) != 2 * len(pairs):
        raise SystemExit(f"{shadows}: {len(got)} shadows for {len(pairs)} pairs (two each): an old file? --shadow-only")
    twins, diverged, shadow, raw, env = {}, {}, {}, {}, []
    steps_ref, same = [], 0
    for _, seat, sub, ref in pairs:
        steps_ref += [c for s, c, _ in ref["steps"] if s == seat]
        same += sub["actions"] == ref["actions"]
    for (st, seat, sub, ref) in pairs:
        a_ = [c for s, c, _ in sub["steps"] if s == seat]
        b_ = [c for s, c, _ in ref["steps"] if s == seat]
        twins.setdefault(st, []).append((sum(a_), len(a_), sum(b_), len(b_)))
        if sub["actions"] != ref["actions"]:
            diverged.setdefault(st, []).append((sum(a_), len(a_), sum(b_), len(b_)))
    bad = []
    if got:
        for i, (st, seat, sub, ref) in enumerate(pairs):
            rows, b = shadow_rows([(sub, ref, seat)], got[2 * i:2 * i + 2])
            bad += b
            if rows:
                shadow.setdefault(st, []).append(rows[0])
                raw.setdefault(st, []).append((rows[0][0], rows[0][1], 1, 1))
                env.append(rows[0][2] / rows[0][3])
    allsh = [r for v in shadow.values() for r in v]
    unit = next(iter(logs.values())).get("cpu_unit")
    scale = 1e6 if unit == "ns" else 1
    out = {"standin": args.standin, "sets": args.sets, "pairs": len(pairs), "identical_games": same, "cpu_unit": unit,
           "wall_s": None if args.analyze_only else round(time.time() - t0),
           "default_step": {"mean": round(S.fmean(steps_ref) / scale, 2), "median": round(S.median(steps_ref) / scale, 2),
                            "unit": "ms" if unit == "ns" else unit},
           "shadow": method(shadow) | {"pairs_back": sum(len(v) for v in shadow.values()), "problems": bad[:10]},
           "shadow_raw": method(raw),
           "game_over_shadow": summary(env) | {"pooled": round(sum(r[2] for r in allsh) / sum(r[3] for r in allsh), 4)
                                               if allsh else None},
           "twins": method(twins), "twins_diverged": method(diverged)}
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
