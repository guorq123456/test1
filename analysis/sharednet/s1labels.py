"""How much of S1's labels the deck pair explains (the architecture thread 2026-10-29 08:34Z; a diagnostic: deck ids
go into no feature of any net).

    python analysis/sharednet/s1labels.py --records runs/s1/rec --out analysis/sharednet/s1/labels.json

Every S1 game's result from seat 0's view (1 a win, 0 a loss, 0.5 a draw), and how well each of these predicts it,
by 10-fold cross-validation over games (folds by key % 10), as the Brier score and the share of the constant's Brier
it removes (1 - Brier / Brier of the base rate):
- first: who went first only;
- strength: a logistic model, logit = s[seat 0's deck] - s[seat 1's deck] + b·(seat 0 went first) + c, L2 0.5 on s
  (each deck one strength, whatever it meets);
- pair: the mean result of the training games with the same ordered pair of decks, shrunk toward the strength model's
  prediction with 3 pseudo-games (a pair met about 3 times in 20000 games of 112 decks).
Turn-end rows carry their game's result, so this is also what a position's label owes to the decks alone.

Condition: 对手卡表已知（牌序、手牌未知）.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
from pathlib import Path

import numpy as np


def _games(folder: str) -> list:
    out = []
    for path in sorted(glob.glob(str(Path(folder) / "rec-*.jsonl.gz"))):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                w = r.get("winner")
                y = 1.0 if w == 0 else 0.0 if w == 1 else 0.5
                out.append((r["seed"], r["names"][0], r["names"][1], int(r["first"] == 0), y))
    return out


def _fit_strength(rows, decks: dict, l2: float = 0.5, iters: int = 300, lr: float = 0.5):
    """(s per deck, b, c) by gradient descent on the logistic loss."""
    a = np.array([decks[r[1]] for r in rows])
    o = np.array([decks[r[2]] for r in rows])
    f = np.array([r[3] for r in rows], float)
    y = np.array([r[4] for r in rows], float)
    s = np.zeros(len(decks))
    b = c = 0.0
    n = len(rows)
    for _ in range(iters):
        z = s[a] - s[o] + b * f + c
        p = 1 / (1 + np.exp(-z))
        g = p - y
        gs = np.bincount(a, g, len(decks)) - np.bincount(o, g, len(decks))
        s -= lr * (gs / n * len(decks) / 2 + l2 * s / n * len(decks) / 2)
        b -= lr * float(np.mean(g * f))
        c -= lr * float(np.mean(g))
    return s, b, c


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    games = _games(args.records)
    decks = {d: i for i, d in enumerate(sorted({g[1] for g in games} | {g[2] for g in games}))}
    y = np.array([g[4] for g in games])
    pred = {"constant": np.zeros(len(games)), "first": np.zeros(len(games)), "strength": np.zeros(len(games)),
            "pair": np.zeros(len(games))}
    folds = np.array([g[0] % 10 for g in games])
    for k in range(10):
        tr = [g for g, f in zip(games, folds) if f != k]
        te = np.where(folds == k)[0]
        ytr = np.array([g[4] for g in tr])
        pred["constant"][te] = ytr.mean()
        ftr = np.array([g[3] for g in tr])
        p1, p0 = ytr[ftr == 1].mean(), ytr[ftr == 0].mean()
        pred["first"][te] = [p1 if games[i][3] else p0 for i in te]
        s, b, c = _fit_strength(tr, decks)
        z = np.array([s[decks[games[i][1]]] - s[decks[games[i][2]]] + b * games[i][3] + c for i in te])
        ps = 1 / (1 + np.exp(-z))
        pred["strength"][te] = ps
        sums: dict = {}
        for g in tr:
            key = (g[1], g[2])
            t = sums.setdefault(key, [0.0, 0])
            t[0] += g[4]
            t[1] += 1
        out = []
        for j, i in enumerate(te):
            t = sums.get((games[i][1], games[i][2]), [0.0, 0])
            out.append((t[0] + 3 * ps[j]) / (t[1] + 3))
        pred["pair"][te] = out
    base = float(np.mean((pred["constant"] - y) ** 2))
    result = {"games": len(games), "decks": len(decks),
              "brier": {k: round(float(np.mean((v - y) ** 2)), 5) for k, v in pred.items()},
              "share_of_constant_brier_removed": {k: round(1 - float(np.mean((v - y) ** 2)) / base, 4)
                                                  for k, v in pred.items()},
              "condition": "对手卡表已知（牌序、手牌未知）"}
    text = json.dumps(result, indent=1, ensure_ascii=False)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
