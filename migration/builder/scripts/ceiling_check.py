import sys, pickle
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, ".")
from multiprocessing import Pool
from rhino_lethal import position
from svsim.search.lethal import LethalSearch

def run(seed):
    s = position(seed)
    r = LethalSearch(max_nodes=150000, sure_only=True).solve(s)
    return seed, r.sure, r.complete, r.nodes, round(r.seconds, 1)

if __name__ == "__main__":
    res = pickle.load(open("rhino_combo.pkl", "rb"))
    seeds = [r[0] for r in res if r[2] == "ceiling"]
    with Pool(4) as pool:
        out = pool.map(run, seeds)
    pickle.dump(out, open("ceiling_check.pkl", "wb"))
    print("ceiling positions", len(out), "| sure lethal found by exact search:", [o[0] for o in out if o[1]],
          "| exact search complete (proves none):", sum(1 for o in out if o[2] and not o[1]))
    for r in res:
        if r[2] == "ceiling": pass
    print("times", sorted(o[4] for o in out)[-5:])
