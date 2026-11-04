import json, sys, hashlib
p = sys.argv[1]
recs = [json.loads(l) for l in open(p)]
r = recs[0]
print("keys", sorted(r.keys()))
print("seeds", recs[0].get("seed"), recs[-1].get("seed"), "g", recs[0].get("g"), recs[-1].get("g"))
print("ai", r.get("ai"), "version", r.get("version"), "explore", r.get("explore"), r.get("eps"))
s = r.get("search")
print("search len", len(s), "actions", len(r["actions"]))
x = next(v for v in s if v)
print("search entry", json.dumps(x)[:700])
print("sha256", hashlib.sha256(open(p, "rb").read()).hexdigest())
