import sys, pickle, time
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, ".")
from multiprocessing import Pool
from rhino_lethal import position
from svsim.search.combo import solve
from svsim.search.formula import estimate

def run(seed):
    s = position(seed)
    hp = s.players[1].leader_hp
    t = time.perf_counter(); e = estimate(s); te = time.perf_counter() - t
    r = solve(s, search_nodes=20000)
    wards = any(f.keywords & 1 for f in s.players[1].followers)
    return seed, hp, e.damage, r.sure, r.decided_by, r.ceiling, round(r.seconds, 2), te, wards

if __name__ == "__main__":
    with Pool(4) as pool:
        res = pool.map(run, range(5000, 5200))
    pickle.dump(res, open("fresh_eval.pkl", "wb"))
    from collections import Counter
    print("planner decided by:", dict(Counter(r[4] for r in res)), "| sure:", sum(r[3] for r in res))
    lethal = [r for r in res if r[3]]; none = [r for r in res if r[4] == "ceiling"]
    print(f"formula: says enough in {sum(r[2] >= r[1] for r in lethal)}/{len(lethal)} lethals, "
          f"agrees in {sum(r[2] < r[1] for r in none)}/{len(none)} no-lethal")
    print("misses:", [(r[0], r[1], r[2], r[8]) for r in lethal if r[2] < r[1]])
    print("false alarms:", [(r[0], r[1], r[2], r[8]) for r in none if r[2] >= r[1]])
    t = sorted(r[6] for r in res); print(f"planner time median {t[len(t)//2]:.2f}s 90% {t[int(.9*len(t))]:.1f}s max {t[-1]:.1f}s")
    t = sorted(r[7] for r in res); print(f"formula time median {t[len(t)//2]*1000:.1f}ms max {t[-1]*1000:.0f}ms")
    print("positions with Ward:", sum(r[8] for r in res))
