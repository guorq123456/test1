"""Every turn Salem played in the mirror games, and the same turn played by bots.

    cd <svsim checkout> && PYTHONPATH=. python3 <this> POSITIONS_JSON --agent SPEC [--agent SPEC] \
        [--seeds 3] [--workers 4] --out turns.jsonl

POSITIONS_JSON is analysis/mirror-regression/positions.json (its "records" are
Salem's 10 games, Salem in seat 0). For each of Salem's turns: the position at
its start, Salem's moves and what Salem kept at the end (turnlib.kept), and for
each agent and seed the moves it plays from the same start and what it kept.
A turn that wins the game has no end: "won" is true and "kept" is null.
"""
import argparse
import json
from multiprocessing import Pool

from svsim.core.actions import from_dict
from svsim.core.engine import apply, legal_actions
from svsim.tools import records

import turnlib as T

GAMES = {}


def board(p):
    return [f"{T.name(c)} {c.atk}/{c.life}" for c in p.followers]


def salem_turns(gid):
    """(index of the turn's first action, state then, Salem's (state, action) pairs) for seat 0's turns."""
    rec = GAMES[gid]
    acts = [from_dict(a) for a in rec["actions"]]
    st = records.start(rec)
    i = 0
    out = []
    while i < len(acts) and not st.over:
        if st.active != 0 or type(acts[i]).__name__ == "Mulligan":
            apply(st, acts[i])
            i += 1
            continue
        start, snap, turn = i, st.clone(), []
        while i < len(acts) and st.active == 0 and not st.over:
            turn.append((st.clone(), acts[i]))
            apply(st, acts[i])
            i += 1
        out.append((start, snap, turn, st.clone()))
    return out


def summary(start, turn, after):
    """Moves as text, and what was kept (None if the turn won the game)."""
    moves = [T.describe(s, a, 0) for s, a in turn]
    won = after.over and after.winner == 0
    end = turn[-1][0] if turn and type(turn[-1][1]).__name__ == "EndTurn" else None
    return {"moves": moves, "won": won,
            "kept": T.kept(start, end, 0, turn) if end is not None and not won else None}


def bot_turn(job):
    gid, at, spec, seed = job
    from svsim.tools.arena import make_agent
    rec = GAMES[gid]
    st = records.start(rec)
    for a in rec["actions"][:at]:
        apply(st, from_dict(a))
    start = st.clone()
    agent = make_agent(spec, seed)
    turn = []
    while st.active == 0 and not st.over:
        a = agent.act(st, legal_actions(st))
        turn.append((st.clone(), a))
        apply(st, a)
    return gid, at, spec, seed, summary(start, turn, st)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("positions")
    p.add_argument("--agent", action="append", default=[])
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    GAMES.update(json.load(open(args.positions, encoding="utf-8"))["records"])
    rows, jobs = {}, []
    for gid in sorted(GAMES):
        for at, snap, turn, after in salem_turns(gid):
            me, op = snap.players
            rows[(gid, at)] = {
                "game": gid, "at": at, "own_turn": me.turns_taken, "first": snap.first == 0,
                "context": {"pp": f"{me.pp}/{me.max_pp}", "hp": me.leader_hp, "opp_hp": op.leader_hp,
                            "hand": [T.name(c) for c in me.hand], "board": board(me),
                            "opp_board": board(op), "opp_hand": len(op.hand), "ep": me.ep,
                            "sep": me.sep, "bonus": me.bonus_ready},
                "salem": summary(snap, turn, after), "bots": {s: [] for s in args.agent}}
            jobs += [(gid, at, spec, 1000 + k) for spec in args.agent for k in range(args.seeds)]
    print(f"{len(rows)} 个 Salem 回合，{len(jobs)} 次 bot 回合", flush=True)
    with Pool(args.workers, initializer=GAMES.update, initargs=(GAMES,)) as pool:
        for n, (gid, at, spec, seed, res) in enumerate(pool.imap_unordered(bot_turn, jobs), 1):
            rows[(gid, at)]["bots"][spec].append({"seed": seed, **res})
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for key in sorted(rows):
            for runs in rows[key]["bots"].values():
                runs.sort(key=lambda r: r["seed"])
            f.write(json.dumps(rows[key], ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
