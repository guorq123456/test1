import random, sys
sys.path.insert(0, "tests")
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import dragon
from svsim.cards.pool import collectible
from svsim.core.engine import new_game
from svsim.core.enums import Craft
from svsim.core.script import has_script
from svsim.tools.coverage import instrument
from test_cards_dragon import _random_deck, _check

pool = [c for c in collectible(Craft.DRAGON) if has_script(c.card_id) or c in dragon.KEYWORD_ONLY]
fired, expected = instrument(dragon.CARDS + dragon.TOKENS + dragon.LEADER_AREA + dragon.ALTERNATE_FORMS)
for g in range(int(sys.argv[1])):
    rng = random.Random(g)
    d0, d1 = _random_deck(rng, pool), _random_deck(rng, pool)
    state = new_game(d0, d1, seed=g)
    play_game(state, [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)], on_action=_check)
never = sorted(expected - set(fired))
print(len(expected), "hooks;", len(never), "never fired:", never)
print(sorted(fired.items(), key=lambda kv: kv[1])[:10])
