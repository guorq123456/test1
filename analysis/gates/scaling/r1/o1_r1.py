"""R1 offline report (registered in 96c5b24; report only): on D10's 2000 + 2000 ramp-t holdout points, ft-t05 against
a new prior, O1's measures with pi = A-UCB's visits (D10, seeds 76400000 + j / 76402000 + j) and, beside it, the
recorded visits. Top-1 = |argmax pi & argmax q| / |argmax q| (key-merged); KL(pi || q) and KL(pi^2 normalised || q),
natural log, q floored at 1e-12; all points and D9's 4+ stratum; 95% intervals by a bootstrap of games (2000, rng 0).
Condition: the opponent's deck list is known (order and hand not).

    cd <checkout with both priors> && PYTHONPATH=. python3 o1_r1.py NEW_PRIOR.npz --out o1-r1.json
"""
import argparse, gzip, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "d8"))
D10 = os.path.join(HERE, "..", "d10")
REC = {"rec-71600018.jsonl.gz": "analysis/scaling/data/gen4/rec/rec-71600018.jsonl.gz",
       "rec-75400038.jsonl.gz": "analysis/scaling/data/ramp-t4/rec/rec-75400038.jsonl.gz"}
ROOT = "/home/user/test1"


def _top1(v, q):
    v, q = np.asarray(v, float), np.asarray(q, float)
    A, B = set(np.flatnonzero(v == v.max())), set(np.flatnonzero(q == q.max()))
    return len(A & B) / len(B)


def _kl(pi, q):
    pi, q = np.asarray(pi, float), np.maximum(np.asarray(q, float), 1e-12)
    m = pi > 0
    return float((pi[m] * np.log(pi[m] / q[m])).sum())


def _pi(v, tau=1.0):
    v = np.asarray(v, float) ** (1.0 / tau)
    return v / v.sum()


def main():
    import d8
    from svsim.learn.setpolicy import SetPolicy
    ap = argparse.ArgumentParser()
    ap.add_argument("new")
    ap.add_argument("--old", default="analysis/scaling/models/prior-ramp-ft-t05.npz")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    pols = {"ft-t05": SetPolicy.load(args.old), "new": SetPolicy.load(args.new)}
    out = {"new": args.new}
    for name in ("d10-71600018.json.gz", "d10-75400038.json.gz"):
        d = json.load(gzip.open(os.path.join(D10, name), "rt"))
        recs = {r["g"]: r for r in d8._load(os.path.join(ROOT, REC[d["records"]]))}
        want = {}
        for p in d["points"]:
            want.setdefault(p["g"], {})[p["i"]] = p
        rows, maxdiff = [], 0.0
        for g in sorted(want):
            for i, state, legal, keys, key_of, kv, start, end, bad, n_legal in d8._decisions(recs[g]):
                if i not in want[g]:
                    continue
                p = want[g][i]
                q = {}
                for k, pol in pols.items():
                    pr = np.asarray(pol.priors(state, legal), float)
                    qq = np.zeros(len(keys)); np.add.at(qq, key_of, pr); q[k] = qq
                maxdiff = max(maxdiff, float(np.abs(q["ft-t05"] - np.asarray(p["prior"])).max()))
                if p["A-UCB"]["outer"]:
                    continue
                ne = len(keys) - (1 if end is not None else 0)
                row = {"g": g, "wide": ne >= 4}
                for tgt, v in (("aucb", p["A-UCB"]["visits"]), ("rec", p["rec_visits"])):
                    for k in q:
                        row[f"{tgt}.{k}.top1"] = _top1(v, q[k])
                        row[f"{tgt}.{k}.kl"] = _kl(_pi(v), q[k])
                        row[f"{tgt}.{k}.kl5"] = _kl(_pi(v, 0.5), q[k])
                rows.append(row)
        games = sorted({r["g"] for r in rows})
        rng = np.random.default_rng(0)
        res = {"points": len(rows), "ft-t05_vs_D10_prior_maxdiff": maxdiff}
        for sel_name, sel in (("all", rows), ("wide", [r for r in rows if r["wide"]])):
            byg = {}
            for r in sel:
                byg.setdefault(r["g"], []).append(r)
            gl = [byg[g] for g in games if g in byg]
            cols = [c for c in sel[0] if "." in c]
            est = {c: float(np.mean([r[c] for r in sel])) for c in cols}
            boots = {c: [] for c in cols}
            dif = {f"{t}.{m}": [] for t in ("aucb", "rec") for m in ("top1", "kl", "kl5")}
            for _ in range(2000):
                pick = [x for k in rng.integers(0, len(gl), len(gl)) for x in gl[k]]
                for c in cols:
                    boots[c].append(np.mean([r[c] for r in pick]))
                for t in ("aucb", "rec"):
                    for m in ("top1", "kl", "kl5"):
                        dif[f"{t}.{m}"].append(np.mean([r[f"{t}.new.{m}"] - r[f"{t}.ft-t05.{m}"] for r in pick]))
            res[sel_name] = {"n": len(sel),
                             **{c: [est[c]] + list(np.percentile(boots[c], [2.5, 97.5])) for c in cols},
                             **{f"diff.{k}": [float(np.mean(v))] + list(np.percentile(v, [2.5, 97.5])) for k, v in dif.items()}}
        out[d["records"]] = res
        print(d["records"], json.dumps({k: (v if not isinstance(v, dict) else {kk: [round(x, 4) for x in vv] if isinstance(vv, list) else vv for kk, vv in v.items()}) for k, v in res.items()}))
    json.dump(out, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
