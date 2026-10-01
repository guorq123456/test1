import pickle, numpy as np, math
parts = [pickle.load(open(f"out/m13_{k}.pkl", "rb")) for k in range(3)]
total = sum(p["total"] for p in parts); print("total", total, total == math.factorial(13))
hist = sum(p["hist"] for p in parts)
L = max(p["seenlen"] for p in parts)
seen = np.zeros(L, dtype=bool)
for p in parts:
    s = np.unpackbits(p["seen"])[:p["seenlen"]].astype(bool); seen[:len(s)] |= s
best = max(p["best"] for p in parts)
bestw = sorted(set(w for p in parts if p["best"] == best for w in p["bestw"]))
print("max", best, "argmax", bestw)
top = sorted(set(t for p in parts for t in p["top"]), reverse=True)[:12]
for v, w in top: print("  top", v, w)
print("count1", hist[1], "count2", hist[2], "expected", math.comb(24, 12), 4707964 - math.comb(24, 12))
att = np.flatnonzero(seen)
print("distinct attained values", len(att), "min", att.min(), "max", att.max())
print("4:", seen[4], "12:", seen[12], "112:", seen[112])
allowed_missing = [r for r in range(1, 200000) if not seen[r] and r % 4 != 3 and r not in (4, 12)]
print("unattained allowed values < 2e5:", allowed_missing[:30], len(allowed_missing))
m3 = att[att % 4 == 3]
print("#attained 3 mod 4:", len(m3), "smallest:", m3[:20].tolist())
un3 = [r for r in range(3, 2000, 4) if not seen[r]]
print("unattained 3mod4 < 2000:", len(un3))
sw = {}
for p in parts:
    for v, w in p["smallwit"].items():
        sw.setdefault(v, w)
pickle.dump(dict(hist=hist, seen=np.packbits(seen), seenlen=L, best=best, bestw=bestw, top=top, smallwit=sw), open("out/n13_merged.pkl", "wb"))
# compare with n=12 attained set
d12 = pickle.load(open("out/n12.pkl", "rb"))["hist"]
s12 = set(d12)
print("values attained at 12 but not 13:", [v for v in sorted(s12) if v >= L or not seen[v]][:10])
new3 = [r for r in range(3, 2000, 4) if seen[r] and r not in s12]
print("3mod4 values <2000 newly attained at n=13:", new3)
