"""Is a bonus play point still in hand worth more than the installed evaluation says (the architecture thread 17:44,
after Salem's game-21 note)? On the league's turn-end points: the residual regressed on the bonus indicators of both
sides, alone and with their stage and "a card of cost 2 or less in hand" interactions, on top of the existing board
terms (linear_controls.FEAT) with own turn, side and seat fixed; coefficients with bootstrap SE and 95% intervals
(games resampled), each side's sign, and the in-sample log-loss drop the terms bring (against hpphase's 0.0011).

    python3 <this> points.jsonl [--boot 200]        (points from board_residual.py with `bonus` and `cheap`)

The second player alone has a bonus point, so the indicators live inside the seat; the seat dummy is in the fit.
Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import random
import sys

import numpy as np

from board_residual import _fit
from linear_controls import FEAT, SIX

E = lambda x: x["own_turn"] <= 4
M = lambda x: 5 <= x["own_turn"] <= 7
MAIN = [("my_bonus", lambda x: float(x["my_bonus"])), ("op_bonus", lambda x: float(x["op_bonus"]))]
INTER = MAIN + [("my_bonus × 前期", lambda x: float(x["my_bonus"] and E(x))),
                ("my_bonus × 中期", lambda x: float(x["my_bonus"] and M(x))),
                ("my_bonus × 手里有 2 费以下", lambda x: float(x["my_bonus"] and x["cheap"] > 0)),
                ("op_bonus × 前期", lambda x: float(x["op_bonus"] and E(x))),
                ("op_bonus × 中期", lambda x: float(x["op_bonus"] and M(x)))]


def design(sub, cols):
    sides = sorted({(x["deck"], x["opp"]) for x in sub})
    X = []
    for x in sub:
        t = min(x["own_turn"], 12)
        X.append([f(x) for _, f in cols] + [float(x["first"])] + [1.0 if t == u else 0.0 for u in range(2, 13)]
                 + [1.0 if (x["deck"], x["opp"]) == sd else 0.0 for sd in sides[1:]] + [1.0])
    return np.array(X)


def boot_se(pts, cols, nboot, seed=23):
    X = design(pts, cols)
    y = np.array([x["result"] - x["p"] for x in pts])
    k = len(cols)
    b = np.linalg.lstsq(X, y, rcond=None)[0][:k]
    idx = {}
    for i, x in enumerate(pts):
        idx.setdefault((x["pair"], x["k"], x["seat_a"]), []).append(i)
    keys = list(idx)
    rng = random.Random(seed)
    bs = []
    for _ in range(nboot):
        rows = [i for _ in keys for i in idx[keys[rng.randrange(len(keys))]]]
        bs.append(np.linalg.lstsq(X[rows], y[rows], rcond=None)[0][:k])
    bs = np.array(bs)
    return b, bs.std(axis=0), np.percentile(bs, 2.5, axis=0), np.percentile(bs, 97.5, axis=0)


def logloss(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def gain(sub, extra):
    p = np.array([x["p"] for x in sub])
    y = np.array([x["result"] for x in sub])
    r = y - p
    out = []
    for cols in (FEAT, FEAT + extra):
        X = design(sub, cols)
        out.append(logloss(p + X @ np.linalg.lstsq(X, r, rcond=None)[0], y))
    return out[0] - out[1]


def main():
    path = sys.argv[1]
    nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 200
    pts = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    second = [x for x in pts if not x["first"]]
    print(f"条件：对手卡表已知（牌序、手牌未知）。{len(pts)} 点；控制自己的第几回合、卡组 · 对手、先后手和现有场面项（linear_controls.FEAT）；"
          f"按局重抽 {nboot} 次。\n")
    print("**额外 PP 还可用的点有多少**\n")
    for lab, f in (("我方（后手）还留着", lambda x: x["my_bonus"]), ("对方（后手）还留着", lambda x: x["op_bonus"])):
        n = sum(1 for x in pts if f(x))
        print(f"- {lab}：{n} 点（{n / len(pts):.1%}）；其中前期 {sum(1 for x in pts if f(x) and E(x))}、"
              f"中期 {sum(1 for x in pts if f(x) and M(x))}、后期 {sum(1 for x in pts if f(x) and x['own_turn'] >= 8)}")
    for title, cols in (("一、只放两个指示量", MAIN), ("二、加上回合段和「手里有 2 费以下」的交互", INTER)):
        b, se, lo, hi = boot_se(pts, cols, nboot)
        print(f"\n**{title}**（在现有场面项之上）\n")
        print("| 项 | 系数 | 标准误 | 95% |")
        print("|---|---|---|---|")
        for (n, _), x, s, l, h in zip(cols, b, se, lo, hi):
            mark = "**" if l > 0 or h < 0 else ""
            print(f"| {n} | {mark}{x:+.4f}{mark} | {s:.4f} | {l:+.4f}～{h:+.4f} |")
    print("\n**my_bonus 逐个一方**（只放两个指示量；只有后手才有，点估计和区间）\n")
    print("| 一方（对手） | 后手的点 | my_bonus（95%） |")
    print("|---|---|---|")
    signs = []
    for side in sorted({(x["deck"], x["opp"]) for x in pts}):
        sub = [x for x in pts if (x["deck"], x["opp"]) == side]
        bb, ll, hh = _fit(sub, MAIN, nboot)
        sig = ll[0] > 0 or hh[0] < 0
        signs.append((bb[0], sig))
        mark = "**" if sig else ""
        print(f"| {side[0]}（对 {side[1]}） | {sum(1 for x in sub if not x['first'])} | {mark}{bb[0]:+.4f}（{ll[0]:+.4f}～{hh[0]:+.4f}）{mark} |")
    print(f"\n符号：负 {sum(1 for v, _ in signs if v < 0)} / 正 {sum(1 for v, _ in signs if v > 0)}；"
          f"显著负 {sum(1 for v, s in signs if s and v < 0)} / 显著正 {sum(1 for v, s in signs if s and v > 0)}")
    print("\n**样本内对数损失的下降**（现有场面项修正后，再加这些项；是上界）\n")
    print("| 加的项 | 全部 | 跳费龙一方（ramp-t 的四个一方） |")
    print("|---|---|---|")
    ramp = [x for x in pts if x["deck"] == "ramp-t"]
    for lab, cols in (("两个指示量", MAIN), ("指示量 + 交互", INTER), ("对照：hpphase 4 维", SIX[2:])):
        print(f"| {lab} | {gain(pts, cols):.4f} | {gain(ramp, cols):.4f} |")


if __name__ == "__main__":
    main()
