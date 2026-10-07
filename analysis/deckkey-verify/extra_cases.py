"""More fixed-seed games for the deck-keyed model lookup (svsim 491c6aa): every move recorded.

    cd <checkout> && PYTHONPATH=. python3 <this> OUT.json

Run on the commit before 491c6aa and on 491c6aa; compare.py says which games
differ. Cases (A, B, A's deck, B's deck), 2 seeds each:
  0-5 must be identical before and after: the Ramp mirror with the parts the
      replay check did not cover (v1's reply uses the ACT model, the value net,
      the policy prior), and Ramp against Rhino at the strong level, both seats.
  6-9 Face Dragon: after the change, v2 must play exactly as the installed
      mcts:100+plan+learned (no Face model: both fall back to Learned); compare.py
      checks 6 against 7 and 8 against 9 within one file.
"""
import json
import sys
from multiprocessing import Pool

from svsim.cards import decks
from svsim.core.actions import to_dict
from svsim.core.engine import apply, legal_actions, new_game
from svsim.tools.arena import make_agent

INSTALLED, V2, V2S = "mcts:100+plan+learned", "mcts:100+plan+learned+phased", "mcts:200+plan+learned+phased"
V1 = "mcts-reply:100+plan+learned+phased+lazy+focus"
CASES = [
    (V1, INSTALLED, "ramp", "ramp"),
    ("mcts:100+plan+learned+net", INSTALLED, "ramp", "ramp"),
    (V2 + "+prior", V2, "ramp", "ramp"),
    (V2S, "mcts:200+plan+learned", "ramp", "ramp"),
    (V2S, "mcts:200+plan+learned", "ramp", "rhino"),
    ("mcts:200+plan+learned", V2S, "rhino", "ramp"),
    (V2, INSTALLED, "ramp", "face"),
    (INSTALLED, INSTALLED, "ramp", "face"),
    (V2, INSTALLED, "face", "face"),
    (INSTALLED, INSTALLED, "face", "face"),
]


def one(job):
    from svsim.ui.session import DECKS
    i, g = job
    a, b, da, db = CASES[i]
    st = new_game(decks.build(DECKS[da][1]), decks.build(DECKS[db][1]), seed=31337 + g)
    agents = [make_agent(a, 100 + g), make_agent(b, 200 + g)]
    acts = []
    while not st.over:
        x = agents[st.active].act(st, legal_actions(st))
        acts.append(to_dict(x))
        apply(st, x)
    return f"{i}-{g}", acts


if __name__ == "__main__":
    with Pool(4) as pool:
        res = dict(pool.map(one, [(i, g) for i in range(len(CASES)) for g in range(2)]))
    json.dump(res, open(sys.argv[1], "w"))
    print(len(res), "games")
