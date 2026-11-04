import random, sys, importlib
sys.path.insert(0, "tests")
from test_fuzz import check_invariants
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.core.engine import new_game
from svsim.cards.pool import POOL
NEW = {i for i in POOL if str(i).startswith("110") and POOL[i].card_set == 10010} | {90061140}
for mod, fn, pre in (("test_cards_rune", "random_rune_deck", "1103"), ("test_cards_abyss", "random_abyss_deck", "1105"),
                     ("test_cards_haven", "_random_deck", "1106"), ("test_cards_portal", "random_deck", "1107")):
    make = getattr(importlib.import_module(mod), fn)
    with_new = 0
    for g in range(300):
        rng = random.Random(700_000 + g)
        d0, d1 = make(rng), make(rng)
        with_new += any(str(c.card_id).startswith(pre) for c in d0 + d1)
        state = new_game(d0, d1, seed=700_000 + g)
        w = play_game(state, [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)],
                      on_action=check_invariants)
        assert state.over and w in (0, 1, -1)
    print(mod, "300 games ok,", with_new, "with set-10 cards")
