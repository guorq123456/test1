"""O1 (registered 95dc772 + 42cec2a): the analysis line's own run of the move priors on every holdout decision, and
the pass criteria. Condition: the opponent's deck list is known (order and hand not).

    cd <builder checkout> && PYTHONPATH=. python3 o1.py run REC --scan scan.json --prior NAME=PATH ... [--old PATH] \
        --out probs.npz --workers 4
    python3 o1.py read --scan scan.json --probs probs.npz --taus NAME=TAU ... [--dump DUMP] --deck ramp|elft --out o1.json

run: per decision of the D8 scan (same population as learn.setpolicy.decisions), each prior's probability per legal
move (SetPolicy.priors / PolicyNet.priors, the search's path), added per action key. Saved as one flat array per
method plus offsets.
"""
import argparse, gzip, json, math, os, sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_P = {}


def _init(priors, old):
    from svsim.learn.setpolicy import SetPolicy
    from svsim.learn.policy import PolicyNet
    from pathlib import Path
    for name, path in priors:
        _P[name] = SetPolicy.load(path)
    if old:
        _P["old"] = PolicyNet.load(Path(old))


def _run_games(job):
    import d8
    from svsim.search.mcts import _locator, action_key
    from svsim.learn.netdata import _search
    from svsim.tools.arena import make_agent
    path, gs = job
    recs = {r["g"]: r for r in d8._load(path) if r["g"] in gs}
    out, searches = [], {}
    for g in sorted(recs):
        spec = d8._spec(recs[g])
        if spec not in searches:
            searches[spec] = _search(make_agent(spec, 0))
        for i, state, legal, keys, key_of, kv, start, end, bad, n_legal in d8._decisions(recs[g]):
            firsts = [key_of.index(k) for k in range(len(keys))]
            pos = {k: n for n, k in enumerate(keys)}
            order = [pos[k] for k in searches[spec]._options(state, state.active, None) if k in pos]
            order += [k for k in range(len(keys)) if k not in order]
            row = {"g": g, "i": i, "raw": {}, "start": bool(start), "visits_raw": list(recs[g]["search"][i]["visits"]),
                   "order_legal": [firsts[k] for k in order]}
            for name, pol in _P.items():
                pr = np.asarray(pol.priors(state, legal), float)
                q = np.zeros(len(keys))
                np.add.at(q, key_of, pr)
                row[name] = q
                row["raw"][name] = pr
            out.append(row)
    return out


def run_main(args):
    import d8
    priors = [p.split("=", 1) for p in args.prior]
    recs = d8._load(args.records)
    games = sorted(r["g"] for r in recs)
    chunks = [(args.records, set(games[k::args.workers * 4])) for k in range(args.workers * 4)]
    rows = []
    with Pool(args.workers, initializer=_init, initargs=(priors, args.old)) as pool:
        for part in pool.imap_unordered(_run_games, chunks):
            rows.extend(part)
    rows.sort(key=lambda r: (r["g"], r["i"]))
    scan = json.load(open(args.scan))["rows"]
    assert [(r["g"], r["i"]) for r in rows] == [(r["g"], r["i"]) for r in scan], "decisions differ from the scan"
    names = [n for n, _ in priors] + (["old"] if args.old else [])
    arrays = {"g": np.array([r["g"] for r in rows]), "i": np.array([r["i"] for r in rows]),
              "koff": np.cumsum([0] + [len(r[names[0]]) for r in rows]),
              "loff": np.cumsum([0] + [len(r["raw"][names[0]]) for r in rows])}
    for n in names:
        arrays[n] = np.concatenate([r[n] for r in rows])
        arrays["raw_" + n] = np.concatenate([r["raw"][n] for r in rows])
    np.savez(args.out, names=np.array(names), **arrays)
    json.dump([{"g": r["g"], "i": r["i"], "start": r["start"], "visits": r["visits_raw"], "order": r["order_legal"]}
               for r in rows], gzip.open(args.out.replace(".npz", "-meta.json.gz"), "wt"))
    print(len(rows), "decisions,", names)


# --- read ---------------------------------------------------------------------------------------------------------

def _argmax_set(x):
    m = x.max()
    return set(np.flatnonzero(x == m).tolist())


def _kl(t, q):
    q = np.maximum(q, 1e-12)
    nz = t > 0
    return float((t[nz] * (np.log(t[nz]) - np.log(q[nz]))).sum())


def _sharp(v, tau):
    x = np.asarray(v, float) ** (1.0 / tau)
    return x / x.sum()


def _per_decision(rows, P, names, taus):
    """Per decision: a dict of per-method figures."""
    out = []
    for n, r in enumerate(rows):
        v = np.asarray(r["visits"], float)
        k = len(v)
        pi, pi5 = v / v.sum(), _sharp(v, 0.5)
        A = _argmax_set(v)
        u = np.full(k, 1.0 / k)
        d = {"g": r["g"], "start": r["start"], "end_top": (r["end"] is not None and r["end"] in A),
             "uni_top1": len(A) / k, "exp_top1": 1.0 if r["exp"][0] in A else 0.0,
             "kl_u": _kl(pi, u), "kl5_u": _kl(pi5, u)}
        for m in names:
            q = P[m][n]
            B = _argmax_set(q)
            o = np.argsort(-q, kind="stable")
            d[m] = {"top1": len(A & B) / len(B), "kl": _kl(pi, q), "kl5": _kl(pi5, q),
                    "ce": -float((pi * np.log(np.maximum(q, 1e-12))).sum()), "top2": float(pi[o[:2]].sum()),
                    "p_end": float(q[r["end"]]) if r["end"] is not None else None,
                    "top_end": (r["end"] is not None and r["end"] in B)}
            if m == "old":
                q2 = q ** 2 / (q ** 2).sum()
                d["old2_kl5"] = _kl(pi5, q2)
        out.append(d)
    return out


def _boot(groups, cols, reps=2000):
    """cols: dict name -> per-decision array. Returns, per name, (mean, lo, hi) and per-replicate means."""
    rng = np.random.default_rng(0)
    games = sorted(set(groups))
    gi = np.array([games.index(g) for g in groups]) if len(games) < 50 else None
    if gi is None:
        idx = {g: n for n, g in enumerate(games)}
        gi = np.array([idx[g] for g in groups])
    cnt = np.bincount(gi, minlength=len(games)).astype(float)
    sums = {k: np.bincount(gi, weights=np.asarray(c, float), minlength=len(games)) for k, c in cols.items()}
    picks = [rng.integers(0, len(games), len(games)) for _ in range(reps)]
    reps_ = {k: np.array([s[p].sum() / cnt[p].sum() for p in picks]) for k, s in sums.items()}
    est = {k: s.sum() / cnt.sum() for k, s in sums.items()}
    return est, reps_


def _ci(x):
    return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]


def _auc(scores, labels):
    s, y = np.asarray(scores, float), np.asarray(labels, bool)
    if y.all() or (~y).all():
        return None
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s))
    sorted_s = s[order]
    i = 0
    while i < len(s):                      # average ranks for ties
        j = i
        while j + 1 < len(s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    n1, n0 = y.sum(), (~y).sum()
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def read_main(args):
    scan = json.load(open(args.scan))["rows"]
    z = dict(np.load(args.probs))
    names = [str(x) for x in z["names"]]
    koff = z["koff"]
    P = {m: [z[m][koff[n]:koff[n + 1]] for n in range(len(scan))] for m in names}
    taus = dict((a, float(b)) for a, b in (t.split("=") for t in args.taus))
    news = [m for m in names if m != "old"]
    per = _per_decision(scan, P, names, taus)
    res = {"deck": args.deck, "decisions": len(per), "methods": names, "taus": taus, "strata": {}}
    for stratum, keep in (("all", lambda d: True), ("start", lambda d: d["start"]), ("mid", lambda d: not d["start"])):
        sel = [d for d in per if keep(d)]
        cols = {"uni_top1": [d["uni_top1"] for d in sel], "exp_top1": [d["exp_top1"] for d in sel],
                "kl_u": [d["kl_u"] for d in sel], "kl5_u": [d["kl5_u"] for d in sel]}
        for m in names:
            for f in ("top1", "kl", "kl5", "ce", "top2"):
                cols[f"{m}.{f}"] = [d[m][f] for d in sel]
        if "old" in names:
            cols["old2_kl5"] = [d["old2_kl5"] for d in sel]
        est, R = _boot([d["g"] for d in sel], cols)
        st = {"decisions": len(sel), "uniform_top1": est["uni_top1"], "expansion_top1": est["exp_top1"],
              "kl_uniform": est["kl_u"], "kl5_uniform": est["kl5_u"], "methods": {}}
        for m in names:
            tgt = "kl5" if taus.get(m, 1.0) == 0.5 else "kl"
            ku = "kl5_u" if tgt == "kl5" else "kl_u"
            mm = {f: est[f"{m}.{f}"] for f in ("top1", "kl", "kl5", "ce", "top2")}
            mm["top1_minus_exp"] = [est[f"{m}.top1"] - est["exp_top1"]] + _ci(R[f"{m}.top1"] - R["exp_top1"])
            mm["kl_ratio_own_target"] = [est[f"{m}.{tgt}"] / est[ku]] + _ci(R[f"{m}.{tgt}"] / R[ku])
            mm["top1_ci"] = _ci(R[f"{m}.top1"])
            if "old" in names and m != "old":
                mm["top1_minus_old"] = [est[f"{m}.top1"] - est["old.top1"]] + _ci(R[f"{m}.top1"] - R["old.top1"])
                mm["kl_vs_old"] = ([est[f"{m}.kl"], est["old.kl"]] if tgt == "kl" else [est[f"{m}.kl5"], est["old2_kl5"]])
            ends = [d for d in sel if d[m]["p_end"] is not None]
            if stratum == "all":
                mm["end_auc"] = _auc([d[m]["p_end"] for d in ends], [d["end_top"] for d in ends])
                mm["end_confusion"] = {
                    "search_end_prior_end": sum(1 for d in ends if d["end_top"] and d[m]["top_end"]),
                    "search_end_prior_cont": sum(1 for d in ends if d["end_top"] and not d[m]["top_end"]),
                    "search_cont_prior_end": sum(1 for d in ends if not d["end_top"] and d[m]["top_end"]),
                    "search_cont_prior_cont": sum(1 for d in ends if not d["end_top"] and not d[m]["top_end"])}
            st["methods"][m] = mm
        res["strata"][stratum] = st
    # pass / fail
    verdict = {}
    for m in news:
        a, s, mid = (res["strata"][k]["methods"][m] for k in ("all", "start", "mid"))
        c = {"O1-1": a["top1_minus_exp"][1] >= 0.15, "O1-2": a["kl_ratio_own_target"][2] <= 0.70,
             "O1-3": s["top1_minus_exp"][1] >= 0 and mid["top1_minus_exp"][1] >= 0}
        if args.deck == "ramp":
            c["O1-4"] = a["top1_minus_old"][1] >= -0.01 and a["kl_vs_old"][0] <= a["kl_vs_old"][1]
        verdict[m] = {"criteria": c, "pass": all(c.values()), "tau": taus.get(m, 1.0),
                      "top1": a["top1"], "own_kl": a["kl5"] if taus.get(m, 1.0) == 0.5 else a["kl"]}
    res["verdict"] = verdict
    passing = [m for m in news if verdict[m]["pass"]]
    choice = None
    if passing:
        t05 = [m for m in passing if verdict[m]["tau"] == 0.5]
        t1 = [m for m in passing if verdict[m]["tau"] == 1.0]
        pool = t05
        if not t05 or (t1 and max(verdict[m]["top1"] for m in t1) - max(verdict[m]["top1"] for m in t05) >= 0.02):
            pool = t1
        pool = sorted(pool, key=lambda m: verdict[m]["own_kl"])
        choice = pool[0]
        if len(pool) > 1 and verdict[pool[1]]["own_kl"] - verdict[pool[0]]["own_kl"] < 0.005:
            frozen = [m for m in pool[:2] if m.startswith("fz")]
            choice = frozen[0] if frozen else pool[0]
    res["choice"] = choice
    # cross-check against the builder's dump (per legal move, as recorded; names mapped by --dump-map DUMP=MINE)
    if args.dump:
        loff = z["loff"]
        dmap = dict(x.split("=", 1) for x in args.dump_map)
        by = {(int(r["g"]), int(r["i"])): k for k, r in enumerate(scan)}
        mx, bad, n, seen = {}, {}, 0, set()
        for line in gzip.open(args.dump, "rt"):
            d = json.loads(line)
            k = by.get((int(d["g"]), int(d["i"])))
            if k is None:
                bad["not_in_scan"] = bad.get("not_in_scan", 0) + 1
                continue
            seen.add(k)
            n += 1
            if [int(x) for x in d["visits"]] and d.get("start") is not None and bool(d["start"]) != scan[k]["start"]:
                bad["start"] = bad.get("start", 0) + 1
            for name, pr in d["priors"].items():
                mine_name = dmap.get(name, name)
                if "raw_" + mine_name not in z:
                    bad["no_method_" + name] = bad.get("no_method_" + name, 0) + 1
                    continue
                mine = z["raw_" + mine_name][loff[k]:loff[k + 1]]
                if len(mine) != len(pr):
                    bad["len_" + name] = bad.get("len_" + name, 0) + 1
                    continue
                mx[name] = max(mx.get(name, 0.0), float(np.abs(np.asarray(pr, float) - mine).max()))
            if d.get("order") is not None and scan[k]["exp"][0] >= 0:
                pass                                   # the order is checked separately (legal indices vs keys)
        bad["scan_not_in_dump"] = len(scan) - len(seen)
        res["dump_check"] = {"rows": n, "max_abs_diff": mx, "problems": bad}
    json.dump(res, open(args.out, "w"), indent=1, default=float)
    print(json.dumps({"verdict": verdict, "choice": choice, "dump": res.get("dump_check")}, indent=1, default=float))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("records")
    r.add_argument("--scan", required=True)
    r.add_argument("--prior", action="append", default=[])
    r.add_argument("--old")
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=4)
    q = sub.add_parser("read")
    q.add_argument("--scan", required=True)
    q.add_argument("--probs", required=True)
    q.add_argument("--taus", nargs="*", default=[])
    q.add_argument("--deck", required=True, choices=("ramp", "elft"))
    q.add_argument("--dump")
    q.add_argument("--dump-map", nargs="*", default=[])
    q.add_argument("--out", required=True)
    args = ap.parse_args()
    {"run": run_main, "read": read_main}[args.cmd](args)


if __name__ == "__main__":
    main()
