"""C3 candidates side by side: the residual regressed on a candidate set at once (own turn, side and seat held
fixed, games resampled), then the strongest candidate's slope side by side (each of the 11 sides), so the
<= 6 functional features handed to the build stand on a joint fit, not on one-at-a-time slopes.

    python3 <this> points.jsonl [--boot 200]        (points from board_residual.py)

Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import sys

from board_residual import _fit

EARLY = lambda x: x["own_turn"] <= 4
MID = lambda x: 5 <= x["own_turn"] <= 7
LATE = lambda x: x["own_turn"] >= 8


def pressure(x):
    """The opponent's board threat (attack past my Ward defense next turn) over my leader HP, capped at 1.5."""
    return min(x["op_threat"] / max(x["my_hp"], 1), 1.5)


def my_pressure(x):
    return min(x["my_threat"] / max(x["op_hp"], 1), 1.5)


CANDIDATES = [
    ("压力 = 对方威胁 ÷ 我方 HP（封顶 1.5）", pressure),
    ("压力 × 前期（1–4）", lambda x: pressure(x) if EARLY(x) else 0.0),
    ("我方 HP × 前期（1–4）", lambda x: float(x["my_hp"]) if EARLY(x) else 0.0),
    ("我方 HP × 中期（5–7）", lambda x: float(x["my_hp"]) if MID(x) else 0.0),
    ("随从数差（对方 − 我方）", lambda x: float(x["op_n"] - x["my_n"])),
    ("解不掉的对方体力 = max(对方随从总体力 − 3 × 我方手牌解场量, 0)", lambda x: max(x["op_life"] - 3 * x["removal"], 0.0)),
    ("反压力 = 我方威胁 ÷ 对方 HP（封顶 1.5）", my_pressure),
]


def main():
    path = sys.argv[1]
    nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 200
    pts = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    print(f"条件：对手卡表已知（牌序、手牌未知）。{len(pts)} 点；残差同时对候选回归，固定自己的第几回合、卡组 · 对手和先后手；"
          f"区间 95%，按局重抽 {nboot} 次。\n")
    b, lo, hi = _fit(pts, CANDIDATES, nboot)
    print("**候选联合回归**\n")
    print("| 候选 | 系数（95%） |")
    print("|---|---|")
    for (name, _), x, l, h in zip(CANDIDATES, b, lo, hi):
        mark = "**" if l > 0 or h < 0 else ""
        print(f"| {name} | {mark}{x:+.4f}（{l:+.4f}～{h:+.4f}）{mark} |")
    print("\n**压力的斜率，逐个一方**（一次一个一方，控制自己的第几回合和先后手）\n")
    print("| 一方（对手） | 点数 | 压力的斜率（95%） | 压力均值 |")
    print("|---|---|---|---|")
    for side in sorted({(x["deck"], x["opp"]) for x in pts}):
        sub = [x for x in pts if (x["deck"], x["opp"]) == side]
        bb, ll, hh = _fit(sub, [("压力", pressure)], nboot)
        mark = "**" if ll[0] > 0 or hh[0] < 0 else ""
        mean = sum(pressure(x) for x in sub) / len(sub)
        print(f"| {side[0]}（对 {side[1]}） | {len(sub)} | {mark}{bb[0]:+.4f}（{ll[0]:+.4f}～{hh[0]:+.4f}）{mark} | {mean:.3f} |")


if __name__ == "__main__":
    main()
