"""Coordinate search over evaluation weights with greedy self-play (starter decks)."""
import sys, time, json, dataclasses
from multiprocessing import Pool
sys.path.insert(0, "/home/user/test1")
from svsim.agents.greedy_agent import GreedyAgent
from svsim.cards import decks, library  # noqa
from svsim.core.engine import apply, legal_actions, new_game
from svsim.search.evaluate import Weights

PARAMS = ["hand", "hp", "hp_sqrt", "life", "atk", "danger", "pressure", "ep", "sep", "max_pp",
          "ward", "bane", "amulet", "crest", "barrier", "drain"]


def game(job):
    wa, wb, g = job
    pirate, ramp = decks.build(decks.PIRATE_SWORD), decks.build(decks.RAMP_DRAGON)
    d = (pirate, ramp) if g % 2 == 0 else (ramp, pirate)
    seat = (g // 2) % 2
    agents = [None, None]
    agents[seat] = GreedyAgent(g, weights=Weights(**wa))
    agents[1 - seat] = GreedyAgent(g + 7, weights=Weights(**wb))
    s = new_game(*d, seed=50000 + g)
    while not s.over:
        apply(s, agents[s.active].act(s, legal_actions(s)))
    return 1.0 if s.winner == seat else 0.5 if s.winner not in (0, 1) else 0.0


def score(pool, wa, wb, n):
    return sum(pool.map(game, [(wa, wb, g) for g in range(n)])) / n


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    best = dataclasses.asdict(Weights())
    with Pool(4) as pool:
        for rnd in range(2):
            for name in PARAMS:
                for factor in (1.6, 0.6):
                    cand = dict(best, **{name: best[name] * factor})
                    t = time.time()
                    s = score(pool, cand, best, n)
                    print(f"round {rnd} {name} x{factor}: {s:.3f} ({time.time()-t:.0f}s)", flush=True)
                    if s >= 0.55:
                        best = cand
                        print("  accepted", flush=True)
                        break
    print(json.dumps(best))
