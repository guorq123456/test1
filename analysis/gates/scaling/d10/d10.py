"""D10 and the c* recompute (registered in 379f4bf before any number; report only, offline): A's and B's searches
re-run on the same ramp-t holdout roots. Per point and per search: the root's visits per action key (the record's
keys), the move the agent plays, the root's own prior (PUCT), and ft-t05's prior per key (SetPolicy.priors over all
legal moves, added per key: O1's path). Condition: the opponent's deck list is known (order and hand not).

    cd <checkout of fbb3c21> && PYTHONPATH=. python3 d10.py REC.jsonl.gz --scan scan.json --seed-base B --out out.json

d8.py (analysis/gates/scaling/d8/) must sit next to this file or on the path; the scan is D8's.
"""
import argparse, json, os, random, sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

P = "plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
M = "analysis/scaling/models"
SPECS = {
    "A-PUCT": f"mcts:83+{P}+setnet={M}/net-mid-ramp-t.npz+netmid+puct={M}/prior-ramp-ft-t05.npz:2:1",
    "B-PUCT": f"mcts:88+{P}+setnet={M}/net-gen3-30000.npz+neteot+puct={M}/prior-ramp-ft-t05.npz:2:1",
    "A-UCB": f"mcts:200+{P}+setnet={M}/net-mid-ramp-t.npz+netmid",
    "B-UCB": f"mcts:200+{P}+setnet={M}/net-gen3-30000.npz+neteot",
}
_POL = {}


def _game(job):
    import numpy as np
    import d8
    from svsim.core.actions import EndTurn
    from svsim.core.engine import legal_actions
    from svsim.learn.netdata import _search
    from svsim.learn.setpolicy import SetPolicy
    from svsim.tools.arena import make_agent
    path, g, want = job                       # want: {i: (j, seed)}
    if "pol" not in _POL:
        _POL["pol"] = SetPolicy.load(f"{M}/prior-ramp-ft-t05.npz")
    pol = _POL["pol"]
    rec = next(r for r in d8._load(path) if r["g"] == g)
    out = []
    for i, state, legal, keys, key_of, kv, start, end, bad, n_legal in d8._decisions(rec):
        if i not in want:
            continue
        j, seed = want[i]
        pr = np.asarray(pol.priors(state, legal), float)
        q = np.zeros(len(keys))
        np.add.at(q, key_of, pr)
        row = {"j": j, "g": g, "i": i, "seed": seed, "keys": len(keys), "end": end, "start": bool(start),
               "rec_visits": kv, "prior": q.tolist()}
        pos = {k: n for n, k in enumerate(keys)}
        for name, spec in SPECS.items():
            agent = make_agent(spec, seed)
            search = _search(agent)
            search.last_root = None
            s = state.clone()
            act = agent.act(s, legal_actions(s))
            root = search.last_root
            r = {"chose_end": isinstance(act, EndTurn)}
            if root is None or not root.children:
                r["outer"] = True
            else:
                rv = [0] * len(keys)
                for k, child in root.children.items():
                    if k in pos:
                        rv[pos[k]] = child.visits
                r.update(outer=False, visits=rv, unmatched=sum(1 for k in root.children if k not in pos))
                if root.prior is not None:
                    rp = [None] * len(keys)
                    for k, x in root.prior.items():
                        if k in pos:
                            rp[pos[k]] = x
                    r["root_prior"] = rp
            row[name] = r
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("--scan", required=True)
    ap.add_argument("--seed-base", type=int, required=True)
    ap.add_argument("--sample-seed", type=int, default=74800000)
    ap.add_argument("--points", type=int, default=2000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    rows = json.load(open(args.scan))["rows"]
    pick = sorted(random.Random(args.sample_seed).sample(range(len(rows)), min(args.points, len(rows))))
    per = {}
    for j, n in enumerate(pick):
        per.setdefault(rows[n]["g"], {})[rows[n]["i"]] = (j, args.seed_base + j)
    jobs = [(args.records, g, w) for g, w in sorted(per.items())]
    out = []
    with Pool(args.workers) as pool:
        for part in pool.imap_unordered(_game, jobs):
            out.extend(part)
            print(len(out), "points", flush=True)
    out.sort(key=lambda r: r["j"])
    assert [r["j"] for r in out] == list(range(len(pick)))
    json.dump({"records": os.path.basename(args.records), "sample_seed": args.sample_seed, "seed_base": args.seed_base,
               "specs": SPECS, "picked": pick, "points": out}, open(args.out, "w"))


if __name__ == "__main__":
    main()
