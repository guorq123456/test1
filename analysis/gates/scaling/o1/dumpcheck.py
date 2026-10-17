"""O1 check: the builder's per-decision dump against the analysis line's own run (decisions, start, recorded visits,
expansion order, every prior per legal move)."""
import gzip, json, sys
import numpy as np
probs, dump = sys.argv[1], sys.argv[2]
z = dict(np.load(probs))
meta = json.load(gzip.open(probs.replace(".npz", "-meta.json.gz"), "rt"))
names = [str(x) for x in z["names"]]
loff = z["loff"]
by = {(m["g"], m["i"]): k for k, m in enumerate(meta)}
seen, prob = set(), {"not_mine": 0, "start": 0, "visits": 0, "order": 0, "order_first": 0}
mx = {n: 0.0 for n in names}
rows = 0
for line in gzip.open(dump, "rt"):
    d = json.loads(line)
    rows += 1
    k = by.get((d["g"], d["i"]))
    if k is None:
        prob["not_mine"] += 1
        continue
    seen.add(k)
    m = meta[k]
    prob["start"] += d["start"] != m["start"]
    prob["visits"] += [int(x) for x in d["visits"]] != m["visits"]
    prob["order"] += d["order"] != m["order"]
    prob["order_first"] += d["order"][0] != m["order"][0]
    for n in names:
        mine = z["raw_" + n][loff[k]:loff[k + 1]]
        theirs = np.asarray(d["priors"][n], float)
        mx[n] = max(mx[n], float(np.abs(mine - theirs).max()))
prob["mine_not_in_dump"] = len(meta) - len(seen)
print(json.dumps({"dump_rows": rows, "my_decisions": len(meta), "problems": prob,
                  "max_abs_diff": {n: f"{v:.2e}" for n, v in mx.items()}}))
