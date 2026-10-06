"""Exp D: what the learned Ramp model knows, on recorded decision points.

- calibration and AUC of its win estimate, per matchup (vs Rhino, the mirror),
  against the hand-set evaluation and plain leader-defense difference;
- how both evaluations score Burnite's Super-Evolve crest (a curse given to the
  opponent: 2 damage to their leader at the start of each of their turns);
- coefficients that are exactly 0 because the feature never varied in training.

    PYTHONPATH=<svsim checkout>:. python learned_checks.py positions.pkl
"""
from svsim.cards import library as _lib, decks as _decks  # register every card script

import bisect, json, math, pickle, statistics as st, sys
from collections import defaultdict
from svsim.core.actions import Evolve
from svsim.core.engine import apply, legal_actions
from svsim.core.enums import Craft
from svsim.learn.model import WEIGHTS, Learned, deck_craft
from svsim.search.evaluate import DEFAULT, after_end_of_turn, evaluate

rows = pickle.load(open(sys.argv[1], "rb"))
L = Learned(fallback=DEFAULT)
sig = lambda x: 1 / (1 + math.exp(-max(-60, min(60, x / 8))))


def auc(pairs):
    pos = [p for p, w in pairs if w]
    neg = sorted(p for p, w in pairs if not w)
    return sum(bisect.bisect_left(neg, p) + 0.5 * (bisect.bisect_right(neg, p) - bisect.bisect_left(neg, p))
               for p in pos) / (len(pos) * len(neg))


by = defaultdict(lambda: defaultdict(list))
for r in rows:
    s, me = r["state"], r["state"].active
    if deck_craft(s, me) != Craft.DRAGON:
        continue
    e = after_end_of_turn(s)
    if e.over:
        continue
    k = r["game"].rstrip("0123456789")
    by[k]["L"].append((evaluate(e, me, L), r["won"]))
    by[k]["H"].append((evaluate(e, me, DEFAULT), r["won"]))
    by[k]["hp"].append((e.players[me].leader_hp - e.players[1 - me].leader_hp, r["won"]))
    if "learned" in r["spec"]:
        by[k]["cal"].append((sig(evaluate(e, me, L)), r["won"]))
for k, v in by.items():
    hi = [w for p, w in v["cal"] if p > 0.9]
    print(f"{k}: AUC learned {auc(v['L']):.3f} hand-set {auc(v['H']):.3f} defense diff {auc(v['hp']):.3f} | "
          f"learned side: mean estimate {st.mean(p for p, _ in v['cal']):.3f}, actual {st.mean(w for _, w in v['cal']):.3f}; "
          f"estimate > 0.9 at {len(hi)} points, actual {st.mean(hi):.3f}")

dL, dH, could, did = [], [], 0, 0
for r in rows:
    s, me = r["state"], r["state"].active
    if deck_craft(s, me) != Craft.DRAGON:
        continue
    burnite = [a for a in legal_actions(s) if isinstance(a, Evolve) and a.super_ and "Burnite" in s.on_field(a.uid).defn.name]
    if burnite:
        could += 1
        did += r["action"] in burnite
    for a in burnite:
        t = s.clone(); apply(t, a); e = after_end_of_turn(t)
        if e.over:
            continue
        u = e.clone()
        u.players[1 - me].leader_area = [c for c in u.players[1 - me].leader_area if "Burnite" not in c.defn.name]
        if len(u.players[1 - me].leader_area) == len(e.players[1 - me].leader_area):
            continue
        dL.append(evaluate(e, me, L) - evaluate(u, me, L))
        dH.append(evaluate(e, me, DEFAULT) - evaluate(u, me, DEFAULT))
print(f"\nBurnite could be super-evolved at {could} decisions, was at {did}")
print(f"score change from the curse crest on the opponent: learned {st.mean(dL):+.2f}, hand-set {st.mean(dH):+.2f} (n={len(dL)}; + is good for Ramp)")

d = json.load(open(WEIGHTS / "dragon.json"))
zero = [n for n, c in zip(d["names"], d["coef"]) if abs(c) < 1e-9]
print("\ncoefficients exactly 0 in dragon.json (never varied in training):", ", ".join(zero))
