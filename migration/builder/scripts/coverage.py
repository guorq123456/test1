import json, sys, glob
from multiprocessing import Pool
sys.path.insert(0, "/home/user/test1")
from svsim.tools.infer_check import _load
def pts(job):
    record, side = job
    from svsim.core.enums import Phase
    from svsim.learn.model import Learned
    from svsim.learn.phased import PhasedLearned
    from svsim.search.infer import unplayed_gains
    from svsim.tools import records as R
    w = PhasedLearned(fallback=Learned()); out = []; seen = set()
    for st, _ in R.steps(record):
        p = st.active; t = (p, st.players[p].turns_taken)
        if st.phase != Phase.MAIN or t in seen or (side is not None and p != side): continue
        seen.add(t)
        if st.players[p].turns_taken < 2 or not st.players[1 - p].hand: continue
        g = unplayed_gains(st, p, w)
        out.append((st.players[1 - p].pp >= 1, any(v >= 0 for v in g.values())))
    return out
if __name__ == "__main__":
    side = None if sys.argv[1] == "-" else int(sys.argv[1]); games = int(sys.argv[2])
    recs = [r for f in sys.argv[3:] for r in _load(f)[:games]]
    with Pool(4) as p: res = [x for part in p.map(pts, [(r, side) for r in recs]) for x in part]
    n = len(res)
    print(f"{n} points, {len(recs)} games: opponent left >=1 PP {sum(a for a,_ in res)/n:.1%}; >=1 flagged card (tau 0) {sum(b for _,b in res)/n:.1%}")
