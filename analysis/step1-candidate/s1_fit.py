"""Step 1's candidate and its B' (the architecture thread 22:22Z), from labels.jsonl and s1_extract.py's examples.

Candidate (cand-tl-ramp-ramp): learn.contrast.fit_contrast, the settings chosen in ddfef2f before any step-1 data:
mu 0.03, L2 1e-4, start at zero, 3000 iterations, lr 0.05, version-2 features, the version's signs, the stock
prefixes held at zero, the intercept free. Examples: each training label (step 1's and the teacher re-run's) with
its weight W spread evenly over its kept determinizations (W / their count each); none kept: the label drops out
(counted). Calibration: the decided games' ENDED turn ends of both self-play sets, training games (g % 11 != 0).

B' (cand-tl-ramp-ramp-bprime): the same objective without the contrast term, i.e. the limit mu -> infinity:
learn.fit.fit on the same calibration rows, L2 1e-4 / 0.03 (the candidate's L2 relative to its calibration
weight), 3000 iterations, lr 0.05, the same signs and stock prefixes.
usage: s1_fit.py LABELS S1_DATA.npz OUT_ROOT"""
import hashlib, json, sys, time
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, "/home/user/test1")
from svsim.learn.contrast import ContrastLinear, contrast_loss, feature_names, fit_contrast, to_linear_value
from svsim.learn import fit as F
from svsim.learn.features import signs
from svsim.learn.model import LinearValue
from svsim.learn.phased import STOCK
MU, L2, ITERS, LR = 0.03, 1e-4, 3000, 0.05
labels_path, data_path, root = sys.argv[1:4]
lab = [json.loads(l) for l in open(labels_path) if l.strip()]
header, lab = lab[0], lab[1:]
z = np.load(data_path)
X, ia, ib, key = z["X"], z["ia"], z["ib"], z["key"]
keys = [tuple(json.loads(k)) for k in z["keys"]]
names = feature_names(2, ()); bias = names.index("bias")
assert X.shape[1] == len(names)
keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
sg = list(signs(False, 2))
by_key = defaultdict(list)
for i, k in enumerate(key):
    by_key[k].append(i)
kidx = {k: i for i, k in enumerate(keys)}
src_of = {"step1": "step1", "teacher_ends": "old"}
rows, L, w = [], [], []
count = defaultdict(int)
for r in lab:
    if r["split"] != "train":
        continue
    ex = by_key.get(kidx.get((src_of[r["source"]], r["k"], r["plan"])), [])
    if not ex:
        count[f"{r['source']}_no_examples"] += 1
        continue
    count[f"{r['source']}_labels"] += 1
    count[f"{r['source']}_examples"] += len(ex)
    for i in ex:
        rows.append(i); L.append(r["label"]); w.append(r["weight"] / len(ex))
rows, L, w = np.array(rows), np.array(L), np.array(w)
src = np.array([keys[key[i]][0] for i in rows])
share = {s: round(float(w[src == s].sum() / w.sum()), 4) for s in ("step1", "old")}
ess = float(w.sum() ** 2 / np.sum(w * w) / len(w))
XA, XB = X[ia[rows]].astype(np.float32), X[ib[rows]].astype(np.float32)
ctr = np.where(z["Cg"] % 11 != 0)[0]
XC, yc = z["Cx"][ctr].astype(np.float32), z["Cy"][ctr]
t0 = time.time()
model, report = fit_contrast(XA, XB, L, w, XC, yc, mu=MU, l2=L2, iters=ITERS, lr=LR, signs=sg, bias=bias, keep=keep)
secs = round(time.time() - t0)
s = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))
Ef = lambda m, Xs: m.forward(m.standardize(np.asarray(Xs, float) * keep).astype(np.float32))
d = s(Ef(model, XA)) - s(Ef(model, XB))
zc = Ef(model, XC)
train = {"contrast_mse_w": round(float(np.sum(w * (d - L) ** 2) / w.sum()), 6),
         "sign_w": round(float(np.sum(w * (np.sign(d) == np.sign(L))) / w.sum()), 4),
         "calib_logloss": round(float(np.mean(np.logaddexp(0, zc) - yc * zc)), 4)}
# B': calibration only
coef_b, mean_b, std_b, rep_b = F.fit(np.asarray(XC, float) * keep, yc, None, l2=L2 / MU, iters=ITERS, lr=LR,
                                     signs=sg, bias=bias)
coef_b = coef_b * keep
zb_c = ((np.asarray(XC, float) * keep - mean_b) / std_b) @ coef_b
Eb = lambda Xs: ((np.asarray(Xs, float) * keep - mean_b) / std_b) @ coef_b
db = s(Eb(XA)) - s(Eb(XB))
train_b = {"contrast_mse_w": round(float(np.sum(w * (db - L) ** 2) / w.sum()), 6),
           "sign_w": round(float(np.sum(w * (np.sign(db) == np.sign(L))) / w.sum()), 4),
           "calib_logloss": round(float(np.mean(np.logaddexp(0, zb_c) - yc * zb_c)), 4)}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
common = {"labels": sha(labels_path), "label_calibration": header, "data_commit": "6f11111",
          "hold_out_every": 11, "version": 2, "stock_zeroed": list(STOCK), "calibration_rows": int(len(ctr)),
          "examples": int(len(rows)), "counts": dict(count), "weight_share": share, "ess": round(ess, 4)}
out = Path(root)
cand, bp = out / "cand-tl-ramp-ramp", out / "cand-tl-ramp-ramp-bprime"
for p in (cand, bp):
    p.mkdir(parents=True, exist_ok=True)
info = {"moment": "ended", "contrast": True, "mu": MU, "l2": L2, "iters": ITERS, "lr": LR, "start": "zero",
        **common, "report": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in report.items()},
        "train": train, "seconds": secs}
to_linear_value(model, 2, (), info).save(cand / "ramp-ramp-ended.json")
info_b = {"moment": "ended", "contrast": False, "bprime_of": "cand-tl-ramp-ramp", "objective": "calibration log loss only (mu -> infinity)",
          "l2": L2 / MU, "iters": ITERS, "lr": LR, "start": "zero", **common,
          "report": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in rep_b.items()}, "train": train_b}
LinearValue([float(x) for x in coef_b], [float(x) for x in mean_b], [float(x) for x in std_b], False, info_b,
            version=2).save(bp / "ramp-ramp-ended.json")
print(json.dumps({"candidate": {"train": train, "intercept": round(float(model.w[bias]), 4), "seconds": secs},
                  "bprime": {"train": train_b, "intercept": round(float(coef_b[bias]), 4)}, **common}, ensure_ascii=False))
