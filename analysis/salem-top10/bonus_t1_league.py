"""How often the second player spends the bonus play point on their own first turn in the league rerun (3000 games,
v2s against v2s, the four tournament decks), and the win rate with and without (the architecture thread 17:20,
numbers only: it decides nothing, the hands that make a player spend it are not the hands that don't).

    python3 <this> PART1.jsonl.gz PART2.jsonl.gz PART3.jsonl.gz

"Spent" = UseBonusPP in the second player's first turn followed by a card played in that turn (an unspent bonus point
goes back). Condition: the opponent's 40-card list is known (order and hand not).
"""
import gzip
import json
import sys
from collections import defaultdict


def first_turn_of_second(actions):
    i = 0
    while i < len(actions) and actions[i]["type"] == "Mulligan":
        i += 1
    while i < len(actions) and actions[i]["type"] != "EndTurn":    # the first player's turn 1
        i += 1
    i += 1
    seg = []
    while i < len(actions) and actions[i]["type"] != "EndTurn":
        seg.append(actions[i]["type"])
        i += 1
    return seg


def main():
    rows = defaultdict(lambda: {"n": [0, 0], "w": [0.0, 0.0]})       # key -> [not spent, spent]
    for path in sys.argv[1:]:
        for line in gzip.open(path, "rt", encoding="utf-8"):
            g = json.loads(line)
            rec = g["record"]
            second = 1 - rec["first"]
            seg = first_turn_of_second(rec["actions"])
            spent = int("UseBonusPP" in seg and "PlayCard" in seg[seg.index("UseBonusPP"):])
            win = 0.5 if g["winner"] is None else float(g["winner"] == second)
            names = rec["names"]
            for key in ("全部", f"后手是 {names[second]}", f"{names[second]}（后手）对 {names[rec['first']]}"):
                rows[key]["n"][spent] += 1
                rows[key]["w"][spent] += win
    print("条件：对手卡表已知（牌序、手牌未知）。联赛重跑 3000 局（v2s 对 v2s，四套比赛卡组）。只报数：花不花额外 PP 取决于手牌，"
          "两组的手牌不同，胜率差不是「花额外 PP」的因果效应。\n")
    print("| 后手 | 局数 | 第 1 回合花了额外 PP | 花了时后手胜率 | 没花时后手胜率 | 差（花 − 没花，95%） |")
    print("|---|---|---|---|---|---|")
    order = sorted(rows, key=lambda k: (k != "全部", not k.startswith("后手是"), k))
    for k in order:
        n0, n1 = rows[k]["n"]
        w0, w1 = rows[k]["w"]
        if n0 + n1 < 50:
            continue
        p0 = w0 / n0 if n0 else float("nan")
        p1 = w1 / n1 if n1 else float("nan")
        se = ((p0 * (1 - p0) / n0 if n0 else 0) + (p1 * (1 - p1) / n1 if n1 else 0)) ** 0.5
        d = p1 - p0
        print(f"| {k} | {n0 + n1} | {n1 / (n0 + n1):.0%}（{n1}） | {p1:.1%} | {p0:.1%} | {d:+.1%}（{d - 1.96 * se:+.1%}～{d + 1.96 * se:+.1%}） |")


if __name__ == "__main__":
    main()
