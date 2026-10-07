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
import os
import time
from multiprocessing import Pool

from svsim.tools.gate import cr_text, play_pair, summary


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
        s0 = sum(d["points"][0] for d in rows) / len(rows)
        s1 = sum(d["points"][1] for d in rows) / len(rows)
        print(f"{2 * len(rows)} 局（{len(rows)} 对）：A 得分 {mean:.1%} ± {margin:.1%}"
              f"（95% 区间 {mean - margin:.1%}～{mean + margin:.1%}），{cr_text(mean, margin)}；"
              f"A 先手 {s0:.1%}、后手 {s1:.1%}", flush=True)

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
