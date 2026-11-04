"""Held-out (split "val") reads of cand-nl-ramp-ramp against cand-kc-ramp-ramp with intervals: weighted contrast MSE
and weighted sign agreement, the difference resampled by start (source, k) 2000 times, seed 0. The models are read
from their files (learn.model.LinearValue's own forward on the stored standardization).
Condition: the opponent's deck list is known (order and hand not).
usage: nl_read.py LABELS KC_DATA.npz"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
P = ROOT / "svsim/learn/phased_models"


def model_logit(path, X):
    d = json.loads(Path(path).read_text())
    x = (np.asarray(X, float) - np.array(d["mean"])) / np.array(d["std"])
    z = x @ np.array(d["coef"])
    if d.get("hidden"):
        h = d["hidden"]
        z = z + np.tanh(x @ np.array(h["W1"]) + np.array(h["b1"])) @ np.array(h["w2"])
    return z


def main():
    labels, data = sys.argv[1:3]
    lab = [json.loads(l) for l in open(labels) if l.strip()][1:]
    z = np.load(data)
    X, ia, ib, key = z["X"], z["ia"], z["ib"], z["key"]
    keys = [tuple(json.loads(k)) for k in z["keys"]]
    by_key = defaultdict(list)
    for i, k in enumerate(key):
        by_key[k].append(i)
    kidx = {k: i for i, k in enumerate(keys)}
    src_of = {"step1": "step1", "teacher_ends": "old"}
    rows, L, w, cl = [], [], [], []
    for r in lab:
        if r["split"] != "val":
            continue
        ex = by_key.get(kidx.get((src_of[r["source"]], r["k"], r["plan"])), [])
        for i in ex:
            rows.append(i); L.append(r["label"]); w.append(r["weight"] / len(ex)); cl.append((r["source"], r["k"]))
    rows, L, w = np.array(rows), np.array(L), np.array(w)
    sig = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))   # noqa: E731
    out = {}
    per = {}
    for name in ("cand-kc-ramp-ramp", "cand-nl-ramp-ramp"):
        f = P / name / "ramp-ramp-ended.json"
        d = sig(model_logit(f, X[ia[rows]])) - sig(model_logit(f, X[ib[rows]]))
        per[name] = ((d - L) ** 2, (np.sign(d) == np.sign(L)).astype(float))
        out[name] = {"contrast_mse_w": round(float(np.sum(w * per[name][0]) / w.sum()), 6),
                     "sign_w": round(float(np.sum(w * per[name][1]) / w.sum()), 4)}
    groups = defaultdict(list)
    for i, c in enumerate(cl):
        groups[c].append(i)
    gl = list(groups.values())
    rng = np.random.default_rng(0)
    dm, ds = [], []
    for _ in range(2000):
        idx = np.concatenate([gl[j] for j in rng.integers(0, len(gl), len(gl))])
        ww = w[idx]
        dm.append(float(np.sum(ww * (per["cand-nl-ramp-ramp"][0][idx] - per["cand-kc-ramp-ramp"][0][idx])) / ww.sum()))
        ds.append(float(np.sum(ww * (per["cand-nl-ramp-ramp"][1][idx] - per["cand-kc-ramp-ramp"][1][idx])) / ww.sum()))
    q = lambda v: [round(float(np.quantile(v, 0.025)), 5), round(float(np.quantile(v, 0.975)), 5)]   # noqa: E731
    out["val examples"], out["val starts"] = int(len(rows)), len(gl)
    out["cand-nl - cand-kc"] = {
        "contrast_mse_w": round(out["cand-nl-ramp-ramp"]["contrast_mse_w"] - out["cand-kc-ramp-ramp"]["contrast_mse_w"], 6),
        "contrast_mse_w 95%": q(dm),
        "sign_w points": round(100 * (out["cand-nl-ramp-ramp"]["sign_w"] - out["cand-kc-ramp-ramp"]["sign_w"]), 2),
        "sign_w points 95%": [round(100 * x, 2) for x in q(ds)]}
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
