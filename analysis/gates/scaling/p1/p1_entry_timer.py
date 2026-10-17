"""P1 cross-check without cProfile: wrap only the block entry points (GameState.clone, view.determinize, engine.apply,
engine.legal_actions, SetNet.logit, linear evaluate) with an exclusive timer stack, everywhere they are referenced,
and time `act` on the same decision points. Per-call overhead lands on those few entry calls only."""
import sys, time, types
from collections import defaultdict
sys.path.insert(0, "/tmp/claude-0/-home-user-test1/cf6df9ad-c705-526d-b63f-e3d01c619a8e/scratchpad/d5")
from d5_agree import decisions

rec, seed, n, spec = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from svsim.core.engine import legal_actions as _legal
from svsim.tools.arena import make_agent
dec = decisions(rec, seed, n)
make_agent(spec, 0)                                     # import everything the agent uses
acc = defaultdict(float)
stack = [["other", 0.0]]
clock = time.perf_counter

def wrap(fn, cat):
    def w(*a, **k):
        t = clock()
        top = stack[-1]
        acc[top[0]] += t - top[1]
        stack.append([cat, t])
        try:
            return fn(*a, **k)
        finally:
            t2 = clock()
            acc[cat] += t2 - stack[-1][1]
            stack.pop()
            stack[-1][1] = t2
    w.__wrapped__ = fn
    return w

import svsim.core.engine as E, svsim.core.view as V, svsim.core.state as ST, svsim.learn.setnet as SN, svsim.search.evaluate as EV
targets = {E.apply: "simulator", E.legal_actions: "simulator", V.determinize: "simulator", EV.evaluate: "linear evaluation"}
wrapped = {f: wrap(f, c) for f, c in targets.items()}
for m in list(sys.modules.values()):
    if isinstance(m, types.ModuleType) and (getattr(m, "__name__", "") or "").startswith("svsim"):
        for name, val in list(vars(m).items()):
            if callable(val) and any(val is f for f in wrapped):
                setattr(m, name, wrapped[next(f for f in wrapped if f is val)])
ST.GameState.clone = wrap(ST.GameState.clone, "simulator")
SN.SetNet.logit = wrap(SN.SetNet.logit, "net")
total = 0.0
inside = defaultdict(float)
calls = defaultdict(int)
for k, (g, i, state) in enumerate(dec):
    s = state.clone(); legal = _legal(s)
    a = make_agent(spec, seed + k)
    before = dict(acc)
    t0 = clock(); stack[:] = [["other", t0]]
    a.act(s, legal)
    t1 = clock()
    total += t1 - t0
    for c in acc:
        if c != "other":
            inside[c] += acc[c] - before.get(c, 0.0)
inside["other"] = total - sum(v for c, v in inside.items() if c != "other")
print(f"ms/decision {1000 * total / len(dec):.1f}  " + "  ".join(f"{c} {100 * v / total:.1f}%" for c, v in sorted(inside.items(), key=lambda kv: -kv[1])))
