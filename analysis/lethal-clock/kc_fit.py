"""The lethal-clock candidate (the architecture thread 2026-10-10 10:38Z): cand-tl-ramp-ramp's recipe
(analysis/step1-candidate/s1_fit.py) with only the "kclock" columns added (learn.features; 7 columns, signs free).
- Labels: the same step-1 labels (labels.jsonl, c661c8a), training split only; the same examples, weights and
  calibration rows (kc_extract.py builds them in s1_extract.py's order; checked here against s1_data.npz).
- learn.contrast.fit_contrast with mu 0.03, L2 1e-4, start at zero, 3000 iterations, lr 0.05, the version-2 signs
  (the kclock columns free), the stock prefixes held at zero, the intercept free.
- The candidate dir: cand-kc-ramp-ramp. ramp-ramp-ended.json is fit here; ramp-ramp-act.json is copied from
  cand-tl-ramp-ramp (= the installed ACT, unchanged).
Condition: the opponent's deck list is known (order and hand not).
usage: kc_fit.py LABELS KC_DATA.npz S1_DATA.npz OUT_ROOT"""
import hashlib, json, shutil, sys, time
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from svsim.learn.contrast import feature_names, fit_contrast, to_linear_value
from svsim.learn.features import extra_names, signs
from svsim.learn.phased import STOCK
MU, L2, ITERS, LR = 0.03, 1e-4, 3000, 0.05
EXTRAS = ("kclock",)
NAME = "cand-kc-ramp-ramp"


def main():
    labels_path, data_path, s1_path, root = sys.argv[1:5]
    lab = [json.loads(l) for l in open(labels_path) if l.strip()]
    header, lab = lab[0], lab[1:]
    z, z0 = np.load(data_path), np.load(s1_path)
    X, ia, ib, key = z["X"], z["ia"], z["ib"], z["key"]
    names = feature_names(2, EXTRAS)
    base = len(feature_names(2, ()))
    assert X.shape[1] == len(names) and names[base:] == extra_names(EXTRAS)
    # the same examples as cand-tl's: the version-2 columns, pairs and calibration rows are s1_data.npz's
    for k in ("ia", "ib", "key", "keys", "Cg", "Cy"):
        assert np.array_equal(z[k], z0[k]), k
    assert np.array_equal(X[:, :base], z0["X"]) and np.array_equal(z["Cx"][:, :base], z0["Cx"])
    keys = [tuple(json.loads(k)) for k in z["keys"]]
    bias = names.index("bias")
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
    sg = list(signs(False, 2)) + [0] * (len(names) - base)
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
    XA, XB = X[ia[rows]].astype(np.float32), X[ib[rows]].astype(np.float32)
    ctr = np.where(z["Cg"] % 11 != 0)[0]
    XC, yc = z["Cx"][ctr].astype(np.float32), z["Cy"][ctr]
    t0 = time.time()
    model, report = fit_contrast(XA, XB, L, w, XC, yc, mu=MU, l2=L2, iters=ITERS, lr=LR, signs=sg, bias=bias,
                                 keep=keep)
    secs = round(time.time() - t0)
    s = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))   # noqa: E731
    Ef = lambda m, Xs: m.forward(m.standardize(np.asarray(Xs, float) * keep).astype(np.float32))   # noqa: E731
    d = s(Ef(model, XA)) - s(Ef(model, XB))
    zc = Ef(model, XC)
    train = {"contrast_mse_w": round(float(np.sum(w * (d - L) ** 2) / w.sum()), 6),
             "sign_w": round(float(np.sum(w * (np.sign(d) == np.sign(L))) / w.sum()), 4),
             "calib_logloss": round(float(np.mean(np.logaddexp(0, zc) - yc * zc)), 4)}
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()   # noqa: E731
    out = Path(root) / NAME
    out.mkdir(parents=True, exist_ok=True)
    info = {"moment": "ended", "contrast": True, "extras": list(EXTRAS), "mu": MU, "l2": L2, "iters": ITERS,
            "lr": LR, "start": "zero", "labels": sha(labels_path), "label_calibration": header,
            "data_commit": "6f11111", "hold_out_every": 11, "version": 2, "stock_zeroed": list(STOCK),
            "calibration_rows": int(len(ctr)), "examples": int(len(rows)), "counts": dict(count),
            "report": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in report.items()},
            "train": train, "seconds": secs}
    lv = to_linear_value(model, 2, EXTRAS, info)
    lv.save(out / "ramp-ramp-ended.json")
    shutil.copy(ROOT / "svsim/learn/phased_models/cand-tl-ramp-ramp/ramp-ramp-act.json", out / "ramp-ramp-act.json")
    std = {n: round(float(c), 4) for n, c in zip(names[base:], model.w[base:])}
    print(json.dumps({"train": train, "intercept": round(float(model.w[bias]), 4), "seconds": secs,
                      "kclock coefficients (standardized)": std, "counts": dict(count)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
