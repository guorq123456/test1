"""Replay a versus gate's games of A and of B side by side, so the first position where they choose
differently, and the turns after it on both lines, can be read (the architecture thread 18:39: why ramp-t
vs pirate-t loses whenever features are added; numbers only).

Plays what tools.gate.play_pair played in --versus mode, with the gate's own _agent and the same agent
seeds (A and B 2 x seed + seat, the third agent C 2 x seed + 1 - seat + 7919), for every seed and seat whose
A and B games were not move-for-move the same in the gate. A and B are asked at each of their decisions on
the one shared game; C plays once for both while the games are the same. At the first decision where A and
B differ, the game and C are copied and each line goes on alone, until the opponent has ended two more turns
(or the game is over); --full plays both lines to the end and checks both games' points against the gate's
row (that this side-by-side play reproduces the gate). Run it in a checkout of the code the gate ran on.

    cd <checkout> && PYTHONPATH=. python3 <this> --rows GATE.jsonl --a SPEC --out games.jsonl.gz
                                               [--workers 4] [--full] [--pairs K]

Condition: the opponent's 40-card list is known (order and hand not).
"""
import argparse
import copy
import gzip
import json
import os
from multiprocessing import Pool

B = C = "level-strong"
DECK, OPP = "ramp-t", "pirate-t"
OPP_TURNS = 2


def job(args):
    k, seed, seat, spec, full = args
    from svsim.cards import decks
    from svsim.core.actions import EndTurn, to_dict
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.gate import _agent
    from svsim.ui.session import DECKS
    mine, theirs = decks.build(DECKS[DECK][1]), decks.build(DECKS[OPP][1])
    cards = [None, None]
    cards[seat], cards[1 - seat] = mine, theirs
    a, b = _agent(spec, 2 * seed + seat, None, None), _agent(B, 2 * seed + seat, None, None)
    c = _agent(C, 2 * seed + 1 - seat + 7919, None)
    state = new_game(cards[0], cards[1], seed=seed)
    shared, at = [], None
    while not state.over:
        if state.active == seat:
            x = a.act(state, legal_actions(state))
            y = b.act(state, legal_actions(state))
            if to_dict(x) != to_dict(y):
                at = len(shared)
                break
        else:
            x = c.act(state, legal_actions(state))
        shared.append(to_dict(x))
        apply(state, x)
    out = {"k": k, "seed": seed, "seat": seat, "first": state.first, "shared": shared, "at": at}
    if at is None:                                     # the games never split: the gate saw otherwise
        out["winner"] = state.winner
        return out
    lines = {"A": (a, c, state, x), "B": (b, copy.deepcopy(c), state.clone(), y)}
    for side, (me, opp, st, first) in lines.items():
        moves, ended = [to_dict(first)], 0
        apply(st, first)
        while not st.over and (full or ended < OPP_TURNS):
            act = (me if st.active == seat else opp).act(st, legal_actions(st))
            if st.active != seat and isinstance(act, EndTurn):
                ended += 1
            moves.append(to_dict(act))
            apply(st, act)
        out[side] = moves
        out[side + "_over"] = st.over
        if st.over:
            out[side + "_points"] = 1.0 if st.winner == seat else 0.5 if st.winner not in (0, 1) else 0.0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--a", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--pairs", type=int, default=None, help="only pairs k < K")
    args = ap.parse_args()
    rows = {r["k"]: r for r in (json.loads(x) for x in open(args.rows, encoding="utf-8") if x.strip())}
    done = set()
    if os.path.exists(args.out):
        for line in gzip.open(args.out, "rt", encoding="utf-8"):
            d = json.loads(line)
            done.add((d["k"], d["seat"]))
    todo = [(k, r["seed"], seat, args.a, args.full) for k, r in sorted(rows.items())
            if args.pairs is None or k < args.pairs
            for seat in (0, 1) if not r["same"][seat] and (k, seat) not in done]
    print(f"{len(rows)} 对；要重放 {len(todo)} 个座位（已有 {len(done)}）", flush=True)
    bad = nosplit = 0
    with Pool(args.workers) as pool, gzip.open(args.out, "at", encoding="utf-8") as fh:
        for i, d in enumerate(pool.imap_unordered(job, todo), 1):
            r = rows[d["k"]]
            nosplit += d["at"] is None
            for side, key in (("A", "points"), ("B", "b_points")):
                if side + "_points" in d and args.full:
                    d[side + "_matches_gate"] = d[side + "_points"] == r[key][d["seat"]]
                    bad += not d[side + "_matches_gate"]
            fh.write(json.dumps(d, separators=(",", ":")) + "\n")
            fh.flush()
            if i % 50 == 0:
                print(f"  …{i}/{len(todo)}；没分开 {nosplit}；和门不符 {bad}", flush=True)
    print(f"完成；没分开 {nosplit}；和门不符 {bad}", flush=True)


if __name__ == "__main__":
    main()
