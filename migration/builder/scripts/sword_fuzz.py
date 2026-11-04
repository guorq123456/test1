"""300 random Swordcraft games: half with 2 copies of each set-10 Sword card, half plain random decks."""
import random
import sys

sys.path[:0] = [".", "tests"]
from svsim.agents.random_agent import RandomAgent, play_game  # noqa: E402
from svsim.cards import decks  # noqa: E402
from svsim.core.engine import new_game  # noqa: E402
from svsim.core.enums import Craft  # noqa: E402
from test_cards_sword import check_invariants, random_sword_deck  # noqa: E402
from test_set10_sword import set_10_deck  # noqa: E402

done = 0
for g in range(300):
    rng = random.Random(500000 + g)
    make = set_10_deck if g % 2 == 0 else random_sword_deck
    deck0, deck1 = make(rng), make(rng)
    assert decks.validate(deck0, Craft.SWORD) == [] and decks.validate(deck1, Craft.SWORD) == []
    state = new_game(deck0, deck1, seed=g)
    agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
    winner = play_game(state, agents, on_action=check_invariants)
    assert state.over and winner in (0, 1, -1)
    done += 1
print("games", done)
