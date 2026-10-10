"""M1's read (README.md here): from the builder's raw rows (c7ca97d, analysis/speed/data/lethal_m1.jsonl), the share
of sure-lethal own-turn starts the mover did not win that turn; J30 graded on 6f11111 only, golden a side table.
Intervals: resampling games (2000, seed 0) and Wilson. Condition: the opponent's deck list is known (order and hand
not).

    python3 m1_read.py m1/lethal_m1.jsonl
"""
import json
import math
import random
import sys
from collections import Counter, defaultdict


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def main():
    rows = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
    print("条件：对手卡表已知（牌序、手牌未知）。M1：斩杀兑现\n")
    for src in ("6f11111", "golden"):
        sel = [r for r in rows if r["source"] == src and r["sure"]]
        if not sel:
            continue
        miss = [r for r in sel if not r["realized"]]
        n, k = len(sel), len(miss)
        lo, hi = wilson(k, n)
        line = f"- **{src}**：sure 的开头 {n} 个，没兑现 {k} 个 = **{k / n:.2%}**（Wilson {lo:.2%}～{hi:.2%}"
        if src == "6f11111":
            by = defaultdict(lambda: [0, 0])
            for r in sel:
                by[r["game"]][0] += 1
                by[r["game"]][1] += not r["realized"]
            games = sorted(by)
            rng = random.Random(0)
            bs = []
            for _ in range(2000):
                pick = [games[rng.randrange(len(games))] for _ in games]
                nn = sum(by[g][0] for g in pick)
                bs.append(sum(by[g][1] for g in pick) / nn)
            bs.sort()
            line += f"；按局重抽 {bs[49]:.2%}～{bs[1949]:.2%}，{len(games)} 局"
        print(line + "）")
        if src == "6f11111":
            print(f"  - **J30**（份额 ≥ 3%，置信 50%）→ {'对' if k / n >= 0.03 else '错'}（看点估计）")
            print(f"  - 同一局里不止一个 sure 开头的局：{sum(1 for g in by if by[g][0] > 1)}")
            print(f"  - 没兑现的 {k} 个里，开头时 level-strong 自己的检查没找到：{sum(r['agent_check'] is None for r in miss)}；"
                  f"最后一个决策上还判 sure（放着没打）：{sum(bool(r.get('sure_at_last_decision')) for r in miss)}，"
                  f"不判（先走坏了）：{sum(r.get('sure_at_last_decision') is False for r in miss)}")
            nf = sum(r["agent_check"] is None for r in sel)
            print(f"  - 全部 {n} 个里开头的检查没找到 {nf} 个（{nf / n:.1%}），其中后来还是兑现了 "
                  f"{sum(r['agent_check'] is None and r['realized'] for r in sel)} 个；检查找到的方式："
                  + "、".join(f"{c} {v}" for c, v in Counter(r["agent_check"] for r in sel).most_common()))
            print("  - 没兑现的按自己第几回合：" + "、".join(f"{t} {v}" for t, v in sorted(Counter(r["own_turn"] for r in miss).items()))
                  + "；对手 HP：" + "、".join(f"{h} {v}" for h, v in sorted(Counter(r["hp"] for r in miss).items())))


if __name__ == "__main__":
    main()
