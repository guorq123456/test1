"""Statistical checks of the leaderboard and the frozen-pool evaluator on made-up games (phase 1, pre-check before
the real-game sanity checks). No game is played: each "game" is a coin with a known win probability, so the true
strengths are known and runs are cheap.

    python tools/check_stats.py [--pools 40] [--evals 20] [--seed 20261121] [--out FILE]

Model: 21 members, 3 per class, strengths -6, 0, +6 percentage points; P(a beats b) = 0.5 + s_a - s_b.
1. Leaderboard fluctuation: `--pools` independent pools of 31,500 games (each member ~3000 games); per member, the
   spread of its leaderboard value across pools divided by the mean standard error the leaderboard reported.
2. Evaluator fluctuation (plan 阶段 1 波动检查): one candidate (strength 0) evaluated `--evals` times against one frozen
   pool (CRs fixed at the pools' long-run values), 5 repeats x 1200 games, last 600; spread of the evaluations
   divided by the mean reported standard error. Should be in 0.7-1.4.
3. Known strengths: candidates at -6, -3, 0, +3, +6, +12 pp through the evaluator; their order, and the CR per
   percentage point their gaps imply.
4. Removals: how often a member is removed (CR <= mu - 300) by strength, in check 1.
Not a substitute for the real-game checks: real games have draws, class matchups and strategies whose strength
depends on the opponent.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[2])]

from ladder import evaluator as E  # noqa: E402
from ladder import leaderboard as L  # noqa: E402
from ladder import pool as P  # noqa: E402

STRENGTHS = [(c, s) for c in range(1, 8) for s in (-0.06, 0.0, 0.06)]
_DECKS = {}


def deck(craft, i):
    from svsim.cards.decks import random_deck
    from svsim.core.enums import Craft
    if (craft, i) not in _DECKS:
        _DECKS[(craft, i)] = [c.card_id for c in random_deck(Craft(craft), random.Random(99001700 + 100 * craft + i))]
    return _DECKS[(craft, i)]


def prob(sa, sb):
    return min(0.98, max(0.02, 0.5 + sa - sb))


def made_up_pool(strengths, rng_seed):
    series = L.Series()
    pool = P.Pool.create(None, (10 ** 12, 2 * 10 ** 12), rng_seed=rng_seed, on_event=series)  # never played
    for i, (craft, _) in enumerate(strengths):
        pool.enter(deck(craft, i), "made-up", "baseline", rng=random.Random(i))
    for m in pool.active():
        m.full_strategy_period = True          # protection only by games (the made-up pool has no periods)
    return pool, series, {m.mid: strengths[i][1] for i, m in enumerate(pool.active())}


def play_pool(pool, games, strength, rng):
    for _ in range(games):
        job = pool.next_job()
        a, b = job["labels"]["members"]
        pool.settle({"id": job["id"], "result": "normal",
                     "winner": 0 if rng.random() < prob(strength[a], strength[b]) else 1})


def check_leaderboard(pools, seed):
    per, removed, long_run = {}, {}, {}
    for r in range(pools):
        pool, series, strength = made_up_pool(STRENGTHS, seed + r)
        play_pool(pool, 21 * 3000 // 2, strength, random.Random(seed + 10_000 + r))
        for m in pool.members.values():
            if not m.active:
                removed[strength[m.mid]] = removed.get(strength[m.mid], 0) + 1
        for row in L.board(pool, series):
            if row["ranked"]:
                per.setdefault(row["mid"], []).append((row["rel_cr"], row["se"], row["se_batch"]))
                long_run.setdefault(strength[row["mid"]], []).append(row["rel_cr"])
    ratio = [st.stdev([x[0] for x in v]) / st.mean([x[1] for x in v]) for v in per.values() if len(v) > 5]
    ratio_b = [st.stdev([x[0] for x in v]) / st.mean([x[2] for x in v]) for v in per.values() if len(v) > 5]
    return {"pools": pools, "ratio_tau": {"mean": round(st.mean(ratio), 3), "min": round(min(ratio), 3),
                                          "max": round(max(ratio), 3)},
            "ratio_batch_means": {"mean": round(st.mean(ratio_b), 3)},
            "rel_cr_by_strength": {f"{s * 100:+.0f}pp": round(st.mean(v), 1) for s, v in sorted(long_run.items())},
            "removed_by_strength": {f"{s * 100:+.0f}pp": f"{removed.get(s, 0)} of {pools * 7}"
                                    for s in (-0.06, 0.0, 0.06)}}


def frozen_pool(rel_by_strength):
    out = []
    for i, (craft, s) in enumerate(STRENGTHS):
        rel = rel_by_strength[s]
        out.append(E.Frozen(mid=f"f{i:02d}", anon="", craft=craft, cr=round(1500 + rel), deck=deck(craft, i),
                            strategy="made-up"))
    return out


def check_evaluator(evals, seed, rel_by_strength, cand_strengths=(0.0,), repeats=5, games=1200, tail=600):
    frozen = frozen_pool(rel_by_strength)
    strength = {f.mid: STRENGTHS[i][1] for i, f in enumerate(frozen)}
    others, mu = E.opponents_for(frozen, None)
    out = {}
    for cs in cand_strengths:
        results = []
        for e in range(evals):
            vals = []
            for r in range(repeats):
                rng = random.Random(f"{seed}:{cs}:{e}:{r}")
                vals.append(E.repeat_sync(lambda opp, g: g.random() < prob(cs, strength[opp.mid]), others, mu,
                                          games, tail, rng))
            results.append(E.summarize(vals))
        means = [x["rel_cr"] for x in results]
        out[f"{cs * 100:+.0f}pp"] = {"mean": round(st.mean(means), 1),
                                    "sd_of_evals": round(st.stdev(means), 2) if evals > 1 else None,
                                    "mean_reported_se": round(st.mean(x["se"] for x in results), 2),
                                    "ratio": round(st.stdev(means) / st.mean(x["se"] for x in results), 3)
                                    if evals > 1 else None,
                                    "covered": sum(x["lo"] <= st.mean(means) <= x["hi"] for x in results)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pools", type=int, default=40)
    ap.add_argument("--evals", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261121)
    ap.add_argument("--out")
    a = ap.parse_args()
    t0 = time.time()
    lb = check_leaderboard(a.pools, a.seed)
    rel = {s: lb["rel_cr_by_strength"][f"{s * 100:+.0f}pp"] for s in (-0.06, 0.0, 0.06)}
    ev = check_evaluator(a.evals, a.seed, rel)
    known = check_evaluator(3, a.seed + 1, rel, cand_strengths=(-0.06, -0.03, 0.0, 0.03, 0.06, 0.12))
    xs = [-6, -3, 0, 3, 6, 12]
    ys = [known[f"{x:+d}pp"]["mean"] for x in xs]
    slope = sum((x - st.mean(xs)) * (y - st.mean(ys)) for x, y in zip(xs, ys)) / sum((x - st.mean(xs)) ** 2
                                                                                     for x in xs)
    out = {"model": "21 members, 3 per class at -6/0/+6 pp; P = 0.5 + s_a - s_b", "seed": a.seed,
           "leaderboard": lb, "evaluator_fluctuation": ev, "known_strengths": known,
           "known_order_right": ys == sorted(ys), "cr_per_pp_fit": round(slope, 2),
           "seconds": round(time.time() - t0)}
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
