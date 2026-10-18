"""Read D10 and the c* recompute (registered in 379f4bf). Condition: the opponent's deck list is known (order and hand
not).

    python3 d10_read.py d10-71600018.json d10-75400038.json --out d10.json
"""
import argparse, json, math

import numpy as np

CONF = ("A-PUCT", "B-PUCT", "A-UCB", "B-UCB")


def _argmax_set(x):
    x = np.asarray(x, float)
    return set(np.flatnonzero(x == x.max()).tolist())


def _top1(v, p):
    A, B = _argmax_set(v), _argmax_set(p)
    return len(A & B) / len(B)


def _is_end(v, end):
    A = _argmax_set(v)
    return (1.0 / len(A)) if end in A else 0.0


def _bu_bp(v, p):
    n = np.asarray(v, float)
    N = n.sum()
    w = n / N
    p = np.asarray(p, float)
    return float((w * 0.5 * np.sqrt(math.log(N) / np.maximum(n, 1))).sum()), float((w * p * math.sqrt(N) / (1 + n)).sum())


def _boot(groups, fn, reps=2000, seed=76400000):
    """95% percentile interval of fn over a bootstrap of games (groups: list of per-game lists)."""
    rng = np.random.default_rng(seed)
    k = len(groups)
    vals = []
    for _ in range(reps):
        pick = rng.integers(0, k, k)
        vals.append(fn([x for g in pick for x in groups[g]]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def _by_game(items):
    d = {}
    for g, x in items:
        d.setdefault(g, []).append(x)
    return list(d.values())


def _stratum(p):
    ne = p["keys"] - (1 if p["end"] is not None else 0)
    return "4+" if ne >= 4 else str(ne)


def read(path):
    d = json.load(open(path))
    pts = d["points"]
    res = {"records": d["records"], "points": len(pts)}
    vis = {c: (lambda p, c=c: p[c].get("visits") if not p[c]["outer"] else None) for c in CONF}
    vis["rec"] = lambda p: p["rec_visits"]
    # --- D10: top-1 agreement with ft-t05 ---
    top = {}
    for c, f in vis.items():
        items = [(p["g"], _top1(f(p), p["prior"])) for p in pts if f(p) is not None]
        m = float(np.mean([x for _, x in items]))
        top[c] = {"n": len(items), "outer": len(pts) - len(items), "top1": m, "overturn": 1 - m,
                  "top1_ci": _boot(_by_game(items), np.mean)}
    both = [(p["g"], _top1(vis["A-PUCT"](p), p["prior"]) - _top1(vis["B-PUCT"](p), p["prior"])) for p in pts
            if vis["A-PUCT"](p) is not None and vis["B-PUCT"](p) is not None]
    top["A-B_PUCT"] = {"n": len(both), "diff": float(np.mean([x for _, x in both])), "ci": _boot(_by_game(both), np.mean)}
    bu = [(p["g"], _top1(vis["A-UCB"](p), p["prior"]) - _top1(vis["B-UCB"](p), p["prior"])) for p in pts
          if vis["A-UCB"](p) is not None and vis["B-UCB"](p) is not None]
    top["A-B_UCB"] = {"n": len(bu), "diff": float(np.mean([x for _, x in bu])), "ci": _boot(_by_game(bu), np.mean)}
    same = [p for p in pts if vis["B-PUCT"](p) is not None]
    top["B-PUCT_equals_rec"] = sum(1 for p in same if vis["B-PUCT"](p) == p["rec_visits"]) / len(same)
    top["B-PUCT_rec_same_top"] = float(np.mean([_top1(vis["B-PUCT"](p), p["rec_visits"]) for p in same]))
    top["A-PUCT_vs_B-PUCT_same_top"] = float(np.mean([_top1(vis["A-PUCT"](p), vis["B-PUCT"](p)) for p in pts
                                                      if vis["A-PUCT"](p) is not None and vis["B-PUCT"](p) is not None]))
    res["d10"] = top
    # --- end-turn timing, by D9's strata ---
    et = {}
    withend = [p for p in pts if p["end"] is not None]
    for st in ("1", "2", "3", "4+", "all"):
        sel = [p for p in withend if st == "all" or _stratum(p) == st]
        row = {"n": len(sel), "prior_top_end": float(np.mean([_is_end(p["prior"], p["end"]) for p in sel])) if sel else None,
               "rec_top_end": float(np.mean([_is_end(p["rec_visits"], p["end"]) for p in sel])) if sel else None}
        for c in CONF:
            row[c] = {"chose_end": float(np.mean([p[c]["chose_end"] for p in sel])),
                      "top_end": float(np.mean([_is_end(vis[c](p), p["end"]) for p in sel if vis[c](p) is not None]))}
        for a, b in (("A-PUCT", "B-PUCT"), ("A-UCB", "B-UCB")):
            items = [(p["g"], float(p[a]["chose_end"]) - float(p[b]["chose_end"])) for p in sel]
            row[f"{a}-{b}_chose_end"] = [float(np.mean([x for _, x in items]))] + _boot(_by_game(items), np.mean)
        et[st] = row
    res["end_turn"] = et
    # --- c* by c01d2c5's rule ---
    cs = {}
    for c, f in vis.items():
        items = [(p["g"], _bu_bp(f(p), p["prior"])) for p in pts if f(p) is not None and sum(f(p)) > 1]
        U = np.array([x[0] for _, x in items]); Pp = np.array([x[1] for _, x in items])
        cstar = float(U.mean() / Pp.mean())
        dist = {g: abs(math.log2(cstar) - math.log2(g)) for g in (0.5, 1.0, 2.0)}
        best = min(dist.values())
        pick = [g for g in (0.5, 1.0, 2.0) if abs(dist[g] - best) < 1e-12]
        ci = _boot(_by_game(items), lambda xs: np.mean([x[0] for x in xs]) / np.mean([x[1] for x in xs]))
        cs[c] = {"n": len(items), "mean_B_U": float(U.mean()), "mean_B_P": float(Pp.mean()), "c_star": cstar,
                 "c_star_ci": ci, "c_puct": 1.0 if len(pick) > 1 else pick[0],
                 "mean_N": float(np.mean([sum(f(p)) for p in pts if f(p) is not None]))}
    res["c_star"] = cs
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = {}
    for f in args.files:
        r = read(f)
        out[r["records"]] = r
    json.dump(out, open(args.out, "w"), indent=1)
    for k, r in out.items():
        print("==", k, r["points"])
        for c, v in r["d10"].items():
            print("  d10", c, v)
        for st, v in r["end_turn"].items():
            print("  end", st, json.dumps(v))
        for c, v in r["c_star"].items():
            print("  c*", c, v)


if __name__ == "__main__":
    main()
