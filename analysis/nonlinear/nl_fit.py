"""A non-linear turn-end model (the architecture thread 2026-10-10 13:21Z): cand-kc-ramp-ramp's examples, features
(version 2 + the kclock columns) and contrast objective, with one small hidden layer added, so that what a feature
is worth can change with the position. Condition: the opponent's deck list is known (order and hand not).

Form (learn.model.LinearValue with `hidden`, read by the search as it is):
    E(x) = w . x + w2 . tanh(x W1 + b1),   x = (raw - mean) / std,
- the linear part starts at cand-kc's coefficients (the same mean / std), the hidden layer at W1 ~ N(0, 0.1^2),
  b1 = 0, w2 = 0: the fit starts exactly at cand-kc;
- H = 16 hidden units; the stock columns (learn.phased.STOCK) and the bias column don't feed the hidden layer (their
  W1 rows held at 0); the linear part keeps the version-2 signs (the kclock columns free); the hidden part is free.
- Loss: cand-tl's: sum w (sigma(E(a)) - sigma(E(b)) - L)^2 / sum w + mu x calibration log loss + L2 (all weights
  but the intercept), mu 0.03, L2 1e-4; full-batch Adam, lr 0.01, 1500 iterations.
- No card ids, deck ids or pairing as inputs; no per-card table.
All settings fixed before any held-out read. Held out: the labels' split "val" (never used in fitting): weighted
contrast MSE and weighted sign agreement (sign of sigma(E(a)) - sigma(E(b)) against the label's), for cand-kc and
this model, on the same examples (each label's weight spread over its kept determinizations, as in training).

    python3 nl_fit.py LABELS KC_DATA.npz OUT_ROOT [--hidden 16] [--iters 1500]
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
from svsim.learn.contrast import feature_names
from svsim.learn.features import signs
from svsim.learn.fit import project
from svsim.learn.model import LinearValue
from svsim.learn.phased import STOCK

MU, L2, LR = 0.03, 1e-4, 0.01
EXTRAS = ("kclock",)
NAME = "cand-nl-ramp-ramp"
BASE = ROOT / "svsim/learn/phased_models/cand-kc-ramp-ramp"


def sig(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


class Net:
    def __init__(self, w, H, rng, feed):
        n = len(w)
        self.w = np.asarray(w, float)
        self.W1 = rng.normal(0, 0.1, (n, H)) * feed[:, None]
        self.b1 = np.zeros(H)
        self.w2 = np.zeros(H)
        self.feed = feed

    def forward(self, X):
        h = np.tanh(X @ self.W1.astype(X.dtype) + self.b1.astype(X.dtype))
        return (X @ self.w.astype(X.dtype) + h @ self.w2.astype(X.dtype)).astype(float), h

    def grads(self, X, h, dz):
        dz32 = dz.astype(X.dtype)
        gw = X.T @ dz32
        gw2 = h.T @ dz32
        dh = np.outer(dz32, self.w2.astype(X.dtype)) * (1 - h * h)
        return gw.astype(float), (X.T @ dh).astype(float), dh.sum(0).astype(float), gw2.astype(float)


def loss_grads(net, A, B, L, w, C, y, bias):
    za, ha = net.forward(A)
    zb, hb = net.forward(B)
    pa, pb = sig(za), sig(zb)
    d = pa - pb - L
    W = w.sum()
    loss = float(np.sum(w * d * d) / W)
    ga = net.grads(A, ha, 2 * w * d * pa * (1 - pa) / W)
    gb = net.grads(B, hb, -2 * w * d * pb * (1 - pb) / W)
    zc, hc = net.forward(C)
    loss += MU * float(np.mean(np.logaddexp(0, zc) - y * zc))
    gc = net.grads(C, hc, MU * (sig(zc) - y) / len(C))
    g = [a + b + c for a, b, c in zip(ga, gb, gc)]
    mask = np.ones_like(net.w)
    mask[bias] = 0.0
    loss += L2 * float(np.sum((net.w * mask) ** 2) + np.sum(net.W1 ** 2) + np.sum(net.w2 ** 2))
    g[0] = g[0] + 2 * L2 * net.w * mask
    g[1] = (g[1] + 2 * L2 * net.W1) * net.feed[:, None]
    g[3] = g[3] + 2 * L2 * net.w2
    return loss, g


def examples(lab, key, keys, split):
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


def read(z_a, z_b, L, w):
    d = sig(z_a) - sig(z_b)
    return {"contrast_mse_w": round(float(np.sum(w * (d - L) ** 2) / w.sum()), 6),
            "sign_w": round(float(np.sum(w * (np.sign(d) == np.sign(L))) / w.sum()), 4), "examples": int(len(L))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labels")
    ap.add_argument("data")
    ap.add_argument("out_root")
    ap.add_argument("--hidden", type=int, default=16)
    ap.add_argument("--iters", type=int, default=1500)
    args = ap.parse_args()
    lab = [json.loads(l) for l in open(args.labels) if l.strip()]
    header, lab = lab[0], lab[1:]
    z = np.load(args.data)
    X, ia, ib, key = z["X"], z["ia"], z["ib"], z["key"]
    keys = [tuple(json.loads(k)) for k in z["keys"]]
    names = feature_names(2, EXTRAS)
    base = len(feature_names(2, ()))
    bias = names.index("bias")
    kc = json.loads((BASE / "ramp-ramp-ended.json").read_text())
    assert kc["names"] == names
    mean, std = np.array(kc["mean"]), np.array(kc["std"])
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names])
    feed = keep.copy()
    feed[bias] = 0.0
    sg = list(signs(False, 2)) + [0] * (len(names) - base)
    stdz = lambda M: ((np.asarray(M, float) * keep - mean) / std).astype(np.float32)   # noqa: E731  (as in training)
    rows, L, w = examples(lab, key, keys, "train")
    A, B = stdz(X[ia[rows]]), stdz(X[ib[rows]])
    ctr = np.where(z["Cg"] % 11 != 0)[0]
    C, y = stdz(z["Cx"][ctr]), z["Cy"][ctr]
    vr, vL, vw = examples(lab, key, keys, "val")
    VA, VB = stdz(X[ia[vr]]), stdz(X[ib[vr]])
    net = Net(kc["coef"], args.hidden, np.random.default_rng(0), feed)
    lin0 = net.w.copy()
    params = ["w", "W1", "b1", "w2"]
    m = [np.zeros_like(getattr(net, p)) for p in params]
    v = [np.zeros_like(getattr(net, p)) for p in params]
    t0 = time.time()
    log = []
    for t in range(1, args.iters + 1):
        loss, g = loss_grads(net, A, B, L, w, C, y, bias)
        for i, p in enumerate(params):
            m[i] = 0.9 * m[i] + 0.1 * g[i]
            v[i] = 0.999 * v[i] + 0.001 * g[i] * g[i]
            setattr(net, p, getattr(net, p) - LR * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8))
        held = net.w[bias]
        net.w = project(net.w, sg)
        net.w[bias] = held
        net.W1 = net.W1 * feed[:, None]
        if t % 100 == 0 or t == 1:
            log.append((t, round(loss, 6)))
            print(f"iter {t} loss {loss:.6f} ({time.time() - t0:.0f}s)", flush=True)
    secs = round(time.time() - t0)
    train = read(net.forward(A)[0], net.forward(B)[0], L, w)
    held_nl = read(net.forward(VA)[0], net.forward(VB)[0], vL, vw)
    lin = lambda M: (M @ lin0.astype(M.dtype)).astype(float)   # noqa: E731  (cand-kc itself)
    held_kc = read(lin(VA), lin(VB), vL, vw)
    train_kc = read(lin(A), lin(B), L, w)
    zc = net.forward(C)[0]
    out = Path(args.out_root) / NAME
    out.mkdir(parents=True, exist_ok=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()   # noqa: E731
    info = {"moment": "ended", "contrast": True, "extras": list(EXTRAS), "form": "linear + tanh hidden layer",
            "hidden_units": args.hidden, "start": "cand-kc-ramp-ramp (hidden part at zero output)", "mu": MU,
            "l2": L2, "lr": LR, "iters": args.iters, "optimizer": "full-batch Adam", "labels": sha(args.labels),
            "label_calibration": header, "data_commit": "6f11111", "hold_out_every": 11, "version": 2,
            "stock_zeroed": list(STOCK), "calibration_rows": int(len(ctr)), "examples": int(len(rows)),
            "train": train, "calib_logloss": round(float(np.mean(np.logaddexp(0, zc) - y * zc)), 4),
            "held_out_val": held_nl, "held_out_val_cand_kc": held_kc, "loss_log": log, "seconds": secs}
    hidden = {"W1": net.W1.tolist(), "b1": net.b1.tolist(), "w2": net.w2.tolist()}
    LinearValue([float(x) for x in net.w], kc["mean"], kc["std"], False, info, version=2, hidden=hidden,
                extras=EXTRAS).save(out / "ramp-ramp-ended.json")
    shutil.copy(BASE / "ramp-ramp-act.json", out / "ramp-ramp-act.json")
    print(json.dumps({"train": train, "train_cand_kc": train_kc, "held_out_val": held_nl,
                      "held_out_val_cand_kc": held_kc, "calib_logloss": info["calib_logloss"],
                      "hidden_output_scale": round(float(np.std(net.forward(A)[1] @ net.w2)), 4),
                      "seconds": secs}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
