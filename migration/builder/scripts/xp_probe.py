import sys
sys.path.insert(0,'.')
from svsim.tools.puzzles import puzzles
from svsim.core.engine import legal_actions
from svsim.search.xprune import XPrune
from svsim.search.moves import worth_trying
P={n:b for n,b,a in puzzles()}
for name in ("ramp-erntz-normagdala","ramp-erntz-spilling"):
    s=P[name](1); me=s.active; p=s.players[me]
    legal=legal_actions(s); wt=worth_trying(s,legal)
    x=XPrune()
    kept=[a for a in wt if not x(s,a)]
    names={c.uid:c.defn.name for c in p.hand}
    print(name, "legal",len(legal),"worth",len(wt),"kept",len(kept), "pp",p.pp,p.max_pp,"bonus",p.bonus_ready)
    for a in wt:
        if getattr(a,'targets',None) and any(t in names for t in a.targets):
            src=names.get(a.uid,a.uid)
            print("  ", "KEEP" if a in kept else "cut ", src, [names.get(t,t) for t in a.targets])
    print("  hand", [(c.defn.name,c.cost) for c in p.hand])
