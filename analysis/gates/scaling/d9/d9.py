"""D9 (registered in e11fb72 before computing): how much a mid-turn leaf scored as "end the turn now" (SetNetEnded with
+neteot: after_end_of_turn on a copy, then the net; a win / loss at that end is 1 / 0) underestimates the position.
Condition: the opponent's deck list is known (order and hand not).

    cd <checkout 72a5148> && PYTHONPATH=. python3 d9.py run REC NET DECK --out rows.json --workers 4
    python3 d9.py read --mirror NAME=rows1.json,rows2.json ... --out d9.json
"""
import argparse, gzip, json, math, os, sys
from multiprocessing import Pool

import numpy as np

_NET = {}


def _p(state, me, net):
    from svsim.search.evaluate import after_end_of_turn
    end = after_end_of_turn(state.clone())
    if end.winner is not None:
        return (1.0 if end.winner == me else 0.0), True
    return 1.0 / (1.0 + math.exp(-net.logit(end, me))), False


def _games(job):
    path, gs, netpath = job
    from svsim.core.actions import EndTurn
    from svsim.core.engine import legal_actions
    from svsim.core.enums import Phase
    from svsim.learn.setnet import load_cached
    from svsim.search.mcts import _locator, action_key
    from svsim.tools import records as R
    net = load_cached(netpath)
    mids, ends = [], []
    for line in gzip.open(path, "rt"):
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec["g"] not in gs:
            continue
        thoughts = rec.get("search") or []
        cur, step, turn_end, pending = None, 0, {}, []
        for i, (state, action) in enumerate(R.steps(rec)):
            if state.phase != Phase.MAIN:
                continue
            if state.turn != cur:
                cur, step = state.turn, 0
            step += 1
            me = state.active
            if isinstance(action, EndTurn):
                p, over = _p(state, me, net)
                turn_end[state.turn] = p
                if not over:
                    ends.append({"g": rec["g"], "turn": state.turn, "me": me, "p": p})
            t = thoughts[i] if i < len(thoughts) else None
            if t is None or sum(t["visits"]) <= 0:
                continue
            legal = legal_actions(state)
            where = _locator(state, me)
            keys, end_key = {}, False
            for a in legal:
                k = action_key(state, a, where)
                if k not in keys:
                    keys[k] = isinstance(a, EndTurn)
            if len(keys) < 2:
                continue
            n_nonend = sum(1 for v in keys.values() if not v)
            p, _ = _p(state, me, net)
            pending.append({"g": rec["g"], "i": i, "turn": state.turn, "me": me, "step": step, "nonend": n_nonend,
                            "pp": state.players[me].pp, "p_now": p})
        w = rec["winner"]
        for d in pending:
            d["y"] = 1.0 if w == d["me"] else 0.0
            d["p_turnend"] = turn_end.get(d["turn"], d["y"])      # the game ended inside the turn: its result
        for e in ends:
            if e["g"] == rec["g"] and "y" not in e:
                e["y"] = 1.0 if w == e["me"] else 0.0
        mids.extend(pending)
    return mids, ends


def run_main(args):
    gs = sorted(json.loads(l)["g"] for l in gzip.open(args.records, "rt") if l.strip())
    chunks = [(args.records, set(gs[k::args.workers * 4]), args.net) for k in range(args.workers * 4)]
    mids, ends = [], []
    with Pool(args.workers) as pool:
        for m, e in pool.imap_unordered(_games, chunks):
            mids.extend(m)
            ends.extend(e)
    json.dump({"records": os.path.basename(args.records), "net": os.path.basename(args.net), "deck": args.deck,
               "games": len(gs), "mid": mids, "end": ends}, open(args.out, "w"))
    print(len(gs), "games,", len(mids), "mid-turn decisions,", len(ends), "turn ends")


def _grp(v):
    return str(min(int(v), 4)) + ("+" if v >= 4 else "")


class Pool_:
    """Per-game sums of row values for fast game-clustered bootstrap (games resampled within each shard)."""

    def __init__(self, shards, reps=2000):
        rng = np.random.default_rng(0)
        self.ws, self.mid, self.end = [], [], []
        offset = 0
        for mids, ends in shards:
            games = sorted({r["g"] for r in mids} | {r["g"] for r in ends})
            gi = {g: n + offset for n, g in enumerate(games)}
            self.mid.extend((gi[r["g"]], r) for r in mids)
            self.end.extend((gi[r["g"]], r) for r in ends)
            w = np.zeros((reps, len(games)))
            for k in range(reps):
                w[k] = np.bincount(rng.integers(0, len(games), len(games)), minlength=len(games))
            self.ws.append(w)
            offset += len(games)
        self.W = np.concatenate(self.ws, axis=1)          # reps x all games
        self.G = offset

    def sums(self, rows, f, keep=lambda r: True):
        S, C = np.zeros(self.G), np.zeros(self.G)
        for g, r in rows:
            if keep(r):
                S[g] += f(r)
                C[g] += 1
        return S, C

    def mean(self, rows, f, keep=lambda r: True):
        S, C = self.sums(rows, f, keep)
        est = S.sum() / C.sum() if C.sum() else float("nan")
        bs = (self.W @ S) / np.maximum(self.W @ C, 1e-12)
        return est, bs

    @staticmethod
    def ci(est, bs):
        return [float(est), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def read_main(args):
    res = {}
    for spec in args.mirror:
        name, files = spec.split("=")
        data = [json.load(open(f)) for f in files.split(",")]
        sets = {"pooled": [(d["mid"], d["end"]) for d in data]}
        for d in data:
            sets[d["records"]] = [(d["mid"], d["end"])]
        out = {}
        for label, shards in sets.items():
            P = Pool_(shards)
            rm = P.mean(P.mid, lambda r: r["y"] - r["p_now"])
            re_ = P.mean(P.end, lambda r: r["y"] - r["p"])
            dl = P.mean(P.mid, lambda r: r["p_turnend"] - r["p_now"])
            bm = P.mean(P.mid, lambda r: (r["y"] - r["p_now"]) ** 2)
            be = P.mean(P.end, lambda r: (r["y"] - r["p"]) ** 2)
            o = {"mid_decisions": len(P.mid), "turn_ends": len(P.end), "r_mid": P.ci(*rm), "r_end": P.ci(*re_),
                 "E": P.ci(rm[0] - re_[0], rm[1] - re_[1]), "delta": P.ci(*dl),
                 "brier_mid": P.ci(*bm), "brier_end": P.ci(*be), "brier_gap": P.ci(bm[0] - be[0], bm[1] - be[1]),
                 "mean_p_now": float(np.mean([r["p_now"] for _, r in P.mid])), "mean_y_mid": float(np.mean([r["y"] for _, r in P.mid]))}
            for key in ("nonend", "pp", "step"):
                o[key] = {}
                for gname in sorted({_grp(r[key]) for _, r in P.mid}):
                    keep = lambda r, gname=gname, key=key: _grp(r[key]) == gname
                    a = P.mean(P.mid, lambda r: r["y"] - r["p_now"], keep)
                    b = P.mean(P.mid, lambda r: r["p_turnend"] - r["p_now"], keep)
                    o[key][gname] = {"n": sum(1 for _, r in P.mid if keep(r)), "r": P.ci(*a),
                                     "E": P.ci(a[0] - re_[0], a[1] - re_[1]), "delta": P.ci(*b)}
            a4 = P.mean(P.mid, lambda r: r["y"] - r["p_now"], lambda r: r["nonend"] >= 4)
            a1 = P.mean(P.mid, lambda r: r["y"] - r["p_now"], lambda r: r["nonend"] == 1)
            d4 = P.mean(P.mid, lambda r: r["p_turnend"] - r["p_now"], lambda r: r["nonend"] >= 4)
            d1 = P.mean(P.mid, lambda r: r["p_turnend"] - r["p_now"], lambda r: r["nonend"] == 1)
            o["trend_r_4_minus_1"] = P.ci(a4[0] - a1[0], a4[1] - a1[1])
            o["trend_delta_4_minus_1"] = P.ci(d4[0] - d1[0], d4[1] - d1[1])
            out[label] = o
        p = out["pooled"]
        out["verdict"] = {"residual_positive": p["E"][0] >= 0.02 and p["E"][1] > 0,
                          "grows_with_moves": p["trend_r_4_minus_1"][0] >= 0.03 and p["trend_r_4_minus_1"][1] > 0}
        res[name] = out
    res["worth_doing"] = any(v["verdict"]["residual_positive"] or v["verdict"]["grows_with_moves"]
                             for k, v in res.items() if isinstance(v, dict) and "verdict" in v)
    json.dump(res, open(args.out, "w"), indent=1, default=float)
    print(json.dumps({k: (v["verdict"] if isinstance(v, dict) else v) for k, v in res.items()}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("records"); r.add_argument("net"); r.add_argument("deck")
    r.add_argument("--out", required=True); r.add_argument("--workers", type=int, default=4)
    q = sub.add_parser("read")
    q.add_argument("--mirror", action="append", required=True); q.add_argument("--out", required=True)
    args = ap.parse_args()
    {"run": run_main, "read": read_main}[args.cmd](args)


if __name__ == "__main__":
    main()
