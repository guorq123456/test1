"""D5 (analysis/scaling/README): on 500 decision points from the v2skx holdout shard 70200008, how often does each net
(mcts:100 + setnet + neteot) pick the move v2skx picks with 1600 searches? Then the Spearman correlation of those
rates with the gates' strength scale fixed at registration. Condition: the opponent's deck list is known (order and
hand not). Run from (and with PYTHONPATH =) the 342cc14 checkout.

    python3 d5_agree.py --rec .../heldout/rec-70200008.jsonl.gz --seed 73400000 --n 500 --workers 3 --out d5.json
"""
import argparse, gzip, json, random, time
from multiprocessing import Pool

import numpy as np

P = "plan+learned+phased=pkg-kc-ramp-ramp+xprune=3:3:cost"
REF = f"mcts:1600+{P}"
NETS = ["net-10000", "net-gen2-20000", "net-gen3-30000", "net-gen4-39000", "net-gen4-59000", "net-all-131000",
        "net-in2-59000", "net-in2kc-59000"]
SCALE = {"net-all-131000": 0.464, "net-gen4-59000": 0.448, "net-gen3-30000": 0.376, "net-gen4-39000": 0.323,
         "net-in2-59000": 0.288, "net-in2kc-59000": 0.232, "net-gen2-20000": 0.152, "net-10000": -0.088}
SPECS = {"ref": REF, **{n: f"mcts:100+{P}+setnet=analysis/scaling/models/{n}.npz+neteot" for n in NETS}}
_DEC = {}


def decisions(rec, seed, n):
    from svsim.core.engine import legal_actions
    from svsim.core.enums import Phase
    from svsim.tools import records as R
    games = {}
    for line in gzip.open(rec, "rt"):
        if line.strip():
            r = json.loads(line)
            games[r["g"]] = r
    rng = random.Random(seed)
    out = []
    for g in rng.sample(sorted(games), n):
        cands = []
        for i, (state, action) in enumerate(R.steps(games[g])):
            if state.phase == Phase.MAIN and not state.over and len(legal_actions(state)) >= 2:
                cands.append((i, state.clone()))
        i, state = rng.choice(cands)
        out.append((g, i, state))
    return out


def _work(k):
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    g, i, state, seed = _DEC[k]
    row = {"k": k, "g": g, "i": i, "turn": state.turn, "n_legal": len(legal_actions(state))}
    for name, spec in SPECS.items():
        s = state.clone()
        legal = legal_actions(s)
        a = make_agent(spec, seed).act(s, legal)
        row[name] = json.dumps(a.to_dict() if hasattr(a, "to_dict") else repr(a), sort_keys=True)
    return row


def spearman(x, y):
    def rank(v):
        v = np.asarray(v, float)
        order = v.argsort()
        r = np.empty(len(v))
        r[order] = np.arange(len(v))
        for u in np.unique(v):                    # average ranks for ties
            m = v == u
            r[m] = r[m].mean()
        return r
    return float(np.corrcoef(rank(x), rank(y))[0, 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rec", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    t0 = time.time()
    dec = decisions(args.rec, args.seed, args.n)
    for k, (g, i, state) in enumerate(dec):
        _DEC[k] = (g, i, state, args.seed + k)
    print(f"{len(dec)} decision points ({time.time() - t0:.0f}s)", flush=True)
    rows = []
    with Pool(args.workers) as pool:
        for row in pool.imap_unordered(_work, range(len(dec)), chunksize=4):
            rows.append(row)
            if len(rows) % 50 == 0:
                print(f"{len(rows)} / {len(dec)}  {time.time() - t0:.0f}s", flush=True)
    rows.sort(key=lambda r: r["k"])
    agree = {n: np.array([r[n] == r["ref"] for r in rows], float) for n in NETS}
    rng = np.random.default_rng(0)
    B = rng.integers(0, len(rows), (4000, len(rows)))
    summary = {}
    for n in NETS:
        boots = agree[n][B].mean(axis=1)
        summary[n] = {"agree": round(float(agree[n].mean()), 4), "lo": round(float(np.percentile(boots, 2.5)), 4),
                      "hi": round(float(np.percentile(boots, 97.5)), 4), "scale": SCALE[n]}
    rho = spearman([summary[n]["agree"] for n in NETS], [SCALE[n] for n in NETS])
    boot_rho = [spearman([agree[n][b].mean() for n in NETS], [SCALE[n] for n in NETS]) for b in B[:2000]]
    report = {"condition": "对手卡表已知（牌序、手牌未知）", "rec": args.rec, "seed": args.seed, "ref": REF, "specs": SPECS,
              "n": len(rows), "summary": summary, "spearman": round(rho, 4),
              "spearman_boot_95": [round(float(np.percentile(boot_rho, 2.5)), 4), round(float(np.percentile(boot_rho, 97.5)), 4)],
              "seconds": round(time.time() - t0), "rows": rows}
    open(args.out, "w", encoding="utf-8").write(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
