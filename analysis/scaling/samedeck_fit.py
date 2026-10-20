"""Same-deck N against v2skx (the architecture thread 2026-10-20 10:55Z): the candidate's ms per decision (puct_cost.py,
N 75/90/105 or 90/100/110) fitted linearly in N; N where the fit meets v2skx's ms per decision on the same positions.

    python analysis/scaling/samedeck_fit.py COST.json ...
"""
import json, sys
import numpy as np
for f in sys.argv[1:]:
    d = json.load(open(f)); s = d["specs"]
    ns = sorted(int(k[1:]) for k in s if k.startswith("n"))
    y = np.array([s[f"n{n}"]["ms_per_decision"] for n in ns]); x = np.array(ns, float)
    b, a = np.polyfit(x, y, 1); v = s["v2skx"]["ms_per_decision"]
    n0 = (v - a) / b
    el = b * n0 / v                               # d ln ms / d ln N at the crossing
    print(json.dumps({"file": f, "deck": d.get("deck"), "decisions": d["decisions"], "v2skx": v,
                      **{f"n{n}": s[f"n{n}"]["ms_per_decision"] for n in ns}, "slope_ms_per_N": round(b, 4),
                      "N_same_deck": round(n0, 1), "elasticity": round(el, 3)}))
