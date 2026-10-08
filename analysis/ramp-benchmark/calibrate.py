"""CR calibration round: a new bot against the ruler on the four tournament decks, read on Salem's CR scale.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> ramp-t=gate_ramp.jsonl elf-t=gate_elf.jsonl \
        nemesis-t=gate_nemesis.jsonl pirate-t=gate_pirate.jsonl [--anchor 1300] [--boot 4000]

Salem (2026-10-08 04:29Z): after every update of the algorithm, the new bot plays the four tournament decks, and
its CR is read against the ramp-t bot of the ruler (ruler/ramp-20261008 @ 20bcfbe, v2s) anchored at 1300. Each
file is one tools.gate run with --versus: --deck ramp-t, --opponent one of the four decks, A = the new bot, B = the
ruler, C = the ruler playing the opponent's deck; a pair is one seed, A's two games (seat 0, seat 1) and B's two
on the same deals against the same C (`points`, `b_points`). B against C is the ruler against the ruler.

Per cell: A's and B's score against C (a pair's two games averaged, 95% interval over pairs), A - B paired, who
went first (by game; svsim.core.engine.new_game as tools.gate builds the game), and the CR on Salem's scale (236 a
logit; the steady-state figure 800 x difference in brackets). Then the new bot's CR, two ways, each with a 95%
bootstrap interval (pairs resampled within each cell):
- as registered (04:33Z): 1300 + 236 logit(p), p = A's score against C over the four cells pooled;
- adjusted for the decks: 1300 + 236 (logit(p_A) - logit(p_B)), B's own score on the same deals as the zero.
  Outside the mirror the ruler's ramp-t does not score 50% against the ruler's other decks (ramp-t against
  pirate-t is about 40%), so the first way puts the ruler itself below 1300; the second does not.
And the mirror cell alone, both ways (the most direct comparison with the ruler).
Sizes: 100 games a cell is about +-10 points (about +-95 CR) at 95%; 400 games about +-5 points (+-47 CR); about
360 games a cell for +-50 CR in each cell (before the pairing, which narrows A - B).
Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import math
import random
import sys

SALEM = 236.0
ORDER = ["ramp-t", "elf-t", "nemesis-t", "pirate-t"]
NAMES = {"ramp-t": "跳费龙（镜像）", "elf-t": "连击妖", "nemesis-t": "机锋", "pirate-t": "旗皇"}


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def first_seat(seed, deck, opp):
    """Who goes first on `seed` (the same in both seat orders as long as the decks only swap seats)."""
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.ui.session import DECKS
    return new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opp][1]), seed=seed).first


def pooled(cells, key):
    games = [x for rows in cells.values() for d in rows for x in d[key]]
    return sum(games) / len(games)


def cr_two_ways(cells, anchor):
    pa, pb = pooled(cells, "points"), pooled(cells, "b_points")
    return anchor + SALEM * logit(pa), anchor + SALEM * (logit(pa) - logit(pb))


def boot(cells, anchor, n, seed=17):
    rng = random.Random(seed)
    a, b = [], []
    for _ in range(n):
        res = {c: [rows[rng.randrange(len(rows))] for _ in rows] for c, rows in cells.items()}
        x, y = cr_two_ways(res, anchor)
        a.append(x)
        b.append(y)
    q = lambda xs: (sorted(xs)[int(0.025 * len(xs))], sorted(xs)[int(0.975 * len(xs)) - 1])
    return q(a), q(b)


def main():
    files = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a and not a.startswith("--"))
    anchor = float(sys.argv[sys.argv.index("--anchor") + 1]) if "--anchor" in sys.argv else 1300.0
    nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 4000
    cells = {c: [json.loads(line) for line in open(files[c], encoding="utf-8") if line.strip()]
             for c in ORDER if c in files}
    print(f"条件：对手卡表已知（牌序、手牌未知）。A = 新 bot，B = 尺子（20bcfbe，v2s），都打 ramp-t；C = 尺子打对手卡组。"
          f"锚点：尺子 = {anchor:.0f} CR。区间 95%，按对算；CR 按 Salem 刻度（236 / logit），括号里是稳态式。\n")
    print("| 对手 | 对数 | A 对 C | B 对 C | A − B（配对） | A − B 的 CR（稳态式） | A 先手 / 后手 | B 先手 / 后手 |")
    print("|---|---|---|---|---|---|---|---|")
    for c, rows in cells.items():
        ma, ha = ci([sum(d["points"]) / 2 for d in rows])
        mb, hb = ci([sum(d["b_points"]) / 2 for d in rows])
        md, hd = ci([(sum(d["points"]) - sum(d["b_points"])) / 2 for d in rows])
        split = {"points": ([], []), "b_points": ([], [])}
        for d in rows:
            f = first_seat(d["seed"], "ramp-t", c)
            for key in split:
                for seat in (0, 1):
                    split[key][0 if seat == f else 1].append(d[key][seat])
        fs = lambda key: f"{sum(split[key][0]) / len(split[key][0]):.0%} / {sum(split[key][1]) / len(split[key][1]):.0%}"
        print(f"| {NAMES[c]} | {len(rows)} | {ma:.1%} ± {ha:.1%} | {mb:.1%} ± {hb:.1%} | {md:+.1%} ± {hd:.1%} | "
              f"{SALEM * (logit(ma) - logit(mb)):+.0f}（{800 * md:+.0f}） | {fs('points')} | {fs('b_points')} |")
    if len(cells) > 1:
        (na, nb), (ia, ib) = cr_two_ways(cells, anchor), boot(cells, anchor, nboot)
        print(f"\n合计（{len(cells)} 格，A {sum(2 * len(r) for r in cells.values())} 局）：A 对 C {pooled(cells, 'points'):.1%}，"
              f"B 对 C {pooled(cells, 'b_points'):.1%}")
        print(f"  新 bot 的 CR，照登记的算法（1300 + 236·logit(p_A)）：{na:.0f}（{ia[0]:.0f}～{ia[1]:.0f}）")
        print(f"  新 bot 的 CR，扣掉卡组差（1300 + 236·(logit(p_A) − logit(p_B))）：{nb:.0f}（{ib[0]:.0f}～{ib[1]:.0f}）")
    if "ramp-t" in cells:
        m = {"ramp-t": cells["ramp-t"]}
        (na, nb), (ia, ib) = cr_two_ways(m, anchor), boot(m, anchor, nboot)
        print(f"镜像格单独：照登记的算法 {na:.0f}（{ia[0]:.0f}～{ia[1]:.0f}），扣掉卡组差 {nb:.0f}（{ib[0]:.0f}～{ib[1]:.0f}）")
    print("\n规模：每格 100 局约 ±10 个百分点（约 ±95 CR）；合计 400 局约 ±5 个百分点（约 ±47 CR）；"
          "每格要压到 ±50 CR 约需 360 局（A − B 配对后会窄一些）。")


if __name__ == "__main__":
    main()
