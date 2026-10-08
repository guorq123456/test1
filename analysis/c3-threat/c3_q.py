"""C3 hpphase gates pooled as pre-registered (section 7.4): per cell theta = pair score - 50% (direct: A's mean of
the two games; --versus: 0.5 + A - B against C), its variance from the pair-level spread, the inverse-variance
weighted mean, Cochran's Q with df = cells - 1 and its chi-square p, the binomial reading, and the install set.

    python3 <this> [<gates dir>]        (default ../gates/c3-hpphase)

Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import math
import os
import sys

CELLS = [("ramp-t_ramp-t", "跳费龙镜像"), ("elf-t_elf-t", "连击妖镜像"), ("elf-t_nemesis-t", "连击妖对机锋"),
         ("ramp-t_nemesis-t", "跳费龙对机锋"), ("pirate-t_elf-t", "旗皇对连击妖"), ("ramp-t_elf-t", "跳费龙对连击妖"),
         ("elf-t_ramp-t", "连击妖对跳费龙"), ("pirate-t_pirate-t", "旗皇镜像"), ("nemesis-t_ramp-t", "机锋对跳费龙"),
         ("nemesis-t_elf-t", "机锋对连击妖"), ("ramp-t_pirate-t", "跳费龙对旗皇")]
EXTRA = [("ramp_ramp", "original 跳费龙镜像（第 12 道）")]


def pairs(path):
    out = []
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            a = sum(r["points"]) / len(r["points"])
            out.append(0.5 + a - sum(r["b_points"]) / len(r["b_points"]) if "b_points" in r else a)
    return out


def chi2_sf(q, df):
    """Upper tail of chi-square (regularised incomplete gamma by series / continued fraction)."""
    a, x = df / 2.0, q / 2.0
    if x <= 0:
        return 1.0
    if x < a + 1:
        s, t, k = 1.0 / a, 1.0 / a, 1
        while abs(t) > 1e-15 * abs(s):
            t *= x / (a + k)
            s += t
            k += 1
        return 1.0 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b, c, d = x + 1 - a, 1e300, 1.0 / (x + 1 - a)
    h, i = d, 1
    while True:
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
        i += 1
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def pooled(rows, label):
    w = [1 / v for _, _, _, v in rows]
    m = sum(wi * t for wi, (_, _, t, _) in zip(w, rows)) / sum(w)
    se = (1 / sum(w)) ** 0.5
    q = sum(wi * (t - m) ** 2 for wi, (_, _, t, _) in zip(w, rows))
    df = len(rows) - 1
    p = chi2_sf(q, df)
    passed = sum(1 for _, _, t, v in rows if t - 1.96 * v ** 0.5 > 0)
    k = len(rows)
    tail = 1 - sum(math.comb(k, j) * 0.025 ** j * 0.975 ** (k - j) for j in range(passed))
    print(f"\n**{label}**：{k} 格，过 {passed} 格；加权平均 θ = {m:+.1%} ± {1.96 * se:.1%}；"
          f"Q = {q:.1f}（自由度 {df}，p = {p:.3g}）；Bin({k}, 0.025) 下 P(≥{passed}) = {tail:.2%}")


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "gates", "c3-hpphase")
    rows = []
    print("条件：对手卡表已知（牌序、手牌未知）。θ = 一对得分 − 50%，方差按对算。\n")
    print("| 格 | 对数 | θ（95%） | 过？ |")
    print("|---|---|---|---|")
    for fname, label in CELLS + EXTRA:
        path = os.path.join(d, fname + ".jsonl")
        if not os.path.exists(path):
            print(f"| {label} | — | 还没跑 | |")
            continue
        xs = pairs(path)
        n = len(xs)
        m = sum(xs) / n
        v = sum((x - m) ** 2 for x in xs) / (n - 1) / n
        t = m - 0.5
        rows.append((fname, label, t, v))
        print(f"| {label} | {n} | {t:+.1%}（{t - 1.96 * v ** 0.5:+.1%}～{t + 1.96 * v ** 0.5:+.1%}） | "
              f"{'过' if t - 1.96 * v ** 0.5 > 0 else '不过'} |")
    main_rows = [r for r in rows if r[0] != "ramp_ramp"]
    if main_rows:
        pooled(main_rows, "十一门（预注册的那 11 格）")
    if len(rows) > len(main_rows):
        pooled(rows, "加上 original ramp-ramp（12 格）")
        excl = [r for r in main_rows if r[0] not in ("ramp-t_ramp-t", "elf-t_elf-t")]
        pooled(excl, "去掉两个过门格，看其余格之间（照记，不是预注册的）")


if __name__ == "__main__":
    main()
