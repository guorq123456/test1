"""Per cell and per pairing, how much +xprune's pruning acts in a gate's games (README-xprune-np.md, diagnostic):
the companion replay's records (one file per cell, lethal2_games.py play), counted as xprune_count.py does: among
main-phase decisions with 2+ legal moves, the share with a discard choice and with pruning active
(XPrune(3, 3, "cost") vetoes a legal move), and pruning-active decisions per game; A and B apart.
Condition: the opponent's deck list is known (order and hand not).

    python3 xprune_pairings.py ../gates/xprune-cross/records/rec_*.jsonl --out ../gates/xprune-cross/pairings.txt
"""
import argparse
import json
from multiprocessing import Pool
from pathlib import Path

from xprune_count import _game

NAMES = {"elf-t": "连击妖", "nemesis-t": "机锋", "pirate-t": "旗皇", "ramp-t": "跳费龙（比赛版）"}


def tally(games, res, side):
    n = sum(r[side][0] for r in res)
    d = sum(r[side][1] for r in res)
    c = sum(r[side][2] for r in res)
    return n, d, c, len(games)


def fmt(t):
    n, d, c, g = t
    return f"{n} | {d / n:.1%} | {c / n:.1%} | {c / g:.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    cells = {}
    with Pool(args.workers) as pool:
        for f in args.files:
            a, b = Path(f).stem[len("rec_"):].split("_vs_")       # rec_<A's deck>_vs_<B's deck>.jsonl
            games = [json.loads(x) for x in open(f, encoding="utf-8") if x.strip()]
            cells[(a, b)] = (games, pool.map(_game, games))
    head = "| 决策（合法走法 ≥ 2） | 含弃牌选择 | 剪枝起作用 | 每局剪枝起作用的次数 |"
    out = ["条件：对手卡表已知（牌序、手牌未知）。+xprune 非镜像对位门里剪枝起作用的多少（README-xprune-np.md 的诊断）", "",
           "**每格**（A 是开剪枝的一方）", "", "| A 的卡组 对 B 的卡组 | 局 | 方 " + head, "|---|---|---|---|---|---|---|"]
    for (a, b), (games, res) in cells.items():
        for side in ("A", "B"):
            out.append(f"| {NAMES[a]} 对 {NAMES[b]} | {len(games)} | {side} | {fmt(tally(games, res, side))} |")
    out += ["", "**每个对位**（两个方向合起来）", "", "| 对位 | 局 | 方 " + head, "|---|---|---|---|---|---|---|"]
    seen = set()
    for (a, b) in cells:
        key = tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        both = [cells[k] for k in (key, key[::-1]) if k in cells]
        games = [g for gs, _ in both for g in gs]
        res = [r for _, rs in both for r in rs]
        for side in ("A", "B"):
            out.append(f"| {NAMES[key[0]]} — {NAMES[key[1]]} | {len(games)} | {side} | {fmt(tally(games, res, side))} |")
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
