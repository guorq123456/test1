"""Random self-play with the demo decks: a smoke test and a speed benchmark.

    python -m svsim.tools.selfplay --games 1000
"""
import argparse
from collections import Counter
import time

from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards.demo import demo_deck
from svsim.core.engine import new_game


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    deck = demo_deck()
    results, turns, actions = Counter(), 0, 0
    start = time.perf_counter()
    for g in range(args.games):
        state = new_game(deck, deck, seed=args.seed + g)
        agents = [RandomAgent(seed=2 * g, end_turn_weight=0.2),
                  RandomAgent(seed=2 * g + 1, end_turn_weight=0.2)]
        counter = Counter()
        winner = play_game(state, agents, on_action=lambda s, a: counter.update(["a"]))
        results["first" if winner == state.first else "second" if winner in (0, 1) else "draw"] += 1
        turns += state.turn
        actions += counter["a"]
    elapsed = time.perf_counter() - start
    print(f"{args.games} games in {elapsed:.2f}s ({args.games / elapsed:.0f} games/s, "
          f"{actions / elapsed:.0f} actions/s)")
    print(f"avg turns {turns / args.games:.1f}, avg actions {actions / args.games:.1f}")
    print(f"first player wins {results['first']}, second {results['second']}, "
          f"draws {results['draw']}")


if __name__ == "__main__":
    main()
