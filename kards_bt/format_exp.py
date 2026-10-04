"""Do Bo3 / Bo3+ban / Bo5 / Bo5+ban results differ in how decisive they are?

kappa = k[format] multiplies the rating gap; Bo3 without ban is the reference (k = 1).
Bans exist from the top cut on (OCC / expansion / seasonal Top 8, OCC Ultimate, Open top cuts)
and in the World Championship main stage; Bo5 is inferred from a winner with 3 games.
Chosen on DEV (blocks before 2023), confirmed once on HOLDOUT with an event bootstrap.
"""
import itertools
import re
from collections import Counter
from multiprocessing import Pool

import experiments as ex

STAGE = {}
for r in ex.ALL:
    STAGE.setdefault(r["event"], set())


def ban(r):
    return r["tier"] == 1 or (r["block"][1] == "top8") or bool(r.get("topcut"))


# mark top cuts that experiments.ROWS doesn't flag (expansion / seasonal Top 8, Open top cuts, Ultimate)
_rows = [r for r in ex.ALL if r["valid"] == "1" and r["category"] in ("open", "open_special", "official")]
for row, r in zip(_rows, ex.ROWS):
    st = (row["stage"] or "") + " " + (row["stage_type"] or "")
    r["topcut"] = bool(re.search(r"top|cut|final|elim", st, re.I)) and not re.search(r"swiss|group|round robin", st, re.I) \
        and not re.search(r"world championship", row["event"], re.I) or bool(re.search(r"ultimate", row["event"], re.I))
    r["fmt"] = ("Bo5" if r["bo5"] else "Bo3") + (" ban" if ban(r) else "")
FMT = {id(r): r["fmt"] for r in ex.ROWS}


def run(cfg):
    k_b3ban, k_b5, k_b5ban = cfg
    k = {"Bo3": 1.0, "Bo3 ban": k_b3ban, "Bo5": k_b5, "Bo5 ban": k_b5ban}
    out, prev = {}, None
    kappa = lambda r: k[r["fmt"]]  # noqa: E731
    for blk in ex.SCORED:
        t0 = ex.BLOCK_START[blk]
        b = ex.fit(t0, kappa, x0=prev)
        prev = b
        for i, r in enumerate(x for x in ex.ROWS if x["block"] == blk):
            out[(blk, i)] = float(ex.expit(kappa(r) * (b.get(r["w"], 0.0) - b.get(r["l"], 0.0))))
    return cfg, out


def main():
    print("series by format:", Counter(r["fmt"] for r in ex.ROWS))
    dev = ex.keyset(lambda b, r: ex.BLOCK_START[b] < ex.SPLIT)
    hold = ex.keyset(lambda b, r: ex.BLOCK_START[b] >= ex.SPLIT)
    grid = list(itertools.product([0.8, 1.0, 1.25], repeat=3))
    with Pool() as pool:
        res = dict(pool.map(run, grid))
    null = (1.0, 1.0, 1.0)
    for c in sorted(grid, key=lambda c: ex.logloss(res[c], dev))[:8]:
        print(f"  Bo3ban={c[0]:.2f} Bo5={c[1]:.2f} Bo5ban={c[2]:.2f}: dev {ex.logloss(res[c], dev):.4f} holdout {ex.logloss(res[c], hold):.4f}")
    print(f"  null (all 1.0): dev {ex.logloss(res[null], dev):.4f} holdout {ex.logloss(res[null], hold):.4f}")
    best = min(grid, key=lambda c: ex.logloss(res[c], dev))
    if ex.logloss(res[null], dev) - ex.logloss(res[best], dev) < 0.0005:
        best = null
    print("chosen on DEV:", best)
    for name, keys in (("HOLDOUT", hold),):
        pt, lo, hi = ex.boot(res[null], res[best], keys)
        print(f"  {name} gain (null - chosen) = {pt:+.4f} [{lo:+.4f}, {hi:+.4f}]")
    for fmt in ("Bo3", "Bo3 ban", "Bo5", "Bo5 ban"):
        ks = [kk for kk in dev + hold if next(x for j, x in enumerate(y for y in ex.ROWS if y["block"] == kk[0]) if j == kk[1])["fmt"] == fmt]
        print(f"  {fmt:8s} n={len(ks):5d}  null logloss {ex.logloss(res[null], ks):.4f}")


if __name__ == "__main__":
    main()
