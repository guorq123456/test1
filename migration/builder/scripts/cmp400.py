import json, sys, hashlib
a = [json.loads(l) for l in open(sys.argv[1])]
b = [json.loads(l) for l in open(sys.argv[2])]
print(len(a), len(b))
print("sha", hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest()[:16], hashlib.sha256(open(sys.argv[2],"rb").read()).hexdigest()[:16])
ga = {r["g"]: r for r in a}; gb = {r["g"]: r for r in b}
print("g range", min(ga), max(ga), min(gb), max(gb))
print("ai", a[0]["ai"], "|", b[0]["ai"], "seed", a[0]["seed"], b[0]["seed"], "explore", a[0].get("explore"), b[0].get("explore"))
same_seed = sum(1 for g in ga if g in gb and ga[g]["seed"] == gb[g]["seed"])
same_act = sum(1 for g in ga if g in gb and ga[g]["actions"] == gb[g]["actions"])
same_search = sum(1 for g in ga if g in gb and ga[g].get("search") == gb[g].get("search"))
print("same seed", same_seed, "same actions", same_act, "same search", same_search)
