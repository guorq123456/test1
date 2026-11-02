import random, sys
sys.path.insert(0, "tests")
from test_cards_dragon import _random_deck, _check
from test_set10_dragon import SET10
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import decks, dragon
from svsim.cards.pool import collectible
from svsim.core.engine import new_game
from svsim.core.enums import Craft
from svsim.core.script import has_script
pool = [c for c in collectible(Craft.DRAGON) if has_script(c.card_id) or c in dragon.KEYWORD_ONLY]
assert all(c in pool for c in SET10)
played = 0
for g in range(300):
    rng = random.Random(9100 + g)
    if g % 2:   # half the games: a set-10-heavy deck (3 of each new card)
        deck0 = [c for c in SET10 for _ in range(3)] + _random_deck(rng, pool)[:10]
        while any(deck0.count(c) > 3 for c in deck0):
            deck0 = [c for c in SET10 for _ in range(3)] + _random_deck(rng, [c for c in pool if c not in SET10])[:10]
    else:
        deck0 = _random_deck(rng, pool)
    deck1 = _random_deck(rng, pool)
    assert decks.validate(deck0, Craft.DRAGON) == [] and decks.validate(deck1, Craft.DRAGON) == []
    state = new_game(deck0, deck1, seed=g)
    agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
    winner = play_game(state, agents, on_action=_check)
    assert state.over and winner in (0, 1, -1)
    played += 1
print("games", played)
