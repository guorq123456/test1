"""The simulated mulligan (C) without playing games: how stable it is, and how it compares with D and R.

    cd <svsim checkout at c962055 or later> && PYTHONPATH=. python3 <this> --stability [--hands 50] [--ns 4 8 16]
    cd <svsim checkout> && PYTHONPATH=. python3 <this> --behaviour --n 8 [--hands 125] [--workers 4]

Uses svsim.agents.mulligan.opening / decide (1 号, c962055): `opening(deck, opponent, first, seed)` deals
a hand and stops at the deck's own mulligan; `decide(state, spec, seed)` returns the positions to
redraw for spec "default" (D), "rules" (R) or "sim:N:H" (C; N play-outs per redraw subset, H turns a
side, the same N determinizations for every subset).
- --stability: per deck x opponent x seat, --hands hands; C decides twice with two seeds; reported
  is how often the two runs choose the same subset, for each N, and the mean milliseconds per
  decision (measure on an idle machine). The N to use is the smallest with agreement >= 90%.
- --regret: whether the two runs' disagreement is between subsets about as good (the architecture
  thread to decide on C): the play-out loop of agents.sim_mulligan.simulated, repeated here (it returns
  only the best subset) to keep every subset's mean; per hand two runs at --n (seeds 1 and 2) and a
  referee run at 4 x --n (seed 3), all with their own worlds. Each run picks by the mean raw score, as C
  does (8 x logit; a play-out that ends the game scores +-1000). For reading, every play-out is also
  turned into a win chance (1 / (1 + exp(-score / 8)), 1 or 0 for a finished game), so the regret is in
  win-rate points: the referee's best subset minus the referee's value of each run's pick. Also: the
  signal-to-noise per hand, the referee's gap between its best and second-best subsets over the
  standard error of one subset's mean at --n (the decision's own noise); and how often a play-out
  ended the game. The thread's reading, fixed beforehand: a median regret under 1 win-rate point
  means C sways between near-ties at little cost (C: not worth the compute); a large regret means
  real noise; C's gates stay shelved either way.
- --behaviour: the three ways on the same hands (C at --n): how often each card is kept when dealt,
  the mean number redrawn, the C-R and C-D agreement (same subset), and each deck's goal as in
  mulligan_check.py (after the mulligans both sides pass, the hand read at each own turn start).
Condition: the opponent's 40-card list is known (order and hand not); C's play-outs use it too.
"""
import argparse
import time
from collections import Counter, defaultdict
from multiprocessing import Pool

DECKS_T = ("elf-t", "nemesis-t", "ramp-t", "pirate-t")


def stability_job(job):
    from svsim.agents.mulligan import decide, opening
    deck, opp, first, seed, n = job
    st = opening(deck, opp, first, seed)
    t = time.perf_counter()
    a = tuple(sorted(decide(st.clone(), f"sim:{n}:5", seed=1)))
    ms = 1000 * (time.perf_counter() - t)
    b = tuple(sorted(decide(st.clone(), f"sim:{n}:5", seed=2)))
    return deck, n, a == b, ms


def subset_values(state, n, horizon=5, seed=0):
    """agents.sim_mulligan.simulated's loop, keeping each redraw's mean raw score (what C ranks by) and its
    mean win chance with that mean's standard error, and how many play-outs ended the game."""
    import math
    import random
    from itertools import combinations
    from svsim.agents.greedy_agent import GreedyAgent
    from svsim.agents.sim_mulligan import _legal
    from svsim.core.actions import Mulligan
    from svsim.core.engine import apply
    from svsim.core.view import determinize
    from svsim.learn.model import Learned
    from svsim.learn.phased import PhasedLearned
    from svsim.search.evaluate import DEFAULT, evaluate
    me = state.active
    size = len(state.players[me].hand)
    subsets = [c for k in range(size + 1) for c in combinations(range(size), k)]
    rng = random.Random(seed * 7919 + state.turn)
    worlds = [rng.getrandbits(64) for _ in range(n)]
    weights = PhasedLearned(fallback=Learned())
    play = Learned(fallback=DEFAULT)
    out, ended = {}, 0
    for redraw in subsets:
        raw, win = [], []
        for w in worlds:
            s = determinize(state, me, random.Random(w))
            apply(s, Mulligan(redraw))
            agents = [GreedyAgent(w % 100003 + i, samples=1, weights=play) for i in (0, 1)]
            while not s.over and s.turn <= 2 * horizon:
                apply(s, agents[s.active].act(s, _legal(s)))
            v = evaluate(s, me, weights, player_moves_next=(s.active == me))
            raw.append(v)
            if s.over:
                ended += 1
                win.append(1.0 if s.winner == me else 0.0 if s.winner == 1 - me else 0.5)
            else:
                win.append(1 / (1 + math.exp(-max(min(v / 8.0, 50.0), -50.0))))
        m = sum(win) / n
        se = (sum((x - m) ** 2 for x in win) / max(n - 1, 1) / n) ** 0.5
        out[redraw] = (sum(raw) / n, m, se, win)
    return out, ended / (n * len(subsets))


def regret_job(job):
    from svsim.agents.mulligan import opening
    deck, opp, first, seed, n = job
    st = opening(deck, opp, first, seed)
    runs = [subset_values(st.clone(), k, seed=sd) for k, sd in ((n, 1), (n, 2), (4 * n, 3))]
    ended = sum(e for _, e in runs) / 3
    vals = [r for r, _ in runs]
    picks = [max(r, key=lambda c: r[c][0]) for r in vals[:2]]          # by mean raw score, as C picks
    ref = vals[2]
    by_win = sorted((v[1] for v in ref.values()), reverse=True)
    best, second, worst = by_win[0], by_win[1], by_win[-1]
    se_n = sum(v[2] for v in vals[0].values()) / len(vals[0])          # one subset's mean at --n
    regrets = [100 * (best - ref[p][1]) for p in picks]                 # win-rate points (the max is biased up)
    # without the selection bias: the referee's worlds in two halves, the best picked on one half and the
    # pick valued against it on the other, both ways round
    half = 2 * n
    mean = lambda c, a, b: sum(ref[c][3][a:b]) / (b - a)
    split = []
    for (a1, b1), (a2, b2) in (((0, half), (half, 2 * half)), ((half, 2 * half), (0, half))):
        top = max(ref, key=lambda c: mean(c, a1, b1))
        split += [100 * (mean(top, a2, b2) - mean(p, a2, b2)) for p in picks]
    # the noise that matters for ranking: the two best subsets share their worlds, so their paired difference
    r1 = vals[0]
    order = sorted(r1, key=lambda c: -r1[c][1])
    diffs = [x - y for x, y in zip(r1[order[0]][3], r1[order[1]][3])]
    md = sum(diffs) / n
    se_pair = (sum((x - md) ** 2 for x in diffs) / max(n - 1, 1) / n) ** 0.5
    ref_gap = (best - second) / max(se_pair, 1e-9)
    return (deck, picks[0] == picks[1], regrets, 100 * (best - worst), (best - second) / max(se_n, 1e-9), 100 * se_n,
            ended, split, ref_gap, 100 * se_pair, 100 * abs(ref[picks[0]][1] - ref[picks[1]][1]))


def behaviour_job(job):
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from mulligan_check import goal
    from svsim.agents.mulligan import decide, opening
    from svsim.core.actions import EndTurn, Mulligan
    from svsim.core.engine import apply
    deck, opp, first, seed, n = job
    out = {}
    st0 = opening(deck, opp, first, seed)
    me = st0.active
    dealt = [c.defn.card_id for c in st0.players[me].hand]
    for name, spec in (("D", "default"), ("R", "rules"), ("C", f"sim:{n}:5")):
        st = st0.clone()
        idx = tuple(sorted(decide(st, spec, seed=1)))
        kept = [cid for i, cid in enumerate(dealt) if i not in idx]
        apply(st, Mulligan(idx))
        if not st.over and st.phase.name != "MAIN":           # going first: the opponent's mulligan comes after
            from svsim.agents.mulligan import decide as dec
            apply(st, Mulligan(tuple(dec(st, "default"))))
        hands = {}
        while st.players[me].turns_taken < 6 and not st.over:
            if st.active == me:
                hands[st.players[me].turns_taken] = list(st.players[me].hand)
            apply(st, EndTurn())
        out[name] = (idx, kept, goal(deck, hands, first))
    return deck, first, dealt, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stability", action="store_true")
    ap.add_argument("--behaviour", action="store_true")
    ap.add_argument("--regret", action="store_true")
    ap.add_argument("--hands", type=int, default=50)
    ap.add_argument("--ns", type=int, nargs="+", default=[4, 8, 16])
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--seed", type=int, default=34000000)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    print("条件：对手卡表已知（牌序、手牌未知）；C 的推演也按已知卡表发对手的牌。")
    if args.stability:
        jobs = [(d, o, f, args.seed + h, n) for n in args.ns for d in DECKS_T for o in DECKS_T
                for f in (True, False) for h in range(args.hands // 4 or 1)]
        res = defaultdict(lambda: [0, 0, 0.0])
        with Pool(args.workers) as pool:
            for deck, n, same, ms in pool.imap_unordered(stability_job, jobs, chunksize=1):
                r = res[(deck, n)]
                r[0] += 1
                r[1] += same
                r[2] += ms
        for n in args.ns:
            cells = [f"{d} {res[(d, n)][1] / res[(d, n)][0]:.0%}" for d in DECKS_T]
            tot = [sum(res[(d, n)][i] for d in DECKS_T) for i in range(3)]
            print(f"  N={n:<3} 两次运行选中同一换牌组合：{tot[1] / tot[0]:.0%}（" + "，".join(cells) +
                  f"），每次起手平均 {tot[2] / tot[0]:.0f} ms")
    if args.regret:
        jobs = [(d, o, f, args.seed + 500 + h, args.n) for d in DECKS_T for o in DECKS_T for f in (True, False)
                for h in range(args.hands // 32 or 1)]
        res = []
        with Pool(args.workers) as pool:
            for r in pool.imap_unordered(regret_job, jobs, chunksize=1):
                res.append(r)
        n = len(res)
        med = lambda xs: sorted(xs)[len(xs) // 2]
        regrets = [x for r in res for x in r[2]]
        snr = [r[4] for r in res]
        print(f"  --regret，N={args.n}（裁判 N={4 * args.n}），{n} 手；两次选中同一组合 {sum(r[1] for r in res) / n:.0%}")
        print(f"  遗憾（胜率点；裁判的最好组合减去裁判对所选组合的估值）：中位 {med(regrets):.2f}，平均 {sum(regrets) / len(regrets):.2f}，"
              f"超过 1 点的 {sum(x > 1 for x in regrets) / len(regrets):.0%}，超过 3 点的 {sum(x > 3 for x in regrets) / len(regrets):.0%}")
        print(f"  16 个组合最好减最差（裁判，胜率点）：中位 {med([r[3] for r in res]):.1f}；"
              f"单个组合均值的标准误（N={args.n}，胜率点）：平均 {sum(r[5] for r in res) / n:.1f}")
        print(f"  信噪比（裁判的最好减第二好 ÷ N={args.n} 的标准误）：中位 {med(snr):.2f}，"
              f"大于 1 的手 {sum(x > 1 for x in snr) / n:.0%}，大于 2 的手 {sum(x > 2 for x in snr) / n:.0%}")
        print(f"  推演里对局提前结束的比例：{sum(r[6] for r in res) / n:.1%}")
        split = [x for r in res for x in r[7]]
        print(f"  去掉选择偏差的遗憾（裁判的世界分两半：一半挑最好，另一半估值，两个方向都算）：中位 {med(split):.2f}，"
              f"平均 {sum(split) / len(split):.2f}，超过 1 点的 {sum(x > 1 for x in split) / len(split):.0%}")
        print(f"  两次所选组合在裁判眼里的差 |裁判(第一次) − 裁判(第二次)|：中位 {med([r[10] for r in res]):.2f}")
        print(f"  配对信噪比（裁判的最好减第二好 ÷ N={args.n} 时这两个组合配对差的标准误 {sum(r[9] for r in res) / n:.1f} 点）："
              f"中位 {med([r[8] for r in res]):.2f}，大于 1 的手 {sum(r[8] > 1 for r in res) / n:.0%}")
        print(f"  读法（架构线程事先定的）：遗憾中位 < 1 个胜率点 → 摇摆、代价小；否则是真噪声。两种都不重开 C 的闸门。")
        for d in DECKS_T:
            sub = [r for r in res if r[0] == d]
            if sub:
                rr = [x for r in sub for x in r[2]]
                print(f"    {d}：一致 {sum(r[1] for r in sub) / len(sub):.0%}，遗憾中位 {med(rr):.2f}，"
                      f"信噪比中位 {med([r[4] for r in sub]):.2f}，提前结束 {sum(r[6] for r in sub) / len(sub):.1%}")
    if args.behaviour:
        jobs = [(d, o, f, args.seed + h, args.n) for d in DECKS_T for o in DECKS_T for f in (True, False)
                for h in range(args.hands)]
        agg = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))       # deck, first -> method -> [n, redrawn, goal]
        agree = defaultdict(lambda: Counter())
        keep = defaultdict(lambda: defaultdict(lambda: [0, 0]))         # deck -> (method, card) -> [dealt, kept]
        with Pool(args.workers) as pool:
            for deck, first, dealt, out in pool.imap_unordered(behaviour_job, jobs, chunksize=1):
                for m, (idx, kept, ok) in out.items():
                    a = agg[(deck, first)][m]
                    a[0] += 1
                    a[1] += len(idx)
                    a[2] += ok
                    kc = Counter(kept)
                    for cid, cnt in Counter(dealt).items():
                        keep[deck][(m, cid)][0] += cnt
                        keep[deck][(m, cid)][1] += min(kc[cid], cnt)
                agree[deck]["C=R"] += out["C"][0] == out["R"][0]
                agree[deck]["C=D"] += out["C"][0] == out["D"][0]
                agree[deck]["n"] += 1
        from svsim.cards.pool import POOL
        for deck in DECKS_T:
            print(f"\n== {deck}（C 的 N={args.n}）：C 和 R 选同一组合 {agree[deck]['C=R'] / agree[deck]['n']:.0%}，"
                  f"C 和 D {agree[deck]['C=D'] / agree[deck]['n']:.0%}")
            for first in (True, False):
                a = agg[(deck, first)]
                print(f"  {'先手' if first else '后手'}：" + "；".join(
                    f"{m} 平均换 {a[m][1] / a[m][0]:.2f} 张、目标达成 {a[m][2] / a[m][0]:.1%}" for m in "DRC"))
            cards = sorted({cid for (m, cid) in keep[deck]}, key=lambda c: -keep[deck][("D", c)][0])
            for cid in cards:
                cells = " / ".join(f"{keep[deck][(m, cid)][1] / max(keep[deck][(m, cid)][0], 1):.0%}" for m in "DRC")
                print(f"    {POOL[cid].name_zh if cid in POOL else cid:<20} {cells}")


if __name__ == "__main__":
    main()
