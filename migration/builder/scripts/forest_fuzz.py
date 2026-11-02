import random, sys
sys.path[:0] = ["/home/user/test1/.claude/worktrees/agent-a62f4af58b4265052", "/home/user/test1/.claude/worktrees/agent-a62f4af58b4265052/tests"]
from collections import Counter
from svsim.agents.random_agent import RandomAgent, play_game
from svsim.cards import library, forest, decks
from svsim.core.engine import new_game
from svsim.core.enums import Craft
from svsim.core.script import ALL_HOOKS, script_for
from test_cards_forest import random_forest_deck
from test_fuzz import check_invariants
NEW = [forest.DEBONAIR_DOGSITTER, forest.WOLF_PACK_LACKEY, forest.NATURAL_REINCARNATION, forest.INQUIRING_MISCHIEF,
       forest.GARDEN_ELF, forest.UNTAMED_TESTIMONY, forest.SLEUTHS_BEST_FRIEND, forest.NOSCHES_INTERROGATION,
       forest.NOSCHE, forest.HEARTENING_HYPHAE]
fired = Counter()
for defn in NEW + [forest.UNTAMED_TESTIMONY_CREST]:
    s = script_for(defn.card_id)
    for h in ALL_HOOKS:
        m = getattr(s, h)
        if m is None: continue
        def counted(ctx, m=m, key=(type(s).__name__, h)):
            fired[key] += 1; return m(ctx)
        setattr(s, h, counted)
def biased(rng):
    d = [c for c in NEW for _ in range(3)]
    rest = random_forest_deck(rng)
    for c in rest:
        if len(d) >= 40: break
        if d.count(c) < 3: d.append(c)
    return d
games = 0
for g in range(300):
    rng = random.Random(1000 + g)
    make = biased if g % 2 == 0 else random_forest_deck
    d0, d1 = make(rng), make(rng)
    assert decks.validate(d0, Craft.FOREST) == [] and decks.validate(d1, Craft.FOREST) == [], decks.validate(d0, Craft.FOREST)
    state = new_game(d0, d1, seed=5000 + g)
    agents = [RandomAgent(g, end_turn_weight=0.2), RandomAgent(g + 1, end_turn_weight=0.2)]
    w = play_game(state, agents, on_action=check_invariants)
    assert state.over and w in (0, 1, -1)
    games += 1
print("games", games)
for k, v in sorted(fired.items()): print(k, v)
