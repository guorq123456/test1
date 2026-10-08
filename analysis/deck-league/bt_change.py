"""Bradley-Terry deck strengths (mirrors left out) before and after, and the change, paired by seed.

    python3 <this> base=league_v2s_f631e14.jsonl.gz+league_v2s_f631e14_mirror2.jsonl.gz \
        new=part1.jsonl.gz+part2.jsonl.gz+part3.jsonl.gz [--boot 2000]

Both versions play the same seeds, so the bootstrap draws the same pair numbers k in both, within each pairing,
and refits both: the change's interval keeps the pairing. CR on Salem's scale (236 a logit), mean 0 in each
version, so a deck's change is relative to the four's mean. Condition: the opponent's 40-card list is known
(order and hand not).
"""
import random
import sys

from compare_league import load
from league import bt_fit, score_a

SALEM = 236.0


def pairs(cells):
    out = {}
    for pair, ks in cells.items():
        a, b = pair.split("/")
        if a != b:
            out[pair] = {k: sum(score_a(g) for g in gs.values()) / 2 for k, gs in ks.items()}
    return out


def fit(scores, picks):
    counts = {}
    for pair, ks in picks.items():
        a, b = pair.split("/")
        counts[(a, b)] = (2 * sum(scores[pair][k] for k in ks), 2 * len(ks))
    decks = sorted({d for p in picks for d in p.split("/")})
    return bt_fit(counts, decks, iters=400)


def main():
    files = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a and not a.startswith("--"))
    nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 2000
    base, new = (pairs(load(files[v].split("+"))) for v in ("base", "new"))
    common = {p: sorted(set(base[p]) & set(new[p])) for p in base if p in new}
    tb, tn = fit(base, common), fit(new, common)
    rng = random.Random(17)
    boots = {d: ([], [], []) for d in tb}
    for _ in range(nboot):
        picks = {p: [ks[rng.randrange(len(ks))] for _ in ks] for p, ks in common.items()}
        b, n = fit(base, picks), fit(new, picks)
        for d in tb:
            boots[d][0].append(b[d]); boots[d][1].append(n[d]); boots[d][2].append(n[d] - b[d])

    def band(xs):
        xs = sorted(xs)
        return f"{SALEM * xs[int(0.025 * len(xs))]:+.0f}～{SALEM * xs[int(0.975 * len(xs)) - 1]:+.0f}"
    print("条件：对手卡表已知（牌序、手牌未知）。Bradley–Terry（不含镜像），CR 按 Salem 刻度，每个版本平均为 0；"
          f"区间 95%，每个组合内按种子配对重抽 {nboot} 次，两个版本抽同样的对。\n")
    print("| 卡组 | base | new | 变化（配对） |")
    print("|---|---|---|---|")
    for d in sorted(tb, key=lambda d: -tn[d]):
        print(f"| {d} | {SALEM * tb[d]:+.0f}（{band(boots[d][0])}） | {SALEM * tn[d]:+.0f}（{band(boots[d][1])}） | "
              f"**{SALEM * (tn[d] - tb[d]):+.0f}**（{band(boots[d][2])}） |")


if __name__ == "__main__":
    main()
