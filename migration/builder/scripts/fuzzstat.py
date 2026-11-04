import random, sys
sys.path.insert(0, "tests")
from collections import Counter
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import dragon
from svsim.cards.pool import collectible
from svsim.core.actions import PlayCard, Evolve, Attack
from svsim.core.engine import new_game
from svsim.core.enums import Craft
from svsim.core.script import has_script
from test_cards_dragon import _random_deck

pool = [c for c in collectible(Craft.DRAGON) if has_script(c.card_id) or c in dragon.KEYWORD_ONLY]
print(len(pool), [c.name for c in pool if c.craft != Craft.DRAGON])
played = Counter(); turns = []; nact = []; winners = Counter()
for g in range(100):
    rng = random.Random(g)
    d0, d1 = _random_deck(rng, pool), _random_deck(rng, pool)
    state = new_game(d0, d1, seed=g)
    n = [0]
    def on(s, a):
        n[0] += 1
        if isinstance(a, PlayCard):
            pass
    names = {}
    def on_action(s, a):
        n[0] += 1
    # track plays by wrapping
    orig = state
    agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
    from svsim.core.engine import legal_actions, apply
    while not state.over:
        acts = legal_actions(state)
        a = agents[state.active].act(state, acts)
        if isinstance(a, PlayCard):
            c = state.in_hand(state.active, a.uid)
            played[c.defn.name] += 1
        apply(state, a)
        n[0] += 1
    turns.append(state.turn); nact.append(n[0]); winners[state.winner] += 1
print("avg turns", sum(turns)/len(turns), "avg actions", sum(nact)/len(nact), winners)
print(len(played), "distinct cards played")
missing = [c.name for c in pool if c.name not in played]
print("never played:", missing)
