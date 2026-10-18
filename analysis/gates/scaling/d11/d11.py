"""D11 (registered in 0c353df; report only): does the mid-turn net still lean in A-vs-A games? At each mid-turn decision
(learn.setpolicy.decisions) of the A-vs-A records, p = sigmoid(score / SCALE) from the scorer A's own spec builds
(+netmid: the mid-turn branch), and at each turn end the turn-end branch after after_end_of_turn; r = y - p.
Mean r with a 95% bootstrap of games (2000, rng 0), Brier, ece, by first / second, turn, keys left, step in turn.
Condition: the opponent's deck list is known (order and hand not).

    cd <checkout> && PYTHONPATH=. python3 d11.py REC.jsonl.gz SPEC --out d11-<deck>.json
"""
import argparse, gzip, json, math
import numpy as np


def scorer_of(spec):
    from svsim.tools.arena import make_agent
    inner = make_agent(spec, 0)
    for _ in range(5):
        if hasattr(inner, "search") and hasattr(inner.search, "weights"):
            return inner.search.weights
        inner = getattr(inner, "base", None)
    raise RuntimeError("no scorer")


def ece(p, y):
    b = np.minimum((p * 10).astype(int), 9)
    return float(sum((b == k).sum() / len(p) * abs(p[b == k].mean() - y[b == k].mean()) for k in range(10) if (b == k).any()))


def summarize(g, p, y, mask, rng_seed=0, reps=2000):
    g, p, y = g[mask], p[mask], y[mask]
    if len(p) == 0:
        return None
    r = y - p
    games, inv = np.unique(g, return_inverse=True)
    sr = np.bincount(inv, weights=r, minlength=len(games)); cnt = np.bincount(inv, minlength=len(games))
    rng = np.random.default_rng(rng_seed)
    idx = rng.integers(0, len(games), (reps, len(games)))
    boots = sr[idx].sum(1) / cnt[idx].sum(1)
    return {"n": int(len(p)), "games": int(len(games)), "mean_r": [float(r.mean())] + [float(x) for x in np.percentile(boots, [2.5, 97.5])],
            "mean_p": float(p.mean()), "win": float(y.mean()), "brier": float(((p - y) ** 2).mean()), "ece": ece(p, y)}


def main():
    from svsim.core.actions import EndTurn
    from svsim.learn.model import SCALE
    from svsim.learn.setpolicy import decisions
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools import records as R
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sc = scorer_of(args.spec)
    sig = lambda s: 1 / (1 + math.exp(-s / SCALE))
    mid, end = [], []
    recs = [json.loads(l) for l in gzip.open(args.records, "rt") if l.strip()]
    for rec in recs:
        w, first, g = rec["winner"], rec["first"], rec["g"]
        dec = {}
        for i, state, legal, reps, group, pi, start in decisions(rec):
            dec[i] = (state.clone(), legal)
        last_turn, step = None, 0
        for i, (state, action) in enumerate(R.steps(rec)):
            me = state.active
            if i in dec:
                st, legal = dec[i]
                from svsim.learn.setpolicy import distinct
                reps, grp = distinct(st, legal)
                from svsim.core.actions import EndTurn as ET
                has_end = any(isinstance(a, ET) for a in reps)
                nonend = len(reps) - (1 if has_end else 0)
                if st.turn != last_turn:
                    last_turn, step = st.turn, 0
                else:
                    step += 1
                mid.append((g, sig(sc.score(st, me)), float(w == me), me == first, st.turn, nonend, step))
            if isinstance(action, EndTurn):
                e = after_end_of_turn(state.clone())
                p = sig(sc.score(e, me)) if e.winner is None else float(e.winner == me)
                end.append((g, p, float(w == me), me == first, state.turn))
    out = {"records": args.records, "spec": args.spec, "games": len(recs),
           "first_seat_wins": float(np.mean([r["winner"] == r["first"] for r in recs]))}
    for kind, rows in (("mid", mid), ("end", end)):
        g = np.array([r[0] for r in rows]); p = np.array([r[1] for r in rows]); y = np.array([r[2] for r in rows])
        fst = np.array([r[3] for r in rows]); turn = np.array([r[4] for r in rows])
        res = {"all": summarize(g, p, y, np.ones(len(p), bool)),
               "first": summarize(g, p, y, fst), "second": summarize(g, p, y, ~fst)}
        for lo, hi in ((1, 4), (5, 8), (9, 12), (13, 999)):
            res[f"turn {lo}-{hi}"] = summarize(g, p, y, (turn >= lo) & (turn <= hi))
        if kind == "mid":
            ne = np.array([r[5] for r in rows]); stp = np.array([r[6] for r in rows])
            for k in (1, 2, 3):
                res[f"left {k}"] = summarize(g, p, y, ne == k)
            res["left 4+"] = summarize(g, p, y, ne >= 4)
            res["wide"] = summarize(g, p, y, ne >= 4); res["narrow"] = summarize(g, p, y, ne <= 3)
            for k in (0, 1, 2):
                res[f"step {k}"] = summarize(g, p, y, stp == k)
            res["step 3+"] = summarize(g, p, y, stp >= 3)
        out[kind] = res
    json.dump(out, open(args.out, "w"), indent=1)
    for kind in ("mid", "end"):
        for k, v in out[kind].items():
            if v:
                print(kind, k, v["n"], "mean r %+.4f (%+.4f..%+.4f)" % tuple(v["mean_r"]), "brier %.4f ece %.3f" % (v["brier"], v["ece"]))


if __name__ == "__main__":
    main()
