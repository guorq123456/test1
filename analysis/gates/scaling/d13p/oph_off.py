"""Switch-off check for the ophand code: per-position scores through A's scorer on holdout games (printed as hex)."""
import gzip, json, math, sys
from svsim.core.actions import EndTurn
from svsim.learn.setpolicy import decisions
from svsim.search.evaluate import after_end_of_turn
from svsim.tools import records as R
from svsim.tools.arena import make_agent
from svsim.learn.netdata import _search
rec_path, spec = sys.argv[1:3]
sc = _search(make_agent(spec, 0)).weights
out = []
for line in list(gzip.open(rec_path, "rt"))[:20]:
    rec = json.loads(line)
    dec = {i: st.clone() for i, st, *_ in decisions(rec)}
    for i, (state, action) in enumerate(R.steps(rec)):
        if i in dec:
            out.append(float(sc.score(dec[i], dec[i].active)).hex())
        if isinstance(action, EndTurn):
            e = after_end_of_turn(state.clone())
            if e.winner is None:
                out.append(float(sc.score(e, state.active)).hex())
print(len(out))
open(sys.argv[3], "w").write("\n".join(out))
