import sys, pickle
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad")
from multiprocessing import Pool
from rhino_lethal import position
from svsim.search.lethal import LethalSearch

def run(seed):
    s = position(seed)
    r = LethalSearch(max_nodes=100000, sure_only=True).solve(s)
    return seed, r.sure, r.complete, r.nodes, round(r.seconds, 2), len(r.line)

if __name__ == "__main__":
    rows = pickle.load(open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/rhino_rows.pkl", "rb"))
    final = {r["seed"]: (r.get(100000) or r.get(20000) or r[2000]) for r in rows}
    with Pool(4) as pool:
        res = pool.map(run, [r["seed"] for r in rows])
    pickle.dump(res, open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/rhino_sure.pkl", "wb"))
    sure = sum(r[1] for r in res); complete = sum(r[2] for r in res)
    old_sure = sum(v[0] for v in final.values())
    lost = [r[0] for r in res if final[r[0]][0] and not r[1]]
    new = [r[0] for r in res if r[1] and not final[r[0]][0]]
    times = sorted(r[4] for r in res)
    print(f"sure_only: sure {sure} (before {old_sure}), decided {sure + sum(1 for r in res if r[2] and not r[1])}/120, "
          f"undecided {120 - complete - sum(1 for r in res if r[1] and not r[2])}")
    print(f"lost lethals {lost}, newly found {len(new)}")
    print(f"time median {times[60]:.2f}s, 90% {times[108]:.1f}s, max {times[-1]:.1f}s")
