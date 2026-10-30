"""Check mode for the root's moves kept per decision (search.mcts, SVSIM_ROOT_CHECK=1; the architecture thread
2026-10-10 14:11Z). Every search iteration computes the root's moves again and compares them (keys, actions,
order) with the kept ones; a difference means some card's script let hidden information (the opponent's hand, a
deck's order) into the moves of the player to act. Condition: the opponent's deck list is known (order and hand
not).

Coverage:
1. bench: the first move at the first N step-1 training starts (analysis/speed/bench.py's), level-strong's search;
2. the puzzle bank (tools.puzzles), level-strong, seeds 1-8;
3. self-play: every ordered pair of the named decks (cards.decks.NAMED), G games each, mcts:M at both seats;
4. self-play with random legal decks from the whole pool (cards.decks.random_deck, every craft), R games, mcts:M.
Reports roots compared, differences (with the cards in hand and in play), and the distinct card ids seen in a hand
or in play at the compared roots against the implemented pool.

    python3 root_check.py STEP1_DIR [--named-games 2] [--random-games 300] [--iters 12] [--workers 4] [--out f.json]
"""
import argparse
import json
import os
import random
import sys
from pathlib import Path

os.environ["SVSIM_ROOT_CHECK"] = "1"
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _take():
    import svsim.search.mcts as M
    out = {"checks": M.ROOT_CHECKS[0], "mismatches": list(M.ROOT_MISMATCHES), "seen": sorted(M.ROOT_SEEN)}
    M.ROOT_CHECKS[0] = 0
    M.ROOT_MISMATCHES.clear()
    M.ROOT_SEEN.clear()
    return out


def job(item):
    kind = item[0]
    from svsim.tools.arena import make_agent
    if kind == "bench":
        _, d, n = item
        sys.path.insert(0, f"{d}/ana")
        import student_data as SD
        from svsim.core.engine import legal_actions
        from svsim.tools.gate import _search
        games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
        starts = [r for r in SD._lines(f"{d}/starts.jsonl") if r["split"] == "train"][:n]
        for i, r in enumerate(starts):
            s = SD._state_at(games[r["game"]], r["at"])
            if len(legal_actions(s)) > 1:
                _search(make_agent("level-strong", i)).choose(s.clone())
    elif kind == "puzzles":
        from svsim.tools.puzzles import play, puzzles
        for name, build, _ in puzzles():
            for seed in range(1, 9):
                play(build, "level-strong", seed)
    else:                                          # self-play
        _, d0, d1, seed, iters = item
        from svsim.agents.random_agent import play_game
        from svsim.core.engine import new_game
        agents = [make_agent(f"mcts:{iters}", 2 * seed), make_agent(f"mcts:{iters}", 2 * seed + 1)]
        play_game(new_game(d0, d1, seed=seed), agents)
    return kind, _take()


def main():
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("step1")
    ap.add_argument("--named-games", type=int, default=2)
    ap.add_argument("--random-games", type=int, default=300)
    ap.add_argument("--iters", type=int, default=12)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--bench", type=int, default=30)
    ap.add_argument("--out")
    args = ap.parse_args()
    from svsim.cards import decks
    from svsim.core.enums import Craft
    jobs = [("bench", args.step1, args.bench), ("puzzles",)]
    named = {k: decks.build(v) for k, v in decks.NAMED.items()}
    seed = 0
    for a in named:
        for b in named:
            for _ in range(args.named_games):
                jobs.append(("self", named[a], named[b], 7100000 + seed, args.iters))
                seed += 1
    rng = random.Random(0)
    crafts = [c for c in Craft if c != Craft.NEUTRAL]
    for g in range(args.random_games):
        d0, d1 = (decks.random_deck(rng.choice(crafts), rng) for _ in range(2))
        jobs.append(("self", d0, d1, 7200000 + g, args.iters))
    tot = {"checks": 0, "mismatches": [], "seen": set()}
    by_kind = {}
    with Pool(args.workers) as pool:
        for kind, r in pool.imap_unordered(job, jobs, chunksize=1):
            tot["checks"] += r["checks"]
            tot["mismatches"] += r["mismatches"]
            tot["seen"].update(r["seen"])
            k = by_kind.setdefault(kind, [0, 0])
            k[0] += r["checks"]
            k[1] += len(r["mismatches"])
    pool_ids = {c.card_id for c in decks.KNOWN.values()}
    out = {"roots compared": tot["checks"], "differences": len(tot["mismatches"]),
           "by part (compared, differences)": by_kind, "jobs": len(jobs),
           "distinct cards seen at compared roots": len(tot["seen"]), "implemented pool": len(pool_ids),
           "share of the pool seen": round(len(tot["seen"] & pool_ids) / len(pool_ids), 4),
           "first differences": tot["mismatches"][:20]}
    if args.out:
        Path(args.out).write_text(json.dumps(dict(out, seen=sorted(tot["seen"])), ensure_ascii=False))
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
