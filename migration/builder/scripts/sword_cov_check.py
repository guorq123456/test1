import random
import sys
import time

sys.path.insert(0, "tests")
from svsim.tools.coverage import instrument  # noqa: E402
from svsim.agents.random_agent import RandomAgent, play_game  # noqa: E402
from svsim.cards import sword  # noqa: E402
from svsim.core.engine import new_game  # noqa: E402
from test_cards_sword import random_sword_deck, check_invariants  # noqa: E402

fired, expected = instrument(sword.ALL_CARDS + sword.ALL_TOKENS + sword.ALL_LEADER_AREA)
turns = []
t = time.time()
N = int(sys.argv[1])
for g in range(N):
    rng = random.Random(g)
    d0, d1 = random_sword_deck(rng), random_sword_deck(rng)
    state = new_game(d0, d1, seed=g)
    play_game(state, [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)],
              on_action=check_invariants)
    turns.append(state.turn)
print("time", round(time.time() - t, 1), "avg turns", sum(turns) / len(turns))
never = sorted(expected - set(fired))
print(len(expected), "hooks;", len(never), "never fired")
for n in never:
    print("  never:", n)
