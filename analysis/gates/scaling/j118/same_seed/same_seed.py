"""J118 step 1: play gate games (svsim.tools.gate's agents, seeds and deals) and log every action each agent returns,
so two checkouts can be compared move by move. Run with PYTHONPATH = the checkout.

    python3 same_seed.py --a SPEC --b SPEC --deck ramp-t --seed 73200000 --pairs 5 --out moves.json
"""
import argparse, json
from svsim.cards import decks
from svsim.tools import gate
from svsim.ui.session import DECKS

ap = argparse.ArgumentParser()
ap.add_argument("--a", required=True)
ap.add_argument("--b", required=True)
ap.add_argument("--deck", required=True)
ap.add_argument("--seed", type=int, required=True)
ap.add_argument("--pairs", type=int, default=5)
ap.add_argument("--out", required=True)
args = ap.parse_args()
deck = decks.build(DECKS[args.deck][1])
games = []
for k in range(2 * args.pairs):
    seed, seat = args.seed + k // 2, k % 2
    log = []
    agents = []
    for who, spec, s in (("A", args.a, 2 * seed + seat), ("B", args.b, 2 * seed + 1 - seat)):
        ag = gate._agent(spec, s, None)
        act = ag.act

        def logged(state, legal, act=act, who=who):
            a = act(state, legal)
            log.append([who, state.turn, repr(a)])
            return a
        ag.act = logged
        agents.append(ag)
    pts, _ = gate._game(deck, deck, seat, agents[0], agents[1], seed, "j118", [args.deck, args.deck])
    games.append({"seed": seed, "seat": seat, "a_points": pts, "actions": log})
    print(seed, seat, pts, len(log), flush=True)
json.dump({"a": args.a, "b": args.b, "deck": args.deck, "games": games}, open(args.out, "w"), indent=0)
