"""Horizon-corrected labels and the candidates they train (the architecture thread 2026-10-10 07:18Z and 07:33Z, from
the analysis line's M5: 7a68636, the per-half prices ef6e3f0, the gates pre-registered in README-horizon.md, a5bd580).
Condition: the opponent's deck list is known (order and hand not).

Each step-1 contrast label L (labels.jsonl, c661c8a: the shrinkage label the step-1 candidate trained on) gets
    L'' = L + sum_r (price_G,r - price_T,r) x dr,
- candidate A: r in {max PP, hand, SEP}; candidate B (--followers): A plus the own follower count;
- prices in win probability per unit (M5's points / 100; the labels are differences of win probabilities, as
  learn.contrast's loss).
- **Step-1 labels.** dr is the pair's M5 regressor: the mean over the plan's 16 T turn ends minus the bot's
  (check_h.py's rows, the same numbers as m5_pairs.jsonl: checked on 6840/6840 pairs).
  - Prices are cross-fitted by the analysis line's halves: game % 2 of the start (starts.jsonl), training starts,
    end pairs out. A label of a start in one half takes the other half's prices.
  - The five resources' prices are read from m5_halves.json. The own follower count's (B) come from the same
    regression on the same halves (prices.py's fit, every coefficient); this script recomputes the five resources
    too and asserts they match the file.
- **Teacher re-run labels** (other starts, not in M5; 69% of the training weight). They have no M5 pair, so dr is
  the example's own turn-end difference in the version-2 features (me_max_pp, me_hand, me_sep, me_followers; the
  plan's end minus the line's, the same determinization). The price is the mean of the two halves'.
- **Fit.** The step-1 candidate's own recipe (analysis/step1-candidate/s1_fit.py, cand-tl-ramp-ramp):
  learn.contrast.fit_contrast with mu 0.03, L2 1e-4, start at zero, 3000 iterations, lr 0.05, version-2 features
  with the version's signs, the stock prefixes held at zero, the intercept free; the same examples, weights and
  calibration rows. Only the labels differ, so cand-tl-ramp-ramp is the control.
- **Output:** <OUT_ROOT>/<name>/ramp-ramp-ended.json. ramp-ramp-act.json is copied from cand-tl-ramp-ramp (= the
  installed ACT, unchanged).
- **Reported:** the share of L's variance the correction adds, Var(correction) / Var(L), over the training labels
  (step 1: per label; teacher re-run: per example), weighted by the label weights.

usage: fit_h.py LABELS S1_DATA.npz CHECK_ROWS STARTS M5_PAIRS M5_HALVES OUT_ROOT NAME [--followers]"""
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
FOLLOWERS = {"own_followers": "me_followers"}


def m5_fit(pairs, label, weighted):
    """M5's prices.py fit: the five resources' coefficients (win points per unit)."""
    X = np.array([[p["x"][f] for f in RES + CTRL] for p in pairs])
    y = np.array([p[label] for p in pairs])
    if weighted:
        w = np.sqrt(np.array([p["K"] for p in pairs], dtype=float))
        X, y = X * w[:, None], y * w
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return dict(zip(RES + CTRL, beta))


def prices(pairs, correct):
    g, t = m5_fit(pairs, "dG", True), m5_fit(pairs, "dT", False)
    return {"G": g, "T": t, "gap": {r: (g[r] - t[r]) / 100.0 for r in correct}, "pairs": len(pairs),
            "starts": len({p["k"] for p in pairs})}


def main():
    labels_path, data_path, rows_path, starts_path, m5_path, halves_path, root, name = sys.argv[1:9]
    correct = dict(CORRECT, **(FOLLOWERS if "--followers" in sys.argv else {}))
    game = {r["k"]: r["game"] for r in (json.loads(l) for l in open(starts_path)) if "k" in r}
    pairs = [json.loads(l) for l in open(m5_path) if l.strip()]
    main_pairs = [p for p in pairs if p["kind"] != "end" and p["split"] == "train"]
    P = {h: prices([p for p in main_pairs if game[p["k"]] % 2 == h], correct) for h in (0, 1)}
    filed = json.load(open(halves_path))["halves"]
    for h in (0, 1):                                  # the five resources as the analysis line filed them
        for lab, key in (("G", "G_end"), ("T", "T")):
            for r in RES:
                assert abs(P[h][lab][r] - filed[str(h)][key][r]) < 1e-6, (h, lab, r)
    mean_gap = {r: (P[0]["gap"][r] + P[1]["gap"][r]) / 2 for r in correct}
    dr = {}                                           # (k, plan) -> the pair's M5 regressors
    for l in open(rows_path):
        if l.strip():
            q = json.loads(l)
            dr[(q["k"], q["plan"])] = q["x"]
    lab = [json.loads(l) for l in open(labels_path) if l.strip()]
    header, lab = lab[0], lab[1:]
    z = np.load(data_path)
    X, ia, ib, key = z["X"], z["ia"], z["ib"], z["key"]
    keys = [tuple(json.loads(k)) for k in z["keys"]]
    names = feature_names(2, ())
    bias = names.index("bias")
    col = {r: names.index(c) for r, c in correct.items()}
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
    sg = list(signs(False, 2))
    by_key = defaultdict(list)
    for i, k in enumerate(key):
        by_key[k].append(i)
    kidx = {k: i for i, k in enumerate(keys)}
    src_of = {"step1": "step1", "teacher_ends": "old"}
    rows, L0, L, w = [], [], [], []
    count = defaultdict(int)
    var_parts = {"step1": ([], [], []), "teacher_ends": ([], [], [])}     # (L, correction, weight)
    for r in lab:
        if r["split"] != "train":
            continue
        ex = by_key.get(kidx.get((src_of[r["source"]], r["k"], r["plan"])), [])
        if not ex:
            count[f"{r['source']}_no_examples"] += 1
            continue
        count[f"{r['source']}_labels"] += 1
        count[f"{r['source']}_examples"] += len(ex)
        if r["source"] == "step1":
            x = dr.get((r["k"], r["plan"]))
            if x is None:
                count["step1_no_m5_pair"] += 1
                d = 0.0
            else:
                gap = P[1 - game[r["k"]] % 2]["gap"]
                d = sum(gap[res] * x[res] for res in correct)
            var_parts["step1"][0].append(r["label"]); var_parts["step1"][1].append(d)
            var_parts["step1"][2].append(r["weight"])
        for i in ex:
            if r["source"] != "step1":
                d = sum(mean_gap[res] * float(X[ia[i], c] - X[ib[i], c]) for res, c in col.items())
                var_parts["teacher_ends"][0].append(r["label"]); var_parts["teacher_ends"][1].append(d)
                var_parts["teacher_ends"][2].append(r["weight"] / len(ex))
            rows.append(i); L0.append(r["label"]); L.append(r["label"] + d); w.append(r["weight"] / len(ex))

    def wvar(v, wt):
        v, wt = np.asarray(v, float), np.asarray(wt, float)
        m = np.sum(wt * v) / wt.sum()
        return float(np.sum(wt * (v - m) ** 2) / wt.sum())
    variance = {}
    for s_, (lv, cv, wv) in var_parts.items():
        variance[s_] = {"n": len(lv), "var_L": round(wvar(lv, wv), 7), "var_correction": round(wvar(cv, wv), 7),
                        "share": round(wvar(cv, wv) / wvar(lv, wv), 4),
                        "share_unweighted": round(float(np.var(cv) / np.var(lv)), 4),
                        "mean_correction": round(float(np.average(cv, weights=wv)), 6),
                        "mean_abs_correction": round(float(np.average(np.abs(cv), weights=wv)), 6)}
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
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()   # noqa: E731
    rnd = lambda d_: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d_.items()}   # noqa: E731
    price_info = {h: {"G": rnd({k: float(v) for k, v in p["G"].items()}), "T": rnd({k: float(v) for k, v in p["T"].items()}),
                      "gap_prob": {k: round(float(v), 6) for k, v in p["gap"].items()}, "pairs": p["pairs"],
                      "starts": p["starts"]} for h, p in P.items()}
    price_info["teacher_re_run_gap_prob"] = {k: round(float(v), 6) for k, v in mean_gap.items()}
    out = Path(root) / name
    out.mkdir(parents=True, exist_ok=True)
    info = {"moment": "ended", "contrast": True, "horizon_corrected": sorted(correct), "mu": MU, "l2": L2,
            "iters": ITERS, "lr": LR, "start": "zero", "labels": sha(labels_path), "m5_pairs": sha(m5_path),
            "m5_halves": sha(halves_path), "halves": "game % 2 of the start",
            "label_calibration": header, "data_commit": "6f11111", "hold_out_every": 11, "version": 2,
            "stock_zeroed": list(STOCK), "calibration_rows": int(len(ctr)), "examples": int(len(rows)),
            "counts": dict(count), "prices": price_info, "variance": variance,
            "report": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in report.items()},
            "train": train, "seconds": secs}
    to_linear_value(model, 2, (), info).save(out / "ramp-ramp-ended.json")
    shutil.copy(ROOT / "svsim/learn/phased_models/cand-tl-ramp-ramp/ramp-ramp-act.json", out / "ramp-ramp-act.json")
    print(json.dumps({"train": train, "intercept": round(float(model.w[bias]), 4), "seconds": secs,
                      "prices": price_info, "variance": variance, "counts": dict(count)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
