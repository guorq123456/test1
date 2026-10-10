"""Horizon-corrected labels and the candidate they train (the architecture thread 2026-10-10 07:18Z, from the
analysis line's M5, 7a68636 / pre-registration 2240556). Condition: the opponent's deck list is known (order and hand
not).

Each step-1 contrast label L (labels.jsonl, c661c8a: the shrinkage label the step-1 candidate trained on) gets
    L'' = L + sum_r (price_G,r - price_T,r) x dr,   r in {max PP, hand, SEP},
dr the example's resource difference (the plan's turn end minus the bot's / the line's, the same determinization;
the version-2 features me_max_pp, me_hand, me_sep of s1_extract.py's examples), the prices in win probability per
unit (M5's points / 100; the labels are differences of win probabilities, as learn.contrast's loss).
- **Prices, cross-fitted.** M5's regression (its prices.py `fit`: through the origin, five resources and eight
  controls; G_end by WLS on K, T by OLS) on M5's own pairs (m5_pairs.jsonl), end pairs out (its main read),
  training starts only (no held-out start's outcome enters any price).
  - The training starts are split in two halves by k % 2. A step-1 example of a start in one half is corrected with
    the prices estimated on the other half, so no pair's correction uses its own outcome.
  - The teacher re-run's examples (other starts, not in M5) take the prices of all training starts.
- **Fit.** The step-1 candidate's own recipe (analysis/step1-candidate/s1_fit.py, cand-tl-ramp-ramp):
  learn.contrast.fit_contrast with mu 0.03, L2 1e-4, start at zero, 3000 iterations, lr 0.05, version-2 features
  with the version's signs, the stock prefixes held at zero, the intercept free; the same examples, weights and
  calibration rows. Only the labels differ, so cand-tl-ramp-ramp is the control.
- **The candidate dir:** cand-th-ramp-ramp. ramp-ramp-ended.json is fit here; ramp-ramp-act.json is copied from
  cand-tl-ramp-ramp (= the installed ACT, unchanged).

usage: fit_h.py LABELS S1_DATA.npz M5_PAIRS OUT_ROOT"""
import hashlib, json, shutil, sys, time
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from svsim.learn.contrast import feature_names, fit_contrast, to_linear_value
from svsim.learn.features import signs
from svsim.learn.phased import STOCK
MU, L2, ITERS, LR = 0.03, 1e-4, 3000, 0.05
RES = ("ep", "sep", "max_pp", "pp_left", "hand")
CTRL = ("enemy_hp", "own_hp", "own_followers", "own_stats", "enemy_followers", "enemy_stats", "own_amulets",
        "enemy_amulets")
CORRECT = {"max_pp": "me_max_pp", "hand": "me_hand", "sep": "me_sep"}


def m5_fit(pairs, label, weighted):
    """M5's prices.py fit: the five resources' coefficients (win points per unit)."""
    X = np.array([[p["x"][f] for f in RES + CTRL] for p in pairs])
    y = np.array([p[label] for p in pairs])
    if weighted:
        w = np.sqrt(np.array([p["K"] for p in pairs], dtype=float))
        X, y = X * w[:, None], y * w
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return dict(zip(RES, beta[:len(RES)]))


def prices(pairs):
    g, t = m5_fit(pairs, "dG", True), m5_fit(pairs, "dT", False)
    return {"G": g, "T": t, "gap": {r: (g[r] - t[r]) / 100.0 for r in CORRECT}, "pairs": len(pairs),
            "starts": len({p["k"] for p in pairs})}


def main():
    labels_path, data_path, m5_path, root = sys.argv[1:5]
    pairs = [json.loads(l) for l in open(m5_path) if l.strip()]
    main_pairs = [p for p in pairs if p["kind"] != "end" and p["split"] == "train"]
    P = {"half0": prices([p for p in main_pairs if p["k"] % 2 == 0]),
         "half1": prices([p for p in main_pairs if p["k"] % 2 == 1]),
         "all": prices(main_pairs)}
    lab = [json.loads(l) for l in open(labels_path) if l.strip()]
    header, lab = lab[0], lab[1:]
    z = np.load(data_path)
    X, ia, ib, key = z["X"], z["ia"], z["ib"], z["key"]
    keys = [tuple(json.loads(k)) for k in z["keys"]]
    names = feature_names(2, ())
    bias = names.index("bias")
    col = {r: names.index(c) for r, c in CORRECT.items()}
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
    sg = list(signs(False, 2))
    by_key = defaultdict(list)
    for i, k in enumerate(key):
        by_key[k].append(i)
    kidx = {k: i for i, k in enumerate(keys)}
    src_of = {"step1": "step1", "teacher_ends": "old"}
    rows, L0, L, w, srcs = [], [], [], [], []
    count = defaultdict(int)
    shift = defaultdict(list)
    for r in lab:
        if r["split"] != "train":
            continue
        ex = by_key.get(kidx.get((src_of[r["source"]], r["k"], r["plan"])), [])
        if not ex:
            count[f"{r['source']}_no_examples"] += 1
            continue
        count[f"{r['source']}_labels"] += 1
        count[f"{r['source']}_examples"] += len(ex)
        gap = (P["half1"] if r["k"] % 2 == 0 else P["half0"])["gap"] if r["source"] == "step1" else P["all"]["gap"]
        for i in ex:
            d = sum(gap[res] * float(X[ia[i], c] - X[ib[i], c]) for res, c in col.items())
            rows.append(i); L0.append(r["label"]); L.append(r["label"] + d); w.append(r["weight"] / len(ex))
            srcs.append(r["source"])
            shift[r["source"]].append(d)
    rows, L0, L, w = np.array(rows), np.array(L0), np.array(L), np.array(w)
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
             "sign_w_vs_original_labels": round(float(np.sum(w * (np.sign(d) == np.sign(L0))) / w.sum()), 4),
             "calib_logloss": round(float(np.mean(np.logaddexp(0, zc) - yc * zc)), 4)}
    corr = {s_: {"examples": len(v), "mean": round(float(np.mean(v)), 5), "mean_abs": round(float(np.mean(np.abs(v))), 5),
                 "nonzero": int(np.sum(np.abs(np.array(v)) > 1e-12))} for s_, v in shift.items()}
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()   # noqa: E731
    rnd = lambda d_: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d_.items()}   # noqa: E731
    price_info = {h: {"G": rnd({k: float(v) for k, v in p["G"].items()}), "T": rnd({k: float(v) for k, v in p["T"].items()}),
                      "gap_prob": {k: round(float(v), 6) for k, v in p["gap"].items()}, "pairs": p["pairs"],
                      "starts": p["starts"]} for h, p in P.items()}
    out = Path(root) / "cand-th-ramp-ramp"
    out.mkdir(parents=True, exist_ok=True)
    info = {"moment": "ended", "contrast": True, "horizon_corrected": sorted(CORRECT), "mu": MU, "l2": L2,
            "iters": ITERS, "lr": LR, "start": "zero", "labels": sha(labels_path), "m5_pairs": sha(m5_path),
            "label_calibration": header, "data_commit": "6f11111", "hold_out_every": 11, "version": 2,
            "stock_zeroed": list(STOCK), "calibration_rows": int(len(ctr)), "examples": int(len(rows)),
            "counts": dict(count), "prices": price_info, "correction": corr,
            "report": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in report.items()},
            "train": train, "seconds": secs}
    to_linear_value(model, 2, (), info).save(out / "ramp-ramp-ended.json")
    shutil.copy(ROOT / "svsim/learn/phased_models/cand-tl-ramp-ramp/ramp-ramp-act.json", out / "ramp-ramp-act.json")
    print(json.dumps({"train": train, "intercept": round(float(model.w[bias]), 4), "seconds": secs,
                      "prices": price_info, "correction": corr, "counts": dict(count)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
