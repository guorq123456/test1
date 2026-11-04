import hashlib, json, sys
from multiprocessing import Pool
CASES = [("level-strong", "ramp-t", "ramp-t"), ("level-strong", "ramp-t", "pirate-t"), ("level-strong", "elf-t", "elf-t"), ("level-normal", "ramp-t", "ramp-t")]
def game(i):
    from svsim.cards.decks import NAMED
    from svsim.core.engine import apply, legal_actions, new_game
    from svsim.tools.arena import make_agent
    spec, a, b = CASES[i]
    deck = lambda n: [d for d, k in NAMED[n].items() for _ in range(k)]
    agents = [make_agent(spec, 8800 + i * 2 + s) for s in range(2)]
    state = new_game(deck(a), deck(b), seed=8800 + i)
    log = []
    while not state.over:
        x = agents[state.active].act(state, legal_actions(state)); log.append(repr(x)); apply(state, x)
    return i, spec, a, b, state.winner, len(log), hashlib.sha256("\n".join(log).encode()).hexdigest()[:16]
if __name__ == "__main__":
    with Pool(4) as p:
        res = sorted(p.map(game, range(len(CASES))))
    json.dump(res, open(sys.argv[1], "w"))
    for r in res: print(*r)
