"""Print repr of the net's logit at every turn end of the first N games of a recorded shard (run with PYTHONPATH = a checkout)."""
import gzip, json, sys
from svsim.cards import decks
from svsim.core.actions import EndTurn, from_dict
from svsim.core.engine import apply, new_game
from svsim.search.evaluate import after_end_of_turn
from svsim.ui.session import DECKS
from svsim.learn.setnet import load_cached
net = load_cached(sys.argv[1]); rec = sys.argv[2]; ngames = int(sys.argv[3]); DECK = sys.argv[4]
for line in [l for l in gzip.open(rec, "rt") if l.strip()][:ngames]:
    g = json.loads(line)
    st = new_game(decks.build(DECKS[DECK][1]), decks.build(DECKS[DECK][1]), seed=g["seed"])
    for data in g["actions"]:
        if st.over: break
        act = from_dict(data)
        if isinstance(act, EndTurn):
            me = st.active
            end = after_end_of_turn(st.clone())
            if not end.over:
                print(g["g"], end.turn, repr(net.logit(end, me)))
        apply(st, act)
