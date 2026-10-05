"""Random self-play: a smoke test and a speed benchmark.

    python -m svsim.tools.selfplay --games 1000                  # demo decks
    python -m svsim.tools.selfplay --games 1000 --decks starter  # Pirate Sword vs Ramp Dragon
"""
import argparse
from collections import Counter
import time

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks
from svsim.cards.demo import demo_deck
from svsim.core.engine import new_game


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--decks", choices=("demo", "starter"), default="demo")
    args = parser.parse_args()

    if args.decks == "starter":
        names = ("Pirate Sword", "Ramp Dragon")
        lists = (decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON))
    else:
        names, lists = ("Demo A", "Demo B"), (demo_deck(), demo_deck())

    results, turns, actions = Counter(), 0, 0
    start = time.perf_counter()
    for g in range(args.games):
        seat = g % 2                       # alternate which deck sits in seat 0
        state = new_game(lists[seat], lists[1 - seat], seed=args.seed + g)
        agents = [RandomAgent(seed=2 * g, end_turn_weight=0.2),
                  RandomAgent(seed=2 * g + 1, end_turn_weight=0.2)]
        counter = Counter()
        winner = play_game(state, agents, on_action=lambda s, a: counter.update(["a"]))
        if winner in (0, 1):
            results[names[seat if winner == 0 else 1 - seat]] += 1
            results["first" if winner == state.first else "second"] += 1
        else:
            results["draw"] += 1
        turns += state.turn
        actions += counter["a"]
    elapsed = time.perf_counter() - start
    print(f"{args.games} games in {elapsed:.2f}s ({args.games / elapsed:.0f} games/s, "
          f"{actions / elapsed:.0f} actions/s)")
    print(f"avg turns {turns / args.games:.1f}, avg actions {actions / args.games:.1f}")
    print(f"{names[0]} {results[names[0]]}, {names[1]} {results[names[1]]}, "
          f"draws {results['draw']} | first player {results['first']}, second {results['second']}")


if __name__ == "__main__":
    main()
