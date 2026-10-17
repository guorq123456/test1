"""D4 (analysis/scaling/README): are the positions the net scores in the search the same snapshot as the turn ends the
recorder stores for training? Plays gen4-59000 + eot self-play games (learn.netdata.play, as scaledata play) with a
hook on SetNet.logit that fingerprints every scored position (after +neteot) in the v1 and v2 encodings; then takes
every real turn end the recorder's path stores (scaledata.encode_game) and checks it among the positions the search
scored in that turn, and compares it column by column with ISMCTS._step(pre-EndTurn position, EndTurn).
Condition: the opponent's deck list is known (order and hand not). Run with PYTHONPATH = the 342cc14 checkout.

    python3 d4_snapshot.py --seed 73300000 --games 4 --out d4.json
"""
import argparse, json, time
from collections import defaultdict
import numpy as np
from svsim.learn import setnet as SN
from svsim.learn import tokens as T
from svsim.learn.netdata import play
from svsim.learn.scaledata import encode_game
from svsim.search.mcts import ISMCTS
from svsim.core.actions import EndTurn
from svsim.tools import records as R

NET = "analysis/scaling/models/net-gen4-59000.npz"
SPEC = "mcts:200+plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost+setnet=" + NET + "+neteot"


def fp(state, player, inputs):
    c, t, g = T.encode(state, player, inputs)
    return (state.turn, player, c.tobytes(), t.tobytes(), np.asarray(g, np.float32).tobytes())


def diff(a, b, inputs):
    """Columns that differ between two encodings of positions with the same tokens rows (else 'rows')."""
    (ca, ta, ga), (cb, tb, gb) = a, b
    out = {}
    gn = T.global_names(inputs)
    for k, (x, y) in enumerate(zip(ga, gb)):
        if x != y:
            out["g:" + gn[k]] = float(y) - float(x)
    if len(ca) != len(cb) or (ca != cb).any():
        out["rows"] = (len(ca), len(cb))
        return out
    tn = T.token_names(inputs)
    d = tb.astype(np.int64) - ta.astype(np.int64)
    for j in np.flatnonzero((d != 0).any(axis=0)):
        out["t:" + tn[j]] = int(np.abs(d[:, j]).max())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--games", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    net = SN.load_cached(NET)
    orig = SN.SetNet.logit
    scored = defaultdict(set)          # (inputs) -> fingerprints of scored positions
    calls = [0]

    def hooked(self, state, player):
        if self is net:
            calls[0] += 1
            for inp in ("v1", "v2"):
                scored[inp].add(fp(state, player, inp))
        return orig(self, state, player)

    SN.SetNet.logit = hooked
    report = {"spec": SPEC, "seed": args.seed, "games": [], "condition": "对手卡表已知（牌序、手牌未知）"}
    agg = {inp: {"turn_ends": 0, "found_in_search": 0, "step_equal": 0, "step_diff_cols": defaultdict(int)} for inp in ("v1", "v2")}
    t0 = time.time()
    for g in range(args.games):
        for inp in scored:
            scored[inp].clear()
        calls[0] = 0
        record = play((g, args.seed, "ramp-t", "ramp-t", SPEC, 0.0))
        pre = {}                                       # action index of each EndTurn -> the position before it
        for i, (state, action) in enumerate(R.steps(record)):   # (the generator advances one state: copy it here)
            if isinstance(action, EndTurn):
                pre[i] = state.clone()
        gi = {"g": g, "winner": record["winner"], "actions": len(record["actions"]), "net_calls": calls[0]}
        for inp in ("v1", "v2"):
            missing = []
            for cids, toks, glob_, lab, _ in encode_game(record, None, inp):
                a = agg[inp]
                a["turn_ends"] += 1
                key = (lab["turn"], lab["player"], np.asarray(cids, np.int32).tobytes(), np.asarray(toks, np.int16).tobytes(),
                       np.asarray(glob_, np.float32).tobytes())
                if key in scored[inp]:
                    a["found_in_search"] += 1
                else:
                    missing.append((lab["turn"], lab["player"], lab["i"]))
                s = pre[lab["i"]].clone()
                ISMCTS._step(s, EndTurn())
                d = diff((np.asarray(cids), np.asarray(toks), np.asarray(glob_)), T.encode(s, lab["player"], inp), inp)
                if d:
                    for k in d:
                        a["step_diff_cols"][k] += 1
                else:
                    a["step_equal"] += 1
            gi["missing_" + inp] = missing
        report["games"].append(gi)
        print(json.dumps(gi), f"{time.time() - t0:.0f}s", flush=True)
    for inp in agg:
        agg[inp]["step_diff_cols"] = dict(agg[inp]["step_diff_cols"])
    report["summary"] = agg
    text = json.dumps(report, indent=1, ensure_ascii=False)
    open(args.out, "w", encoding="utf-8").write(text + "\n")
    print(json.dumps(agg, indent=1))


if __name__ == "__main__":
    main()
