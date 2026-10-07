"""Opening rules (R) against the default opening (D) for one deck, against a pool of opponents.

    cd <svsim checkout at c962055 or later> && PYTHONPATH=. python3 <this> --deck elf-t \
        --opponents elf-t nemesis-t ramp-t pirate-t --phase sprt --seed 38000000 --out sprt.jsonl
    ... --phase fixed --pairs 300 --seed 38500000 --out fixed.jsonl
    python3 <this> --report sprt.jsonl [fixed.jsonl]

The architecture thread (22:22Z): one gate a deck, the opponents in one pool (they take turns along one
seed bank: seed k meets opponents[k % n]), the table split by opponent; v2s on both sides; SPRT 50 / 55
at most 1200 games, and only on H1 a fixed run on new seeds; who actually went first split out; CR on
Salem's scale.

The pairing. R and D are two ways for the same deck, so they are compared on the same deals rather than
against each other: seed s, the deck in seat 0 and then in seat 1 (who goes first comes from the seed),
and in each seat one game with the deck's agent redrawing by R (`+mull=rules[:VARIANTS]`) and one by D
(the default), the opponent always by D, the agents' seeds by seat (2s, 2s+1) in all four games. A
pair's score is R's points minus D's, averaged over the two seats (d); the SPRT runs on 0.5 + d with H0
0.50 and H1 0.55 (tools.gate's normal approximation): H1 is "R lifts the deck's score by 5 points".
When R and D redraw the same cards, the two games are the same game (the agent is nearly deterministic
given the deal), so d is 0 there. Reported side by side, both with intervals over pairs: (a) all pairs,
the effect of deploying R; (b) only the pairs where R and D differ in at least one seat, the effect when
the rule actually acts: more power, but a conditional effect, not the deployed one.
Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import json
import math
import os
import sys
import time
from multiprocessing import Pool

V2S = "mcts:200+plan+learned+phased"
CONDITION = "对手卡表已知（牌序、手牌未知）"
SALEM_CR_PER_LOGIT = 236.0


def play(seed, deck, opp, seat, way, spec):
    """One game: `deck` in `seat` redrawing by `way` ("rules[...]" or "default"), `opp` by default."""
    from svsim.agents.mulligan import decide
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    from svsim.ui.session import DECKS
    names = [deck, opp] if seat == 0 else [opp, deck]
    cards = [decks.build(DECKS[n][1]) for n in names]
    agents = [make_agent(spec + (f"+mull={way}" if i == seat and way != "default" else ""), 2 * seed + i)
              for i in (0, 1)]
    state = new_game(cards[0], cards[1], seed=seed)
    ways = None
    t0 = time.perf_counter()
    while not state.over:
        if ways is None and state.active == seat and state.phase.name == "MULLIGAN":
            ways = [sorted(decide(state.clone(), w)) for w in (way, "default")]
        apply(state, agents[state.active].act(state, legal_actions(state)))
    pts = 0.5 if state.winner not in (0, 1) else 1.0 if state.winner == seat else 0.0
    return {"points": pts, "first": state.first == seat, "turns": state.turn, "seconds": time.perf_counter() - t0,
            "redraw": ways}


def play_seed(job):
    k, seed, deck, opp, way, spec = job
    out = {"k": k, "seed": seed, "opp": opp}
    for seat in (0, 1):
        r = play(seed, deck, opp, seat, way, spec)
        d = play(seed, deck, opp, seat, "default", spec)
        out[f"seat{seat}"] = {"R": r, "D": d, "differ": r["redraw"][0] != r["redraw"][1]}
    return out


def d_of(row):
    return sum(row[f"seat{s}"]["R"]["points"] - row[f"seat{s}"]["D"]["points"] for s in (0, 1)) / 2


def ci(xs):
    n = len(xs)
    if n == 0:
        return 0.0, 0.0
    m = sum(xs) / n
    return m, 1.96 * math.sqrt(sum((x - m) ** 2 for x in xs) / max(n - 1, 1) / n)


def salem_cr(delta, base=0.5):
    """The CR that lifting a score from `base` (D's own) to base + delta is worth, on Salem's scale (236 a logit)."""
    base = min(max(base, 1e-6), 1 - 1e-6)
    p = min(max(base + delta, 1e-6), 1 - 1e-6)
    return SALEM_CR_PER_LOGIT * (math.log(p / (1 - p)) - math.log(base / (1 - base)))


def report(paths):
    for path in paths:
        rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        if not rows:
            continue
        deck = rows[0].get("deck", "?")
        print(f"== {os.path.basename(path)}：{deck}，{len(rows)} 对（每对 R、D 各 2 局）")
        print(f"条件：{CONDITION}。d = 同一副发牌上 R 的得分 − D 的得分（两个座位平均）；区间按对算。")
        opps = sorted({r["opp"] for r in rows})
        print(f"  {'对手':<12}{'对数':>5}  (a) 全部对：R − D（95%）          (b) 至少一边 R≠D 的对：R − D（95%）   R≠D 的对占")
        for opp in opps + ["合计"]:
            sub = rows if opp == "合计" else [r for r in rows if r["opp"] == opp]
            a = [d_of(r) for r in sub]
            b = [d_of(r) for r in sub if r["seat0"]["differ"] or r["seat1"]["differ"]]
            ma, ha = ci(a)
            mb, hb = ci(b)
            base = sum(r[f"seat{x}"]["D"]["points"] for r in sub for x in (0, 1)) / (2 * len(sub))   # D's own score
            print(f"  {opp:<12}{len(sub):>5}  {ma:+.1%} ± {ha:.1%}（CR {salem_cr(ma, base):+.0f}，D 自己 {base:.0%}）"
                  f"          {mb:+.1%} ± {hb:.1%}（{len(b)} 对）          {len(b) / max(len(sub), 1):.0%}")
        for first in (True, False):
            xs = [r[f"seat{s}"]["R"]["points"] - r[f"seat{s}"]["D"]["points"] for r in rows for s in (0, 1)
                  if r[f"seat{s}"]["D"]["first"] == first]
            m, h = ci(xs)
            print(f"  该卡组{'先' if first else '后'}手的局：{len(xs)} 个座位，R − D {m:+.1%} ± {h:.1%}（按座位算）")
        same = sum(s["R"]["redraw"][0] == s["R"]["redraw"][1] and s["R"]["points"] != s["D"]["points"]
                   for r in rows for s in (r["seat0"], r["seat1"]))
        print(f"  R=D 却胜负不同的座位：{same}（agent 种子相同，几乎确定，应接近 0）\n")


def main():
    if "--report" in sys.argv:
        report(sys.argv[sys.argv.index("--report") + 1:])
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True)
    ap.add_argument("--opponents", nargs="+", required=True)
    ap.add_argument("--way", default="rules", help="R's spec for +mull=, e.g. rules or rules:nem4")
    ap.add_argument("--agent", default=V2S)
    ap.add_argument("--phase", choices=("sprt", "fixed"), required=True)
    ap.add_argument("--pairs", type=int, default=600, help="pairs at most (sprt: 1200 R games) or exactly (fixed)")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from svsim.tools.gate import bounds, llr
    rows = []
    if os.path.exists(args.out):
        rows = [json.loads(line) for line in open(args.out, encoding="utf-8") if line.strip()]
    done = {r["k"] for r in rows}
    lo, hi = bounds(0.05, 0.05)
    jobs = [(k, args.seed + k, args.deck, args.opponents[k % len(args.opponents)], args.way, args.agent)
            for k in range(args.pairs) if k not in done]
    print(f"条件：{CONDITION}；{args.deck} 对 {args.opponents}，R = +mull={args.way}，{args.phase}", flush=True)

    def verdict():
        v = llr([0.5 + d_of(r) for r in rows], 0.50, 0.55)
        return v, ("H1" if v >= hi else "H0" if v <= lo else None)

    if args.phase == "sprt" and len(rows) >= 25 and verdict()[1]:
        print(f"已判定：{verdict()}", flush=True)
        return
    with Pool(args.workers) as pool, open(args.out, "a", encoding="utf-8") as fh:
        for r in pool.imap_unordered(play_seed, jobs, chunksize=1):
            r["deck"] = args.deck
            fh.write(json.dumps(r) + "\n")
            fh.flush()
            rows.append(r)
            if len(rows) % 25 == 0:
                m, h = ci([d_of(x) for x in rows])
                v, _ = verdict()
                print(f"  {len(rows)} 对：R − D {m:+.1%} ± {h:.1%}，LLR {v:+.2f}（{lo:.2f} / {hi:.2f}）", flush=True)
            if args.phase == "sprt" and len(rows) % 25 == 0:      # judged every 25 pairs, as tools.gate does
                v, res = verdict()
                if res:
                    print(f"SPRT 停：{res}，{len(rows)} 对，LLR {v:+.2f}", flush=True)
                    pool.terminate()
                    break


if __name__ == "__main__":
    main()
