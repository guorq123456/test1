"""Milliseconds per decision for two agents, measured in the same games (for picking equal compute).

    cd <svsim checkout> && PYTHONPATH=. python3 time_step.py --a SPEC --b SPEC [--pairs 3] [--seed 900000]

Plays the gate's pairs (same decks and seeds, A in each seat once) in this one
process and times every decision of each agent. Run on an idle machine: both
agents are timed under the same conditions, but absolute times move with load.
"""
import argparse
import statistics
import time

from svsim.cards import decks
from svsim.core.engine import apply, legal_actions, new_game
from svsim.tools.gate import _agent
from svsim.ui.session import DECKS


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--deck", default="ramp")
    p.add_argument("--opponent", default="ramp")
    p.add_argument("--pairs", type=int, default=3)
    p.add_argument("--seed", type=int, default=900000)
    args = p.parse_args()
    times = {args.a: [], args.b: []}
    for k in range(args.pairs):
        seed = args.seed + k
        for seat in (0, 1):
            specs = [None, None]
            specs[seat], specs[1 - seat] = args.a, args.b
            agents = [_agent(s, 2 * seed + i, None) for i, s in enumerate(specs)]
            cards = [None, None]
            cards[seat] = decks.build(DECKS[args.deck][1])
            cards[1 - seat] = decks.build(DECKS[args.opponent][1])
            st = new_game(cards[0], cards[1], seed=seed)
            while not st.over:
                t0 = time.perf_counter()
                a = agents[st.active].act(st, legal_actions(st))
                times[specs[st.active]].append(1000 * (time.perf_counter() - t0))
                apply(st, a)
    for spec, ts in times.items():
        print(f"{spec}: {len(ts)} 步，平均 {statistics.mean(ts):.1f} ms，中位数 {statistics.median(ts):.1f} ms")


if __name__ == "__main__":
    main()
