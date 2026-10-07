"""Tables for realized.py's rows: does the teacher's T explain the realized G beyond the control Q?

    python3 analyse.py ROWS.jsonl [--boot 2000]

For all items and by own turn (1-3, 4-6, 7+):
- Spearman rank correlations T~G and Q~G;
- the partial rank correlation of T and G given Q (ranks, then the usual
  partial correlation): what T says about G that Q does not;
- AUC for "keeping c pays" (G > 0) from Q alone and from Q and T together (a
  logistic fit on standardized ranks, scored by 5-fold cross-validation), and
  the gain;
with 95% intervals from resampling items. Also for the third of items with the
smallest |Q| (where the one-turn search hesitates: where a teacher should help),
and the noise ceiling: the rank agreement of G measured on two independent sets
of determinizations (G1, G2), and what that allows for their mean.
"""
import json
import math
import random
import sys

import numpy as np


def ranks(x):
    order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x))
    r[order] = np.arange(len(x))
    # average ties
    xs = np.asarray(x)[order]
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = (i + j) / 2
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    return float(np.corrcoef(ra, rb)[0, 1])


def partial(t, g, q):
    rtg, rtq, rgq = spearman(t, g), spearman(t, q), spearman(g, q)
    den = math.sqrt(max((1 - rtq ** 2) * (1 - rgq ** 2), 1e-12))
    return (rtg - rtq * rgq) / den


def auc(score, y):
    pos = [s for s, v in zip(score, y) if v]
    neg = [s for s, v in zip(score, y) if not v]
    if not pos or not neg:
        return float("nan")
    r = ranks(list(pos) + list(neg))
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) - 1) / 2) / (len(pos) * len(neg)))


def logistic(X, y, iters=50):
    X = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
        W = p * (1 - p) + 1e-9
        H = X.T @ (X * W[:, None]) + 1e-6 * np.eye(X.shape[1])
        w += np.linalg.solve(H, X.T @ (y - p))
    return w


def cv_auc(features, y, folds=5, seed=0):
    n = len(y)
    idx = list(range(n))
    random.Random(seed).shuffle(idx)
    score = np.zeros(n)
    for f in range(folds):
        test = idx[f::folds]
        train = [i for i in idx if i not in set(test)]
        w = logistic(features[train], y[train])
        Xt = np.column_stack([np.ones(len(test)), features[test]])
        score[test] = Xt @ w
    return auc(score, y)


def stats(rows):
    t = np.array([r["T"] for r in rows])
    q = np.array([r["Q"] for r in rows])
    g = np.array([r["G"] for r in rows])
    y = (g > 0).astype(float)
    z = lambda v: (ranks(v) - (len(v) - 1) / 2) / max(len(v), 1)
    fq = z(q)[:, None]
    fqt = np.column_stack([z(q), z(t)])
    a_q, a_qt = cv_auc(fq, y), cv_auc(fqt, y)
    return {"n": len(rows), "TG": spearman(t, g), "QG": spearman(q, g), "TG|Q": partial(t, g, q),
            "AUC_Q": a_q, "AUC_QT": a_qt, "gain": a_qt - a_q, "pays": float(y.mean())}


def ceiling(rows):
    """Agreement of the two independent halves of G, and what it allows for G (the mean of both)."""
    r = spearman([x["G1"] for x in rows], [x["G2"] for x in rows])
    rel = 2 * r / (1 + r) if r > -1 else float("nan")       # Spearman-Brown: the mean of the two halves
    return r, rel, math.sqrt(rel) if rel > 0 else float("nan")


def main():
    path = sys.argv[1]
    boots = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 1000
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r["Q"] is not None]
    if rows and "G1" in rows[0]:
        r, rel, top = ceiling(rows)
        print(f"噪声天花板：两组独立确定化的 G 之间 Spearman {r:+.3f}；两组平均后的信度 {rel:.3f}，"
              f"任何预测和 G 的相关最多约 {top:.3f}")
    absq = sorted(abs(r["Q"]) for r in rows)
    cut = absq[len(absq) // 3] if absq else 0.0
    groups = [("全部", rows)] + [(b, [r for r in rows if (r["own_turn"] <= 3 if b == "1-3" else
                                                       4 <= r["own_turn"] <= 6 if b == "4-6" else r["own_turn"] >= 7)])
                                for b in ("1-3", "4-6", "7+")]
    groups.append((f"|Q|小", [r for r in rows if abs(r["Q"]) <= cut]))   # the third where the one-turn search hesitates
    keys = ("TG", "QG", "TG|Q", "AUC_Q", "AUC_QT", "gain")
    print(f"{'组':<5}{'项':>6}{'留了更好':>9}" + "".join(f"{k:>22}" for k in keys))
    for title, rs in groups:
        if len(rs) < 30:
            continue
        s = stats(rs)
        rng = random.Random(7)
        bs = {k: [] for k in keys}
        for _ in range(boots):
            pick = [rs[rng.randrange(len(rs))] for _ in rs]
            b = stats(pick)
            for k in keys:
                bs[k].append(b[k])
        cells = []
        for k in keys:
            v = sorted(x for x in bs[k] if x == x)
            lo, hi = v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]
            cells.append(f"{s[k]:+.3f}（{lo:+.3f}～{hi:+.3f}）")
        print(f"{title:<5}{s['n']:>6}{s['pays']:>9.0%}" + "".join(f"{c:>22}" for c in cells))


if __name__ == "__main__":
    main()
