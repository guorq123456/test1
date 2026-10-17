"""B-tier pre-check: with +puct on, the prior hung on the root equals SetPolicy.priors on the real position over the
root's open moves (renormalized), first 20 games of a holdout shard. Run in the B-tier checkout."""
import sys
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, sys.argv[4])
import d8

REC, SPEC, PRIOR = sys.argv[1], sys.argv[2], sys.argv[3]


def one(g):
    from svsim.core.engine import legal_actions
    from svsim.learn.netdata import _search
    from svsim.learn.setpolicy import SetPolicy
    from svsim.tools.arena import make_agent
    pol = SetPolicy.load(PRIOR)
    rec = next(r for r in d8._load(REC) if r["g"] == g)
    out = {"n": 0, "outer": 0, "key_mismatch": 0, "max": 0.0}
    for i, state, legal, keys, key_of, kv, start, end, bad, n_legal in d8._decisions(rec):
        agent = make_agent(SPEC, 1000 + i)
        search = _search(agent)
        search.last_root = None
        agent.act(state.clone(), legal_actions(state))
        root = search.last_root
        if root is None or root.prior is None:
            out["outer"] += 1
            continue
        opts = search._options(state, state.active, None)
        p = np.asarray(pol.priors(state, list(opts.values())), float)
        p = p / p.sum()
        if list(opts) != list(root.prior):
            out["key_mismatch"] += 1
            continue
        mine = np.asarray([root.prior[k] for k in opts])
        out["max"] = max(out["max"], float(np.abs(mine - p).max()))
        out["n"] += 1
    return out


if __name__ == "__main__":
    games = sorted(r["g"] for r in d8._load(REC))[:20]
    with Pool(4) as pool:
        res = pool.map(one, games)
    print({"positions": sum(r["n"] for r in res), "outer": sum(r["outer"] for r in res),
           "key_mismatch": sum(r["key_mismatch"] for r in res), "max_abs_diff": max(r["max"] for r in res)})
