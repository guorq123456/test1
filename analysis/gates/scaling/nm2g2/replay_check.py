import glob, gzip, json, os, sys
from svsim.learn.scaledata import _play, _stable
P = "plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"; M = "analysis/scaling/models"
RAMP = f"mcts:94+{P}+setnet={M}/net-nm2f-ramp-nem.npz+netmid+puct={M}/prior-nm2-ramp-t.npz:2:1"
NEM = f"mcts:75+{P}+setnet={M}/net-nm2f-ramp-nem.npz+netmid+puct={M}/prior-nm2-nemesis-t.npz:2:1"
gs = tuple(int(x) for x in sys.argv[2].split(","))
n = same = 0
for path in sorted(glob.glob(os.path.join(sys.argv[1], "rec-*.jsonl.gz"))):
    seed = int(os.path.basename(path)[4:-9])
    want = {r["g"]: _stable(r) for r in map(json.loads, gzip.open(path, "rt")) if r["g"] in gs}
    for g in gs:
        ok = _stable(json.loads(json.dumps(_play((seed, g, "ramp-t", "nemesis-t", RAMP, NEM))[1]))) == want[g]
        n += 1; same += ok
        print(seed, g, "same" if ok else "DIFFERENT", flush=True)
print(json.dumps({"games": n, "same": same}))
