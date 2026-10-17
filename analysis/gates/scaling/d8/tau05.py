"""O1 addendum (tau = 0.5, the architecture thread 11:44Z): prior-free figures on pi_0.5 = v^2 / sum v^2 (key-merged)."""
import json, math, sys
import numpy as np
sys.path.insert(0, ".")
from d8_read import boot, entropy

def sharp(v):
    q = np.asarray(v, float) ** 2
    return q / q.sum()

out = {}
for deck in ("ramp", "elft"):
    rows = json.load(open(f"scan-{deck}.json"))["rows"]
    by = {(r["g"], r["i"]): r for r in rows}
    res = {}
    for name, keep in (("all", lambda r: True), ("start", lambda r: r["start"]), ("mid", lambda r: not r["start"])):
        sel = [r for r in rows if keep(r)]
        vals = [(math.log(len(r["visits"])) - entropy(sharp(r["visits"])), float(sharp(r["visits"]).max())) for r in sel]
        est, lo, hi = boot([r["g"] for r in sel], vals)
        res[name] = {"decisions": len(sel), "kl_uniform_t05": [est[0], lo[0], hi[0]], "top_share_t05": est[1]}
    rr = json.load(open(f"rerun-{deck}.json"))
    for name, keep in (("all", lambda r: True), ("start", lambda r: r["start"]), ("mid", lambda r: not r["start"])):
        g, vals = [], []
        for p in rr["points"]:
            if p["outer"]:
                continue
            r = by[(p["g"], p["i"])]
            if not keep(r):
                continue
            a = sharp(r["visits"])
            w = np.asarray(p["rerun"], float) ** 2
            b = np.maximum(w / w.sum(), 1e-12)
            vals.append(float((a[a > 0] * (np.log(a[a > 0]) - np.log(b[a > 0]))).sum()))
            g.append(r["g"])
        est, lo, hi = boot(g, vals)
        res[name]["d8_kl_t05"] = [est[0], lo[0], hi[0]]
    out[deck] = res
json.dump(out, open("tau05.json", "w"), indent=1)
for d, res in out.items():
    for k, x in res.items():
        print(d, k, x["decisions"], [round(y, 4) for y in x["kl_uniform_t05"]], round(x["top_share_t05"], 4), [round(y, 4) for y in x["d8_kl_t05"]])
