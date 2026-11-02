import sys
from svsim.learn.phased import PhasedLearned
from svsim.learn.model import matchup_keys, ALIASES
from svsim.cards.decks import NAMED
from svsim.core.engine import new_game
def deck(n): return [d for d, k in NAMED[n].items() for _ in range(k)]
p = PhasedLearned()
for a, b in [("ramp-t","ramp-t"),("ramp-t","elf-t"),("ramp","ramp")]:
    s = new_game(deck(a), deck(b), seed=1)
    keys = matchup_keys(s, 0, ALIASES)
    hit = next(k for k in keys if k + ("ended",) in p.models)
    m = p.models[hit + ("ended",)]
    print(a, b, "keys", keys, "-> uses", hit, "extras", getattr(m, "extras", ()), "score", round(p.score(s, 0), 4))
