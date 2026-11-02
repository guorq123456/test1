import random
import sys
import time
from collections import Counter

sys.path.insert(0, ".")
from svsim.tools.coverage import instrument  # noqa: E402
from svsim.agents.random_agent import RandomAgent, play_game  # noqa: E402
from svsim.cards import neutral  # noqa: E402
from svsim.cards.pool import collectible  # noqa: E402
from svsim.core.engine import new_game  # noqa: E402
from svsim.core.enums import Craft  # noqa: E402
from svsim.core.script import has_script  # noqa: E402
sys.path.insert(0, "tests")
from test_fuzz import check_invariants  # noqa: E402

fired, expected = instrument(neutral.CARDS + neutral.LEADER_AREA + neutral.ALTERNATE_FORMS)
pool = [c for c in collectible(Craft.NEUTRAL)
        if c.craft == Craft.NEUTRAL and (has_script(c.card_id) or not c.has_ability)]
turns = []
winners = Counter()
t = time.time()
N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
for g in range(N):
    rng = random.Random(g)
    d0 = rng.sample([c for c in pool for _ in range(3)], 40)
    d1 = rng.sample([c for c in pool for _ in range(3)], 40)
    s = new_game(d0, d1, seed=g)
    w = play_game(s, [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)], on_action=check_invariants)
    turns.append(s.turn)
    winners[w] += 1
print("time", time.time() - t, "avg turns", sum(turns) / len(turns), "max", max(turns), winners)
never = sorted(expected - set(fired))
print(len(expected), "hooks;", len(expected) - len(never), "fired")
for n in never:
    print("never:", n)
print(sorted(fired.items(), key=lambda kv: kv[1])[:15])
