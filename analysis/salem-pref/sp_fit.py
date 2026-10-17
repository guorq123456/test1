"""Teach the turn-end model Salem's own choices (the architecture thread 2026-10-10 16:49Z): cand-kc-ramp-ramp's
objective plus a preference term, his turn end above the others the installed search considered, with lambda chosen
by leaving whole games out. Condition: the opponent's deck list is known (order and hand not).

- **Model:** cand-kc's form, linear over version 2 + kclock (84 columns), its standardization (mean / std from its
  file), the version-2 signs, the stock prefixes held at zero. No card ids, deck ids or pairing; no per-card table.
- **Loss:**
  - cand-kc's: the weighted contrast error on the step-1 labels' training split, + 0.03 x calibration log loss,
    + L2 1e-4 (not the intercept);
  - + lambda x preference: the mean over Salem's turns of the mean over its other candidates c of
    softplus(-(E(Salem's end) - E(c))), E in logit units.
- **Data:** sp_extract.py's Ramp mirror turns (the other pairings are kept apart, not fitted). A turn with no other
  candidate gives no pairs.
- **Optimiser:** start at cand-kc's coefficients, full-batch Adam, lr 0.01, 600 iterations.
- **lambda:** chosen from {0, 0.003, 0.01, 0.03, 0.1, 0.3} by leaving whole games out, 9 folds of 3 Ramp-mirror
  games (games sorted by id, fold = index mod 9).
  - Rule, fixed before any fit: the lambda with the highest held-out pairwise accuracy against the bot, among those
    whose mean held-out self-play contrast error (the labels' "val" split) is within +3% of lambda 0's; ties go to
    the smaller lambda.
  - Then one fit on every Ramp-mirror game at that lambda: cand-sp-ramp-ramp.
- **Reads, on held-out games** (each turn scored by the fold model that didn't see its game):
  - top-1: Salem's end ranks first among the turn's candidates;
  - pairwise against the bot: Salem's end above the installed agent's own play of the turn, where they differ;
  - pairwise against all candidates.
  The installed model and cand-kc are read on the same turns (no fitting involved).

    python3 sp_fit.py TURNS.jsonl LABELS KC_DATA.npz OUT_ROOT --out-json folds.json [--workers 4]
"""
import argparse
import hashlib
import json
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
MU, L2, LR, ITERS = 0.03, 1e-4, 0.01, 600
LAMBDAS = (0.0, 0.003, 0.01, 0.03, 0.1, 0.3)
FOLDS = 9
RAMP = ["跳费龙", "跳费龙"]
KC = ROOT / "svsim/learn/phased_models/cand-kc-ramp-ramp/ramp-ramp-ended.json"
INSTALLED = ROOT / "svsim/learn/phased_models/ramp-ramp-ended.json"
D = {}


def sig(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def _examples(lab, key, keys, split):
    by_key = defaultdict(list)
    for i, k in enumerate(key):
        by_key[k].append(i)
    kidx = {k: i for i, k in enumerate(keys)}
    src_of = {"step1": "step1", "teacher_ends": "old"}
    rows, L, w = [], [], []
    for r in lab:
        if r["split"] != split:
            continue
        ex = by_key.get(kidx.get((src_of[r["source"]], r["k"], r["plan"])), [])
        for i in ex:
            rows.append(i); L.append(r["label"]); w.append(r["weight"] / len(ex))
    return np.array(rows), np.array(L), np.array(w)


def load(turns_path, labels_path, data_path):
    from svsim.learn.contrast import feature_names
    from svsim.learn.features import signs
    from svsim.learn.phased import STOCK
    kc = json.loads(KC.read_text())
    names = feature_names(2, ("kclock",))
    assert kc["names"] == names
    base = len(feature_names(2, ()))
    mean, std = np.array(kc["mean"]), np.array(kc["std"])
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
    stdz = lambda M: ((np.asarray(M, float) * keep - mean) / std).astype(np.float32)   # noqa: E731
    lab = [json.loads(l) for l in open(labels_path) if l.strip()][1:]
    z = np.load(data_path)
    X, ia, ib, key = z["X"], z["ia"], z["ib"], z["key"]
    keys = [tuple(json.loads(k)) for k in z["keys"]]
    r, L, w = _examples(lab, key, keys, "train")
    vr, vL, vw = _examples(lab, key, keys, "val")
    ctr = np.where(z["Cg"] % 11 != 0)[0]
    turns = [json.loads(l) for l in open(turns_path) if l.strip()]
    ramp = [t for t in turns if t["pairing"] == RAMP]
    games = sorted({t["game"] for t in ramp})
    fold_of = {g: i % FOLDS for i, g in enumerate(games)}
    P = []
    for t in ramp:
        xs = np.array([c["x"] for c in t["candidates"]], float)
        s = next(i for i, c in enumerate(t["candidates"]) if c["salem"])
        b = next((i for i, c in enumerate(t["candidates"]) if c["bot"]), None)
        P.append({"game": t["game"], "fold": fold_of[t["game"]], "X": stdz(xs), "raw": xs, "s": s, "b": b,
                  "turn": t["turn"]})
    inst = json.loads(INSTALLED.read_text())
    D.update(names=names, base=base, keep=keep, mean=mean, std=std, kc=kc, inst=inst,
             A=stdz(X[ia[r]]), B=stdz(X[ib[r]]), L=L, w=w,
             VA=stdz(X[ia[vr]]), VB=stdz(X[ib[vr]]), VL=vL, Vw=vw,
             C=stdz(z["Cx"][ctr]), y=z["Cy"][ctr], P=P, games=games, fold_of=fold_of,
             signs=list(signs(False, 2)) + [0] * (len(names) - base), bias=names.index("bias"))


def _pref_pairs(turn_ids):
    """Stacked (Salem row, other row, weight) over the given turns: each turn's pairs weigh 1 / its pair count."""
    S, O, W = [], [], []
    for i in turn_ids:
        p = D["P"][i]
        n = len(p["X"])
        if n < 2:
            continue
        for c in range(n):
            if c != p["s"]:
                S.append(p["X"][p["s"]]); O.append(p["X"][c]); W.append(1.0 / (n - 1))
    if not S:
        return None
    W = np.array(W)
    return np.array(S, np.float32), np.array(O, np.float32), W / len({i for i in turn_ids if len(D["P"][i]["X"]) > 1})


def fit(lam, train_turns):
    from svsim.learn.fit import project
    w = np.array(D["kc"]["coef"], float)
    A, B, L, wt, C, y = D["A"], D["B"], D["L"], D["w"], D["C"], D["y"]
    pairs = _pref_pairs(train_turns) if lam > 0 else None
    bias, sg, keep = D["bias"], D["signs"], D["keep"]
    mask = np.ones_like(w)
    mask[bias] = 0.0
    fixed = (keep == 0) & (np.arange(len(w)) != bias)
    m, v = np.zeros_like(w), np.zeros_like(w)
    W = wt.sum()
    for t in range(1, ITERS + 1):
        w32 = w.astype(np.float32)
        za, zb = A @ w32, B @ w32
        pa, pb = sig(za), sig(zb)
        d = pa - pb - L
        g = (A.T @ (2 * wt * d * pa * (1 - pa) / W).astype(np.float32) -
             B.T @ (2 * wt * d * pb * (1 - pb) / W).astype(np.float32)).astype(float)
        zc = C @ w32
        g += MU * (C.T @ ((sig(zc) - y) / len(C)).astype(np.float32)).astype(float)
        g += 2 * L2 * w * mask
        if pairs is not None:
            S, O, pw = pairs
            diff = (S - O) @ w32
            g += lam * ((S - O).T @ (-pw * sig(-diff)).astype(np.float32)).astype(float)
        g[fixed] = 0.0
        m = 0.9 * m + 0.1 * g
        v = 0.999 * v + 0.001 * g * g
        w -= LR * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
        held = w[bias]
        w = project(w, sg)
        w[bias] = held
    return w


def _val_mse(w):
    w32 = w.astype(np.float32)
    d = sig(D["VA"] @ w32) - sig(D["VB"] @ w32)
    return float(np.sum(D["Vw"] * (d - D["VL"]) ** 2) / D["Vw"].sum())


def _inst_logits(raw):
    inst = D["inst"]
    n = len(inst["names"])
    return ((raw[:, :n] - np.array(inst["mean"])) / np.array(inst["std"])) @ np.array(inst["coef"])


def read_turns(score, turn_ids):
    """top-1, pairwise vs the bot, pairwise vs all: (hits, count) each."""
    top = [0, 0]; bot = [0, 0]; allp = [0, 0]
    for i in turn_ids:
        p = D["P"][i]
        z = score(p)
        n = len(z)
        if n >= 2:
            top[1] += 1
            top[0] += int(np.argmax(z) == p["s"] and np.sum(z == z[p["s"]]) == 1)
            for c in range(n):
                if c != p["s"]:
                    allp[1] += 1
                    allp[0] += int(z[p["s"]] > z[c])
        if p["b"] is not None and p["b"] != p["s"]:
            bot[1] += 1
            bot[0] += int(z[p["s"]] > z[p["b"]])
    return {"top1": top, "vs_bot": bot, "vs_all": allp}


def _cv_job(item):
    lam, fold = item
    train = [i for i, p in enumerate(D["P"]) if p["fold"] != fold]
    test = [i for i, p in enumerate(D["P"]) if p["fold"] == fold]
    w = fit(lam, train)
    r = read_turns(lambda p: p["X"] @ w.astype(np.float32), test)
    return lam, fold, r, _val_mse(w), w.tolist()


def main():
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("turns"); ap.add_argument("labels"); ap.add_argument("data"); ap.add_argument("out_root")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    load(args.turns, args.labels, args.data)
    t0 = time.time()
    jobs = [(lam, f) for lam in LAMBDAS for f in range(FOLDS)]
    with Pool(args.workers, initializer=load, initargs=(args.turns, args.labels, args.data)) as pool:
        res = pool.map(_cv_job, jobs, chunksize=1)
    agg = {}
    fold_w = {}
    for lam, fold, r, mse, w in res:
        a = agg.setdefault(lam, {"top1": [0, 0], "vs_bot": [0, 0], "vs_all": [0, 0], "val_mse": []})
        for k in ("top1", "vs_bot", "vs_all"):
            a[k][0] += r[k][0]; a[k][1] += r[k][1]
        a["val_mse"].append(mse)
        fold_w[(lam, fold)] = w
    table = {}
    for lam, a in sorted(agg.items()):
        table[lam] = {k: round(a[k][0] / a[k][1], 4) for k in ("top1", "vs_bot", "vs_all")}
        table[lam]["counts"] = {k: a[k] for k in ("top1", "vs_bot", "vs_all")}
        table[lam]["val_mse_mean"] = round(float(np.mean(a["val_mse"])), 6)
    base_mse = table[0.0]["val_mse_mean"]
    ok = [lam for lam in LAMBDAS if table[lam]["val_mse_mean"] <= 1.03 * base_mse]
    best = max(ok, key=lambda lam: (table[lam]["vs_bot"], -lam))
    all_turns = list(range(len(D["P"])))
    kc_w = np.array(D["kc"]["coef"], np.float32)
    baselines = {"installed": read_turns(lambda p: _inst_logits(p["raw"]), all_turns),
                 "cand-kc": read_turns(lambda p: p["X"] @ kc_w, all_turns)}
    baselines = {m: {k: (round(v[0] / v[1], 4), v) for k, v in r.items()} for m, r in baselines.items()}
    w_final = fit(best, all_turns)
    secs = round(time.time() - t0)
    # the model file
    from svsim.learn.model import LinearValue
    out = Path(args.out_root) / "cand-sp-ramp-ramp"
    out.mkdir(parents=True, exist_ok=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()   # noqa: E731
    info = {"moment": "ended", "contrast": True, "extras": ["kclock"], "preference": "Salem's turn ends",
            "lambda": best, "lambdas": list(LAMBDAS), "folds": FOLDS, "mu": MU, "l2": L2, "lr": LR, "iters": ITERS,
            "start": "cand-kc-ramp-ramp", "turns": args.turns and sha(args.turns), "labels": sha(args.labels),
            "ramp_turns": len(D["P"]), "ramp_games": len(D["games"]), "cv": {str(k): v for k, v in table.items()},
            "baselines": baselines, "val_mse_final": round(_val_mse(w_final), 6), "seconds": secs}
    LinearValue([float(x) for x in w_final], D["kc"]["mean"], D["kc"]["std"], False, info, version=2,
                extras=("kclock",)).save(out / "ramp-ramp-ended.json")
    shutil.copy(KC.parent / "ramp-ramp-act.json", out / "ramp-ramp-act.json")
    Path(args.out_json).write_text(json.dumps({"lambda": best, "cv": {str(k): v for k, v in table.items()},
                                               "baselines": baselines, "fold_of": D["fold_of"],
                                               "fold_weights": {f"{k[0]}|{k[1]}": v for k, v in fold_w.items()},
                                               "final": w_final.tolist(), "val_mse_final": info["val_mse_final"]}))
    print(json.dumps({"lambda": best, "cv": {str(k): {kk: vv for kk, vv in v.items() if kk != "counts"} for k, v in table.items()},
                      "baselines": {m: {k: v[0] for k, v in r.items()} for m, r in baselines.items()},
                      "val_mse_final": info["val_mse_final"], "ramp_turns": len(D["P"]), "seconds": secs}, indent=1))


if __name__ == "__main__":
    main()
