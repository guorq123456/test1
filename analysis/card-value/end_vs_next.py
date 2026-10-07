"""How far the evaluation world is from real game results: G_end against G_next, raw and corrected for noise.

    python3 end_vs_next.py END_ROWS.jsonl [--boot 2000]

END_ROWS is realized_end.py's output: each item has G (G_next: the two-turn value by mcts-raw:400 at the
start of the own next turn, realized.py), G_end (both arms played to the end by v2, common random
numbers), each measured on two independent halves of the determinizations (G1 / G2, G_end1 / G_end2),
and the teacher's T and the control Q.

Both labels are noisy, G_end much more (a game result is 0 or 1; 4 games a half). And G_end and G_next
are measured on the same determinizations with the same agent seeds: up to the start of the own next
turn the two follow the same path, so their sampling noise is shared and the raw correlation of the
full measures overstates their agreement (and a plain correction for attenuation, which assumes
independent errors, goes above 1). So the comparison that counts is across halves, whose
determinizations are independent:
- r_cross = mean of r(G_end half 1, G_next half 2) and r(G_end half 2, G_next half 1);
- the halves' own agreement, r(G_end1, G_end2) and r(G1, G2);
- the correlation of the true values, corrected for attenuation: r_cross / sqrt(r_end12 * r_next12).
For the teacher (its own determinizations, independent of both labels): r(T, label half) averaged over
the halves, divided by sqrt(r12 of that label). Spearman (ranks) and Pearson (values) both; G_end has
many ties at 0, which weighs on ranks. 95% intervals from resampling items.
"""
import json
import math
import random
import sys

import numpy as np

from analyse import spearman


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def numbers(rows):
    col = lambda k: [x[k] for x in rows]
    out = {}
    for tag, r in (("秩", spearman), ("值", pearson)):
        out[f"{tag} r(G_end,G_next) 同一批确定化"] = r(col("G_end"), col("G"))
        cross = (r(col("G_end1"), col("G2")) + r(col("G_end2"), col("G1"))) / 2
        e12, n12 = r(col("G_end1"), col("G_end2")), r(col("G1"), col("G2"))
        out[f"{tag} r_cross(G_end,G_next)"] = cross
        out[f"{tag} r(G_end1,G_end2)"] = e12
        out[f"{tag} r(G1,G2)"] = n12
        out[f"{tag} 真值相关(G_end,G_next)"] = cross / math.sqrt(e12 * n12) if e12 > 0 and n12 > 0 else float("nan")
        t_end = (r(col("T"), col("G_end1")) + r(col("T"), col("G_end2"))) / 2
        t_next = (r(col("T"), col("G1")) + r(col("T"), col("G2"))) / 2
        out[f"{tag} r(T,G_end 半组)"] = t_end
        out[f"{tag} 真值相关(T,G_end)"] = t_end / math.sqrt(e12) if e12 > 0 else float("nan")
        out[f"{tag} 真值相关(T,G_next)"] = t_next / math.sqrt(n12) if n12 > 0 else float("nan")
    return out


def main():
    rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
    boots = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 2000
    point = numbers(rows)
    rng = random.Random(11)
    samples = {k: [] for k in point}
    for _ in range(boots):
        b = numbers([rows[rng.randrange(len(rows))] for _ in rows])
        for k, v in b.items():
            if math.isfinite(v):
                samples[k].append(v)
    print(f"{len(rows)} 项")
    for k, v in point.items():
        s = np.array(samples[k])
        lo, hi = (np.percentile(s, 2.5), np.percentile(s, 97.5)) if len(s) else (float("nan"),) * 2
        print(f"  {k:<26} {v:+.3f}（{lo:+.3f}～{hi:+.3f}）")


if __name__ == "__main__":
    main()
