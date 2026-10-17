"""Expansion order with a fresh search object per game (as in play: an agent is made per game), so XPrune's cache
(keyed by hand uids, which repeat across games) never carries over between games."""
import gzip, json, sys
from multiprocessing import Pool
sys.path.insert(0, sys.argv[3])
import d8


def one(job):
    path, g = job
    from svsim.learn.netdata import _search
    from svsim.tools.arena import make_agent
    rec = next(r for r in d8._load(path) if r["g"] == g)
    search = _search(make_agent(d8._spec(rec), 0))
    out = []
    for i, state, legal, keys, key_of, kv, start, end, bad, n_legal in d8._decisions(rec):
        firsts = [key_of.index(k) for k in range(len(keys))]
        pos = {k: n for n, k in enumerate(keys)}
        order = [pos[k] for k in search._options(state, state.active, None) if k in pos]
        order += [k for k in range(len(keys)) if k not in order]
        out.append((g, i, [firsts[k] for k in order], order[:2]))
    return out


if __name__ == "__main__":
    path, out = sys.argv[1], sys.argv[2]
    games = sorted(r["g"] for r in d8._load(path))
    rows = []
    with Pool(4) as pool:
        for part in pool.imap_unordered(one, [(path, g) for g in games], chunksize=8):
            rows.extend(part)
    rows.sort()
    json.dump(rows, gzip.open(out, "wt"))
    print(len(rows))
