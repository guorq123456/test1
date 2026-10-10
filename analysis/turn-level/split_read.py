"""The split measurement's read (README.md here, "拆分测量"): R1 (the turn pick against level-strong) and R2
(mcts:1043 against level-strong), both on the same seeds, so the pairs line up seed by seed. Each: A's pair score
(the mean of its two games), the 95% interval (normal, as tools.gate reports it), CR on Salem's scale (236 per logit;
the steady-state form 800 x (score - 0.5) in brackets). Then R1 - R2 paired by seed: the mean difference of the pair
scores, its normal interval and a bootstrap one (resampling seeds, 4000, seed 0). Condition: the opponent's deck list
is known (order and hand not).

    python3 split_read.py analysis/gates/turnpick/r1_ramp_ramp.jsonl analysis/gates/turnpick/r2_ramp_ramp.jsonl
"""
import json
import math
import random
import sys


def pairs(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[r["seed"]] = sum(r["points"]) / len(r["points"])
    return out


def cr(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return 236 * math.log(p / (1 - p))


def interval(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1))
    h = 1.96 * sd / math.sqrt(n)
    return m, m - h, m + h


def main():
    r1, r2 = pairs(sys.argv[1]), pairs(sys.argv[2])
    print("条件：对手卡表已知（牌序、手牌未知）。拆分测量\n")
    for name, d in (("R1（挑打法 对 level-strong）", r1), ("R2（mcts:1043 对 level-strong）", r2)):
        m, lo, hi = interval(list(d.values()))
        print(f"- {name}：{len(d)} 对，种子 {min(d)}～{max(d)}，{m:.1%}（{lo:.1%}～{hi:.1%}），"
              f"CR {cr(m):+.0f}（{cr(lo):+.0f}～{cr(hi):+.0f}；稳态式 {800 * (m - 0.5):+.0f}）")
    common = sorted(set(r1) & set(r2))
    if not common:
        sys.exit("- 两组的种子一个也对不上，不能配对")
    if len(common) < len(r1) or len(common) < len(r2):
        print(f"- 注意：两组的种子只有 {len(common)} 个对得上，差只算这些")
    diff = [r1[s] - r2[s] for s in common]
    m, lo, hi = interval(diff)
    rng = random.Random(0)
    bs = sorted(sum(diff[rng.randrange(len(diff))] for _ in diff) / len(diff) for _ in range(4000))
    print(f"- R1 − R2（按种子配对，{len(common)} 对）：{100 * m:+.1f} 个百分点（正态 {100 * lo:+.1f}～{100 * hi:+.1f}；"
          f"重抽 {100 * bs[99]:+.1f}～{100 * bs[3899]:+.1f}）")


if __name__ == "__main__":
    main()
