import sys, pickle, time
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, "/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad")
from multiprocessing import Pool
from rhino_lethal import position
from svsim.search.formula import estimate
from svsim.search.combo import plan

def run(seed):
    s = position(seed)
    hp = s.players[1].leader_hp
    t = time.perf_counter(); e = estimate(s); te = time.perf_counter() - t
    wards = any(f.keywords & 1 for f in s.players[1].followers)
    return seed, hp, e.damage, te, wards, e.text(hp)

if __name__ == "__main__":
    combo = {r[0]: r for r in pickle.load(open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/rhino_combo.pkl", "rb"))}
    with Pool(4) as pool:
        res = pool.map(run, sorted(combo))
    lethal = [r for r in res if combo[r[0]][1]]
    none = [r for r in res if not combo[r[0]][1] and combo[r[0]][2] == "ceiling"]
    open_ = [r for r in res if not combo[r[0]][1] and combo[r[0]][2] == "search"]
    print(f"verified lethals {len(lethal)}: formula says enough in {sum(r[2] >= r[1] for r in lethal)}")
    print(f"planner says no lethal {len(none)}: formula agrees in {sum(r[2] < r[1] for r in none)}")
    print(f"open {len(open_)}: formula says enough in {sum(r[2] >= r[1] for r in open_)} (ward in {sum(r[4] for r in open_)})")
    t = sorted(r[3] for r in res)
    print(f"formula time: median {t[len(t)//2]*1000:.1f} ms, max {t[-1]*1000:.0f} ms")
    under = [r for r in lethal if r[2] < r[1]]
    over = [r for r in none if r[2] >= r[1]]
    pickle.dump((under, over), open("/tmp/claude-0/-home-user-test1/4558b0d4-7d84-547b-a46c-c361326f3747/scratchpad/formula_diff.pkl", "wb"))
    print("under (seed, hp, formula):", [(r[0], r[1], r[2]) for r in under])
    print("over (seed, hp, formula, ward):", [(r[0], r[1], r[2], r[4]) for r in over])
