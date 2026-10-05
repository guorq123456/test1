"""Round-robin matches between agents, in parallel.

    python -m svsim.tools.arena --agents greedy mcts:200 --games 100
    python -m svsim.tools.arena --agents random lethal greedy mcts:200 mcts:800 --games 60

Agents: random, lethal (random + lethal search), greedy (one-ply greedy +
lethal search), mcts:N (ISMCTS with N iterations per decision + lethal search),
greedy-raw / mcts-raw:N (without the lethal search). Each pairing plays both
seats and, for --decks starter, both decks equally often. Prints win rates
with a 95% margin and the average thinking time per decision.
"""
import argparse
from collections import Counter, defaultdict
from itertools import combinations
from multiprocessing import Pool
import random
import time

from svsim.agents.greedy_agent import GreedyAgent
from svsim.agents.lethal_agent import LethalAgent
from svsim.agents.mcts_agent import MCTSAgent
from svsim.agents.random_agent import RandomAgent
from svsim.cards import decks, library
from svsim.core.engine import apply, legal_actions, new_game
from svsim.core.enums import Craft

assert library.__all__
CRAFTS = [c for c in Craft if c != Craft.NEUTRAL]


def make_agent(spec: str, seed: int):
    name, _, arg = spec.partition(":")
    if name == "random":
        return RandomAgent(seed, 0.2)
    if name == "lethal":
        return LethalAgent(RandomAgent(seed, 0.2), seed=seed)
    if name == "greedy-raw":
        return GreedyAgent(seed)
    if name == "greedy":
        return LethalAgent(GreedyAgent(seed), seed=seed)
    if name in ("mcts", "mcts-raw"):
        agent = MCTSAgent(int(arg or 400), seed=seed)
        return agent if name == "mcts-raw" else LethalAgent(agent, seed=seed)
    raise ValueError(f"unknown agent {spec!r}")


def play_one(job) -> tuple:
    """One game; returns (winner spec or None, {spec: (seconds, decisions)})."""
    a, b, g, deck_kind, seed = job
    rng = random.Random(seed * 100003 + g)
    if deck_kind == "starter":
        pirate, ramp = decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON)
        d0, d1 = (pirate, ramp) if g % 2 == 0 else (ramp, pirate)
    else:
        d0, d1 = (decks.random_deck(rng.choice(CRAFTS), rng) for _ in range(2))
    specs = (a, b) if (g // 2) % 2 == 0 else (b, a)
    agents = [make_agent(spec, seed * 1000 + g * 2 + i) for i, spec in enumerate(specs)]
    state = new_game(d0, d1, seed=seed * 100003 + g)
    clock = {a: [0.0, 0], b: [0.0, 0]}
    while not state.over:
        start = time.perf_counter()
        action = agents[state.active].act(state, legal_actions(state))
        clock[specs[state.active]][0] += time.perf_counter() - start
        clock[specs[state.active]][1] += 1
        apply(state, action)
    winner = specs[state.winner] if state.winner in (0, 1) else None
    return a, b, winner, clock


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--agents", nargs="+", required=True)
    parser.add_argument("--games", type=int, default=100, help="games per pairing")
    parser.add_argument("--decks", choices=("starter", "random"), default="starter")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    jobs = [(a, b, g, args.decks, args.seed) for a, b in combinations(args.agents, 2)
            for g in range(args.games)]
    results, clock = defaultdict(Counter), defaultdict(lambda: [0.0, 0])
    start = time.perf_counter()
    with Pool(args.workers) as pool:
        for a, b, winner, game_clock in pool.imap_unordered(play_one, jobs):
            results[(a, b)][winner] += 1
            for spec, (secs, n) in game_clock.items():
                clock[spec][0] += secs
                clock[spec][1] += n
    print(f"{len(jobs)} games in {time.perf_counter() - start:.0f}s ({args.decks} decks)")
    for a, b in combinations(args.agents, 2):
        r = results[(a, b)]
        n = r[a] + r[b] + r[None]
        p = (r[a] + 0.5 * r[None]) / n
        margin = 1.96 * (p * (1 - p) / n) ** 0.5
        print(f"  {a:>12} vs {b:<12} {r[a]:>4}-{r[b]:<4} draws {r[None]:<3} "
              f"{a} wins {p:.0%} ± {margin:.0%}")
    for spec in args.agents:
        secs, n = clock[spec]
        print(f"  {spec:>12}: {secs / max(n, 1) * 1000:.0f} ms per decision")


if __name__ == "__main__":
    main()
