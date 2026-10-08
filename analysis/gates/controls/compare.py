"""B' control for ramp-t vs pirate-t (63700000) against the three feature gates of the same cell: each gate's pair
score (--versus: 0.5 + A - B against C), and B' minus each (and minus C2's two banks pooled), with a normal 95%
interval from the pair-level variances (different banks, so unpaired).

    python3 <this>        (from analysis/)

Condition: the opponent's 40-card list is known (order and hand not).
"""
import json


def pairs(path):
    out = []
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            a = sum(r["points"]) / len(r["points"])
            out.append(0.5 + a - sum(r["b_points"]) / len(r["b_points"]))
    return out


def stats(xs):
    n = len(xs)
    m = sum(xs) / n
    var = sum((x - m) ** 2 for x in xs) / (n - 1) / n
    return m, var


def main():
    bp = stats(pairs("gates/controls/ramp-t_pirate-t_bprime.jsonl"))
    others = {
        "C2（60400000）": pairs("gates/c2-hand/ramp-t_pirate-t.jsonl"),
        "C2（62200000）": pairs("gates/c2-hand/ramp-t_pirate-t_rerun62200000.jsonl"),
        "C3 6 维（62500000）": pairs("gates/c3-board/ramp-t_pirate-t.jsonl"),
    }
    others["C2 两库合并"] = others["C2（60400000）"] + others["C2（62200000）"]
    print("条件：对手卡表已知（牌序、手牌未知）。一对得分 = 0.5 + A − B（对 C）；不同库，不配对，正态 95%。\n")
    print(f"B′（63700000）：{bp[0]:.1%} ± {1.96 * bp[1] ** 0.5:.1%}\n")
    print("| 门 | 一对得分 | B′ − 它（95%） |")
    print("|---|---|---|")
    for name, xs in others.items():
        m, v = stats(xs)
        d, h = bp[0] - m, 1.96 * (bp[1] + v) ** 0.5
        mark = "**" if d - h > 0 or d + h < 0 else ""
        print(f"| {name} | {m:.1%} ± {1.96 * v ** 0.5:.1%} | {mark}{d:+.1%}（{d - h:+.1%}～{d + h:+.1%}）{mark} |")


if __name__ == "__main__":
    main()
