"""Play games and save every main-phase decision state with metadata.

Rhinoceroach Forest (mcts:200+plan) vs Ramp Dragon (mcts:200+plan+learned), 40
games, and the Ramp mirror (learned vs hand-set evaluation), 24 games; seats
alternate.

    PYTHONPATH=<svsim checkout>:. python collect.py positions.pkl
"""
import pickle, sys, random
from multiprocessing import Pool
from svsim.cards import decks
from svsim.core.engine import new_game, legal_actions, apply
from svsim.core.enums import Phase
from svsim.tools.arena import make_agent

OUT = sys.argv[1]

def game(job):
    g, kind = job
    rng = random.Random(g)
    if kind == "rhino":
        d = [decks.build(decks.RHINO_FOREST), decks.build(decks.RAMP_DRAGON)]
        specs = ["mcts:200+plan", "mcts:200+plan+learned"]
    else:
        d = [decks.build(decks.RAMP_DRAGON), decks.build(decks.RAMP_DRAGON)]
        specs = ["mcts:200+plan+learned", "mcts:200+plan"]
    if g % 2:
        d.reverse(); specs.reverse()
    s = new_game(d[0], d[1], seed=1000 + g)
    ag = [make_agent(specs[i], g * 7 + i) for i in range(2)]
    rows = []
    while not s.over:
        acts = legal_actions(s)
        a = ag[s.active].act(s, acts)
        if s.phase == Phase.MAIN and len(acts) > 1:
            rows.append(dict(game=f"{kind}{g}", spec=specs[s.active], state=s.clone(), action=a, turn=s.turn))
        apply(s, a)
    for r in rows:
        r["won"] = int(s.winner == r["state"].active)
    return rows

if __name__ == "__main__":
    jobs = [(g, "rhino") for g in range(40)] + [(g, "mirror") for g in range(100, 124)]
    allrows = []
    with Pool(4) as p:
        for rows in p.imap_unordered(game, jobs):
            allrows += rows
            print(len(allrows), flush=True)
    pickle.dump(allrows, open(OUT, "wb"))
    print("done", len(allrows))
