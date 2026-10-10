"""cand-sp refit under the analysis line's pre-registered reading (c8a04a0, analysis/lethal-setup/README-sp.md;
the architecture thread 16:50Z). Condition: the opponent's deck list is known (order and hand not).

Same model, loss, data and optimiser as sp_fit.py (cand-kc's objective + lambda x preference over the Ramp-mirror
turns; the other pairings are not fitted). What changes is the folding and the lambda rule:
- **Outer 5 folds:** all of Salem's games (every pairing) sorted by game id, game j in fold j mod 5.
- **Inner 4 folds:** the outer fold's training games sorted by id, game j in inner fold j mod 4; used only to choose
  lambda from {0, 0.003, 0.01, 0.03, 0.1, 0.3}: the highest inner pairwise accuracy, ties to the smaller lambda.
- **Pairwise accuracy:** Salem's turn end against each of the installed 1043's 8 most visited ends (the candidates
  marked in_top), an end identical to his (same state_key) left out; a higher score for Salem's counts 1, equal 0.5.
  Pairs of every pairing count (each turn's ends read with the Ramp-mirror models).
- **The final model:** lambda chosen the same way by 4 folds over all games, then one fit on all Ramp-mirror turns:
  svsim/learn/phased_models/cand-sp-ramp-ramp (replaces sp_fit.py's model).
- **Out:** per outer held-out turn, every candidate's score under cand-sp (that outer fold's model), cand-kc and the
  installed Ramp-mirror ENDED model (all three are Ramp-mirror models, also on the other pairings' turns); the
  readings are the analysis line's.

    python3 sp_nested.py TURNS.jsonl LABELS KC_DATA.npz OUT_ROOT --scores scores.jsonl --out-json nested.json
"""
import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis/salem-pref"))
import sp_fit as F   # noqa: E402

OUTER, INNER = 5, 4
T = []   # every turn, every pairing


def load(turns_path, labels_path, data_path):
    F.load(turns_path, labels_path, data_path)
    D = F.D
    turns = [json.loads(l) for l in open(turns_path) if l.strip()]
    games = sorted({t["game"] for t in turns})
    outer = {g: j % OUTER for j, g in enumerate(games)}
    T.clear()
    for t in turns:
        xs = np.array([c["x"] for c in t["candidates"]], float)
        X = ((xs * D["keep"] - D["mean"]) / D["std"]).astype(np.float32)
        s = next(i for i, c in enumerate(t["candidates"]) if c["salem"])
        top = [i for i, c in enumerate(t["candidates"]) if c["in_top"] and not c["salem"]]
        T.append({"game": t["game"], "turn": t["turn"], "pairing": t["pairing"], "ramp": t["pairing"] == F.RAMP,
                  "outer": outer[t["game"]], "X": X, "raw": xs, "s": s, "top": top, "t": t})
    # sp_fit's fit() trains on D["P"] by index: keep D["P"] the Ramp-mirror turns, mapped from T
    D["P"] = [{"game": x["game"], "X": x["X"], "s": x["s"]} for x in T if x["ramp"]]
    D["P_of_T"] = {i: j for j, i in enumerate(i for i, x in enumerate(T) if x["ramp"])}
    D["games_all"] = games


def pairwise(score, ids):
    hit, n = 0.0, 0
    for i in ids:
        x = T[i]
        if not x["top"]:
            continue
        z = score(x)
        for c in x["top"]:
            n += 1
            hit += 1.0 if z[x["s"]] > z[c] else (0.5 if z[x["s"]] == z[c] else 0.0)
    return hit, n


def _fit_on_games(lam, games):
    D = F.D
    train = [D["P_of_T"][i] for i, x in enumerate(T) if x["ramp"] and x["game"] in games]
    return F.fit(lam, train)


def _inner_job(item):
    lam, train_games, held_games = item
    w = _fit_on_games(lam, set(train_games)).astype(np.float32)
    ids = [i for i, x in enumerate(T) if x["game"] in set(held_games)]
    return lam, pairwise(lambda x: x["X"] @ w, ids)


def _choose(pool, games):
    """lambda by INNER folds over `games` (sorted, j mod INNER): the highest pooled pairwise accuracy, ties smaller."""
    games = sorted(games)
    folds = [[g for j, g in enumerate(games) if j % INNER == k] for k in range(INNER)]
    jobs = [(lam, [g for g in games if g not in set(f)], f) for lam in F.LAMBDAS for f in folds]
    tot = {lam: [0.0, 0] for lam in F.LAMBDAS}
    for lam, (h, n) in pool.map(_inner_job, jobs, chunksize=1):
        tot[lam][0] += h; tot[lam][1] += n
    acc = {lam: tot[lam][0] / tot[lam][1] for lam in F.LAMBDAS}
    best = max(F.LAMBDAS, key=lambda lam: (acc[lam], -lam))
    return best, {str(k): round(v, 4) for k, v in acc.items()}


def _final_job(item):
    lam, games = item
    return _fit_on_games(lam, set(games))


def main():
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("turns"); ap.add_argument("labels"); ap.add_argument("data"); ap.add_argument("out_root")
    ap.add_argument("--scores", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    load(args.turns, args.labels, args.data)
    D = F.D
    t0 = time.time()
    games = D["games_all"]
    kc_w = np.array(D["kc"]["coef"], np.float32)
    out = {"outer": {}}
    w_outer = {}
    with Pool(args.workers, initializer=load, initargs=(args.turns, args.labels, args.data)) as pool:
        for k in range(OUTER):
            train = [g for j, g in enumerate(games) if j % OUTER != k]
            lam, acc = _choose(pool, train)
            w_outer[k] = pool.apply(_final_job, ((lam, train),))
            out["outer"][str(k)] = {"lambda": lam, "inner_pairwise": acc,
                                    "held_games": [g for j, g in enumerate(games) if j % OUTER == k],
                                    "val_mse": round(F._val_mse(w_outer[k]), 6)}
            print(k, lam, acc, flush=True)
        lam_all, acc_all = _choose(pool, games)
        w_final = pool.apply(_final_job, ((lam_all, games),))
    with open(args.scores, "w", encoding="utf-8") as fh:
        for i, x in enumerate(T):
            w = w_outer[x["outer"]].astype(np.float32)
            sp, kc, inst = x["X"] @ w, x["X"] @ kc_w, F._inst_logits(x["raw"])
            cands = [{"salem": c["salem"], "in_top": c["in_top"], "bot": c["bot"], "visits": c["visits"],
                      "cand-sp": round(float(sp[j]), 6), "cand-kc": round(float(kc[j]), 6),
                      "installed": round(float(inst[j]), 6)} for j, c in enumerate(x["t"]["candidates"])]
            fh.write(json.dumps({"game": x["game"], "turn": x["turn"], "global_turn": x["t"]["global_turn"],
                                 "pairing": x["pairing"], "ramp_mirror": x["ramp"], "outer_fold": x["outer"],
                                 "lambda": out["outer"][str(x["outer"])]["lambda"], "candidates": cands},
                                ensure_ascii=False) + "\n")
    # builder's own pooled readings, for the record (the analysis line's are the ones that count)
    own = {}
    for part, sel in (("all", lambda x: True), ("ramp mirror", lambda x: x["ramp"]),
                      ("other pairings", lambda x: not x["ramp"])):
        ids = [i for i, x in enumerate(T) if sel(x)]
        r = {}
        for m, f in (("cand-sp", lambda x: x["X"] @ w_outer[x["outer"]].astype(np.float32)),
                     ("cand-kc", lambda x: x["X"] @ kc_w), ("installed", lambda x: F._inst_logits(x["raw"]))):
            h, n = pairwise(f, ids)
            r[m] = round(h / n, 4)
        r["pairs"] = pairwise(lambda x: x["X"] @ kc_w, ids)[1]
        r["turns"] = len(ids)
        r["games"] = len({T[i]["game"] for i in ids})
        own[part] = r
    out["builder pooled pairwise (outer held out)"] = own
    vk = F._val_mse(np.array(D["kc"]["coef"], float))
    out["val_mse"] = {"cand-kc": round(vk, 6), "outer folds": {k: v["val_mse"] for k, v in out["outer"].items()}}
    # the final model
    from svsim.learn.model import LinearValue
    dst = Path(args.out_root) / "cand-sp-ramp-ramp"
    dst.mkdir(parents=True, exist_ok=True)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()   # noqa: E731
    vf = F._val_mse(w_final)
    info = {"moment": "ended", "contrast": True, "extras": ["kclock"], "preference": "Salem's turn ends",
            "lambda": lam_all, "lambdas": list(F.LAMBDAS), "lambda_rule": "4 folds over all games by id, highest "
            "pairwise vs the installed 1043's top 8, ties smaller (analysis line c8a04a0)", "inner_pairwise": acc_all,
            "mu": F.MU, "l2": F.L2, "lr": F.LR, "iters": F.ITERS, "start": "cand-kc-ramp-ramp",
            "turns": sha(args.turns), "labels": sha(args.labels), "ramp_turns": len(D["P"]),
            "games": len(games), "val_mse_final": round(vf, 6), "seconds": round(time.time() - t0)}
    LinearValue([float(v) for v in w_final], D["kc"]["mean"], D["kc"]["std"], False, info, version=2,
                extras=("kclock",)).save(dst / "ramp-ramp-ended.json")
    shutil.copy(F.KC.parent / "ramp-ramp-act.json", dst / "ramp-ramp-act.json")
    out["final"] = {"lambda": lam_all, "inner_pairwise": acc_all, "val_mse": round(vf, 6),
                    "val_mse_ratio_vs_cand-kc": round(vf / vk, 4), "sha256": sha(dst / "ramp-ramp-ended.json"),
                    "weights": w_final.tolist()}
    out["outer_weights"] = {k: w.tolist() for k, w in w_outer.items()}
    out["seconds"] = round(time.time() - t0)
    Path(args.out_json).write_text(json.dumps(out, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k not in ("outer_weights",)} | {"final": {
        k: v for k, v in out["final"].items() if k != "weights"}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
