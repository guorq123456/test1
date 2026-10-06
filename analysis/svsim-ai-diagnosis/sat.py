"""Exp A: saturation of the learned evaluation at Ramp decision points: how close
to 0 or 1 its win estimate is, how much one or two more points of damage to the
enemy leader move it, the gap between the best and second-best single moves,
and its calibration against the games' results.

    PYTHONPATH=<svsim checkout>:. python sat.py positions.pkl sat.pkl
"""
from svsim.cards import library as _lib, decks as _decks  # register every card script

import pickle, sys, math, statistics as st
from collections import Counter
from svsim.core.engine import apply, legal_actions
from svsim.core.actions import EndTurn
from svsim.search.evaluate import evaluate, after_end_of_turn, DEFAULT
from svsim.learn.model import Learned, deck_craft
from svsim.core.enums import Craft

rows = pickle.load(open(sys.argv[1], "rb"))
L = Learned(fallback=DEFAULT)
sig = lambda x: 1 / (1 + math.exp(-max(-60, min(60, x / 8))))

def after(s, a):
    if isinstance(a, EndTurn):
        return after_end_of_turn(s)
    t = s.clone(); apply(t, a); return t

out = dict(root_L=[], root_H=[], d1_L=[], d1_H=[], d2_L=[], d2_H=[], gap_L=[], gap_H=[], cal=[])
seen = 0
for r in rows:
    s = r["state"]; me = s.active
    if deck_craft(s, me) != Craft.DRAGON:
        continue
    seen += 1
    if seen % 3:                       # every third decision is enough
        continue
    e = after_end_of_turn(s)
    if e.over:
        continue
    for tag, w in (("L", L), ("H", DEFAULT)):
        v = sig(evaluate(e, me, w))
        out["root_" + tag].append(v)
        for k in (1, 2):
            t = e.clone(); t.players[1 - me].leader_hp -= k
            if t.players[1 - me].leader_hp > 0:
                out[f"d{k}_{tag}"].append(sig(evaluate(t, me, w)) - v)
        vals = []
        for a in legal_actions(s):
            t = after(s, a)
            if not t.over:
                vals.append(sig(evaluate(t, me, w)))
        vals = sorted(set(round(x, 9) for x in vals), reverse=True)
        if len(vals) > 1:
            out["gap_" + tag].append(vals[0] - vals[1])
    out["cal"].append((sig(evaluate(e, me, L)), r["won"]))

def q(xs, ps=(0.1, 0.25, 0.5, 0.75, 0.9)):
    xs = sorted(xs); return " ".join(f"p{int(p*100)}={xs[int(p*(len(xs)-1))]:.4f}" for p in ps)

print("ramp decisions analysed:", len(out["root_L"]))
for tag, name in (("L", "learned"), ("H", "hand-set")):
    r = out["root_" + tag]
    print(f"\n[{name}] value at end of turn: {q(r)}")
    print(f"   share with value>0.95 or <0.05: {sum(v > .95 or v < .05 for v in r)/len(r):.0%};  >0.99 or <0.01: {sum(v > .99 or v < .01 for v in r)/len(r):.0%}")
    print(f"   value gained by 1 more enemy damage: {q(out['d1_'+tag])}")
    print(f"   value gained by 2 more enemy damage: {q(out['d2_'+tag])}")
    print(f"   gap best vs 2nd-best distinct action (one step): {q(out['gap_'+tag])}")
# calibration of learned
bins = Counter(); wins = Counter()
for v, w in out["cal"]:
    b = min(int(v * 10), 9); bins[b] += 1; wins[b] += w
print("\nlearned calibration (predicted bin -> actual win rate, n):")
for b in sorted(bins):
    print(f"  {b/10:.1f}-{(b+1)/10:.1f}: {wins[b]/bins[b]:.0%}  (n={bins[b]})")
pickle.dump(out, open(sys.argv[2], "wb"))
