"""CR calibration: a lazy round robin of a new version against the reference version, read on Salem's CR scale.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> analysis/calibration/round2 [--ref <sha>] \
        [--ref-cr ramp-t=1300 elf-t=1300 nemesis-t=1300 pirate-t=1300] [--boot 4000] [--identity]
    ... <this> analysis/calibration/levels --levels      # each sparring level against the ruler

Salem (2026-10-08 04:29Z, 04:30Z), the coordinating session and the architecture thread (04:52Z): four decks x
four opponents (the mirror included) = 16 cells. A cell `<deck>_vs_<opponent>.jsonl` is one tools.gate run with
--versus: A (the new version) and B (the reference) play <deck>, C (the reference) plays <opponent>; a pair is one
seed, A's two games and B's two on the same deals against the same C. Per cell dCR = 236 (logit p_A - logit p_B),
p the score against C; each deck's bot gets CR_new = CR_ref + the mean of its four cells' dCR. A cell whose
models did not change is not run: A and B play it pair for pair alike, so its dCR is 0, marked "models unchanged,
identical pair for pair". The ramp-t bot's CR is the mean of its four cells, the ones Salem named. Each deck's
chain starts at 20bcfbe = 1300 and is never compared across decks. Intervals: 95% bootstrap, pairs resampled within
each cell that was run. Error: a cell is about +-95 CR at 50 pairs; one changed cell moves its deck's CR by a
quarter of that (about +-24), four changed cells about +-47.

--identity (the identity check, 04:49Z): every pair must come out A - B = 0 with every game move for move alike
(A the top-level models, B and C the ruler snapshot `ruler-20261008`, alias ruler20261008; the snapshot's files
checked with sha256sum against its README first); any pair that is not raises the alarm.

--levels: the sparring table's levels against the ruler, files `<level>_ramp-t_vs_<opponent>.jsonl`; each level's
CR = 1300 + the mean of its four cells' dCR (for svsim/ui/ratings.json).
Condition: the opponent's 40-card list is known (order and hand not).
"""
import json
import math
import os
import random
import sys

SALEM = 236.0
DECKS = ["ramp-t", "elf-t", "nemesis-t", "pirate-t"]
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
    from svsim.ui.session import DECKS as D
    return new_game(decks.build(D[deck][1]), decks.build(D[opp][1]), seed=seed).first


def dcr(rows):
    pa = sum(x for d in rows for x in d["points"]) / (2 * len(rows))
    pb = sum(x for d in rows for x in d["b_points"]) / (2 * len(rows))
    return SALEM * (logit(pa) - logit(pb)), pa, pb


def mean_dcr(cells, opps):
    """The mean over the four opponents; a cell not run counts 0."""
    return sum(dcr(cells[o])[0] if o in cells else 0.0 for o in opps) / len(opps)


def boot(cells, opps, n, seed=17):
    rng = random.Random(seed)
    xs = sorted(mean_dcr({o: [rows[rng.randrange(len(rows))] for _ in rows] for o, rows in cells.items()}, opps)
                for _ in range(n))
    return xs[int(0.025 * n)], xs[int(0.975 * n) - 1]


def cell_table(label_of, cells, opps, deck_of):
    print("| 格 | 对数 | A 对 C | B 对 C | A − B（配对） | ΔCR（稳态式） | A 先手 / 后手 | A、B 逐局相同 |")
    print("|---|---|---|---|---|---|---|---|")
    for o in opps:
        if o not in cells:
            print(f"| {label_of(o)} | — | — | — | — | 0（模型未变，逐对恒等，没跑） | — | — |")
            continue
        rows = cells[o]
        ma, ha = ci([sum(d["points"]) / 2 for d in rows])
        mb, hb = ci([sum(d["b_points"]) / 2 for d in rows])
        md, hd = ci([(sum(d["points"]) - sum(d["b_points"])) / 2 for d in rows])
        first, second = [], []
        for d in rows:
            f = first_seat(d["seed"], deck_of(o), o)
            for seat in (0, 1):
                (first if seat == f else second).append(d["points"][seat])
        same = sum(sum(d.get("same") or [False, False]) for d in rows)
        print(f"| {label_of(o)} | {len(rows)} | {ma:.1%} ± {ha:.1%} | {mb:.1%} ± {hb:.1%} | {md:+.1%} ± {hd:.1%} | "
              f"{dcr(rows)[0]:+.0f}（{800 * md:+.0f}） | {sum(first) / len(first):.0%} / {sum(second) / len(second):.0%} | "
              f"{same} / {2 * len(rows)} |")


def identity_alarm(all_cells):
    return [(name, r["k"]) for name, rows in all_cells.items() for r in rows
            if r["points"] != r["b_points"] or not all(r.get("same") or [False])]


def load_folder(folder, pattern):
    out = {}
    for name in sorted(os.listdir(folder)):
        if name.endswith(".jsonl") and pattern(name):
            out[name[:-6]] = [json.loads(line) for line in open(os.path.join(folder, name), encoding="utf-8") if line.strip()]
    return out


def main():
    folder = next(a for a in sys.argv[1:] if not a.startswith("--") and "=" not in a)
    ref = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "20bcfbe"
    nboot = int(sys.argv[sys.argv.index("--boot") + 1]) if "--boot" in sys.argv else 4000
    refcr = {d: 1300.0 for d in DECKS}
    if "--ref-cr" in sys.argv:
        for a in sys.argv[sys.argv.index("--ref-cr") + 1:]:
            if "=" not in a or a.startswith("--"):
                break
            d, v = a.split("=")
            refcr[d] = float(v)
    identity = "--identity" in sys.argv
    if "--levels" in sys.argv:
        files = load_folder(folder, lambda n: "_ramp-t_vs_" in n)
        levels = sorted({n.split("_ramp-t_vs_")[0] for n in files})
        print(f"条件：对手卡表已知（牌序、手牌未知）。{folder}：各档 A 打 ramp-t，B = C = 尺子（ruler20261008）；"
              f"每档 CR = 1300 + 四格 ΔCR 的平均，区间 95%（按对的自助法）。\n")
        for lv in levels:
            cells = {n.split("_ramp-t_vs_")[1]: rows for n, rows in files.items() if n.startswith(lv + "_ramp-t_vs_")}
            print(f"**{lv}**\n")
            cell_table(lambda o: f"跳费龙对{NAMES[o]}", cells, DECKS, lambda o: "ramp-t")
            lo, hi = boot(cells, DECKS, nboot)
            print(f"\n  {lv} 的 CR：**{1300 + mean_dcr(cells, DECKS):.0f}**（{1300 + lo:.0f}～{1300 + hi:.0f}），"
                  f"跑了 {len(cells)} / 4 格\n")
        return
    files = load_folder(folder, lambda n: "_vs_" in n)
    digits = 1 if identity else 0
    print(f"条件：对手卡表已知（牌序、手牌未知）。{folder}：A = 新版本，B = 参考版本 {ref}，C = 参考版本打对手卡组。"
          f"每格 ΔCR = 236·(logit p_A − logit p_B)；每套牌 CR = 参考 CR + 四个对手格 ΔCR 的平均（没跑的格按 0："
          f"模型未变、逐对恒等）；各套牌一条链，不跨卡组比；区间 95%（按对的自助法）。"
          + ("恒等校验：每对 A − B 必须为 0、着法全同。" if identity else "") + "\n")
    print("| 套牌 bot | 参考 CR | 跑了几格 | 新 CR（95%） | 变化 |")
    print("|---|---|---|---|---|")
    per_deck = {}
    for d in DECKS:
        cells = {n.split("_vs_")[1]: rows for n, rows in files.items() if n.split("_vs_")[0] == d}
        per_deck[d] = cells
        m = mean_dcr(cells, DECKS)
        if cells:
            lo, hi = boot(cells, DECKS, nboot)
            band = f"（{refcr[d] + lo:.{digits}f}～{refcr[d] + hi:.{digits}f}）"
        else:
            band = "（四格模型都没变）"
        print(f"| {NAMES[d]} | {refcr[d]:.0f} | {len(cells)} / 4 | **{refcr[d] + m:.{digits}f}**{band} | {m:+.{digits}f} |")
    for d in DECKS:
        if per_deck[d]:
            print(f"\n**{NAMES[d]} bot 的格**\n")
            cell_table(lambda o, d=d: f"{NAMES[d]}对{NAMES[o]}", per_deck[d], DECKS, lambda o, d=d: d)
    if identity:
        bad = identity_alarm(files)
        n = sum(len(r) for r in files.values())
        print(f"\n**恒等校验**：{n} 对里 A − B ≠ 0 或着法不同的 {len(bad)} 对"
              + ("：通过" if not bad else "：**报警**，" + "、".join(f"{c} 第 {k} 对" for c, k in bad[:20])))
    print("\n误差：每格 50 对约 ±95 CR；一格变了，那套牌的 CR 误差约是它的 1/4（约 ±24）；四格都变约 ±47。")


if __name__ == "__main__":
    main()
