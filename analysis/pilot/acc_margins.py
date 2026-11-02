"""Per-item margins (Salem line minus bot line) for Salem's four positions, hand-set evaluator and value nets, both
branches, logit scale for nets; same scoring as acc_net.py (acceptance.score, k=40). Written for the acceptance
library's clear/marginal tiers (architecture thread 2026-11-02).

    cd <deck-search worktree> && python <this file> NET.npz [NET.npz ...]
"""
import sys
sys.path.insert(0, "/home/claude/test1/.wt/ds/analysis/resource-value")
import acceptance as A
from svsim.search import evaluate as EV
from svsim.learn.setnet import load_cached
def table(label, ev):
    out = []
    for name, opp, seed, first, turn, salem, bot, kind in A.ITEMS:
        state, seat = A.position(opp, seed, first, turn)
        a, b = A.score(state, seat, salem, evaluate=ev), A.score(state, seat, bot, evaluate=ev)
        out.append(f"  {name[:18]:18s} salem {a:+.4f} bot {b:+.4f} margin {a-b:+.4f} {'PASS' if a>b else 'fail'}")
    print(label); print("\n".join(out), flush=True)
table("hand-set (default evaluator, its own score scale)", None)
for f in sys.argv[1:]:
    net = load_cached(f)
    n = f.rsplit("/",1)[-1]
    table(f"{n} turn-end logit", lambda t, p: net.logit(EV.after_end_of_turn(t), p))
    table(f"{n} mid-turn logit", lambda t, p: net.logit(t, p, mid=True))
