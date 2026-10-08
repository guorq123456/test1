"""The ramp depth curve: the score of mcts:N against v2 by iteration count, read as a curve.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> 50=gate_50.jsonl 200=gate_200.jsonl ... [--deck ramp-t] \
        [cell:ramp-t/elf-t=gate.jsonl ...]       # --versus cells: DECK/OPPONENT, A and B both play DECK against C

Each file is a tools.gate result (one line a pair: A's points in seat 0 and seat 1; with --versus, `b_points` too
and the pair's score is 0.5 + A's mean - B's). Per iteration count: the score (pairs averaged, 95% interval over
pairs), the CR on Salem's scale (236 a logit; the steady-state figure 800 x (score - 1/2) in brackets), and the
score when A went first and when it went second (by game; who goes first comes from the seed, svsim.core.engine
.new_game). Then: a weighted least-squares line of logit(score) on log2(N), its slope per doubling with a 95%
interval (all counts, and without those below B's 100); whether 200, 400 and 800 can be read as one level (a
chi-square test of homogeneity on logit(score), 2 degrees of freedom); whether 1600 is above the mean of 200-800
(the difference of scores with its 95% interval, independent samples); the 400 -> 800 change in CR; and the
readings registered in README.md. Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import math
import sys

SALEM = 236.0


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def pair_score(d):
    if d.get("b_points"):
        return 0.5 + sum(d["points"]) / 2 - sum(d["b_points"]) / 2
    return sum(d["points"]) / 2


def mean_var(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n          # the mean and its variance


def first_of(seed, deck, opp=None):
    """Who goes first on `seed` with `deck` in seat 0 (tools.gate builds the seat-1 game with the decks swapped
    on the same seed; the first player comes from the seed alone)."""
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.ui.session import DECKS
    return new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opp or deck][1]), seed=seed).first


def wls(xs, ys, ws):
    sw = sum(ws)
    mx = sum(w * x for w, x in zip(ws, xs)) / sw
    my = sum(w * y for w, y in zip(ws, ys)) / sw
    sxx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    b = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys)) / sxx
    return b, math.sqrt(1 / sxx), my - b * mx                   # slope, its standard error (known weights), intercept


def main():
    args = [a for a in sys.argv[1:] if "=" in a and not a.startswith("--") and not a.startswith("cell:")]
    cell_args = [a[5:] for a in sys.argv[1:] if a.startswith("cell:")]
    deck = sys.argv[sys.argv.index("--deck") + 1] if "--deck" in sys.argv else "ramp-t"
    rows = {}
    for a in args:
        n, path = a.split("=", 1)
        rows[int(n)] = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    print(f"条件：对手卡表已知（牌序、手牌未知）。{deck} 镜像，A = mcts:N+plan+learned+phased，B = v2（100 次）；"
          f"区间 95%，按对算；CR 按 Salem 刻度，括号里是稳态式 800 × (得分 − 0.5)。\n")
    print("| N | 对数 | A 得分 | CR（稳态式） | A 先手 / 后手（按局） |")
    print("|---|---|---|---|---|")
    stats = {}
    for n in sorted(rows):
        rs = rows[n]
        m, v = mean_var([pair_score(d) for d in rs])
        firsts, seconds = [], []
        for d in rs:
            f = first_of(d["seed"], deck)
            for seat in (0, 1):
                (firsts if seat == f else seconds).append(d["points"][seat])
        stats[n] = (m, v, len(rs))
        print(f"| {n} | {len(rs)} | {m:.1%} ± {1.96 * math.sqrt(v):.1%} | {SALEM * logit(m):+.0f}（{800 * (m - 0.5):+.0f}） | "
              f"{sum(firsts) / len(firsts):.1%} / {sum(seconds) / len(seconds):.1%} |")
    lx = {n: logit(m) for n, (m, v, _) in stats.items()}
    lw = {n: (m * (1 - m)) ** 2 / v for n, (m, v, _) in stats.items()}       # 1 / var(logit), delta method
    print()
    for label, ns in (("全部", sorted(stats)), ("只用 N ≥ 100", [n for n in sorted(stats) if n >= 100])):
        if len(ns) >= 3:
            b, se, a = wls([math.log2(n) for n in ns], [lx[n] for n in ns], [lw[n] for n in ns])
            chi = sum(lw[n] * (lx[n] - (a + b * math.log2(n))) ** 2 for n in ns)
            print(f"拟合 logit(得分) = a + b·log2(N)（{label}，{'、'.join(map(str, ns))}）：每翻一倍 b = {b:+.3f} ± {1.96 * se:.3f} logit，"
                  f"即 {SALEM * b:+.0f} ± {SALEM * 1.96 * se:.0f} CR；残差 χ² = {chi:.1f}（自由度 {len(ns) - 2}）")
    mid = [n for n in (200, 400, 800) if n in stats]
    if len(mid) == 3:
        xbar = sum(lw[n] * lx[n] for n in mid) / sum(lw[n] for n in mid)
        q = sum(lw[n] * (lx[n] - xbar) ** 2 for n in mid)
        print(f"200、400、800 是否同一水平：χ² = {q:.2f}（自由度 2），p = {math.exp(-q / 2):.2f}"
              f"（{'可以看作同一水平' if math.exp(-q / 2) > 0.05 else '不是同一水平'}）")
        if 1600 in stats:
            mm = sum(stats[n][0] for n in mid) / 3
            vm = sum(stats[n][1] for n in mid) / 9
            d = stats[1600][0] - mm
            se = math.sqrt(stats[1600][1] + vm)
            z = d / se
            p = math.erfc(abs(z) / math.sqrt(2))
            print(f"1600 对 200～800 的均值（{mm:.1%}）：{d:+.1%} ± {1.96 * se:.1%}，z = {z:.2f}，双侧 p = {p:.3f}"
                  f"（{'显著高于' if d > 0 and p < 0.05 else '不显著'}）")
    if 400 in stats and 800 in stats:
        dcr = SALEM * (lx[800] - lx[400])
        se = SALEM * math.sqrt(1 / lw[800] + 1 / lw[400])
        print(f"400 → 800：{dcr:+.0f} ± {1.96 * se:.0f} CR")
    if cell_args:
        print("\n--versus 的格（A、B 都打前一个卡组，C 打后一个；一对的得分 = 0.5 + A 的平均 − B 的平均）：\n")
        print("| 格 | 对数 | 一对的得分 | CR（稳态式） | A 对 C | B 对 C | A 先手 / 后手 |")
        print("|---|---|---|---|---|---|---|")
        for a in cell_args:
            label, path = a.split("=", 1)
            d1, d2 = label.split("/")
            rs = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
            m, v = mean_var([pair_score(d) for d in rs])
            pa = sum(x for d in rs for x in d["points"]) / (2 * len(rs))
            pb = sum(x for d in rs for x in d["b_points"]) / (2 * len(rs))
            firsts, seconds = [], []
            for d in rs:
                f = first_of(d["seed"], d1, d2)
                for seat in (0, 1):
                    (firsts if seat == f else seconds).append(d["points"][seat])
            print(f"| {label} | {len(rs)} | {m:.1%} ± {1.96 * math.sqrt(v):.1%} | {SALEM * logit(m):+.0f}（{800 * (m - 0.5):+.0f}） | "
                  f"{pa:.1%} | {pb:.1%} | {sum(firsts) / len(firsts):.1%} / {sum(seconds) / len(seconds):.1%} |")


if __name__ == "__main__":
    main()
