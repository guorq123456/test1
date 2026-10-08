"""A non-linear turn-end / in-turn evaluation: the same functional features, one tanh hidden layer.

The architecture session, 2026-10-08: the linear models on these features have stopped improving (the
pirate-t mirror's second round 49.0%, the ramp-t mirror's own fit 49.9% against the alias), so the next
try is a small network on the same feature vector (learn.features, version 2: no card ids, no deck ids):

    logit = coef . x + w2 . tanh(W1 x + b1)        x = the standardized features

which `model.LinearValue` already evaluates (its "hidden" layer), so the result is an ordinary
<deck>-<deck>-<moment>.json model in a folder that "+phased=FOLDER" loads. The linear part starts from the
linear fit (learn.fit, as learn.phased does) on the training games and w2 from zero, so training starts at
the linear model and the hidden units add what it can't; everything is then trained together by weighted
log loss (Adam, early stopping on the held-out games). One game in ten (by its line in its file) is held
out and reported for the linear and the network fit side by side.

    python -m svsim.learn.mlp --games A.jsonl B.jsonl --matchup ramp-t-ramp-t --out FOLDER [--hidden 64]
"""
from __future__ import annotations

import argparse
import json
import pickle
from multiprocessing import Pool
from pathlib import Path

import numpy as np


def _rows(job):
    from svsim.learn.phased import _rows as phased_rows
    gid, rest = job
    return gid, phased_rows(rest)


def collect(paths: list, matchup: str, version: int = 2, weights=None, workers: int = 4) -> list:
    """[(game id (file index, line index), rows of learn.phased._rows)] for every game of `paths`."""
    from svsim.learn.model import split_keys
    keys = split_keys(matchup)
    side = tuple(keys) if all(isinstance(k, str) for k in keys) else None
    weights = weights or [1.0] * len(paths)
    jobs = [((f, i), (line, version, w, 1.0, 1.0, None, side))
            for f, (path, w) in enumerate(zip(paths, weights))
            for i, line in enumerate(open(path, encoding="utf-8"))]
    with Pool(workers) as pool:
        return pool.map(_rows, jobs, chunksize=8)


def held_out(gid) -> bool:
    return gid[1] % 10 == 0


def _logloss(z, y, w):
    p = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
    eps = 1e-9
    return float(np.sum(w * -(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))) / np.sum(w))


def _accuracy(z, y):
    return float(np.mean((z > 0) == (y > 0.5)))


def fit_moment(games: list, phase, version: int = 2, hidden: int = 64, epochs: int = 40, lr: float = 1e-3,
               l2: float = 1e-4, batch: int = 2048, seed: int = 0, patience: int = 4, min_epochs: int = 8,
               say=print):
    """(LinearValue with a hidden layer, report) for one moment from collect()'s games."""
    from svsim.learn import fit as F
    from svsim.learn.features import names, signs
    from svsim.learn.model import LinearValue
    from svsim.learn.phased import STOCK
    tr, va = [], []
    for gid, rows in games:
        for r in rows:
            if r[1] == phase and r[3] != 0.5:
                (va if held_out(gid) else tr).append(r)
    X = np.array([r[2] for r in tr], np.float64)
    y = np.array([r[3] for r in tr], np.float64)
    w = np.array([r[5] for r in tr], np.float64)
    Xv = np.array([r[2] for r in va], np.float64)
    yv = np.array([r[3] for r in va], np.float64)
    wv = np.array([r[5] for r in va], np.float64)
    N = names(False, version)
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in N])
    coef, mean, std, report = F.fit(X * keep, y, None, iters=2500, signs=signs(False, version),
                                    weights=None if np.all(w == 1.0) else w)
    coef = np.asarray(coef) * keep
    mean, std = np.asarray(mean), np.asarray(std)
    Xs = ((X * keep - mean) / std) * keep
    Vs = ((Xv * keep - mean) / std) * keep
    lin = {"loss": _logloss(Vs @ coef, yv, wv), "accuracy": _accuracy(Vs @ coef, yv)}
    say(f"  linear: train {len(X)} positions, held-out {len(Xv)}: loss {lin['loss']:.4f}, accuracy {lin['accuracy']:.4f}")
    rng = np.random.default_rng(seed)
    d = X.shape[1]
    p = {"c": coef.copy(), "W1": rng.normal(0, 1 / np.sqrt(d), (d, hidden)) * keep[:, None],
         "b1": np.zeros(hidden), "w2": np.zeros(hidden)}
    m = {k: np.zeros_like(v) for k, v in p.items()}
    v_ = {k: np.zeros_like(v) for k, v in p.items()}

    def logits(A, q):
        return A @ q["c"] + np.tanh(A @ q["W1"] + q["b1"]) @ q["w2"]

    best, best_p, worse, step = float("inf"), None, 0, 0
    for epoch in range(epochs):
        order = rng.permutation(len(Xs))
        for i in range(0, len(order), batch):
            idx = order[i:i + batch]
            A, yy, ww = Xs[idx], y[idx], w[idx]
            h = np.tanh(A @ p["W1"] + p["b1"])
            z = A @ p["c"] + h @ p["w2"]
            g_z = ww * (1 / (1 + np.exp(-np.clip(z, -30, 30))) - yy) / ww.sum()
            dh = np.outer(g_z, p["w2"]) * (1 - h ** 2)
            g = {"c": A.T @ g_z + l2 * p["c"], "w2": h.T @ g_z + l2 * p["w2"],
                 "W1": (A.T @ dh) * keep[:, None] + l2 * p["W1"], "b1": dh.sum(0)}
            step += 1
            for k in p:
                m[k] = 0.9 * m[k] + 0.1 * g[k]
                v_[k] = 0.999 * v_[k] + 0.001 * g[k] ** 2
                p[k] = p[k] - lr * (m[k] / (1 - 0.9 ** step)) / (np.sqrt(v_[k] / (1 - 0.999 ** step)) + 1e-8)
        val = _logloss(logits(Vs, p), yv, wv)
        say(f"  epoch {epoch + 1}: held-out loss {val:.4f}")
        if val < best - 1e-5:
            best, best_p, worse = val, {k: x.copy() for k, x in p.items()}, 0
        else:
            worse += 1
            if worse >= patience and epoch + 1 >= min_epochs:   # w2 starts at zero: give the units time to grow
                break
    zv = logits(Vs, best_p)
    net = {"loss": _logloss(zv, yv, wv), "accuracy": _accuracy(zv, yv),
           "train_loss": _logloss(logits(Xs, best_p), y, w)}
    say(f"  network: held-out loss {net['loss']:.4f}, accuracy {net['accuracy']:.4f} (train loss {net['train_loss']:.4f})")
    model = LinearValue([float(x) for x in best_p["c"] * keep], [float(x) for x in mean], [float(x) for x in std],
                        False, {}, version=version,
                        hidden={"W1": (best_p["W1"] * keep[:, None]).tolist(), "b1": best_p["b1"].tolist(),
                                "w2": best_p["w2"].tolist()})
    return model, {"train_positions": len(X), "held_out_positions": len(Xv), "linear": lin, "network": net,
                   "linear_train": {k: float(v) for k, v in report.items()}}


def main() -> None:
    from svsim.learn.model import split_keys
    from svsim.learn.netdata import ACT, ENDED
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", nargs="+", required=True)
    parser.add_argument("--file-weights", type=float, nargs="+", default=None)
    parser.add_argument("--matchup", required=True, help="<deck>-<deck> (cards.decks.NAMED keys)")
    parser.add_argument("--out", required=True)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--moments", nargs="+", default=["ended", "act"], choices=("ended", "act"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch", type=int, default=2048)
    parser.add_argument("--cache", default=None, help="a pickle of the collected rows: written once, then read")
    args = parser.parse_args()
    if args.cache and Path(args.cache).exists():
        games = pickle.loads(Path(args.cache).read_bytes())
    else:
        games = collect(args.games, args.matchup, 2, args.file_weights, args.workers)
        if args.cache:
            Path(args.cache).write_bytes(pickle.dumps(games))
    print(f"{len(games)} games, held out {sum(held_out(g) for g, _ in games)} (one in ten by line)", flush=True)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    mine, theirs = (k if isinstance(k, str) else k.name.lower() for k in split_keys(args.matchup))
    for label in args.moments:
        print(f"{label}:", flush=True)
        model, report = fit_moment(games, {"ended": ENDED, "act": ACT}[label], 2, args.hidden, args.epochs, args.lr,
                                   batch=args.batch, seed=args.seed, say=lambda t: print(t, flush=True))
        model.info = {"deck": mine, "opponent": theirs, "moment": label, "kind": "mlp", "hidden": args.hidden,
                      "epochs": args.epochs, "lr": args.lr, "batch": args.batch,
                      "games": args.games, "file_weights": args.file_weights, "held_out": "line % 10 == 0",
                      "report": report}
        model.save(out / f"{args.matchup}-{label}.json")
        print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
