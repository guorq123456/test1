"""CR calibration round: a new version against the reference version on seven cells, read on Salem's CR scale.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> analysis/calibration/round1 [--ref 20bcfbe] \
        [--ref-cr ramp-t=1300 elf-t=1300 nemesis-t=1300 pirate-t=1300] [--boot 4000]

Salem (2026-10-08 04:29Z, 04:30Z) and the coordinating session: after every install the new version plays the
current reference version (the first is the ruler, ruler/ramp-20261008 @ 20bcfbe, at 1300 CR) on seven cells,
its CR is read, it goes to the sparring table with that CR, and it becomes the next round's reference. Each cell
is one tools.gate run with --versus, a file `<deck>_vs_<opponent>.jsonl` in the round's folder:
- ramp-t_vs_{ramp-t, elf-t, nemesis-t, pirate-t}: A (the new version) and B (the reference) play ramp-t, C (the
  reference) plays the opponent's deck: the ramp-t bot's CR, one number from the four cells;
- {elf-t, nemesis-t, pirate-t}_vs_ramp-t: A and B play that deck, C (the reference) plays ramp-t: each of those
  bots' own CR, one chain per deck, each starting at 1300 at 20bcfbe, never compared across decks.
A pair is one seed: A's two games (seat 0, seat 1) and B's two on the same deals against the same C.

The CR, as decided (04:43Z): CR_new = CR_ref + 236 (logit p_A - logit p_B), p the score against C over the cells
pooled, B's own score on the same deals the zero; 95% bootstrap interval (pairs resampled within each cell).
Beside it, in brackets for the first rounds, the registered first form CR_ref + 236 logit p_A: outside the mirror
the reference's ramp-t does not score 50% against the reference's other decks (ramp-t against pirate-t is about
40%), so with A = B it puts the reference itself near 1262 instead of 1300.
Round 1 (A = B = 20bcfbe) is an identity check, not a statistical one (04:49Z): A runs the top-level "+phased"
models of a checkout that has `phased_models/ruler-20261008/`, B and C "+phased=ruler-20261008"; with the same
seeds and the same models, every pair must come out A - B = 0 with every game move for move alike, and the CR
exactly 1300.0; 10 pairs a cell (--max 40). Any pair whose moves differ raises the alarm. (Before running, the
snapshot's files are checked with sha256sum against the hashes in its README.) The first real link of the chain
is the next install, at 50 pairs a cell.
Per cell: A's and B's score against C (95% over pairs), A - B paired, who went first, and the CR of A - B on
Salem's scale (the steady-state figure 800 x difference in brackets). Sizes: 100 games a cell is about +-10 points
(+-95 CR); 400 about +-5 points (+-47 CR); about 360 games a cell for +-50 CR (before the pairing narrows A - B).
Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import math
import os
import random
import sys

SALEM = 236.0
RAMP_CELLS = ["ramp-t", "elf-t", "nemesis-t", "pirate-t"]          # ramp-t_vs_<these>
OTHER_DECKS = ["elf-t", "nemesis-t", "pirate-t"]                     # <these>_vs_ramp-t
NAMES = {"ramp-t": "跳费龙", "elf-t": "连击妖", "nemesis-t": "机锋", "pirate-t": "旗皇"}


def logit(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def ci(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def first_seat(seed, deck, opp):
    """Who goes first on `seed` (tools.gate plays both seats on the same seed; the first player comes from it)."""
    from svsim.cards import decks
    from svsim.core.engine import new_game
    from svsim.ui.session import DECKS
    return new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opp][1]), seed=seed).first


def pooled(cells, key):
    games = [x for rows in cells.values() for d in rows for x in d[key]]
    return sum(games) / len(games)


def cr_two_ways(cells, ref):
    pa, pb = pooled(cells, "points"), pooled(cells, "b_points")
    return ref + SALEM * (logit(pa) - logit(pb)), ref + SALEM * logit(pa)


def boot(cells, ref, n, seed=17):
    rng = random.Random(seed)
    a, b = [], []
    for _ in range(n):
        res = {c: [rows[rng.randrange(len(rows))] for _ in rows] for c, rows in cells.items()}
        x, y = cr_two_ways(res, ref)
        a.append(x)
        b.append(y)
    q = lambda xs: (sorted(xs)[int(0.025 * len(xs))], sorted(xs)[int(0.975 * len(xs)) - 1])
    return q(a), q(b)


def cell_rows(cells, deck_of):
    print("| 格 | 对数 | A 对 C | B 对 C | A − B（配对） | A − B 的 CR（稳态式） | A 先手 / 后手 | B 先手 / 后手 | A、B 逐局相同 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for (deck, opp), rows in cells.items():
        ma, ha = ci([sum(d["points"]) / 2 for d in rows])
        mb, hb = ci([sum(d["b_points"]) / 2 for d in rows])
        md, hd = ci([(sum(d["points"]) - sum(d["b_points"])) / 2 for d in rows])
        split = {"points": ([], []), "b_points": ([], [])}
        for d in rows:
            f = first_seat(d["seed"], deck, opp)
            for key in split:
                for seat in (0, 1):
                    split[key][0 if seat == f else 1].append(d[key][seat])
        fs = lambda key: f"{sum(split[key][0]) / len(split[key][0]):.0%} / {sum(split[key][1]) / len(split[key][1]):.0%}"
        print(f"| {NAMES[deck]}对{NAMES[opp]} | {len(rows)} | {ma:.1%} ± {ha:.1%} | {mb:.1%} ± {hb:.1%} | {md:+.1%} ± {hd:.1%} | "
              f"{SALEM * (logit(ma) - logit(mb)):+.0f}（{800 * md:+.0f}） | {fs('points')} | {fs('b_points')} | "
              f"{sum(sum(d.get('same') or [False, False]) for d in rows)} / {2 * len(rows)} |")


def report_cr(label, cells, ref, nboot, round1):
    (adj, reg), (ia, ir) = cr_two_ways(cells, ref), boot(cells, ref, nboot)
    games = sum(2 * len(r) for r in cells.values())
    fmt = ".1f" if round1 else ".0f"
    line = (f"  {label}：**{adj:{fmt}}**（{ia[0]:.0f}～{ia[1]:.0f}）；A 对 C {pooled(cells, 'points'):.1%}、B 对 C "
            f"{pooled(cells, 'b_points'):.1%}，A {games} 局［照登记的算法 {reg:.0f}（{ir[0]:.0f}～{ir[1]:.0f}）］")
    if round1:
        line += f"；恒等校验要求正好 {ref:.1f}：{'对' if abs(adj - ref) < 0.05 else '不对，报警'}"
    print(line)


def identity_check(cells):
    """Round 1: every pair A - B = 0 and every game move for move alike; the pairs that are not."""
    bad = [(f"{d}_vs_{o}", r["k"]) for (d, o), rows in cells.items() for r in rows
           if r["points"] != r["b_points"] or not all(r.get("same") or [False])]
    return bad


def main():
    folder = next(a for a in sys.argv[1:] if not a.startswith("--") and "=" not in a)
    ref = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "20bcfbe"
    nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 4000
    refcr = {d: 1300.0 for d in NAMES}
    if "--ref-cr" in sys.argv:
        for a in sys.argv[sys.argv.index("--ref-cr") + 1:]:
            if "=" not in a or a.startswith("--"):
                break
            d, v = a.split("=")
            refcr[d] = float(v)
    load = lambda name: [json.loads(line) for line in open(os.path.join(folder, name), encoding="utf-8") if line.strip()]
    ramp = {("ramp-t", o): load(f"ramp-t_vs_{o}.jsonl") for o in RAMP_CELLS if os.path.exists(os.path.join(folder, f"ramp-t_vs_{o}.jsonl"))}
    other = {(d, "ramp-t"): load(f"{d}_vs_ramp-t.jsonl") for d in OTHER_DECKS if os.path.exists(os.path.join(folder, f"{d}_vs_ramp-t.jsonl"))}
    round1 = ref == "20bcfbe" and "--not-control" not in sys.argv
    print(f"条件：对手卡表已知（牌序、手牌未知）。{folder}：A = 新版本，B = 参考版本 {ref}，C = 参考版本打对手卡组。"
          f"CR = 参考 CR + 236·(logit p_A − logit p_B)，区间 95%（按对的自助法）。"
          + ("第 1 轮 A = B，是恒等校验：每对 A − B 必须为 0、着法全同，CR 正好是参考值。" if round1 else "") + "\n")
    if ramp:
        print(f"**① 跳费龙 bot 的 CR**（参考 {refcr['ramp-t']:.0f}）\n")
        cell_rows(ramp, None)
        print()
        report_cr(f"合计（{len(ramp)} 格）", ramp, refcr["ramp-t"], nboot, round1)
        if ("ramp-t", "ramp-t") in ramp:
            report_cr("镜像格单独", {("ramp-t", "ramp-t"): ramp[("ramp-t", "ramp-t")]}, refcr["ramp-t"], nboot, round1)
    if other:
        print("\n**② 连击妖 / 机锋 / 旗皇 bot 各自的 CR**（每套牌一条链，各自从 20bcfbe = 1300 起算，不跨卡组比）\n")
        cell_rows(other, None)
        print()
        for (d, o), rows in other.items():
            report_cr(f"{NAMES[d]}（参考 {refcr[d]:.0f}）", {(d, o): rows}, refcr[d], nboot, round1)
    if round1:
        bad = identity_check({**ramp, **other})
        n = sum(len(r) for r in {**ramp, **other}.values())
        print(f"\n**恒等校验**（第 1 轮，A = B）：{n} 对里 A − B ≠ 0 或着法不同的 {len(bad)} 对"
              + ("：通过" if not bad else "：**报警**，" + "、".join(f"{c} 第 {k} 对" for c, k in bad[:20])))
    print("\n规模：每格 100 局约 ±10 个百分点（约 ±95 CR）；合计 400 局约 ±5 个百分点（约 ±47 CR）；"
          "每格要压到 ±50 CR 约需 360 局（A − B 配对后会窄一些）。")


if __name__ == "__main__":
    main()
