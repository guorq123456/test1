"""B-tier c_puct rule (registered in c01d2c5 before this was computed): c* = mean B_U / mean B_P on the holdout
roots, B_U = sum_a (n_a/N) 0.5 sqrt(ln N / max(n_a, 1)), B_P = sum_a (n_a/N) P_a sqrt(N) / (1 + n_a); pick the grid
value nearest in log2, 1 on a tie."""
import json, math, sys
import numpy as np
S = sys.argv[1]
out = {}
for deck in ("ramp", "elft"):
    rows = json.load(open(f"{S}/d8/scan-{deck}.json"))["rows"]
    z = dict(np.load(f"{S}/o1/probs-{deck}.npz"))
    koff, P = z["koff"], z["ft-t05"]
    bu, bp = [], []
    for k, r in enumerate(rows):
        n = np.asarray(r["visits"], float)
        N = n.sum()
        w = n / N
        p = P[koff[k]:koff[k + 1]]
        bu.append(float((w * 0.5 * np.sqrt(math.log(N) / np.maximum(n, 1))).sum()))
        bp.append(float((w * p * math.sqrt(N) / (1 + n)).sum()))
    c = float(np.mean(bu) / np.mean(bp))
    d = {g: abs(math.log2(c) - math.log2(g)) for g in (0.5, 1.0, 2.0)}
    best = min(d.values())
    pick = [g for g in (0.5, 1.0, 2.0) if abs(d[g] - best) < 1e-12]
    choice = 1.0 if len(pick) > 1 else pick[0]
    out[deck] = {"decisions": len(rows), "mean_B_U": float(np.mean(bu)), "mean_B_P": float(np.mean(bp)), "c_star": c,
                 "log2_dist": d, "c_puct": choice}
    print(deck, json.dumps(out[deck]))
json.dump(out, open(f"{S}/o1/cpuct.json", "w"), indent=1)
