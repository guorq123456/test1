"""D5 check point (README ae44936): one more net's moves on D5's 500 decision points (same sampling, same seeds
73400000 + k), against the reference moves stored in d5.json; agreement, and the J119 prediction from the line
fixed at registration (scale = a + b * agreement over D5's 8 nets; prediction sigma(s_hat - 0.448))."""
import json, math, sys
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/d5")
import d5_agree as D

d5, net, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
SPEC = f"mcts:100+{D.P}+setnet=analysis/scaling/models/{net}.npz+neteot"
dec = D.decisions(d5["rec"], d5["seed"], d5["n"])
_D = {k: (g, i, s, d5["seed"] + k) for k, (g, i, s) in enumerate(dec)}

def work(k):
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    g, i, state, seed = _D[k]
    s = state.clone()
    return k, g, i, json.dumps(repr(make_agent(SPEC, seed).act(s, legal_actions(s))), sort_keys=True)

rows = d5["rows"]
with Pool(3) as pool:
    got = sorted(pool.map(work, range(len(dec)), chunksize=4))
assert all(r["k"] == k and r["g"] == g and r["i"] == i for r, (k, g, i, _) in zip(rows, got))
agree = np.array([m == r["ref"] for r, (_, _, _, m) in zip(rows, got)], float)
rng = np.random.default_rng(0)
B = rng.integers(0, len(rows), (4000, len(rows)))
x = np.array([d5["summary"][n]["agree"] for n in D.NETS]); y = np.array([D.SCALE[n] for n in D.NETS])
b, a = np.polyfit(x, y, 1)
s_hat = a + b * agree.mean()
pred = 1 / (1 + math.exp(-(s_hat - 0.448)))
g459 = np.array([r["net-gen4-59000"] == r["ref"] for r in rows], float)
dd = (agree - g459)[B].mean(axis=1)
res = {"net": net, "spec": SPEC, "agree": round(float(agree.mean()), 4),
       "agree_95": [round(float(np.percentile(agree[B].mean(axis=1), q)), 4) for q in (2.5, 97.5)],
       "minus_gen4_59000": round(float((agree - g459).mean()), 4), "minus_gen4_59000_95": [round(float(np.percentile(dd, q)), 4) for q in (2.5, 97.5)],
       "line": [round(float(a), 4), round(float(b), 4)], "scale_hat": round(float(s_hat), 4), "J119_prediction": round(pred, 4),
       "moves": [m for *_, m in got]}
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "moves"}, indent=1))
