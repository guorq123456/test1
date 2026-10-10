"""The +xprune non-mirror (NI) gate's per-cell read (README-xprune-cross.md): each cell's and each pairing's point
estimate (both directions together), and the milliseconds per searched decision pooled over the cells. The
judgement itself is pooled.py's stratified bootstrap over the same files.
Condition: the opponent's deck list is known (order and hand not).

    python3 xprune_cells.py ../gates/xprune-cross/gate_*.jsonl --out ../gates/xprune-cross/cells.txt
"""
import argparse
import json
import math
from pathlib import Path

NAMES = {"elf-t": "连击妖", "nemesis-t": "机锋", "pirate-t": "旗皇", "ramp-t": "跳费龙（比赛版）"}


def rows(path):
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def score(r):
    return sum(r["points"]) / len(r["points"])


def ci(xs):
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
    h = 1.96 * sd / math.sqrt(len(xs))
    return m, m - h, m + h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    cells = {}
    for f in args.files:
        a, b = Path(f).stem[len("gate_"):].split("_vs_")      # gate_<A's deck>_vs_<B's deck>.jsonl
        cells[(a, b)] = rows(f)
    out = ["条件：对手卡表已知（牌序、手牌未知）。+xprune 非镜像对位门的分格读数（README-xprune-cross.md）", "",
           "| A 的卡组 对 B 的卡组 | 对 | A 得分（正态 95%） |", "|---|---|---|"]
    for (a, b), rs in cells.items():
        m, lo, hi = ci([score(r) for r in rs])
        out.append(f"| {NAMES[a]} 对 {NAMES[b]} | {len(rs)} | {m:.1%}（{lo:.1%}～{hi:.1%}） |")
    out += ["", "| 对位（两个方向合起来） | 对 | A 得分（正态 95%） |", "|---|---|---|"]
    seen = set()
    for (a, b) in cells:
        key = tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        xs = [score(r) for r in cells.get(key, [])] + [score(r) for r in cells.get(key[::-1], [])]
        m, lo, hi = ci(xs)
        out.append(f"| {NAMES[key[0]]} — {NAMES[key[1]]} | {len(xs)} | {m:.1%}（{lo:.1%}～{hi:.1%}） |")
    at = an = bt = bn = 0
    for rs in cells.values():
        for r in rs:
            at += sum(x["total"] for x in r["ms"])
            an += sum(x["n"] for x in r["ms"])
            bt += sum(x["total"] for x in r["ms_b"])
            bn += sum(x["n"] for x in r["ms_b"])
    out += ["", f"- 每搜索决策毫秒（各格合起来）：A {at / an:.2f} / B {bt / bn:.2f} = **{(at / an) / (bt / bn):.3f}**"]
    text = "\n".join(out)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
