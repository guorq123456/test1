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
