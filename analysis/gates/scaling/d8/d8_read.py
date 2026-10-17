"""D8 read and O1's prior-free baselines (registered in 95dc772). Condition: the opponent's deck list is known
(order and hand not).

    python3 d8_read.py --scan scan-ramp.json --rerun rerun-ramp.json --records REC --out d8-ramp.json
"""
import argparse, gzip, json, math

import numpy as np


def argmax_set(v):
    m = max(v)
    return {k for k, x in enumerate(v) if x == m}


def entropy(p):
    nz = p[p > 0]
    return float(-(nz * np.log(nz)).sum())


def boot(groups, values, reps=2000):
    """Game-clustered bootstrap of the mean of each column of values (list of per-decision tuples)."""
    rng = np.random.default_rng(0)
    games = sorted(set(groups))
    gi = {g: n for n, g in enumerate(games)}
    vals = np.asarray(values, float)
    if vals.ndim == 1:
        vals = vals[:, None]
    sums = np.zeros((len(games), vals.shape[1]))
    cnt = np.zeros(len(games))
    for g, row in zip(groups, vals):
        sums[gi[g]] += row
        cnt[gi[g]] += 1
    est = sums.sum(0) / cnt.sum()
    out = []
    for _ in range(reps):
        pick = rng.integers(0, len(games), len(games))
        out.append(sums[pick].sum(0) / cnt[pick].sum())
    out = np.asarray(out)
    return est, np.percentile(out, 2.5, axis=0), np.percentile(out, 97.5, axis=0)


def fmt(est, lo, hi, k=0, pct=True):
    f = (lambda x: f"{100 * x:.1f}%") if pct else (lambda x: f"{x:.4f}")
    return f"{f(est[k])} ({f(lo[k])}–{f(hi[k])})"


def baselines(rows):
    out = {}
    for name, keep in (("all", lambda r: True), ("start", lambda r: r["start"]), ("mid", lambda r: not r["start"])):
        sel = [r for r in rows if keep(r)]
        groups, vals = [], []
        for r in sel:
            v = r["visits"]
            n = len(v)
            p = np.asarray(v, float) / sum(v)
            A = argmax_set(v)
            e0 = r["exp"][0]
            e1 = r["exp"][1] if len(r["exp"]) > 1 else -1
            cov_exp = p[e0] + (p[e1] if e1 >= 0 else 0.0)
            vals.append((len(A) / n, 1.0 if e0 in A else 0.0, 2.0 / n if n > 2 else 1.0, cov_exp,
                         math.log(n) - entropy(p), float(p.max()), 1.0 if (r["end"] is not None and r["end"] in A) else 0.0))
            groups.append(r["g"])
        est, lo, hi = boot(groups, vals)
        out[name] = {"decisions": len(sel), "games": len(set(groups)),
                     "uniform_top1": [est[0], lo[0], hi[0]], "expansion_top1": [est[1], lo[1], hi[1]],
                     "uniform_top2_cover": [est[2], lo[2], hi[2]], "expansion_top2_cover": [est[3], lo[3], hi[3]],
                     "kl_uniform": [est[4], lo[4], hi[4]], "top_share": [est[5], lo[5], hi[5]],
                     "top_is_end": [est[6], lo[6], hi[6]],
                     "mean_keys": float(np.mean([len(r["visits"]) for r in sel])),
                     "mean_legal": float(np.mean([r["n_legal"] for r in sel]))}
    return out


def raw_stats(path):
    """The builder's background numbers, from the records alone: decisions with >= 2 legal moves and visits, raw
    (unmerged) π."""
    n, legal, top, over80 = 0, 0, 0.0, 0
    for line in gzip.open(path, "rt"):
        if not line.strip():
            continue
        r = json.loads(line)
        for s in r.get("search") or []:
            if not s or len(s["visits"]) < 2 or sum(s["visits"]) <= 0:
                continue
            v = s["visits"]
            share = max(v) / sum(v)
            n += 1
            legal += len(v)
            top += share
            over80 += share > 0.8
    return {"decisions": n, "mean_legal": legal / n, "top_share": top / n, "share_over_80": over80 / n}


def rerun_read(rows, rerun):
    by = {(r["g"], r["i"]): r for r in rows}
    out = {"points": len(rerun["points"]), "outer": sum(1 for p in rerun["points"] if p["outer"]),
           "unmatched_children": sum(p.get("unmatched_children", 0) for p in rerun["points"])}
    for name, keep in (("all", lambda r: True), ("start", lambda r: r["start"]), ("mid", lambda r: not r["start"])):
        groups, vals = [], []
        for p in rerun["points"]:
            if p["outer"]:
                continue
            r = by[(p["g"], p["i"])]
            if not keep(r):
                continue
            v, w = r["visits"], p["rerun"]
            A, B = argmax_set(v), argmax_set(w)
            pv = np.asarray(v, float) / sum(v)
            pw = np.maximum(np.asarray(w, float) / max(sum(w), 1), 1e-12)
            kl = float((pv[pv > 0] * (np.log(pv[pv > 0]) - np.log(pw[pv > 0]))).sum())
            e = r["end"]
            end_same = 1.0 if e is None or ((e in A) == (e in B)) else 0.0
            vals.append((len(A & B) / len(B), kl, end_same, 1.0 if min(w) == 0 else 0.0, float(sum(w)), 1.0 if list(v) == list(w) else 0.0))
            groups.append(r["g"])
        est, lo, hi = boot(groups, vals)
        out[name] = {"points": len(vals), "top1": [est[0], lo[0], hi[0]], "kl": [est[1], lo[1], hi[1]],
                     "end_same": [est[2], lo[2], hi[2]], "share_with_zero_visit_key": est[3],
                     "mean_rerun_visits": est[4], "identical": [est[5], lo[5], hi[5]], "kl_median": float(np.median([x[1] for x in vals]))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", required=True)
    ap.add_argument("--rerun")
    ap.add_argument("--records", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    scan = json.load(open(args.scan))
    rows = scan["rows"]
    res = {"records": scan["records"], "games": scan["games"], "decisions": len(rows),
           "dup_mismatch": sum(r["dup_mismatch"] for r in rows),
           "merged_share": float(np.mean([r["n_legal"] > len(r["visits"]) for r in rows])),
           "exp_not_found": sum(1 for r in rows if r["exp"][0] < 0),
           "baselines": baselines(rows), "raw": raw_stats(args.records)}
    if args.rerun:
        res["d8"] = rerun_read(rows, json.load(open(args.rerun)))
    json.dump(res, open(args.out, "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
