# python analysis/scaling/inputcost.py  (scratch paths: the 70200006 holdout records)
"""Per-call cost of three nets on the same positions: the (state, player) pairs gen4-59000 was called on in 8 search
decisions (ramp-t mirror, mcts:200 + neteot), replayed in order through each net with cold caches, interleaved rounds."""
import os, sys
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import gzip, json, time
sys.path.insert(0, "/home/user/test1"); os.chdir("/home/user/test1")
from svsim.core.engine import legal_actions
from svsim.core.enums import Phase
from svsim.tools import records as R
from svsim.tools.arena import make_agent
from svsim.learn import setnet
S = "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/scale/held"
recs = [json.loads(l) for l, _ in zip(gzip.open(f"{S}/rec-70200006.jsonl.gz", "rt"), range(10))]
starts = [s.clone() for r in recs for s, a in R.steps(r) if s.phase == Phase.MAIN and s.turn >= 3 and len(legal_actions(s)) > 1]
starts = starts[::max(1, len(starts) // 8)][:8]
calls = []
plain = setnet.SetNet.logit
def rec(self, state, player):
    calls.append((state.clone(), player)); return plain(self, state, player)
setnet.SetNet.logit = rec
SPEC = "mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=analysis/scaling/models/net-gen4-59000.npz+neteot"
for i, s in enumerate(starts):
    make_agent(SPEC, 2000 + i).act(s.clone(), legal_actions(s))
setnet.SetNet.logit = plain
names = ["net-gen4-59000", "net-in2-59000", "net-in2kc-59000"]
best = {n: 1e9 for n in names}
for rnd in range(5):
    for n in (names if rnd % 2 == 0 else names[::-1]):
        net = setnet.SetNet.load(f"analysis/scaling/models/{n}.npz")
        t = time.perf_counter()
        for st, p in calls:
            net.logit(st, p)
        best[n] = min(best[n], (time.perf_counter() - t) / len(calls))
print(json.dumps({"positions": len(calls), "decisions": len(starts),
                  "us_per_call_best_of_5": {n: round(v * 1e6, 1) for n, v in best.items()},
                  "ratio_to_gen4_59000": {n: round(v / best[names[0]], 3) for n, v in best.items()}}, indent=1))
