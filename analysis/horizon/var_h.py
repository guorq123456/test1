"""How much of L's variance the horizon correction adds (the architecture thread 07:33Z, item 3): Var(correction) /
Var(L) over the training examples, weighted by the example weights (W / kept determinizations), for candidate A
and B as fit_h.py builds their labels (the same prices, the same per-example dr). Per source and pooled; also per
label for step 1 (the example corrections averaged within a label).
usage: var_h.py LABELS S1_DATA.npz M5_PAIRS"""
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import fit_h as F
from svsim.learn.contrast import feature_names

labels_path, data_path, m5_path = sys.argv[1:4]
pairs = [json.loads(l) for l in open(m5_path) if l.strip()]
main_pairs = [p for p in pairs if p["kind"] != "end" and p["split"] == "train"]
lab = [json.loads(l) for l in open(labels_path) if l.strip()][1:]
z = np.load(data_path)
X, ia, ib, key = z["X"], z["ia"], z["ib"], z["key"]
keys = [tuple(json.loads(k)) for k in z["keys"]]
names = feature_names(2, ())
by_key = defaultdict(list)
for i, k in enumerate(key):
    by_key[k].append(i)
kidx = {k: i for i, k in enumerate(keys)}
src_of = {"step1": "step1", "teacher_ends": "old"}


def wvar(v, w):
    m = np.sum(w * v) / w.sum()
    return float(np.sum(w * (v - m) ** 2) / w.sum())


out = {}
for cand, correct in (("A", F.CORRECT), ("B", dict(F.CORRECT, **F.FOLLOWERS))):
    P = {h: F.prices([p for p in main_pairs if p["k"] % 2 == h], correct) for h in (0, 1)}
    P["all"] = F.prices(main_pairs, correct)
    col = {r: names.index(c) for r, c in correct.items()}
    acc = defaultdict(lambda: ([], [], []))
    per_label = ([], [], [])
    for r in lab:
        if r["split"] != "train":
            continue
        ex = by_key.get(kidx.get((src_of[r["source"]], r["k"], r["plan"])), [])
        if not ex:
            continue
        gap = P[1 - r["k"] % 2]["gap"] if r["source"] == "step1" else P["all"]["gap"]
        ds = [sum(gap[res] * float(X[ia[i], c] - X[ib[i], c]) for res, c in col.items()) for i in ex]
        for d in ds:
            for s in (r["source"], "all"):
                acc[s][0].append(r["label"]); acc[s][1].append(d); acc[s][2].append(r["weight"] / len(ex))
        if r["source"] == "step1":
            per_label[0].append(r["label"]); per_label[1].append(float(np.mean(ds))); per_label[2].append(r["weight"])
    res = {}
    for s, (L, D, W) in list(acc.items()) + [("step1_per_label", per_label)]:
        L, D, W = np.array(L), np.array(D), np.array(W)
        res[s] = {"n": len(L), "share": round(wvar(D, W) / wvar(L, W), 4),
                  "share_unweighted": round(float(np.var(D) / np.var(L)), 4),
                  "corr_L_correction": round(float(np.corrcoef(L, D)[0, 1]), 4)}
    out[cand] = res
print(json.dumps(out, indent=1))
