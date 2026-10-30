"""Ended model under L2 1e-4 against the current L2 1e-3 (signs kept, 2500 iterations, STOCK zeroed) on the same
training rows (line % 11 != 0), scored on the held-out rows (line % 11 == 0) with a per-game bootstrap (2000 draws).
usage: l2cmp.py DATA MATCHUP EXTRAS(comma or -)"""
import json, random, sys
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, "/home/user/test1")
from svsim.learn.phased import _rows, STOCK
from svsim.learn import fit as F
from svsim.learn.features import names, signs, extra_names
from svsim.learn.netdata import ENDED
from svsim.learn.model import split_keys

data, matchup, ex = sys.argv[1:4]
extras = tuple(e for e in ex.split(",") if e and e != "-")
side = tuple(split_keys(matchup))
lines = list(open(data, encoding="utf-8"))
def job(i): return [r + (i,) for r in _rows((lines[i], 2, 1.0, 1.0, 1.0, (ENDED,), side, extras))]
if __name__ == "__main__":
    with Pool(4) as p:
        rows = [r for part in p.map(job, range(len(lines)), chunksize=8) for r in part]
    rows = [r for r in rows if r[3] != 0.5]
    N = names(False, 2) + extra_names(extras)
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in N])
    tr = [r for r in rows if r[-1] % 11 != 0]; ho = [r for r in rows if r[-1] % 11 == 0]
    Xt = np.array([r[2] for r in tr], float) * keep; yt = np.array([r[3] for r in tr], float)
    Xh = np.array([r[2] for r in ho], float) * keep; yh = np.array([r[3] for r in ho], float)
    games = np.array([r[-1] for r in ho])
    sg = list(signs(False, 2)) + [0] * len(extra_names(extras))
    ll = {}
    for l2 in (1e-3, 1e-4):
        w, mean, std, rep = F.fit(Xt, yt, None, l2=l2, iters=2500, signs=sg)
        w = w * keep
        pr = 1 / (1 + np.exp(-np.clip(((Xh - mean) / std) @ w, -30, 30)))
        ll[l2] = -(yh * np.log(pr + 1e-9) + (1 - yh) * np.log(1 - pr + 1e-9))
    d = ll[1e-4] - ll[1e-3]
    ids = sorted(set(games.tolist())); by = {g: np.where(games == g)[0] for g in ids}
    rng = random.Random(1); diffs = []
    for _ in range(2000):
        pick = np.concatenate([by[ids[rng.randrange(len(ids))]] for _ in ids])
        diffs.append(float(d[pick].mean()))
    diffs.sort()
    print(json.dumps({"matchup": matchup, "extras": list(extras), "train": len(Xt), "n": len(Xh), "games": len(ids),
                      "l2_1e-3": round(float(ll[1e-3].mean()), 4), "l2_1e-4": round(float(ll[1e-4].mean()), 4),
                      "diff": round(float(d.mean()), 4), "lo": round(diffs[50], 4), "hi": round(diffs[1949], 4)}), flush=True)
