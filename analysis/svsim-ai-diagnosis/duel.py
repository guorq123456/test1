"""Matches between two agents, seats alternating.

    PYTHONPATH=<svsim checkout>:. python duel.py A B mirror|rhino GAMES SEED

Specs: anything tools.arena knows, mctsmax:N (variants.MaxISMCTS) or
turnplan[:budget], each with +plan / +learned; '#label' tells two copies of
the same spec apart. In "rhino" games A plays Rhinoceroach Forest and B Ramp
Dragon; in "mirror" both play Ramp Dragon.
"""
from svsim.cards import library as _lib, decks as _decks  # register every card script
import sys, time
from multiprocessing import Pool
from svsim.cards import decks
from svsim.core.engine import new_game, legal_actions, apply
from turnplan import make

A, B, KIND, N = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 0

def game(g):
    if KIND == "mirror":
        d = [decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON)]
        specs = [A, B] if g % 2 == 0 else [B, A]
    else:                                  # A plays rhino, B plays ramp; seats alternate
        d = [decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON)]
        specs = [A, B]
        if g % 2:
            d.reverse(); specs.reverse()
    s = new_game(d[0], d[1], seed=SEED * 100000 + 5000 + g)
    ag = [make(specs[i], SEED * 1000 + g * 2 + i) for i in range(2)]
    clock = {A: [0.0, 0], B: [0.0, 0]}
    while not s.over:
        t = time.perf_counter()
        a = ag[s.active].act(s, legal_actions(s))
        clock[specs[s.active]][0] += time.perf_counter() - t; clock[specs[s.active]][1] += 1
        apply(s, a)
    return (specs[s.winner] if s.winner in (0, 1) else None), clock

if __name__ == "__main__":
    wins = {A: 0, B: 0, None: 0}; tot = {A: [0.0, 0], B: [0.0, 0]}
    t0 = time.time()
    with Pool(4) as p:
        for w, c in p.imap_unordered(game, range(N)):
            wins[w] += 1
            for k in c: tot[k][0] += c[k][0]; tot[k][1] += c[k][1]
    n = N; pa = (wins[A] + 0.5 * wins[None]) / n
    print(f"{KIND}: {A} vs {B}: {wins[A]}-{wins[B]} draws {wins[None]}  {A} wins {pa:.0%} ± {1.96*(pa*(1-pa)/n)**.5:.0%}  "
          f"({time.time()-t0:.0f}s; ms/decision {A} {1000*tot[A][0]/max(1,tot[A][1]):.0f}, {B} {1000*tot[B][0]/max(1,tot[B][1]):.0f})", flush=True)
