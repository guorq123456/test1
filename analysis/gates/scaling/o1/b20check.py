"""O1 check: the training / batch path (setpolicy encode + SetPolicy.evaluate) against the search's path
(SetPolicy.priors, the analysis line's o1 run) on the first 20 games of each holdout. Run inside the builder checkout."""
import sys, numpy as np
from svsim.learn.setpolicy import SetPolicy, Decisions
S = sys.argv[1]
for deck, seed in (("elft", 74100038), ("ramp", 71600018)):
    z = dict(np.load(f"{S}/o1/probs-{deck}.npz"))
    key = {(int(g), int(i)): n for n, (g, i) in enumerate(zip(z["g"], z["i"]))}
    koff = z["koff"]
    for v in ("ft", "fz", "ft-t05", "fz-t05"):
        pol = SetPolicy.load(f"analysis/scaling/models/prior-{deck}-{v}.npz")
        np.savez(f"{S}/o1/b20/cards-{deck}-{v}.npz", card_id=pol.card_ids, static=pol.static)
        data = Decisions([f"{S}/o1/b20/dec/dec-{seed}.npz"], f"{S}/o1/b20/cards-{deck}-{v}.npz")
        p = pol.evaluate(data)
        mx, n, miss = 0.0, 0, 0
        for d in range(data.n):
            k = key.get((int(data.g[d]), int(data.step[d])))
            if k is None:
                miss += 1
                continue
            mine = z[v][koff[k]:koff[k + 1]]
            theirs = p[data.moff[d]:data.moff[d + 1]]
            if len(mine) != len(theirs):
                miss += 1
                continue
            mx = max(mx, float(np.abs(mine - theirs).max()))
            n += 1
        print(deck, v, "decisions", n, "unmatched", miss, "max |batch - search path|", f"{mx:.2e}")
