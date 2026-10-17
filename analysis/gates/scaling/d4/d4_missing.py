"""For D4's turn ends not found among scored positions: was any decision of that turn searched?"""
import json, sys
from svsim.learn.netdata import play
from svsim.tools import records as R
from svsim.core.actions import EndTurn
from svsim.core.engine import legal_actions
SPEC = "mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-gen4-59000.npz+neteot"
rep = json.load(open(sys.argv[1]))
out = []
for gi in rep["games"]:
    if not gi["missing_v2"]:
        continue
    record = play((gi["g"], rep["seed"], "ramp-t", "ramp-t", SPEC, 0.0))
    seq = []
    for i, (state, action) in enumerate(R.steps(record)):
        seq.append((i, state.turn, state.active, type(action).__name__, len(legal_actions(state)), record["search"][i] is not None))
    for turn, player, i in gi["missing_v2"]:
        j = i
        while j > 0 and seq[j - 1][2] == seq[i][2] and seq[j - 1][1] == seq[i][1]:
            j -= 1
        out.append({"g": gi["g"], "label_turn": turn, "player": player, "i": i, "decisions": seq[j:i + 1]})
print(json.dumps(out, indent=1))
