"""Mid-turn net pre-gate check: through the agent's own scorer (make_agent(A spec) -> SetNetEnded with +netmid), the
probability at mid-turn decisions (mover to act, scored as is) and at turn ends (after_end_of_turn, turn-end branch)
on the first 20 games of a holdout, against the builder's per-position file (p_new)."""
import gzip, json, math, sys
import numpy as np
from svsim.core.actions import EndTurn
from svsim.core.enums import Phase
from svsim.learn.model import SCALE
from svsim.search.evaluate import after_end_of_turn
from svsim.tools import records as R
from svsim.tools.arena import make_agent

rec_path, spec, mid_npz, end_npz = sys.argv[1:5]
agent = make_agent(spec, 0)
inner = agent
for _ in range(5):
    if hasattr(inner, "search") and hasattr(inner.search, "weights"):
        break
    inner = getattr(inner, "base", None)
scorer = inner.search.weights
zm, ze = np.load(mid_npz), np.load(end_npz)
mid = {(int(g), int(i)): float(p) for g, i, p in zip(zm["g"], zm["i"], zm["p_new"])}
end = {(int(g), int(t)): float(p) for g, t, p in zip(ze["g"], ze["turn"], ze["p_new"])}
games = sorted((json.loads(l) for l in gzip.open(rec_path, "rt") if l.strip()), key=lambda r: r["g"])[:20]
nm = ne = miss = 0
dm = de = 0.0
for rec in games:
    thoughts = rec.get("search") or []
    for i, (state, action) in enumerate(R.steps(rec)):
        if state.phase != Phase.MAIN:
            continue
        me = state.active
        key = (rec["g"], i)
        if key in mid:
            p = 1 / (1 + math.exp(-scorer.score(state, me) / SCALE))
            dm = max(dm, abs(p - mid[key])); nm += 1
        if isinstance(action, EndTurn):
            e = after_end_of_turn(state.clone())
            if e.winner is None:
                k2 = (rec["g"], e.turn)
                if k2 in end:
                    p = 1 / (1 + math.exp(-scorer.score(e, me) / SCALE))
                    de = max(de, abs(p - end[k2])); ne += 1
                else:
                    miss += 1
print(f"mid-turn {nm} positions max |p diff| {dm:.2e}; turn ends {ne} max {de:.2e}; turn ends missing {miss}")
