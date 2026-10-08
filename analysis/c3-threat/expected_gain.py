"""How much log loss the C3 dims could take off at most (the architecture thread 16:25: about 0.5 x d^2 x p(1-p),
some 0.001 a point, against held-out intervals of +-0.007): on the league points, the installed p corrected by the
OLS fit of the residual on the existing board terms (linear_controls.FEAT) with the usual controls, then on those
plus the six dims (or the four HP x stage ones); the drop in mean log loss between the two, in sample (an upper
bound), and the second-order 0.5 x mean(d^2 / (p(1-p))) of the dims' own correction d.

    python3 <this> points.jsonl        (points from board_residual.py)

Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import sys

import numpy as np

from linear_controls import FEAT, SIX


def design(sub, cols):
    sides = sorted({(x["deck"], x["opp"]) for x in sub})
    X = []
    for x in sub:
        t = min(x["own_turn"], 12)
        X.append([f(x) for _, f in cols] + [float(x["first"])] + [1.0 if t == u else 0.0 for u in range(2, 13)]
                 + [1.0 if (x["deck"], x["opp"]) == sd else 0.0 for sd in sides[1:]] + [1.0])
    return np.array(X)


def logloss(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def main():
    pts = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
    print("条件：对手卡表已知（牌序、手牌未知）。样本内，是上界。\n")
    print("| 一方 | 点数 | 现有场面项修正后 | + 6 维 | + 4 维 HP × 回合段 | 6 维的下降 | 4 维的下降 | 二阶近似（6 维） |")
    print("|---|---|---|---|---|---|---|---|")
    for name, sub in (("全部 11 个", pts),
                      ("ramp-t 对 pirate-t", [x for x in pts if (x["deck"], x["opp"]) == ("ramp-t", "pirate-t")])):
        p = np.array([x["p"] for x in sub])
        y = np.array([x["result"] for x in sub])
        r = y - p
        fits = {}
        for lab, cols in (("feat", FEAT), ("six", FEAT + SIX), ("hp4", FEAT + SIX[2:])):
            X = design(sub, cols)
            fits[lab] = X @ np.linalg.lstsq(X, r, rcond=None)[0]
        base, six, hp4 = (logloss(p + fits[k], y) for k in ("feat", "six", "hp4"))
        d = fits["six"] - fits["feat"]
        second = 0.5 * float(np.mean(d ** 2 / np.clip(p * (1 - p), 0.02, None)))
        print(f"| {name} | {len(sub)} | {base:.4f} | {six:.4f} | {hp4:.4f} | {base - six:.4f} | {base - hp4:.4f} | "
              f"{second:.4f} |")


if __name__ == "__main__":
    main()
