"""cand-kc-ramp-t (the architecture thread 2026-10-13 23:58Z): cand-kc-ramp-ramp's recipe (analysis/lethal-clock/
kc_fit.py, itself cand-tl's s1_fit.py) on the ramp-t mirror's step-1 data, over the installed ramp-t mirror model's
features (version 2 + "hand" + "hpphase") plus "kclock".
- Labels: step1.py labels on this run's data (bank 69900000), training split only.
- learn.contrast.fit_contrast with mu 0.03, L2 1e-4, start at zero, 3000 iterations, lr 0.05; the version-2 signs,
  the hand / hpphase / kclock columns free; the stock prefixes held at zero; the intercept free.
- Calibration rows: the self-play set's decided ENDED turn ends, games with g % 11 != 0.
- The candidate dir: cand-kc-ramp-t. ramp-t-ramp-t-ended.json is fit here; ramp-t-ramp-t-act.json is the installed
  one, copied.
Condition: the opponent's deck list is known (order and hand not).
usage: krt_fit.py LABELS KRT_DATA.npz OUT_ROOT"""
import hashlib, json, shutil, sys, time
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from svsim.learn.contrast import feature_names, fit_contrast, to_linear_value   # noqa: E402
from svsim.learn.features import extra_names, signs                            # noqa: E402
from svsim.learn.phased import STOCK                                            # noqa: E402
MU, L2, ITERS, LR = 0.03, 1e-4, 3000, 0.05
EXTRAS = ("hand", "hpphase", "kclock")
NAME = "cand-kc-ramp-t"


def examples(lab, z, split):
    keys = [tuple(json.loads(k)) for k in z["keys"]]
    by_key = defaultdict(list)
    for i, k in enumerate(z["key"]):
        by_key[k].append(i)
    kidx = {k: i for i, k in enumerate(keys)}
    rows, L, w, count = [], [], [], defaultdict(int)
    for r in lab:
        if r["split"] != split or r["source"] != "step1":
            continue
        ex = by_key.get(kidx.get(("step1", r["k"], r["plan"])), [])
        if not ex:
            count["no_examples"] += 1
            continue
        count["labels"] += 1
        count["examples"] += len(ex)
        for i in ex:
            rows.append(i); L.append(r["label"]); w.append(r["weight"] / len(ex))
    return np.array(rows), np.array(L), np.array(w), dict(count)


def main():
    labels_path, data_path, root = sys.argv[1:4]
    lab = [json.loads(l) for l in open(labels_path) if l.strip()]
    header, lab = lab[0], lab[1:]
    z = np.load(data_path)
    X, ia, ib = z["X"], z["ia"], z["ib"]
    names = feature_names(2, EXTRAS)
    base = len(feature_names(2, ()))
    assert X.shape[1] == len(names) and names[base:] == extra_names(EXTRAS)
    bias = names.index("bias")
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
    sg = list(signs(False, 2)) + [0] * (len(names) - base)
    rows, L, w, count = examples(lab, z, "train")
    XA, XB = X[ia[rows]].astype(np.float32), X[ib[rows]].astype(np.float32)
    ctr = np.where(z["Cg"] % 11 != 0)[0]
    XC, yc = z["Cx"][ctr].astype(np.float32), z["Cy"][ctr]
    t0 = time.time()
    model, report = fit_contrast(XA, XB, L, w, XC, yc, mu=MU, l2=L2, iters=ITERS, lr=LR, signs=sg, bias=bias,
                                 keep=keep)
    secs = round(time.time() - t0)
    s = lambda v: 1 / (1 + np.exp(-np.clip(v, -30, 30)))   # noqa: E731
    Ef = lambda m, Xs: m.forward(m.standardize(np.asarray(Xs, float) * keep).astype(np.float32))   # noqa: E731

    def reads(rows_, L_, w_, C, y):
        d = s(Ef(model, X[ia[rows_]])) - s(Ef(model, X[ib[rows_]]))
        zc = Ef(model, C)
        return {"contrast_mse_w": round(float(np.sum(w_ * (d - L_) ** 2) / w_.sum()), 6),
                "sign_w": round(float(np.sum(w_ * (np.sign(d) == np.sign(L_))) / w_.sum()), 4),
                "calib_logloss": round(float(np.mean(np.logaddexp(0, zc) - y * zc)), 4)}
    train = reads(rows, L, w, XC, yc)
    vrows, vL, vw, vcount = examples(lab, z, "val")
    cva = np.where(z["Cg"] % 11 == 0)[0]
    val = reads(vrows, vL, vw, z["Cx"][cva].astype(np.float32), z["Cy"][cva])
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()   # noqa: E731
    out = Path(root) / NAME
    out.mkdir(parents=True, exist_ok=True)
    info = {"moment": "ended", "contrast": True, "extras": list(EXTRAS), "mu": MU, "l2": L2, "iters": ITERS,
            "lr": LR, "start": "zero", "labels": sha(labels_path), "label_calibration": header,
            "data": "analysis/kc-ramp-t (step1.py, bank 69900000)", "hold_out_every": 11, "version": 2,
            "stock_zeroed": list(STOCK), "calibration_rows": int(len(ctr)), "examples": int(len(rows)),
            "counts": count, "report": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in report.items()},
            "train": train, "val": val, "seconds": secs}
    lv = to_linear_value(model, 2, EXTRAS, info)
    lv.save(out / "ramp-t-ramp-t-ended.json")
    shutil.copy(ROOT / "svsim/learn/phased_models/ramp-t-ramp-t-act.json", out / "ramp-t-ramp-t-act.json")
    std = {n: round(float(c), 4) for n, c in zip(names[base:], model.w[base:])}
    print(json.dumps({"train": train, "val": val, "intercept": round(float(model.w[bias]), 4), "seconds": secs,
                      "extra coefficients (standardized)": std, "counts": count, "val_counts": vcount},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
