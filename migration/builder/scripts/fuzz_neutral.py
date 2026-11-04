import random, sys, collections
sys.path.insert(0, "tests")
from test_cards_neutral import _random_neutral_deck
from test_fuzz import check_invariants
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.core.engine import new_game
from svsim.cards import neutral
NEW = {c.card_id for c in (neutral.EXIAS, neutral.DYNAMES, neutral.SCENE_OF_DEICIDE, neutral.KYRIOS, neutral.NACREHEIM, neutral.REZEAL)}
games = 0; with_new = 0; results = collections.Counter()
for g in range(300):
    rng = random.Random(10_000 + g)
    d0, d1 = _random_neutral_deck(rng), _random_neutral_deck(rng)
    with_new += any(c.card_id in NEW for c in d0 + d1)
    state = new_game(d0, d1, seed=10_000 + g)
    agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
    w = play_game(state, agents, on_action=check_invariants)
    assert state.over and w in (0, 1, -1)
    games += 1; results[w] += 1
print(games, "games ok;", with_new, "with set-10 neutral cards;", dict(results))
