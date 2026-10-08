"""Per-point overlap for alpha 1 vs alpha 0.1 at tau 0 (svsim.tools.infer_check's own functions), then a
game-clustered bootstrap of the difference. Run from a svsim checkout at c3204a8 with PYTHONPATH=.
    python3 check_ci.py OUT.json FILE.jsonl ... [--games 40] [--samples 150] [--side N]
"""
import json, random, sys
from multiprocessing import Pool
from svsim.tools.infer_check import _load, _points, overlap

def main():
    args = sys.argv[1:]
    out = args.pop(0)
    def opt(k, d):
        if k in args:
            i = args.index(k); v = args[i + 1]; del args[i:i + 2]; return v
        return d
    games, samples = int(opt("--games", "40")), int(opt("--samples", "150"))
    side = opt("--side", None); side = int(side) if side is not None else None
    records = []
    for path in args:
        records += [(path, r) for r in _load(path)[:games]]
    with Pool(4) as pool:
        parts = pool.map(_points, [(r, [0.0], side, 2) for _, r in records])
    rows = []
    rng = random.Random(1)
    for g, part in enumerate(parts):
        for t, pl, f in part:
            hand = {u for u, _ in pl[:len(t)]}
            rows.append({"g": g, "n": len(t), "pool": len(pl), "flag": len(f[0.0]),
                         "flag_in": sum(1 for u in f[0.0] if u in hand),
                         "o1": overlap(t, pl, f[0.0], 1.0, samples, rng),
                         "o01": overlap(t, pl, f[0.0], 0.1, samples, rng)})
    json.dump(rows, open(out, "w"))
    n = len(rows); o1 = sum(r["o1"] for r in rows) / n; o01 = sum(r["o01"] for r in rows) / n
    fl = sum(r["flag"] for r in rows); fi = sum(r["flag_in"] for r in rows)
    base = sum(r["n"] / r["pool"] for r in rows) / n
    print(f"{n} points, {len(records)} games; base {base:.3f}; flagged per point {fl / n:.2f}, in hand {fi / max(1, fl):.3f}")
    print(f"overlap alpha 1 {o1:.4f}, alpha 0.1 {o01:.4f}, diff {o01 - o1:+.4f} ({(o01 - o1) / o1:+.1%})")
    by = {}
    for r in rows: by.setdefault(r["g"], []).append(r)
    keys = list(by); brng = random.Random(7); bs = []
    for _ in range(4000):
        s = [r for _ in keys for r in by[keys[brng.randrange(len(keys))]]]
        a = sum(r["o1"] for r in s) / len(s); b = sum(r["o01"] for r in s) / len(s)
        bs.append(b - a)
    bs.sort()
    print(f"diff 95% (games resampled, MC noise included): {bs[100]:+.4f} .. {bs[3899]:+.4f}")
    trig = [r for r in rows if r["flag"] > 0]
    if trig:
        a = sum(r["o1"] for r in trig) / len(trig); b = sum(r["o01"] for r in trig) / len(trig)
        print(f"points with >= 1 flagged card: {len(trig)} ({len(trig) / n:.1%}); overlap {a:.4f} -> {b:.4f} ({b - a:+.4f})")

if __name__ == "__main__":
    main()
