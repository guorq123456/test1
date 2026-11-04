"""Where the net's calls come from in a decision of mcts:N + gen2 + neteot, by the innermost caller, and the decision
time against v2skx at the same N (the architecture thread 2026-10-16 00:09Z). Condition: the opponent's deck list is
known (order and hand not).

    python analysis/scaling/fixedcost.py N [DECISIONS] [--records RECDIR]

Decisions: every decision (turn >= 3, more than one legal move) of the first 10 holdout games (s = 70200000),
DECISIONS of them evenly spread. Each side searches the same position with the same seed; the net's caches are
emptied before each decision.
"""
import os, sys
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import gzip, json, time, traceback, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from svsim.core.engine import legal_actions
from svsim.core.enums import Phase
from svsim.tools import records as R
from svsim.tools.arena import make_agent
from svsim.learn import setnet

args = [a for a in sys.argv[1:] if not a.startswith("--records")]
N = int(args[0]); NDEC = int(args[1]) if len(args) > 1 else 60
RECDIR = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--records=")),
              "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/scale/held")
REST = "+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
NET = "+setnet=analysis/scaling/models/net-gen2-20000.npz+neteot"
recs = []
with gzip.open(os.path.join(RECDIR, "rec-70200000.jsonl.gz"), "rt") as fh:
    for line, _ in zip(fh, range(10)):
        recs.append(json.loads(line))
starts = []
for r in recs:          # every decision of the games (not just turn starts): what a gate's game asks
    for s, a in R.steps(r):
        if s.phase == Phase.MAIN and s.turn >= 3 and len(legal_actions(s)) > 1:
            starts.append(s.clone())
starts = starts[::max(1, len(starts) // NDEC)][:NDEC]

def who():
    st = traceback.extract_stack()[:-3]
    for f in reversed(st):                       # innermost first
        fn, name = os.path.basename(f.filename), f.name
        if fn == "mcts.py":
            return "mcts center" if name == "choose" else "mcts " + name
        if fn in ("crossturn_agent.py", "turnplan.py", "xprune.py", "lethal.py", "greedy_agent.py", "turnpick_agent.py",
                  "formula.py", "combo.py", "race.py", "foresight.py", "candidates.py"):
            return fn[:-3] + "." + name
    return "other " + "/".join(os.path.basename(f.filename) + ":" + f.name for f in st[-4:])

stats = collections.defaultdict(lambda: [0, 0.0])
plain = setnet.SetNetEnded.score
def wrapped(self, state, player, player_moves_next=False):
    t = time.perf_counter()
    v = plain(self, state, player, player_moves_next)
    dt = time.perf_counter() - t
    if not player_moves_next and state.winner is None:
        k = who()
        stats[k][0] += 1
        stats[k][1] += dt
    return v
setnet.SetNetEnded.score = wrapped
net = setnet.load_cached("analysis/scaling/models/net-gen2-20000.npz")
total = {"A": 0.0, "B": 0.0}
for i, s in enumerate(starts):
    net._table = None
    a = make_agent(f"mcts:{N}{REST}{NET}", 1000 + i)
    t = time.perf_counter(); a.act(s.clone(), legal_actions(s)); total["A"] += time.perf_counter() - t
    b = make_agent(f"mcts:{N}{REST}", 1000 + i)
    t = time.perf_counter(); b.act(s.clone(), legal_actions(s)); total["B"] += time.perf_counter() - t
n = len(starts)
print(json.dumps({"N": N, "decisions": n, "A_ms": round(total["A"] / n * 1e3, 1), "B_ms_same_N": round(total["B"] / n * 1e3, 1),
                  "by_caller": {k: {"calls_per_decision": round(c / n, 1), "ms_per_decision": round(t / n * 1e3, 2)}
                                for k, (c, t) in sorted(stats.items(), key=lambda kv: -kv[1][1])}}, indent=1))
