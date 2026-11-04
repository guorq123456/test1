"""The static rows of every card in the tok-, mid- and dec- files of shards k < K (S1's cards-all.npz, for K shards)."""
import sys
import numpy as np
K, out = int(sys.argv[1]), sys.argv[2]
rows, names = {}, None
c = np.load("runs/s1/tok/cards.npz")
names = c["static_names"]
rows.update({int(i): r for i, r in zip(c["card_id"], c["static"])})
for k in range(K):
    s = 85830000 + 2 * k
    for f in (f"runs/s1/tok/tok-{s}.npz", f"runs/s1/mid/mid-{s}.npz", f"runs/s1/dec/dec-{s}.npz"):
        z = np.load(f)
        if "card_id" in z.files:
            for i, r in zip(z["card_id"], z["static"]):
                if int(i) in rows and not np.array_equal(rows[int(i)], r):
                    raise SystemExit(f"card {i}: two static rows")
                rows.setdefault(int(i), r)
ids = sorted(rows)
np.savez(out, card_id=np.asarray(ids, np.int64), static=np.stack([rows[i] for i in ids]), static_names=names)
print(len(ids), "cards ->", out)
