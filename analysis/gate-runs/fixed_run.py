"""Play a fixed number of the gate's pairs (no sequential stop) and report an unbiased interval.

    cd <svsim checkout> && PYTHONPATH=. python3 fixed_run.py --a SPEC --b SPEC --pairs 300 --seed 2000000 --out FILE

Uses svsim.tools.gate's own pair player (same seeds, seat swap and scoring),
so the games are the gate's; only the stopping rule differs: all pairs are
played, so the score's interval is not biased by stopping at a boundary.
Resumes from --out.
"""
import argparse
import inspect
import json
import math
import os
import random
import time
from multiprocessing import Pool

from svsim.tools.gate import cr_text, play_pair, summary

SALEM_CR_PER_LOGIT = 236.0     # Salem: a 200 CR gap wins about 70% (the report scale since 2026-10-07)


def salem_cr(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return SALEM_CR_PER_LOGIT * math.log(p / (1 - p))


def first_seat(seed: int) -> int:
    """The seat that goes first in the gate's games of this seed: engine.new_game with first=None
    draws it as the first number of random.Random(seed)."""
    return random.Random(seed).randrange(2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--deck", default="ramp")
    p.add_argument("--opponent", default="ramp")
    p.add_argument("--pairs", type=int, default=300)
    p.add_argument("--seed", type=int, default=2_000_000)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--every", type=int, default=50, help="report every this many pairs")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    done = {}
    if os.path.exists(args.out):
        for line in open(args.out, encoding="utf-8"):
            d = json.loads(line)
            done[d["k"]] = d

    def report():
        rows = [d for _, d in sorted(done.items())]
        scores = [sum(d["points"]) / 2 for d in rows]
        mean, margin = summary(scores)
        # points[i] is A in seat i; who goes first comes from the seed, not the seat
        firsts = [first_seat(d["seed"]) for d in rows]
        s_first = sum(d["points"][f] for d, f in zip(rows, firsts)) / len(rows)
        s_second = sum(d["points"][1 - f] for d, f in zip(rows, firsts)) / len(rows)
        print(f"{2 * len(rows)} 局（{len(rows)} 对）：A 得分 {mean:.1%} ± {margin:.1%}"
              f"（95% 区间 {mean - margin:.1%}～{mean + margin:.1%}），"
              f"CR 约 {salem_cr(mean):+.0f}（{salem_cr(mean - margin):+.0f}～{salem_cr(mean + margin):+.0f}，Salem 刻度；"
              f"稳态式：{cr_text(mean, margin)}）；A 先手 {s_first:.1%}、后手 {s_second:.1%}", flush=True)

    # the gate's pair job gained two fields (each side's +phased model folder) in later svsim
    extra = (None, None) if "phased_a" in inspect.getsource(play_pair) else ()
    todo = [(k, args.seed + k, args.a, args.b, None, None, args.deck, args.opponent) + extra
            for k in range(args.pairs) if k not in done]
    t0 = time.time()
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for res in pool.imap_unordered(play_pair, todo):
            done[res["k"]] = res
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            if len(done) % args.every == 0:
                print(f"  …{2 * len(done)} 局 {time.time() - t0:.0f}s", flush=True)
                report()
    report()


if __name__ == "__main__":
    main()
