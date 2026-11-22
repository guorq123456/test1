"""Made-up probes of Salem's ruling S2 (11-22: never matched past 200), no game played (LD-22, LD-24).

    python tools/probe_far_rule.py [--out probe/far-rule-2026-11-22.json]

1. Frozen-pool evaluator at the edge: a frozen field at the 11-21 baseline's relative CRs (+271, +250, +155, +46, -8,
   -97 over 1500), a candidate of known true level T at or past the strongest (or the weakest) member; P(candidate
   beats a member at CR c) = 0.5 + (T - c) / 800 (8 CR a point, §3), clipped to 5-95%. 200 repeats of 1200 games,
   last 600, per T. Rule "wait" (S2 strictly: nobody within 200 -> the repeat stops, the rest counted at that CR)
   against "closest" (A28: nobody within 200 -> the closest member). Reports the mean reading minus T.
2. Small live pools: made-up pools of 3 and 7 members (strengths +5, 0, -5 pp, the rest 0; P = 0.5 + s_a - s_b),
   how soon no two members are within 200 (stalled), and how often someone has nobody within 200.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[2])]

from ladder import evaluator as E  # noqa: E402
from ladder import pool as P  # noqa: E402
from ladder import rules  # noqa: E402

FIELD = [271, 250, 155, 46, -8, -97]


def one_repeat(others, mu, T, games, tail, rng, far):
    cand = E.Candidate("c", 0, [], "")
    cr, crs, n_far = round(mu), [], 0
    while len(crs) < games:
        try:
            opp, how = P.pick_opponent(cand, others, mu, rng, cr=cr, far=far)
        except P.NoOpponent:
            crs += [cr] * (games - len(crs))
            break
        n_far += how == "far"
        won = rng.random() < min(0.95, max(0.05, 0.5 + (T - opp.cr) / 800))
        cr += rules.delta(cr, opp.cr, won)
        crs.append(cr)
    return sum(crs[-tail:]) / tail, n_far


def edge(n=200, games=1200, tail=600):
    frozen = [E.Frozen(mid=f"f{i}", anon="", craft=i % 7 + 1, cr=1500 + r, deck=[], strategy="")
              for i, r in enumerate(FIELD)]
    others, mu = E.opponents_for(frozen, None)
    top, bottom = max(f.cr for f in others), min(f.cr for f in others)
    rows = []
    for side, ref, gaps in (("top", top, (-100, 0, 50, 100, 150)), ("bottom", bottom, (0, -50, -100))):
        for g in gaps:
            T = ref + g
            row = {"side": side, "true_minus_edge": g}
            for far in ("wait", "closest"):
                out = [one_repeat(others, mu, T, games, tail, random.Random(k), far) for k in range(n)]
                row[far] = {"bias": round(st.mean(v for v, _ in out) - T, 1),
                            "sd": round(st.stdev(v for v, _ in out), 1),
                            "games_past_200": round(sum(f for _, f in out) / (n * games), 4)}
            rows.append(row)
    return rows


def small_pools(sizes=(3, 7), runs=5, games=8000):
    from svsim.cards.decks import random_deck
    from svsim.core.enums import Craft
    out = []
    for k in sizes:
        strengths = [0.05, 0.0, -0.05] + [0.0] * (k - 3)
        for seed in range(runs):
            pool = P.Pool.create(None, (1, 10 ** 7), rng_seed=3 + seed)
            for i in range(k):
                deck = [c.card_id for c in random_deck(Craft(i % 7 + 1), random.Random(99001700 + i))]
                pool.enter(deck, "bot:greedy", "baseline", rng=random.Random(50 + i))
            s = {m.mid: strengths[i] for i, m in enumerate(pool.active())}
            rng = random.Random(4 + seed)
            iso, n, stalled = 0, 0, None
            for n in range(games):
                try:
                    job = pool.next_job()
                except P.Stalled:
                    stalled = n
                    break
                a, b = job["labels"]["members"]
                pool.settle({"id": job["id"], "result": "normal",
                             "winner": 0 if rng.random() < 0.5 + s[a] - s[b] else 1})
                iso += bool(pool.isolated())
            out.append({"members": k, "run": seed, "stalled_after": stalled,
                        "share_with_someone_isolated": round(iso / max(1, n), 4),
                        "crs": sorted(m.cr for m in pool.active())})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    res = {"field": FIELD, "edge": edge(), "small_pools": small_pools()}
    text = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
