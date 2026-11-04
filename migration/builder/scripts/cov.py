"""Scratch: runtime hook coverage for Rune scripts in random Rune-vs-Rune games."""
import random
import sys
import time

sys.path.insert(0, "tests")
from svsim.agents.random_agent import RandomAgent, play_game  # noqa: E402
from svsim.cards.pool import POOL  # noqa: E402
from svsim.core.engine import new_game  # noqa: E402
from svsim.core.enums import Craft  # noqa: E402
from svsim.tools.coverage import instrument  # noqa: E402
from test_cards_rune import random_rune_deck  # noqa: E402
from test_fuzz import check_invariants  # noqa: E402

fired, expected = instrument([c for c in POOL.values() if c.craft == Craft.RUNE])
rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
games = int(sys.argv[1])
turns = actions = 0
t = time.time()
for g in range(games):
    state = new_game(random_rune_deck(rng), random_rune_deck(rng), seed=g)
    n = [0]

    def on(s, a):
        n[0] += 1
        check_invariants(s, a)
    play_game(state, [RandomAgent(2 * g, end_turn_weight=0.2),
                      RandomAgent(2 * g + 1, end_turn_weight=0.2)], on_action=on)
    turns += state.turn
    actions += n[0]
print(f"{games} games in {time.time() - t:.1f}s, avg turns {turns / games:.1f}, "
      f"avg actions {actions / games:.1f}")
never = sorted(expected - set(fired))
print(f"{len(expected)} hooks, {len(expected) - len(never)} fired")
for name, hook in never:
    print("  never:", name, hook)
print("least:", sorted(fired.items(), key=lambda kv: kv[1])[:12])
