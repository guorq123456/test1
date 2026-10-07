"""The realized-value test against real game results: is the evaluation world the teacher shares right?

    cd <svsim checkout> && PYTHONPATH=. python3 <this> RECORDS... --rows realized.jsonl --items 150 \
        [--k 4] [--workers 4] --out end_rows.jsonl

realized.py judges both arms at the start of the own next turn with a search
on the same evaluation the teacher uses (learn.phased), so T and G share its
blind spots. Here the same positions (rebuilt from realized.py's job list:
same records, same --seed, same sampling) are played on to the end: on the
same two sets of k determinizations as G, each arm is v2 for the rest of the
turn (one arm never playing c), then v2 against v2 to the end of the game;
G_end = mean over determinizations of (keep arm's result - line arm's result),
a result being 1 / 0.5 / 0. The first --items rows of --rows are used.
"""
import argparse
import json
import random
from multiprocessing import Pool

from svsim.core.engine import apply, legal_actions

import realized as R


def play_out(base, me, veto, seed):
    from svsim.tools.arena import make_agent
    st = base.clone()
    mine = R.agent_with_veto(R.V2, seed, veto)
    while not st.over and st.active == me:
        apply(st, mine.act(st, legal_actions(st)))
    agents = {me: make_agent(R.V2, seed + 3), 1 - me: make_agent(R.V2, seed + 1)}
    while not st.over:
        apply(st, agents[st.active].act(st, legal_actions(st)))
    return 1.0 if st.winner == me else 0.0 if st.winner == 1 - me else 0.5


def measure(job):
    line_text, i, seed, k, row = job
    from svsim.core.view import determinize
    record = json.loads(line_text)
    st = R.state_at(record, i)
    me = st.active
    cid = row["card"]
    outs = []
    for j in range(2 * k):                    # the same determinizations and seeds as G in realized.py
        base = determinize(st, me, random.Random(seed * 1000 + j))
        sd = seed * 1000 + 10 * j
        outs.append(play_out(base, me, R.keeps_card(cid), sd) - play_out(base, me, None, sd))
    return {**row, "G_end": sum(outs) / len(outs), "G_end1": sum(outs[:k]) / k, "G_end2": sum(outs[k:]) / k,
            "G_end_samples": outs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="+")
    ap.add_argument("--rows", required=True)
    ap.add_argument("--items", type=int, default=150)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1, help="realized.py's --seed")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    games = [line for path in args.records for line in R.lines_of(path)]
    rows = [json.loads(l) for l in open(args.rows, encoding="utf-8") if l.strip()][:args.items]
    want = {r["seed"]: r for r in rows}
    rng = random.Random(args.seed)              # realized.py's sampling, replayed to find each row's game
    jobs, n, starts_cache = [], 0, {}
    while want and n < 10 ** 6:
        g, u = rng.randrange(len(games)), rng.random()
        seed = args.seed * 100000 + n
        n += 1
        if seed not in want:
            continue
        if g not in starts_cache:
            starts_cache[g] = R.turn_starts(json.loads(games[g]))
        starts = starts_cache[g]
        i = starts[int(u * len(starts))]
        row = want.pop(seed)
        assert row["i"] == i, (seed, row["i"], i)
        jobs.append((games[g], i, seed, args.k, row))
    with Pool(args.workers) as pool, open(args.out, "w", encoding="utf-8") as fh:
        for out in pool.imap_unordered(measure, jobs):
            fh.write(json.dumps(out) + "\n")
            fh.flush()


if __name__ == "__main__":
    main()
