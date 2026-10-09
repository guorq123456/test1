"""The turnpick gate's parameters (README.md here, "turnpick 的等算力门"; a check for choosing them, not a reading):
on step 1's 1821 training starts, the installed ENDED model's V on seed A's 8 T turn ends (paired by
determinization); per direction A pick the best plan among the allowed kinds, switch when V(best) - V(bot) > Z
paired standard errors (agents.turnpick_agent's rule, margin 0); gain = dG_end(best - bot) (appendix 3's merged
K = 16 where it played that plan, else the original K = 4), 0 when not switched; the mean over all 3642 directions
(per own-turn start), interval by resampling starts (2000, seed 1). The same data choose and measure, so it flatters;
only to compare the choices. Condition: the opponent's deck list is known (order and hand not).

    PYTHONPATH=<svsim>:<this folder>:<analysis>/card-value python3 turnpick_params.py <step 1 dir> gendmore.jsonl out.txt
"""
import json, math, sys, pickle, os
import numpy as np
D, more_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
import step1, student_data as SD
cache = out + ".V.pkl"
if os.path.exists(cache):
    V = pickle.load(open(cache, "rb"))
else:
    V = step1._turn_end_values(f"{D}/selfplay.jsonl", f"{D}/teacher_ends.jsonl.gz", step1._weights({"i": "v2s"}))["i"]
    pickle.dump(V, open(cache, "wb"))
starts = {r["k"]: r for r in SD._lines(f"{D}/starts.jsonl")}
order = {r["k"]: [p["kind"] for p in r["plans"]] for r in SD._lines(f"{D}/plans.jsonl")}
G = {r["k"]: r["results"] for r in SD._lines(f"{D}/gend.jsonl")}
for r in SD._lines(more_path):
    G[r["k"]] = {c: v + r["results"].get(c, []) for c, v in G[r["k"]].items()}
ks = sorted(k for k in starts if starts[k]["split"] == "train" and k in order)
def se_ok(a, b, z):
    d = [x - y for x, y in zip(a, b)]; n = len(d); m = sum(d) / n
    se = math.sqrt(sum((x - m) ** 2 for x in d) / max(n - 1, 1) / n)
    return m > 0 and m > z * se
sets = {"str": {"second", "third", "race"}, "strk": {"second", "third", "race", "keep"},
        "all": {"second", "third", "race", "keep", "save", "noevo", "end"}}
rng = np.random.default_rng(1)
lines = []
for name, allowed in sets.items():
    for z in (0.0, 0.5, 1.0, 1.5):
        per_start = {}
        n_sw = 0; kinds = {}
        for k in ks:
            g = []
            for a in (0, 1):
                cand = [c for c in order[k] if c == "bot" or c.split(":")[0] in allowed]
                best = max(cand, key=lambda c: sum(V[(k, c, a)]) / 8)
                if best != "bot" and se_ok(V[(k, best, a)], V[(k, "bot", a)], z):
                    n_sw += 1; kinds[best.split(":")[0]] = kinds.get(best.split(":")[0], 0) + 1
                    d = [x - y for x, y in zip(G[k][best], G[k]["bot"])]
                    g.append(100 * sum(d) / len(d))
                else:
                    g.append(0.0)
            per_start[k] = g
        arr = np.array([per_start[k] for k in ks])          # (starts, 2)
        m = arr.mean()
        bs = [arr[rng.integers(0, len(ks), len(ks))].mean() for _ in range(2000)]
        sw = arr[arr != 0]
        gain_sw = sum(per_start[k][i] for k in ks for i in (0, 1)) / max(n_sw, 1)
        lines.append(f"{name:5s} Z {z:.1f}: switch {n_sw}/{2*len(ks)} ({n_sw/(2*len(ks)):.1%}), "
                     f"gain per switch {gain_sw:+.2f}, per turn start {m:+.3f} ({np.percentile(bs,2.5):+.3f}..{np.percentile(bs,97.5):+.3f}) "
                     f"kinds {dict(sorted(kinds.items(), key=lambda kv: -kv[1]))}")
        print(lines[-1], flush=True)
open(out, "w").write("\n".join(lines) + "\n")
