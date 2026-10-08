"""Per-game timing for the C* confirmation run: the same games and the same definition as
`svsim.tools.search_cost --whole-games` (svsim.tools.search_cost._whole_game: seconds on searched decisions only),
one JSON line per (spec, game) with n = searched decisions, mean = ms per searched decision, plus the totals.
A 90% bootstrap interval (resampling games, paired across the specs by seed) of the ratio of ms per searched decision.

usage: python whole_games_dump.py --deck ramp-t --opponent ramp-t --seed 62000000 --games 40 --out <file.jsonl>
           --spec <uniform> <alloc>
"""
import argparse
import json
import random

import time


def _whole_game(job, lo=50, hi=800):
    """svsim.tools.search_cost._whole_game (747cd58), plus how many searched decisions ran exactly LO or HI
    iterations (the allocation's clip)."""
    spec, deck, opponent, seed = job
    from svsim.cards import decks
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    from svsim.ui.session import DECKS
    agents = [make_agent(spec, 2 * seed + i) for i in range(2)]
    searches = [_search(a) for a in agents]
    state = new_game(decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1]), seed=seed)
    searched_s, searched, decisions, iterations, all_s, at_lo, at_hi = 0.0, 0, 0, 0, 0.0, 0, 0
    while not state.over:
        search = searches[state.active]
        if search is not None:
            search.last_iterations = None
        t = time.perf_counter()
        action = agents[state.active].act(state, legal_actions(state))
        took = time.perf_counter() - t
        all_s += took
        decisions += 1
        if search is not None and search.last_iterations is not None:
            searched_s += took
            searched += 1
            iterations += search.last_iterations
            at_lo += search.last_iterations == lo
            at_hi += search.last_iterations == hi
        apply(state, action)
    return searched_s, searched, decisions, iterations, all_s, at_lo, at_hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True)
    ap.add_argument("--opponent", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--games", type=int, default=40)
    ap.add_argument("--spec", nargs=2, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    args = ap.parse_args()
    rows = {s: [] for s in args.spec}
    with open(args.out, "w", encoding="utf-8") as fh:
        for g in range(args.games):                # game by game, the specs alternating, so both see the same load
            for spec in args.spec:
                seed = args.seed + g
                secs, searched, decisions, iterations, all_s, at_lo, at_hi = _whole_game(
                    (spec, args.deck, args.opponent, seed))
                row = {"spec": spec, "seed": seed, "n": searched, "mean": 1000 * secs / max(1, searched),
                       "total_ms": 1000 * secs, "decisions": decisions, "iterations": iterations,
                       "all_ms": 1000 * all_s, "at_lo": at_lo, "at_hi": at_hi}
                rows[spec].append(row)
                fh.write(json.dumps(row) + "\n")
    base, alloc = (rows[s] for s in args.spec)

    def ratio(idx):
        a = sum(alloc[i]["total_ms"] for i in idx) / sum(alloc[i]["n"] for i in idx)
        b = sum(base[i]["total_ms"] for i in idx) / sum(base[i]["n"] for i in idx)
        return a / b

    idx = list(range(args.games))
    point = ratio(idx)
    rng = random.Random(0)
    boots = sorted(ratio([rng.randrange(args.games) for _ in idx]) for _ in range(args.boot))
    lo, hi = boots[int(0.05 * args.boot)], boots[int(0.95 * args.boot) - 1]
    print(f"{args.spec[1]} vs {args.spec[0]}: ms per searched decision ratio {point:.4f} ({point - 1:+.1%}), "
          f"90% bootstrap over games {lo:.4f}..{hi:.4f}; {args.deck} vs {args.opponent}, seeds {args.seed}.., "
          f"{args.games} games each")
    for spec in args.spec:
        n = sum(r["n"] for r in rows[spec])
        print(f"{spec}: {n} searched decisions, {sum(r['iterations'] for r in rows[spec]) / n:.1f} iterations each, "
              f"at LO {sum(r['at_lo'] for r in rows[spec]) / n:.1%}, at HI {sum(r['at_hi'] for r in rows[spec]) / n:.1%}")


if __name__ == "__main__":
    main()
