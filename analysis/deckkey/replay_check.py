"""Fixed-seed games whose every move is recorded, to check a refactor plays exactly the same.

    cd <checkout> && python analysis/deckkey/replay_check.py OUT.json

before.json: the commit before models were looked up by deck (class pairs); after.json: after.
Cases 0, 1 (Ramp mirror) and 5 (Ramp vs Rhino) must be identical; 2-4 involve Face Dragon,
which now falls back (no Face Dragon model) and so plays differently by design."""
import sys, json
sys.path.insert(0, ".")
from multiprocessing import Pool
from svsim.cards import decks
from svsim.core.actions import to_dict
from svsim.core.engine import apply, legal_actions, new_game
from svsim.tools.arena import make_agent
CASES = [("v2", "v2", "ramp", "ramp"), ("mcts:100+plan+learned", "mcts:100+plan+learned", "ramp", "ramp"),
         ("v2", "mcts:100+plan+learned", "ramp", "face"), ("v2", "mcts:100+plan+learned", "face", "ramp"),
         ("mcts:100+plan+learned", "mcts:100+plan+learned", "face", "face"),
         ("v2", "mcts:100+plan+learned", "ramp", "rhino")]
def one(job):
    from svsim.ui.session import DECKS
    i, g = job
    a, b, da, db = CASES[i]
    st = new_game(decks.build(DECKS[da][1]), decks.build(DECKS[db][1]), seed=4242 + g)
    ag = [make_agent(a, 10 + g), make_agent(b, 20 + g)]
    acts = []
    while not st.over:
        x = ag[st.active].act(st, legal_actions(st)); acts.append(to_dict(x)); apply(st, x)
    return f"{i}-{g}", acts
if __name__ == "__main__":
    with Pool(4) as pool:
        res = dict(pool.map(one, [(i, g) for i in range(len(CASES)) for g in range(2)]))
    json.dump(res, open(sys.argv[1], "w"))
    print(len(res), "games")
