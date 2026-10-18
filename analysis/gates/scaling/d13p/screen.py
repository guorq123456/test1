"""D13' step 1 (registered in f385567; a screen, not a gate): holdout Brier of the omniscient net (opponent's real hand
read as a zone) against its control (same start, data and epochs, no zone), from the builder's per-position dumps.
Per holdout and kind: Brier and ece of each; the paired drop control - omniscient on the same positions, the two
holdouts of a kind pooled, with a 95% bootstrap of games (2000, rng 0). Passes if either kind's pooled drop >= 0.005.
Also checks the omniscient start (zone weights 0) against net-mid-ramp-t's committed dump, bit for bit.
Condition: the omniscient net reads the opponent's real hand (measurement only); otherwise the opponent's deck list is
known (order and hand not).

    python3 screen.py --oph DUMP_DIR --ctl DUMP_DIR [--start DUMP_DIR --base DUMP_DIR] --out screen.json
"""
import argparse, glob, json, os
import numpy as np


def ece(p, y):
    b = np.minimum((p * 10).astype(int), 9)
    return float(sum((b == k).sum() / len(p) * abs(p[b == k].mean() - y[b == k].mean()) for k in range(10) if (b == k).any()))


def load(d, name):
    z = np.load(os.path.join(d, name))
    key = "i" if "i" in z.files else "turn"
    return {"seed": z["seed"], "g": z["g"], "k": z[key], "y": z["y"].astype(float), "p": z["p_new"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oph", required=True)
    ap.add_argument("--ctl", required=True)
    ap.add_argument("--start")
    ap.add_argument("--base")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = {"files": {}, "pooled": {}}
    pool = {"end": [], "mid": []}
    for f in sorted(os.path.basename(x) for x in glob.glob(os.path.join(args.oph, "*.npz"))):
        kind = "mid" if f.endswith("-mid.npz") else "end"
        a, b = load(args.oph, f), load(args.ctl, f)
        for k in ("seed", "g", "k", "y"):
            assert np.array_equal(a[k], b[k]), (f, k)
        y = a["y"]
        rec = {"n": int(len(y)), "brier_oph": float(((a["p"] - y) ** 2).mean()), "brier_ctl": float(((b["p"] - y) ** 2).mean()),
               "ece_oph": ece(a["p"], y), "ece_ctl": ece(b["p"], y)}
        rec["drop"] = rec["brier_ctl"] - rec["brier_oph"]
        if args.start and args.base:
            s, base = load(args.start, f), load(args.base, f) if os.path.exists(os.path.join(args.base, f)) else None
            if base is not None:
                rec["start_vs_base_identical"] = bool(np.array_equal(s["p"], base["p"]) and np.array_equal(s["g"], base["g"]))
                rec["start_vs_base_maxdiff"] = float(np.abs(s["p"] - base["p"]).max())
        out["files"][f] = rec
        if f.startswith("v2skx") and kind == "end":
            pass
        pool[kind].append((f, a["seed"], a["g"], (b["p"] - y) ** 2 - (a["p"] - y) ** 2, (a["p"] - y) ** 2, (b["p"] - y) ** 2))
        print(f, json.dumps(rec))
    rng = np.random.default_rng(0)
    for kind in ("end", "mid"):
        # the holdouts of D13' (registered): turn ends 70200000 series + 71600018 + 75400038, mid-turn 71600018 + 75400038
        parts = pool[kind]
        gid = np.concatenate([np.char.add(np.char.add(p[0], "/"), (p[1].astype(np.int64) * 100000 + p[2]).astype(str)) for p in parts])
        d = np.concatenate([p[3] for p in parts]); bo = np.concatenate([p[4] for p in parts]); bc = np.concatenate([p[5] for p in parts])
        games, inv = np.unique(gid, return_inverse=True)
        sd = np.bincount(inv, weights=d, minlength=len(games)); cnt = np.bincount(inv, minlength=len(games))
        idx = rng.integers(0, len(games), (2000, len(games)))
        boots = sd[idx].sum(1) / cnt[idx].sum(1)
        out["pooled"][kind] = {"n": int(len(d)), "games": int(len(games)), "brier_oph": float(bo.mean()), "brier_ctl": float(bc.mean()),
                               "drop": [float(d.mean())] + [float(x) for x in np.percentile(boots, [2.5, 97.5])],
                               "passes": bool(d.mean() >= 0.005)}
        print("pooled", kind, json.dumps(out["pooled"][kind]))
    out["screen_passes"] = any(out["pooled"][k]["passes"] for k in ("end", "mid"))
    print("screen passes:", out["screen_passes"])
    json.dump(out, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
