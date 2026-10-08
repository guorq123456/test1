"""Step B offline: does one shared linear model predict held-out games as well as one model per pairing?

    cd <checkout> && PYTHONPATH=. python3 analysis/universal-bot/holdout.py positions.npz [--out report.txt]

positions.npz from extract.py (all ten pairings of the four tournament decks, 2000 v2 self-play games
each). Games are split by game number (g % 5 == 0 held out, 20%). For each moment (turn end, in turn),
fitted as learn.phased fits (learn.fit, the same signs, own hand/deck roles left out):

- specialist: one model per (my deck, opponent deck) pair, on that pair's training positions only;
- single: one model for everything, no deck information;
- additive: one model, the features plus each feature times "my deck is d" and times "the opponent's
  deck is d" (the w0 + a[me] + b[op] form), interactions not sign-constrained;
- leave ramp-t out: single and additive fitted without any game that has ramp-t in it, scored on the
  ramp-t pairings (ramp-t's own deck terms are then zero: a deck the model never saw).

Reported per pairing and moment: held-out log loss and accuracy (the result of the game from that
position, draws left out). The data are the beginner v2 bot's self-play (Salem 10-08: "still a
beginner bot"); this ranks evaluators on that bot's games, it is not a strength measure.
"""
import argparse
from collections import defaultdict

import numpy as np

from svsim.learn import fit as F
from svsim.learn.encode import ACT, ENDED
from svsim.learn.features import names, signs
from svsim.learn.phased import STOCK


def logloss(z, y):
    return float(np.mean(np.logaddexp(0, z) - y * z))


def augment(X, me, op, nd):
    base = X[:, :-1]
    parts = [base]
    for d in range(nd):
        parts.append(base * (me == d)[:, None])
    for d in range(nd):
        parts.append(base * (op == d)[:, None])
    parts.append(np.stack([(me == d).astype(float) for d in range(nd)] + [(op == d).astype(float) for d in range(nd)], 1))
    parts.append(X[:, -1:])
    return np.concatenate(parts, 1)


def fitpred(Xtr, ytr, Xte, sg, iters):
    w, mean, std, _ = F.fit(Xtr, ytr, None, iters=iters, signs=sg)
    return ((Xte - mean) / std) @ w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("npz")
    ap.add_argument("--out")
    ap.add_argument("--iters", type=int, default=1500)
    ap.add_argument("--cap", type=int, default=250000, help="positions per moment at most (random subset)")
    a = ap.parse_args()
    D = np.load(a.npz, allow_pickle=True)
    decks = list(D["decks"])
    nd = len(decks)
    keep = np.array([0.0 if n.startswith(STOCK) else 1.0 for n in names(False, 2)])
    sg = np.array(signs(False, 2))
    X = D["X"].astype(np.float32) * keep.astype(np.float32)
    y, phase, me, op = D["y"].astype(float), D["phase"], D["me"], D["op"]
    test = (D["game"] % 5 == 0)
    rng = np.random.default_rng(0)
    ramp = decks.index("ramp-t")
    lines = [f"positions {len(y)}, held out {int(test.sum())}; decks {decks}"]
    for ph, label in ((ENDED, "ended"), (ACT, "act")):
        idx = np.flatnonzero(phase == ph)
        if len(idx) > a.cap:                     # memory: a random subset of the moment's positions, the same for all
            idx = np.sort(rng.choice(idx, a.cap, replace=False))
        Xp, yp, mp, op_, tp = X[idx], y[idx], me[idx], op[idx], test[idx]
        tr, te = ~tp, tp
        Xa = augment(Xp, mp, op_, nd).astype(np.float32)
        sga = np.concatenate([sg[:-1], np.zeros(Xa.shape[1] - len(sg)), sg[-1:]])
        n = len(yp)
        preds = {m: np.full(n, np.nan) for m in ("specialist", "single", "additive", "single-noramp", "additive-noramp")}
        preds["single"][te] = fitpred(Xp[tr], yp[tr], Xp[te], sg, a.iters)
        preds["additive"][te] = fitpred(Xa[tr], yp[tr], Xa[te], sga, a.iters)
        noramp = tr & (mp != ramp) & (op_ != ramp)
        hasramp = te & ((mp == ramp) | (op_ == ramp))
        preds["single-noramp"][hasramp] = fitpred(Xp[noramp], yp[noramp], Xp[hasramp], sg, a.iters)
        preds["additive-noramp"][hasramp] = fitpred(Xa[noramp], yp[noramp], Xa[hasramp], sga, a.iters)
        for i in range(nd):
            for j in range(nd):
                k_tr, k_te = tr & (mp == i) & (op_ == j), te & (mp == i) & (op_ == j)
                if k_tr.sum() < 200:
                    continue
                preds["specialist"][k_te] = fitpred(Xp[k_tr], yp[k_tr], Xp[k_te], sg, a.iters)
        lines.append(f"\n== {label}: {n} positions (held out {int(te.sum())}); held-out log loss / accuracy, lower loss is better")
        lines.append(f"{'my deck':10s} {'opponent':10s} {'n':>6s}  " + "  ".join(f"{m:>17s}" for m in preds))
        tot = defaultdict(lambda: [0.0, 0])
        for i in range(nd):
            for j in range(nd):
                k = te & (mp == i) & (op_ == j)
                if k.sum() == 0:
                    continue
                cells = []
                for m, z in preds.items():
                    if np.isnan(z[k]).any():
                        cells.append(f"{'':>17s}")
                        continue
                    ll, acc = logloss(z[k], yp[k]), float(np.mean((z[k] > 0) == (yp[k] > 0.5)))
                    cells.append(f"{ll:9.4f} / {acc:.3f}")
                    tot[m][0] += ll * k.sum(); tot[m][1] += k.sum()
                lines.append(f"{decks[i]:10s} {decks[j]:10s} {int(k.sum()):6d}  " + "  ".join(cells))
        lines.append("position-weighted log loss over the pairings each model was scored on: "
                     + ", ".join(f"{m} {v[0] / v[1]:.4f}" for m, v in tot.items()))
        print("\n".join(lines[-20:]), flush=True)
    text = "\n".join(lines)
    print(text)
    if a.out:
        open(a.out, "w").write(text + "\n")


if __name__ == "__main__":
    main()
