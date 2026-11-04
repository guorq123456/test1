"""Paired difference of two gate files' X arms on the same deals (k, seed): mean over pairs of the X points."""
import json, sys, math
def load(p):
    out = {}
    for line in open(p):
        r = json.loads(line)
        xs = [g["points"] for g in r["games"] if g["arm"] == "x"]
        bs = [g["points"] for g in r["games"] if g["arm"] != "x"]
        out[(r["k"], r["seed"])] = (sum(xs) / len(xs), sum(bs) / len(bs))
    return out
a, b = load(sys.argv[1]), load(sys.argv[2])
keys = sorted(set(a) & set(b))
d = [a[k][0] - b[k][0] for k in keys]
m = sum(d) / len(d)
sd = math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1))
print(f"{len(keys)} 对：A {100*sum(a[k][0] for k in keys)/len(keys):.1f}%，B {100*sum(b[k][0] for k in keys)/len(keys):.1f}%，"
      f"A−B {100*m:+.1f} ± {196*sd/math.sqrt(len(d)):.1f}；基线 {100*sum(a[k][1] for k in keys)/len(keys):.1f}% / {100*sum(b[k][1] for k in keys)/len(keys):.1f}%")
