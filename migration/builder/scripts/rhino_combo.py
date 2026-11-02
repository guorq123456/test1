import sys, pickle
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad")
from multiprocessing import Pool
from rhino_lethal import position
from svsim.search.combo import solve

def run(seed):
    s = position(seed)
    r = solve(s, search_nodes=20000)
    return seed, r.sure, r.decided_by, r.ceiling, s.players[1].leader_hp, round(r.seconds, 2), len(r.line), r.search_nodes

if __name__ == "__main__":
    rows = pickle.load(open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/rhino_rows.pkl", "rb"))
    truth = {r["seed"]: (r.get(100000) or r.get(20000) or r[2000]) for r in rows}
    with Pool(4) as pool:
        res = pool.map(run, sorted(truth))
    pickle.dump(res, open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/rhino_combo.pkl", "wb"))
    from collections import Counter
    by = Counter(r[2] for r in res)
    known_lethal = {s for s, t in truth.items() if t[0]}
    known_none = {s for s, t in truth.items() if not t[0] and t[2]}
    unknown = set(truth) - known_lethal - known_none
    found = {r[0] for r in res if r[1]}
    print("decided by:", dict(by))
    print(f"known sure lethals {len(known_lethal)}: found {len(found & known_lethal)}")
    print(f"known no-lethal {len(known_none)}: model/search wrongly claims lethal {len(found & known_none)}")
    print(f"previously undecided {len(unknown)}: lethal found {len(found & unknown)}, "
          f"model says none {sum(1 for r in res if r[0] in unknown and r[2] == 'ceiling')}, "
          f"still open {sum(1 for r in res if r[0] in unknown and r[2] == 'search' and not r[1])}")
    missed = [(r[0], r[3], r[4], r[2]) for r in res if r[0] in known_lethal and not r[1]]
    print("known lethals missed (seed, model damage, hp, how):", missed)
    t = sorted(r[5] for r in res)
    print(f"time per position: median {t[len(t)//2]:.2f}s, 90% {t[int(len(t)*.9)]:.1f}s, max {t[-1]:.1f}s, total {sum(t):.0f}s")
